# Importando bibliotecas necessárias
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
# Configurações iniciais da página do Streamlit
st.set_page_config(page_title="Paramount Têxteis - Santa Isabel", layout="centered")

# Título do app
st.title("Produção - Paramount SI")

# Carrega os dados da planilha Excel, usando cache para melhorar performance
@st.cache_data
def carregar_dados():
    caminho = os.path.join(os.path.dirname(__file__), "Power Bi - PLANTA DE PRODUÇÃO (FIOS  INDUSTRIAIS).xlsx")
    df = pd.read_excel(caminho)
    df = df[["PRODUTO", "OPERAÇÃO", "N° FUSOS", "KG/MH"]].dropna()
    return df

# Carrega os dados da planilha
dados = carregar_dados()

# Função para tratar valores numéricos que vêm como string com vírgula
def parse_float(valor):
    if isinstance(valor, str):
        return float(valor.replace(",", "."))
    return float(valor)

# Input do usuário: número máximo de dias úteis disponíveis
diasMax = st.number_input("📆 Max Dias Úteis", min_value=1, max_value=31, step=1)

# Criação de duas colunas para entrada dos dados dos dois produtos
col1, col2 = st.columns(2)

# --- Entradas para o Produto 1 ---
with col1:
    st.subheader("🧵 Produto 1")
    produto1 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto1")
    meta1 = st.number_input("🎯 Meta (kg)", min_value=1, step=1000, key="meta1")
    operacoes1 = dados[dados["PRODUTO"] == produto1]["OPERAÇÃO"].unique()
    operacao1 = st.selectbox("⚙️ Operação", sorted(operacoes1), key="operacao1")
    maquinas1 = st.number_input("🏭 Quantidade de máquinas", min_value=1, step=1, key="maquinas1")
    almoco1 = st.radio("🍽️ Pausa para almoço?", ["Sim", "Não"], key="almoco1") == "Sim"
    pico1 = st.radio("📈 Pico no turno B?", ["Sim", "Não"], key="pico1") == "Sim"
    turnos1 = st.multiselect("🕐 Turnos", ["A", "B", "C"], default=["A", "B", "C"], key="turnos1")

# --- Entradas para o Produto 2 ---
with col2:
    st.subheader("🧵 Produto 2")
    produto2 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto2")
    meta2 = st.number_input("🎯 Meta (kg)", min_value=1, step=1000, key="meta2")
    operacoes2 = dados[dados["PRODUTO"] == produto2]["OPERAÇÃO"].unique()
    operacao2 = st.selectbox("⚙️ Operação", sorted(operacoes2), key="operacao2")
    maquinas2 = st.number_input("🏭 Quantidade de máquinas", min_value=1, step=1, key="maquinas2")
    almoco2 = st.radio("🍽️ Pausa para almoço?", ["Sim", "Não"], key="almoco2") == "Sim"
    pico2 = st.radio("📈 Pico no turno B?", ["Sim", "Não"], key="pico2") == "Sim"
    turnos2 = st.multiselect("🕐 Turnos", ["A", "B", "C"], default=["A", "B", "C"], key="turnos2")

# Função para buscar dados da operação de um produto
def get_operacao(produto, operacao):
    filtro = dados[(dados["PRODUTO"] == produto) & (dados["OPERAÇÃO"] == operacao)]
    if filtro.empty:
        return None
    linha = filtro.iloc[0]
    return int(linha["N° FUSOS"]), parse_float(linha["KG/MH"])

# Busca os dados de operação para cada produto
dados1 = get_operacao(produto1, operacao1)
dados2 = get_operacao(produto2, operacao2)

# Validação: se não encontrou os dados, exibe erro
if dados1 is None or dados2 is None:
    st.error("⚠️ Dados insuficientes para simular. Verifique se o produto e operação existem na base.")
    st.stop()

# Extrai os dados de cada operação
fusos_total1, kg_por_hora1 = dados1
fusos_total2, kg_por_hora2 = dados2

# Inputs adicionais sobre eficiência e fusos parados
colf1, colf2 = st.columns(2)

with colf1:
    fusos_parados1 = st.slider(f"🛑 Fusos parados {operacao1} (máx: {fusos_total1})", 0, fusos_total1, step=1, key="fuso1")
    eficiencia_maquina1 = st.slider(f"🛠️ Eficiência Máquina {operacao1} (%)", 0, 100, 100, step=1, key="ef1")

with colf2:
    fusos_parados2 = st.slider(f"🛑 Fusos parados {operacao2} (máx: {fusos_total2})", 0, fusos_total2, step=1, key="fuso2")
    eficiencia_maquina2 = st.slider(f"🛠️ Eficiência Máquina {operacao2} (%)", 0, 100, 100, step=1, key="ef2")

# Função de simulação de produção
def simular(meta, produto, operacao, fusos_total, kg_por_hora, fusos_parados, eficiencia_maquina, maquinas, almoco, pico, turnos_entrada):
    fusos_ativos = fusos_total - fusos_parados
    eficiencia_fusos = fusos_ativos / fusos_total
    eficiencia_maquina = eficiencia_maquina / 100

    if not turnos_entrada:
        return None

    # Simula de 1 até diasMax para encontrar o menor número de dias que atinge a meta
    for dias in range(1, diasMax + 1):
        total_horas = 0
        for t in turnos_entrada:
            h = 8
            if almoco:
                h -= 1
            if t == "B" and pico:
                h -= 3
            total_horas += h
        total_horas *= dias * maquinas
        producao = total_horas * kg_por_hora * eficiencia_fusos * eficiencia_maquina
        if producao >= meta:
            return {
                "dados": pd.DataFrame([{
                    "Produto": produto,
                    "Operação": operacao,
                    "Meta (kg)": meta,
                    "Fusos Parados": fusos_parados,
                    "Máquinas": maquinas,
                    "Eficiência Máquina(%)": eficiencia_maquina * 100,
                    "Almoço": "Sim" if almoco else "Não",
                    "Pico no Turno B": "Sim" if pico else "Não",
                    "Eficiência Fusos(%)": round(eficiencia_fusos * 100, 2),
                    "Turnos Necessários": "".join(turnos_entrada),
                    "Dias Necessários": dias,
                    "Produção Estimada (kg)": round(producao, 2),
                    "Produção Diária Estimada (kg/dia)": round(producao / dias, 2)
                }]),
                "metricas": {
                    "Eficiência Fusos (%)": eficiencia_fusos * 100,
                    "Eficiência Máquina (%)": eficiencia_maquina * 100,
                    "Turnos": "".join(turnos_entrada),
                    "Dias": dias,
                    "Produção (kg)": producao
                }
            }
    return None

# Quando o botão é clicado, realiza a simulação
if st.button("🔍 Calcular Simulações"):
    resultado1 = simular(meta1, produto1, operacao1, fusos_total1, kg_por_hora1, fusos_parados1, eficiencia_maquina1, maquinas1, almoco1, pico1, turnos1)
    resultado2 = simular(meta2, produto2, operacao2, fusos_total2, kg_por_hora2, fusos_parados2, eficiencia_maquina2, maquinas2, almoco2, pico2, turnos2)

    # Calcula produção diária de cada produto
    producao_dia1 = resultado1["metricas"]["Produção (kg)"] / resultado1["metricas"]["Dias"] if resultado1 else 0
    producao_dia2 = resultado2["metricas"]["Produção (kg)"] / resultado2["metricas"]["Dias"] if resultado2 else 0

    # Mostra os resultados na tela em colunas
    colres1, colres2 = st.columns(2)

    if resultado1:
        with colres1:
            st.subheader(f"✅ Resultado: {produto1}")
            for k, v in resultado1["metricas"].items():
                st.metric(k, f"{v:.2f}" if isinstance(v, float) else v)
            st.metric("Produção diária", f"{producao_dia1:,.2f} kg/dia")

    if resultado2:
        with colres2:
            st.subheader(f"✅ Resultado: {produto2}")
            for k, v in resultado2["metricas"].items():
                st.metric(k, f"{v:.2f}" if isinstance(v, float) else v)
            st.metric("Produção diária", f"{producao_dia2:,.2f} kg/dia")

    # Cálculo da produção total e dias totais considerando o número de máquinas
    if operacao1 == operacao2:
        dias_total = (resultado1["metricas"]["Dias"] if resultado1 else 0) + (resultado2["metricas"]["Dias"] if resultado2 else 0)
        producao_total = 0
    else:
        dias_total = max(
            resultado1["metricas"]["Dias"] if resultado1 else 0,
            resultado2["metricas"]["Dias"] if resultado2 else 0
        )
        producao_total = producao_dia1 + producao_dia2

    st.subheader("🔢 Total de Produção Diária(Se a máquina for igual não soma)")
    st.metric("", f"{producao_total:,.2f} kg/dia")

    # Verifica se está dentro do limite de dias úteis
    if dias_total > diasMax:
        st.markdown(
    f"""
    <div style="
        background-color: #f8d7da;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #f5c6cb;
        color: #721c24;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-top: 20px;
    ">
        ⚠️ Limite Excedido: {dias_total} dias (Máximo: {diasMax})
    </div><br>
    """,
    unsafe_allow_html=True
)

    else:
        st.markdown(
    f"""
    <div style="
        background-color: #d4edda;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        color: #155724;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-top: 20px;
    ">
        ✅ Dias Necessários Para Atender o Volume: {dias_total} dias
    </div><br>
    """,
    unsafe_allow_html=True
)


    # Exporta os dados para Excel
    output = io.BytesIO()
    frames = []
    if resultado1:
        frames.append(resultado1["dados"])
    if resultado2:
        frames.append(resultado2["dados"])
    frames.append(pd.DataFrame([{"Produto": "TOTAL", "Dias Necessários": dias_total}]))

    resultado_final = pd.concat(frames, ignore_index=True)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        resultado_final.to_excel(writer, index=False, sheet_name="Simulação Total")

    st.download_button(
        label="📥 Exportar resultados em Excel",
        data=output.getvalue(),
        file_name=f"simulacao_producao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    