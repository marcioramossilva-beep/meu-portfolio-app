import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px # A novidade para gráficos bonitos

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Investidor Pro", layout="wide", page_icon="💎")

# CSS Personalizado para dar ar de "App Nativo"
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    [data-testid="stMetricValue"] {
        font-size: 26px;
        color: #4CAF50; /* Verde Dólar */
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }
</style>
""", unsafe_allow_html=True)

st.title("💎 Dashboard Patrimonial")
st.caption("Visão estratégica de longo prazo")

# --- 1. DADOS (Mantendo a lógica robusta) ---
portfolio_config = {
    "WEGE3.SA": {"qtde": 25,  "meta": 0.075, "pm": 40.67},
    "PRIO3.SA": {"qtde": 10,  "meta": 0.05,  "pm": 37.32},
    "ITSA4.SA": {"qtde": 100, "meta": 0.05,  "pm": 10.64},
    "TAEE3.SA": {"qtde": 100, "meta": 0.05,  "pm": 11.23},
    "CMIG4.SA": {"qtde": 100, "meta": 0.05,  "pm": 10.60},
    "VIVT3.SA": {"qtde": 33,  "meta": 0.025, "pm": 31.28},
    "VGT":      {"qtde": 1.0007, "meta": 0.17, "pm": 665.54},
    "VT":       {"qtde": 5,      "meta": 0.17, "pm": 126.96},
    "IAU":      {"qtde": 2.9999, "meta": 0.06, "pm": 62.85},
    "BTC-USD":  {"qtde": 0,     "meta": 0.05, "pm": 0.00},
}

META_RENDA_FIXA = 0.25 
SALDO_RENDA_FIXA_ATUAL = 1000.00

# Cache para performance
@st.cache_data(ttl=300)
def get_data():
    tickers = list(portfolio_config.keys())
    try:
        dados = yf.download(tickers, period="1d", progress=False)
        prices = dados['Close'].iloc[-1] if 'Close' in dados else dados.iloc[-1]
        
        usd_raw = yf.download("BRL=X", period="1d", progress=False)
        usd_val = usd_raw['Close'].iloc[-1] if 'Close' in usd_raw else usd_raw.iloc[-1]
        
        # Tratamento seguro de float
        if isinstance(usd_val, (pd.Series, pd.DataFrame)):
            usd_brl = float(usd_val.values.flatten()[0])
        else:
            usd_brl = float(usd_val)
            
        return prices, usd_brl
    except Exception as e:
        return None, 5.80

with st.spinner('Atualizando mercado...'):
    prices, usd_brl = get_data()

# Processamento dos Dados
data = []
total_patrimonio = SALDO_RENDA_FIXA_ATUAL
custo_total = SALDO_RENDA_FIXA_ATUAL

if prices is not None:
    for ticker, info in portfolio_config.items():
        try:
            # Busca Preço Seguro
            if ticker in prices.index:
                val_raw = prices[ticker]
                price = float(val_raw.values.flatten()[0]) if isinstance(val_raw, (pd.Series, pd.DataFrame)) else float(val_raw)
            else:
                continue

            qtde = info['qtde']
            pm = info['pm']
            is_br = ticker.endswith(".SA")
            fator = 1 if is_br else usd_brl
            cat = "🇧🇷 Brasil" if is_br else "🇺🇸 Exterior"
            
            # Valores
            total = price * qtde * fator
            custo = pm * qtde * fator
            lucro = total - custo
            rent = (lucro/custo)*100 if custo > 0 else 0
            
            total_patrimonio += total
            custo_total += custo
            
            data.append({
                "Ativo": ticker, "Categoria": cat, "Total R$": total, 
                "Lucro R$": lucro, "Rentab %": rent, "Meta": info['meta']
            })
        except: pass

# Adiciona RF
data.append({
    "Ativo": "🏛️ Renda Fixa", "Categoria": "🛡️ Caixa", "Total R$": SALDO_RENDA_FIXA_ATUAL,
    "Lucro R$": 0, "Rentab %": 0, "Meta": META_RENDA_FIXA
})

df = pd.DataFrame(data)

# --- 2. DASHBOARD EXECUTIVO (KPIs) ---
lucro_abs = total_patrimonio - custo_total
rent_abs = (lucro_abs / custo_total * 100) if custo_total > 0 else 0

# Layout de Colunas Estilo "Big Numbers"
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Patrimônio Total", f"R$ {total_patrimonio:,.2f}")
c2.metric("📈 Rentabilidade Carteira", f"{rent_abs:.2f}%", delta=f"R$ {lucro_abs:,.2f}")
c3.metric("🇺🇸 Dólar Hoje", f"R$ {usd_brl:.2f}")
c4.metric("🛡️ Posição Segura (RF)", f"R$ {SALDO_RENDA_FIXA_ATUAL:,.2f}")

st.divider()

# --- 3. GRÁFICOS INTERATIVOS (PLOTLY) ---
if not df.empty:
    col_graf1, col_graf2 = st.columns([1, 1])

    with col_graf1:
        st.subheader("🍕 Alocação Atual")
        # Gráfico de Rosca (Donut Chart)
        fig_pie = px.pie(
            df, 
            values='Total R$', 
            names='Categoria', 
            hole=0.4, # Faz virar uma rosca
            color_discrete_sequence=px.colors.qualitative.Pastel # Cores elegantes
        )
        fig_pie.update_layout(showlegend=True, height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_graf2:
        st.subheader("📊 Performance por Ativo")
        # Gráfico de Barras Colorido por Lucro/Prejuízo
        df['Cor'] = df['Lucro R$'].apply(lambda x: 'Lucro' if x >= 0 else 'Prejuízo')
        fig_bar = px.bar(
            df[df['Ativo'] != "🏛️ Renda Fixa"], # Remove RF do gráfico de volatilidade
            x='Ativo', 
            y='Rentab %',
            color='Cor',
            color_discrete_map={'Lucro': '#00CC96', 'Prejuízo': '#EF553B'},
            text_auto='.1f'
        )
        fig_bar.update_layout(showlegend=False, height=350, yaxis_title="Rentabilidade (%)")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- 4. TABELA ANALÍTICA (EXPANSÍVEL) ---
with st.expander("🔎 Ver Tabela Detalhada de Ativos", expanded=False):
    st.dataframe(
        df[['Ativo', 'Categoria', 'Total R$', 'Lucro R$', 'Rentab %', 'Meta']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total R$": st.column_config.NumberColumn(format="R$ %.2f"),
            "Lucro R$": st.column_config.NumberColumn(format="R$ %.2f"),
            "Rentab %": st.column_config.NumberColumn(format="%.2f %%"),
            "Meta": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=0.3)
        }
    )

# --- 5. ROBÔ DE REBALANCEAMENTO ---
st.markdown("---")
st.subheader("⚖️ Assistente de Aporte Inteligente")

col_input, col_rec = st.columns([1, 3])
with col_input:
    novo_aporte = st.number_input("Valor disponível (R$)", value=1000.0, step=100.0)

with col_rec:
    meta_total = total_patrimonio + novo_aporte
    df['Meta R$'] = meta_total * df['Meta']
    df['Falta'] = df['Meta R$'] - df['Total R$']
    
    # Filtra e ordena
    sugestao = df[df['Falta'] > 1].sort_values('Falta', ascending=False).head(3)
    
    if not sugestao.empty:
        # Mostra cards horizontais
        for i, row in sugestao.iterrows():
            st.info(f"👉 **Prioridade {i+1}:** Comprar **{row['Ativo']}** (Destinar: R$ {row['Falta']:,.2f})")
    else:
        st.success("✅ Sua carteira está perfeitamente balanceada!")