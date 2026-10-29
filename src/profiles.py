"""Catálogo de perfis de investimento e configuração efetiva por execução.

Os perfis são declarativos e imutáveis. Cada execução recebe uma cópia
independente, evitando mutar Config.WEIGHTS_STOCKS / INDICATOR_CAPS /
MOMENTUM_WEIGHT durante a renderização da UI.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from config import Config


PROFILES: dict[str, dict[str, Any]] = {
    "Conservador": {
        "description": (
            "Prioriza qualidade, rentabilidade, liquidez e menor endividamento. "
            "Reduz exposição a crescimento e momentum."
        ),
        "weights": {
            "cagr_lucros_5_anos": {"weight": 0.05, "normalization": "default"},
            "cagr_receitas_5_anos": {"weight": 0.05, "normalization": "default"},
            "m_líquida": {"weight": 0.10, "normalization": "default"},
            "roe": {"weight": 0.14, "normalization": "default"},
            "roic": {"weight": 0.16, "normalization": "default"},
            "lpa": {"weight": 0.04, "normalization": "default"},
            "dív_líquida_ebitda": {"weight": 0.12, "normalization": "inverter"},
            "passivos_ativos": {"weight": 0.08, "normalization": "inverter"},
            "liq_corrente": {"weight": 0.08, "normalization": "default"},
            "p_l": {"weight": 0.08, "normalization": "inverter_zero"},
            "p_vp": {"weight": 0.06, "normalization": "inverter_one"},
            "dy": {"weight": 0.04, "normalization": "default"},
        },
        "momentum_weight": 0.0,
        "indicator_caps": deepcopy(Config.INDICATOR_CAPS),
        "score_general_weight": 0.55,
        "score_sector_weight": 0.45,
    },
    "Equilibrado": {
        "description": (
            "Combina qualidade, crescimento, valuation e dividendos. "
            "Espelha os pesos padrão atuais do projeto."
        ),
        "weights": deepcopy(Config.WEIGHTS_STOCKS),
        "momentum_weight": Config.MOMENTUM_WEIGHT,
        "indicator_caps": deepcopy(Config.INDICATOR_CAPS),
        "score_general_weight": 0.55,
        "score_sector_weight": 0.45,
    },
    "Crescimento": {
        "description": (
            "Prioriza crescimento de lucros/receitas, rentabilidade e momentum. "
            "Aceita maior volatilidade."
        ),
        "weights": {
            "cagr_lucros_5_anos": {"weight": 0.22, "normalization": "default"},
            "cagr_receitas_5_anos": {"weight": 0.15, "normalization": "default"},
            "m_líquida": {"weight": 0.06, "normalization": "default"},
            "roe": {"weight": 0.12, "normalization": "default"},
            "roic": {"weight": 0.12, "normalization": "default"},
            "lpa": {"weight": 0.04, "normalization": "default"},
            "dív_líquida_ebitda": {"weight": 0.05, "normalization": "inverter"},
            "passivos_ativos": {"weight": 0.03, "normalization": "inverter"},
            "liq_corrente": {"weight": 0.03, "normalization": "default"},
            "p_l": {"weight": 0.07, "normalization": "inverter_zero"},
            "p_vp": {"weight": 0.07, "normalization": "inverter_one"},
            "dy": {"weight": 0.04, "normalization": "default"},
        },
        "momentum_weight": 0.15,
        "indicator_caps": deepcopy(Config.INDICATOR_CAPS),
        "score_general_weight": 0.55,
        "score_sector_weight": 0.45,
    },
    "Dividendos/Value": {
        "description": (
            "Prioriza dividend yield e valuation (P/L, P/VP). "
            "Atenção: DY alto isoladamente não indica qualidade."
        ),
        "weights": {
            "cagr_lucros_5_anos": {"weight": 0.06, "normalization": "default"},
            "cagr_receitas_5_anos": {"weight": 0.05, "normalization": "default"},
            "m_líquida": {"weight": 0.08, "normalization": "default"},
            "roe": {"weight": 0.10, "normalization": "default"},
            "roic": {"weight": 0.10, "normalization": "default"},
            "lpa": {"weight": 0.04, "normalization": "default"},
            "dív_líquida_ebitda": {"weight": 0.08, "normalization": "inverter"},
            "passivos_ativos": {"weight": 0.05, "normalization": "inverter"},
            "liq_corrente": {"weight": 0.05, "normalization": "default"},
            "p_l": {"weight": 0.14, "normalization": "inverter_zero"},
            "p_vp": {"weight": 0.13, "normalization": "inverter_one"},
            "dy": {"weight": 0.12, "normalization": "default"},
        },
        "momentum_weight": 0.05,
        "indicator_caps": deepcopy(Config.INDICATOR_CAPS),
        "score_general_weight": 0.55,
        "score_sector_weight": 0.45,
    },
}


@dataclass
class AnalysisConfig:
    profile_name: str
    weights: dict[str, dict[str, Any]]
    indicator_caps: dict[str, float]
    momentum_weight: float
    temporal_windows: list[int]
    winsor_limits: tuple[float, float]
    score_general_weight: float
    score_sector_weight: float
    outlier_factor: float = 4.5


def list_profiles() -> list[str]:
    return list(PROFILES.keys())


def profile_description(name: str) -> str:
    if name not in PROFILES:
        raise ValueError(f"Perfil desconhecido: {name}")
    return PROFILES[name]["description"]


def build_config(
    profile_name: str,
    *,
    temporal_windows: list[int] | None = None,
    winsor_limits: tuple[float, float] | None = None,
    weights_override: dict[str, dict[str, Any]] | None = None,
    caps_override: dict[str, float] | None = None,
    momentum_override: float | None = None,
) -> AnalysisConfig:
    if profile_name not in PROFILES:
        raise ValueError(f"Perfil desconhecido: {profile_name}")
    base = PROFILES[profile_name]

    weights = deepcopy(weights_override) if weights_override is not None else deepcopy(base["weights"])
    caps = deepcopy(caps_override) if caps_override is not None else deepcopy(base["indicator_caps"])
    momentum = base["momentum_weight"] if momentum_override is None else momentum_override

    wins = winsor_limits if winsor_limits is not None else (0.01, 0.99)
    wins = (float(wins[0]), float(wins[1]))

    tw = temporal_windows if temporal_windows is not None else [30, 90, 180]
    tw = [int(x) for x in tw]

    cfg = AnalysisConfig(
        profile_name=profile_name,
        weights=weights,
        indicator_caps=caps,
        momentum_weight=float(momentum),
        temporal_windows=tw,
        winsor_limits=wins,
        score_general_weight=float(base["score_general_weight"]),
        score_sector_weight=float(base["score_sector_weight"]),
    )
    validate_config(cfg)
    return cfg


def validate_config(cfg: AnalysisConfig) -> None:
    if not cfg.weights:
        raise ValueError("Pesos não podem estar vazios.")

    total = 0.0
    for indicator, meta in cfg.weights.items():
        if "weight" not in meta:
            raise ValueError(f"Indicador {indicator} sem 'weight'.")
        w = float(meta["weight"])
        if w < 0:
            raise ValueError(f"Peso negativo em {indicator}: {w}")
        if "normalization" not in meta:
            raise ValueError(f"Indicador {indicator} sem 'normalization'.")
        total += w

    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Soma dos pesos = {total:.6f}; esperado 1.0")

    if len(cfg.temporal_windows) != 3:
        raise ValueError("temporal_windows deve ter 3 janelas (curta, média, longa).")
    if not (cfg.temporal_windows[0] < cfg.temporal_windows[1] < cfg.temporal_windows[2]):
        raise ValueError(
            f"Janelas inválidas (curta < média < longa): {cfg.temporal_windows}"
        )

    lo, hi = cfg.winsor_limits
    if not (0.0 <= lo < hi <= 1.0):
        raise ValueError(f"winsor_limits inválidos: ({lo}, {hi})")

    if cfg.momentum_weight < 0 or cfg.momentum_weight > 1:
        raise ValueError(f"momentum_weight fora de [0,1]: {cfg.momentum_weight}")


def weights_total(weights: dict[str, dict[str, Any]]) -> float:
    return sum(float(m["weight"]) for m in weights.values())
