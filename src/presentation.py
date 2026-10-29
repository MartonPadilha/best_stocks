"""Catálogo de apresentação: labels, categorias e tooltips para a UI.

Somente apresentação — o domínio continua usando os nomes técnicos.
"""

from __future__ import annotations

INDICATOR_CATEGORIES = {
    "Crescimento": ["cagr_lucros_5_anos", "cagr_receitas_5_anos"],
    "Rentabilidade": ["m_líquida", "roe", "roic", "lpa"],
    "Endividamento": ["dív_líquida_ebitda", "passivos_ativos"],
    "Liquidez": ["liq_corrente"],
    "Valuation": ["p_l", "p_vp"],
    "Dividendos": ["dy"],
}

INDICATOR_LABELS = {
    "cagr_lucros_5_anos": "CAGR de Lucros (5 anos)",
    "cagr_receitas_5_anos": "CAGR de Receitas (5 anos)",
    "m_líquida": "Margem Líquida",
    "roe": "ROE",
    "roic": "ROIC",
    "lpa": "Lucro por Ação (LPA)",
    "dív_líquida_ebitda": "Dív. Líquida / EBITDA",
    "passivos_ativos": "Passivos / Ativos",
    "liq_corrente": "Liquidez Corrente",
    "p_l": "Preço / Lucro (P/L)",
    "p_vp": "Preço / Valor Patrimonial (P/VP)",
    "dy": "Dividend Yield (DY)",
    "momentum": "Momentum de Preço (90 dias)",
}

INDICATOR_TOOLTIPS = {
    "cagr_lucros_5_anos": "Crescimento anual composto do lucro nos últimos 5 anos. Maior valor recebe maior pontuação na normalização atual.",
    "cagr_receitas_5_anos": "Crescimento anual composto da receita nos últimos 5 anos. Maior valor recebe maior pontuação.",
    "m_líquida": "Margem líquida. Maior valor recebe maior pontuação. Comparação relativa à amostra analisada.",
    "roe": "Retorno sobre o patrimônio. Maior valor recebe maior pontuação.",
    "roic": "Retorno sobre o capital investido. Maior valor recebe maior pontuação.",
    "lpa": "Lucro por ação. Maior valor recebe maior pontuação.",
    "dív_líquida_ebitda": "Dívida líquida sobre EBITDA. Menor valor recebe maior pontuação (normalização invertida).",
    "passivos_ativos": "Passivos sobre ativos. Menor valor recebe maior pontuação (normalização invertida).",
    "liq_corrente": "Liquidez corrente. Maior valor recebe maior pontuação.",
    "p_l": "Preço sobre lucro. Menor P/L positivo tende a receber maior pontuação (normalização invertida). Valores ausentes ou não positivos recebem zero.",
    "p_vp": "Preço sobre valor patrimonial. Quanto mais próximo de 1, maior a pontuação (normalização invertida em torno de 1).",
    "dy": "Dividend Yield. Maior valor recebe maior pontuação. DY alto isoladamente não indica qualidade.",
    "momentum": "Variação de preço dos últimos 90 dias via Yahoo Finance. Não é métrica fundamentalista. Valores indisponíveis recebem tratamento padrão.",
}

NORMALIZATION_LABELS = {
    "default": "Maior é melhor",
    "inverter": "Menor é melhor",
    "inverter_zero": "Menor positivo é melhor",
    "inverter_one": "Mais próximo de 1 é melhor",
}


def category_of(indicator: str) -> str:
    for cat, items in INDICATOR_CATEGORIES.items():
        if indicator in items:
            return cat
    return "Outros"


def label_of(indicator: str) -> str:
    return INDICATOR_LABELS.get(indicator, indicator)


def tooltip_of(indicator: str) -> str:
    return INDICATOR_TOOLTIPS.get(indicator, "")


def normalization_label(norm: str) -> str:
    return NORMALIZATION_LABELS.get(norm, norm)


def grouped_indicators(weights: dict) -> dict[str, list[str]]:
    """Retorna os indicadores de `weights` agrupados por categoria, na ordem do catálogo."""
    grouped: dict[str, list[str]] = {}
    for cat in INDICATOR_CATEGORIES:
        members = [ind for ind in INDICATOR_CATEGORIES[cat] if ind in weights]
        if members:
            grouped[cat] = members
    others = [ind for ind in weights if category_of(ind) == "Outros"]
    if others:
        grouped["Outros"] = others
    return grouped
