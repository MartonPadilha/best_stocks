import pandas as pd
import numpy as np
import streamlit as st
from database import Database
from config import Config
from analysis import Calcs
from stock_app import analysis_tickers, analysis_rank, show_dividends, show_news, plot_rank
from fii_app import show_fiis, filter_fiis, FII_NOTICE
from profiles import (
    PROFILES, list_profiles, profile_description, build_config,
    weights_total, AnalysisConfig,
)
from presentation import (
    grouped_indicators, label_of, tooltip_of, normalization_label, category_of,
)
import warnings
import os
import sys
from copy import deepcopy

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.append(src_path)

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=pd.errors.SettingWithCopyWarning)

st.set_page_config(layout='wide', page_title='Best Stocks')


##################### HELPERS #########################

def _format_pct(v):
    try:
        return f"{float(v) * 100:.1f}%" if pd.notna(v) else "—"
    except Exception:
        return "—"


def _format_num(v, digits=2):
    try:
        return f"{float(v):.{digits}f}" if pd.notna(v) else "—"
    except Exception:
        return "—"


def _latest_reference_date(df):
    if df is None or df.empty or 'reference_date' not in df.columns:
        return None
    try:
        return pd.to_datetime(df['reference_date']).max()
    except Exception:
        return None


def _ticker_options(df_ranked):
    if df_ranked is None or df_ranked.empty:
        return []
    return df_ranked['ticker'].tolist()


def _build_explanation(df_ranked, cfg: AnalysisConfig, selected_ticker):
    """Monta DataFrame de explicação por indicador para o ticker selecionado."""
    if df_ranked is None or df_ranked.empty or not selected_ticker:
        return pd.DataFrame()
    row = df_ranked[df_ranked['ticker'] == selected_ticker]
    if row.empty:
        return pd.DataFrame()

    rows = []
    for ind, meta in cfg.weights.items():
        w = float(meta['weight'])
        norm = meta['normalization']
        original = row[ind].iloc[0] if ind in row.columns else np.nan
        rows.append({
            'Indicador': label_of(ind),
            'Categoria': category_of(ind),
            'Valor original': _format_num(original),
            'Peso': _format_pct(w),
            'Normalização': normalization_label(norm),
            'Tooltip': tooltip_of(ind),
        })
    return pd.DataFrame(rows)


##################### HEADER #########################
st.title('Best Stocks')
st.caption('Análise quantitativa multifatorial — não é recomendação de investimento.')

asset_choice = st.radio('Tipo de investimento:', ['Ações', 'FIIs'], horizontal=True)
_type = 'stock' if asset_choice == 'Ações' else 'fii'


##################### SIDEBAR ########################
st.sidebar.markdown("---")
st.sidebar.header("Universo")

sector_filter = None
ticker_filter = None
period_choice = '90d'

if _type == 'stock':
    try:
        df_universe = Database('stock_data', Config.DATABASE).view()
    except Exception:
        df_universe = pd.DataFrame()

    sectors = sorted(df_universe['sector'].dropna().unique().tolist()) if df_universe is not None and not df_universe.empty and 'sector' in df_universe.columns else []
    sector_filter = st.sidebar.selectbox("Setor", ["Todos"] + sectors) if sectors else None
    if sector_filter == "Todos":
        sector_filter = None

    ticker_filter = st.sidebar.text_input("Filtrar ticker (contém)", "")
    if not ticker_filter.strip():
        ticker_filter = None

    st.sidebar.markdown("---")
    st.sidebar.header("Perfil")
    profile_name = st.sidebar.selectbox("Estratégia", list_profiles())
    st.sidebar.caption(profile_description(profile_name))

    if 'custom_weights' not in st.session_state or st.session_state.get('profile_name') != profile_name:
        st.session_state['profile_name'] = profile_name
        st.session_state['custom_weights'] = deepcopy(PROFILES[profile_name]['weights'])

    with st.sidebar.expander("Personalizar pesos", expanded=False):
        custom_weights = st.session_state['custom_weights']
        grouped = grouped_indicators(custom_weights)
        for cat, inds in grouped.items():
            st.markdown(f"**{cat}**")
            for ind in inds:
                cur = float(custom_weights[ind]['weight'])
                new_val = st.number_input(
                    f"{label_of(ind)}",
                    min_value=0.0, max_value=1.0, value=cur, step=0.01,
                    key=f"w_{ind}", help=tooltip_of(ind),
                )
                custom_weights[ind]['weight'] = new_val
        total = weights_total(custom_weights)
        st.metric("Soma dos pesos", _format_pct(total))
        if abs(total - 1.0) > 1e-6:
            st.error(f"Soma = {total:.4f}. Ajuste para 1.0 antes de executar.")
        if st.button("Restaurar padrão do perfil"):
            st.session_state['custom_weights'] = deepcopy(PROFILES[profile_name]['weights'])
            st.rerun()

    with st.sidebar.expander("Configurações avançadas", expanded=False):
        win_30 = st.number_input("Janela curta (dias)", 7, 60, 30, step=1)
        win_90 = st.number_input("Janela média (dias)", 30, 180, 90, step=1)
        win_180 = st.number_input("Janela longa (dias)", 90, 365, 180, step=1)
        winsor_lo = st.slider("Winsorize lower (%)", 0.0, 5.0, 1.0) / 100.0
        winsor_hi = st.slider("Winsorize upper (%)", 95.0, 100.0, 99.0) / 100.0
        cap_dy = st.number_input("Cap DY (%)", 5.0, 30.0, float(Config.INDICATOR_CAPS.get('dy', 15.0)), 1.0)
        cap_cagr = st.number_input("Cap CAGR (%)", 20.0, 100.0, float(Config.INDICATOR_CAPS.get('cagr_lucros_5_anos', 50.0)), 5.0)
        momentum_w = st.slider("Momentum (%)", 0, 30, int(PROFILES[profile_name]['momentum_weight'] * 100), 1) / 100.0

    period_options = {'7 dias': '7d', '30 dias': '30d', '90 dias': '90d', '1 ano': '1y', 'Todas as datas': 'all'}
    period_label = st.sidebar.selectbox("Período do gráfico de evolução", list(period_options.keys()), index=2)
    period_choice = period_options[period_label]

    run_analysis = st.sidebar.button("Executar análise", type="primary")

else:
    st.sidebar.info("FIIs: apenas consulta de dados.")
    run_analysis = False


##################### BODY ###########################

if _type == 'fii':
    st.header("Dados de FIIs")
    st.warning(FII_NOTICE)
    df_fiis = show_fiis()
    fii_ticker = st.text_input("Filtrar ticker (contém)", "")
    df_fiis = filter_fiis(df_fiis, fii_ticker.strip() or None)
    if df_fiis is None or df_fiis.empty:
        st.info("Nenhum dado de FII disponível na base.")
    else:
        st.dataframe(df_fiis, use_container_width=True)
    st.stop()


# ---- Stock flow ----
if not run_analysis and 'last_result' not in st.session_state:
    st.info("Ajuste o perfil e clique em **Executar análise** para gerar o ranking.")
    st.stop()

if run_analysis:
    try:
        caps_override = {
            'dy': cap_dy,
            'cagr_lucros_5_anos': cap_cagr,
            'cagr_receitas_5_anos': cap_cagr,
        }
        cfg = build_config(
            profile_name,
            temporal_windows=[win_30, win_90, win_180],
            winsor_limits=(winsor_lo, winsor_hi),
            weights_override=deepcopy(st.session_state['custom_weights']),
            caps_override=caps_override,
            momentum_override=momentum_w,
        )
        calcs = Calcs(
            deepcopy(cfg.weights),
            temporal_windows=cfg.temporal_windows,
            winsor_limits=cfg.winsor_limits,
        )
        with st.spinner("Calculando ranking..."):
            df_ranked, df_outliers = analysis_tickers(_type, calcs, analysis_config=cfg)
        df_div = show_dividends()
        df_news = show_news()
        df_graph = analysis_rank(_type, calcs, period=period_choice, analysis_config=cfg)

        st.session_state['last_result'] = {
            'cfg': cfg,
            'df_ranked': df_ranked,
            'df_outliers': df_outliers,
            'df_div': df_div,
            'df_news': df_news,
            'df_graph': df_graph,
            'asset_choice': asset_choice,
        }
    except ValueError as e:
        st.error(f"Configuração inválida: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao executar análise: {e}")
        st.stop()

result = st.session_state.get('last_result')
if not result or result.get('asset_choice') != asset_choice:
    st.info("Ajuste o perfil e clique em **Executar análise** para gerar o ranking.")
    st.stop()

cfg: AnalysisConfig = result['cfg']
df_ranked = result['df_ranked']
df_outliers = result['df_outliers']
df_div = result['df_div']
df_news = result['df_news']
df_graph = result['df_graph']

# Apply sector/ticker filters for display
df_display = df_ranked
if sector_filter and 'sector' in df_display.columns:
    df_display = df_display[df_display['sector'] == sector_filter]
if ticker_filter and 'ticker' in df_display.columns:
    df_display = df_display[df_display['ticker'].astype(str).str.contains(ticker_filter, case=False, na=False)]

latest = _latest_reference_date(df_ranked)

##################### TABS ###########################
tab_overview, tab_ranking, tab_detail, tab_news, tab_div, tab_outliers, tab_evo = st.tabs([
    "Visão geral", "Ranking", "Detalhe do ativo", "Notícias", "Dividendos", "Outliers", "Evolução",
])

with tab_overview:
    st.header("Visão geral")
    cols = st.columns(4)
    cols[0].metric("Ativos analisados", len(df_ranked))
    cols[1].metric("Outliers", len(df_outliers))
    cols[2].metric("Data de referência", latest.strftime('%d/%m/%Y') if latest else "—")
    cols[3].metric("Perfil", cfg.profile_name)

    if not df_ranked.empty:
        leader = df_ranked.iloc[0]
        st.metric("Líder do ranking", leader.get('ticker', '—'), _format_num(leader.get('score_final'), 4))

    if 'sector' in df_ranked.columns and not df_ranked.empty:
        st.subheader("Distribuição por setor")
        st.dataframe(df_ranked['sector'].value_counts().rename_axis('Setor').reset_index(name='Ativos'), use_container_width=True)

    st.caption(f"Momentum: {'ativo' if cfg.momentum_weight > 0 else 'desativado'}. "
               f"Pesos geral/setorial: {_format_pct(cfg.score_general_weight)} / {_format_pct(cfg.score_sector_weight)}.")

with tab_ranking:
    st.header("Ranking")
    if df_display.empty:
        st.info("Nenhum ativo corresponde aos filtros.")
    else:
        rank_cols = [c for c in ['ticker', 'sector', 'score_final', 'score_general', 'score_sector', 'momentum', 'reference_date'] if c in df_display.columns]
        df_view = df_display[rank_cols].copy()
        df_view.insert(0, 'Posição', range(1, len(df_view) + 1))
        st.dataframe(df_view, use_container_width=True, hide_index=True)

with tab_detail:
    st.header("Detalhe do ativo")
    tickers = _ticker_options(df_display)
    if not tickers:
        st.info("Nenhum ativo disponível.")
    else:
        selected = st.selectbox("Ticker", tickers)
        row = df_display[df_display['ticker'] == selected]
        if not row.empty:
            r = row.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Score final", _format_num(r.get('score_final'), 4))
            c2.metric("Score geral", _format_num(r.get('score_general'), 4))
            c3.metric("Score setorial", _format_num(r.get('score_sector'), 4))
            if 'momentum' in r.index:
                st.metric("Momentum", _format_num(r.get('momentum'), 4))
            st.subheader("Componentes do score")
            expl = _build_explanation(df_display, cfg, selected)
            st.dataframe(expl, use_container_width=True, hide_index=True)
            st.caption("Score é relativo à amostra analisada. Valores ausentes podem receber zero na normalização.")

with tab_news:
    st.header("Notícias")
    if df_news is None or df_news.empty:
        st.info("Nenhuma notícia disponível na base.")
    else:
        if tickers:
            sel_news = st.selectbox("Ticker", ["Todos"] + tickers, key="news_ticker")
            df_n = df_news if sel_news == "Todos" else df_news[df_news['ticker'] == sel_news]
        else:
            df_n = df_news
        st.dataframe(df_n, use_container_width=True, hide_index=True)

with tab_div:
    st.header("Dividendos")
    if df_div is None or df_div.empty:
        st.info("Nenhum dividendo disponível na base.")
    else:
        if tickers:
            sel_div = st.selectbox("Ticker", ["Todos"] + tickers, key="div_ticker")
            df_d = df_div if sel_div == "Todos" else df_div[df_div['ticker'] == sel_div]
        else:
            df_d = df_div
        st.dataframe(df_d, use_container_width=True, hide_index=True)

with tab_outliers:
    st.header("Outliers")
    st.caption("Outlier estatístico não significa empresa ruim — pode ser uma característica real do ativo.")
    if df_outliers is None or df_outliers.empty:
        st.info("Nenhum outlier identificado.")
    else:
        st.dataframe(df_outliers, use_container_width=True, hide_index=True)

with tab_evo:
    st.header("Evolução do ranking")
    st.caption(f"Período: {period_label}. Ranking médio por ticker, top 10.")
    if df_graph is None or df_graph.empty:
        st.info("Dados históricos insuficientes para o período selecionado.")
    else:
        st.plotly_chart(plot_rank(df_graph, 'date', 'rank'), use_container_width=True)
