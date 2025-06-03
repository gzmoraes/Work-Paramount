# Importando bibliotecas necessárias
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

st.set_page_config(page_title="Produção - Paramount SI", layout="wide")

# 🎨 Sidebar personalizada
with st.sidebar: 
    st.subheader("ℹ️ Sobre")
    st.info("App desenvolvido para auxiliar na gestão da produção da unidade de Santa Isabel.")
    st.markdown("Developed by Gustavo Moraes")
    st.markdown(
        """
        <a href="https://www.linkedin.com/in/devgustavomoraes/" target="_blank">
            <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="30">
        </a>
        <a href="https://github.com/gzmoraes" target="_blank">
            <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" width="30">
        </a>
        """,
        unsafe_allow_html=True
    )


st.title("📊 Produção - Paramount SI")

# Carrega os dados da planilha Excel
@st.cache_data
def carregar_dados():
    caminho = os.path.join(os.path.dirname(__file__), "PLANTA_DE_PRODUÇÃO(FIOS_INDUSTRIAIS).xlsx")
    df = pd.read_excel(caminho)
    df = df[["PRODUTO", "OPERAÇÃO", "N° FUSOS", "KG/MH"]].dropna()
    return df

dados = carregar_dados()

# Função para tratar vírgula e ponto
def parse_float(valor):
    if isinstance(valor, str):
        return float(valor.replace(",", "."))
    return float(valor)

# Seleção de quantidade de produtos
qtd_produtos = st.selectbox("🛠️ Quantidade de produtos para comparar", [1, 2, 3])

# Dias úteis
diasMax = st.number_input("📆 Max Dias Úteis", min_value=1, max_value=31, step=1)

# Inputs adicionais globais
st.subheader("⚙️ Ajustes Globais")
col1, col2 = st.columns(2)
with col1:
    absenteismo = st.number_input("❌ Índice de Absenteísmo (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0) / 100
with col2:
    novatos = st.number_input("🧑‍🏭 Percentual de Novatos (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0) / 200  # divide por 2

# Função para inputs de produtos
def input_produto(idx):
    st.subheader(f"🧵 Produto {idx}")
    produto = st.selectbox(f"Item", sorted(dados["PRODUTO"].unique()), key=f"produto{idx}")
    meta = st.number_input(f"🎯 Meta (kg)", min_value=1, step=1000, key=f"meta{idx}")
    operacoes = dados[dados["PRODUTO"] == produto]["OPERAÇÃO"].unique()
    operacao = st.selectbox(f"⚙️ Operação", sorted(operacoes), key=f"operacao{idx}")
    maquinas = st.number_input(f"🏭 Quantidade de máquinas", min_value=1, step=1, key=f"maquinas{idx}")
    almoco = st.radio(f"🍽️ Pausa para almoço?", ["Sim", "Não"], key=f"almoco{idx}") == "Sim"
    pico = st.radio(f"📈 Pico no turno B?", ["Sim", "Não"], key=f"pico{idx}") == "Sim"
    turnos = st.multiselect(f"🕐 Turnos", ["A", "B", "C"], default=["A", "B", "C"], key=f"turnos{idx}")
    return produto, meta, operacao, maquinas, almoco, pico, turnos

# Inputs dos produtos
colunas = st.columns(qtd_produtos)
inputs = []
for i in range(qtd_produtos):
    with colunas[i]:
        entrada = input_produto(i + 1)
        inputs.append(entrada)

# Buscar dados da operação
def get_operacao(produto, operacao):
    filtro = dados[(dados["PRODUTO"] == produto) & (dados["OPERAÇÃO"] == operacao)]
    if filtro.empty:
        return None
    linha = filtro.iloc[0]
    return int(linha["N° FUSOS"]), parse_float(linha["KG/MH"])

# Simulação
def simular(meta, produto, operacao, fusos_total, kg_por_hora, fusos_parados,
            eficiencia_maquina, maquinas, almoco, pico, turnos_entrada,
            absenteismo, novatos):
    
    fusos_ativos = fusos_total - fusos_parados
    eficiencia_fusos = fusos_ativos / fusos_total
    eficiencia_maquina = eficiencia_maquina / 100

    fator_ajuste = (1 - absenteismo) * (1 - novatos)

    if not turnos_entrada:
        return None

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
        producao = total_horas * kg_por_hora * eficiencia_fusos * eficiencia_maquina * fator_ajuste

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

# Inputs de fusos e eficiência
colfusos = st.columns(qtd_produtos)
fusos_parados_list = []
eficiencia_maquina_list = []
dados_operacao = []

for i, entrada in enumerate(inputs):
    produto, meta, operacao, maquinas, almoco, pico, turnos = entrada
    dados_op = get_operacao(produto, operacao)

    if dados_op is None:
        st.error(f"⚠️ Dados insuficientes para {produto} - {operacao}. Verifique na base.")
        st.stop()

    fusos_total, kg_por_hora = dados_op
    dados_operacao.append((fusos_total, kg_por_hora))

    with colfusos[i]:
        fusos_parados = st.number_input(
            f"🛑 Fusos parados {operacao} (máx: {fusos_total})", 0, fusos_total, step=1, key=f"fuso{i}"
        )
        eficiencia_maquina = st.number_input(
            f"🛠️ Eficiência Máquina {operacao} (%)", 0, 100, 100, step=1, key=f"ef{i}"
        )
        fusos_parados_list.append(fusos_parados)
        eficiencia_maquina_list.append(eficiencia_maquina)

# Botão calcular
if st.button("🔍 Calcular Simulações"):
    resultados = []
    producao_dias = []

    for i, entrada in enumerate(inputs):
        produto, meta, operacao, maquinas, almoco, pico, turnos = entrada
        fusos_total, kg_por_hora = dados_operacao[i]
        fusos_parados = fusos_parados_list[i]
        eficiencia_maquina = eficiencia_maquina_list[i]

        resultado = simular(
            meta, produto, operacao, fusos_total, kg_por_hora, fusos_parados,
            eficiencia_maquina, maquinas, almoco, pico, turnos,
            absenteismo, novatos
        )
        resultados.append(resultado)

        if resultado:
            producao_dia = resultado["metricas"]["Produção (kg)"] / resultado["metricas"]["Dias"]
        else:
            producao_dia = 0
        producao_dias.append(producao_dia)

    # Mostrar os resultados
    cols_result = st.columns(qtd_produtos)
    for i, resultado in enumerate(resultados):
        if resultado:
            with cols_result[i]:
                produto = inputs[i][0]
                st.subheader(f"✅ Resultado: {produto}")
                for k, v in resultado["metricas"].items():
                    st.metric(k, f"{v:.2f}" if isinstance(v, float) else v)
                st.metric(
                    "Produção diária",
                    f"{producao_dias[i]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " kg/dia"
                )

    # Produção total
    operacoes = [entrada[2] for entrada in inputs]
    if len(set(operacoes)) == 1:
        dias_total = sum([resultado["metricas"]["Dias"] if resultado else 0 for resultado in resultados])
        producao_total = 0
    else:
        dias_total = max([resultado["metricas"]["Dias"] if resultado else 0 for resultado in resultados])
        producao_total = sum(producao_dias)

    st.subheader("🔢 Total de Produção Diária")
    st.write("(Se as operações forem iguais, não soma a produção diária!)")
    st.metric(
        "", f"{producao_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " kg/dia"
    )

    # Aviso se ultrapassa dias úteis
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

    # Exporta para Excel
    output = io.BytesIO()
    frames = []

    for resultado in resultados:
        if resultado:
            frames.append(resultado["dados"])

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
