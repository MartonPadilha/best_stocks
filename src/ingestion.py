"""Serviço de ingestão: orquestra coletores e persistência.

Pode ser chamado por:
  - GitHub Actions (via CLI: python -m src.ingestion --target all)
  - UI Streamlit (src/pages/db_management.py)
  - Testes (com db_path temporário e coletores mockados)
"""

import argparse
import importlib.util
import logging
import os
import sys
from typing import Iterable, Optional

import pandas as pd

from config import Config
from database import Database

logger = logging.getLogger(__name__)


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ensure_src_on_path() -> None:
    root = _project_root()
    src_dir = os.path.join(root, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    if root not in sys.path:
        sys.path.insert(0, root)


def _load_collector(file_path: str):
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(_project_root(), file_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Coletor não encontrado: {abs_path}")
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "main"):
        raise AttributeError(f"Coletor {module_name} não expõe main()")
    return module


def _resolve_targets(targets: Optional[Iterable[str]]) -> list:
    if not targets:
        return list(Config.TABLES.keys())
    resolved = []
    for t in targets:
        if t not in Config.TABLES:
            raise ValueError(f"Alvo desconhecido: {t}. Disponíveis: {list(Config.TABLES.keys())}")
        resolved.append(t)
    return resolved


def _expand_with_dependencies(targets: list) -> list:
    ordered: list = []
    seen: set = set()

    def visit(name: str):
        if name in seen:
            return
        for dep in Config.TABLES[name].get("depends_on", []):
            visit(dep)
        seen.add(name)
        ordered.append(name)

    for t in targets:
        visit(t)
    return ordered


def _run_single(target: str, db_path: str) -> dict:
    meta = Config.TABLES[target]
    file_path = meta["file"]
    insert_mode = meta["insert"]
    keys = meta.get("keys", [])

    logger.info("Ingestão iniciada: %s (%s)", target, insert_mode)
    module = _load_collector(file_path)
    df = module.main()

    if df is not None and not isinstance(df, pd.DataFrame):
        raise TypeError(f"{target}: coletor retornou {type(df).__name__}, esperado DataFrame")

    db = Database(target, db_path)

    if insert_mode == "append":
        result = db.append_if_new(df, keys)
    elif insert_mode == "overwrite":
        result = db.replace_if_non_empty(df)
    else:
        raise ValueError(f"Modo de insert desconhecido para {target}: {insert_mode}")

    result["target"] = target
    result["status"] = "success" if not result.get("skipped") else "skipped"
    logger.info(
        "Ingestão %s: fetched=%s inserted=%s rejected=%s skipped=%s",
        target, result["fetched_rows"], result["inserted_rows"],
        result["rejected_rows"], result.get("skipped", False),
    )
    return result


def run_ingestion(
    targets: Optional[Iterable[str]] = None,
    db_path: Optional[str] = None,
    fail_fast: bool = True,
) -> dict:
    _ensure_src_on_path()
    resolved_db = db_path or Config.DATABASE
    os.makedirs(os.path.dirname(resolved_db) or ".", exist_ok=True)

    requested = _resolve_targets(targets)
    ordered = _expand_with_dependencies(requested)

    summary = {"db_path": resolved_db, "results": {}, "failed": False, "failed_target": None}
    completed: set = set()

    for target in ordered:
        deps = Config.TABLES[target].get("depends_on", [])
        failed_deps = [d for d in deps if d not in completed]
        if failed_deps:
            logger.warning("Pulando %s: dependências não concluídas: %s", target, failed_deps)
            summary["results"][target] = {
                "target": target,
                "status": "skipped",
                "reason": f"deps_failed: {failed_deps}",
            }
            continue

        try:
            result = _run_single(target, resolved_db)
            summary["results"][target] = result
            completed.add(target)
        except Exception as e:
            logger.error("Falha na ingestão de %s: %s", target, e)
            summary["results"][target] = {
                "target": target,
                "status": "failed",
                "error": str(e),
            }
            summary["failed"] = True
            summary["failed_target"] = target
            if fail_fast:
                for remaining in ordered:
                    if remaining not in completed and remaining != target:
                        summary["results"].setdefault(remaining, {
                            "target": remaining,
                            "status": "skipped",
                            "reason": "fail_fast",
                        })
                break
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Job de ingestão best_stocks")
    parser.add_argument(
        "--target",
        action="append",
        help="Alvo (stock_data, news, dividends, fii_data). Repita para múltiplos. Omitir = all.",
    )
    parser.add_argument("--db-path", default=None, help="Caminho do SQLite (default: Config.DATABASE)")
    parser.add_argument("--no-fail-fast", action="store_true", help="Continua etapas independentes após falha")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    targets = args.target if args.target else None
    summary = run_ingestion(
        targets=targets,
        db_path=args.db_path,
        fail_fast=not args.no_fail_fast,
    )

    print("Resumo da ingestão:")
    for name, res in summary["results"].items():
        print(f"  {name}: {res.get('status')} "
              f"(fetched={res.get('fetched_rows', '-')}, "
              f"inserted={res.get('inserted_rows', '-')}, "
              f"rejected={res.get('rejected_rows', '-')})")

    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
