import streamlit as st
import pandas as pd
import os
import io

def check_password():
    def password_entered():
        if st.session_state["password"] == "paramountapp":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Remove a senha da memória
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔐 Insira a senha:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔐 Insira a senha:", type="password", on_change=password_entered, key="password")
        st.error("❌ Senha incorreta.")
        return False
    else:
        return True

if not check_password():
    st.stop()

st.set_page_config(page_title="Horas Disponíveis por Máquina", layout="wide")
st.title("⚙️ Cálculo de Horas Disponíveis por OPERAÇÃO")

with st.sidebar: 
    st.subheader("ℹ️ Sobre")
    st.info("App desenvolvido para auxiliar na gestão da produção da unidade de Santa Isabel.")
    st.markdown("---")
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


CAMINHO_PLANILHA = os.path.join(
    os.path.dirname(__file__),
    "PLANTA_DE_PRODUÇÃO(FIOS_INDUSTRIAIS).xlsx"
)

@st.cache_data
def carregar_dados():
    df = pd.read_excel(CAMINHO_PLANILHA)
    df = df[["N° OPERAÇÃO", "OPERAÇÃO", "N° FUSOS", "KG/MH", "PRODUTO", "FIAÇÃO"]].dropna()
    df["OPERAÇÃO"] = df["OPERAÇÃO"].astype(str).str.strip().str.upper()
    df["N° OPERAÇÃO"] = df["N° OPERAÇÃO"].astype(int)
    df["FIAÇÃO"] = df["FIAÇÃO"].astype(str).str.strip().str.upper()
    
    df_agrupado = (
        df.groupby("OPERAÇÃO")
        .agg({
            "N° FUSOS": "first",
            "KG/MH": "first"
        })
        .reset_index()
        .sort_values(by="OPERAÇÃO")
    )
    return df, df_agrupado

df_raw, df = carregar_dados()

st.markdown("---")
fiações_disponíveis = df_raw["FIAÇÃO"].dropna().unique()
fiação_selecionada = st.selectbox("Filtrar por FIAÇÃO", sorted(fiações_disponíveis))

df_raw = df_raw[df_raw["FIAÇÃO"] == fiação_selecionada]
df = df[df["OPERAÇÃO"].isin(df_raw["OPERAÇÃO"].unique())]


# ---------------- CONFIGURAÇÕES GERAIS ----------------
dias_uteis = st.number_input("Dias Úteis", min_value=1, max_value=31, value=25)
absenteismo_geral = st.number_input("Absenteísmo (%)", 0, 100, 5)
novatos_geral = st.number_input("Novatos (%)", 0, 100, 10)

st.markdown("---")
st.subheader("⚙️ Configurações Individuais por OPERAÇÃO")

resultados = []

for idx, row in df.iterrows():
    operacao = row["OPERAÇÃO"]
    total_fusos = row["N° FUSOS"]

    turnos_padrao = ["A", "B", "C"]
    maq_padrao = 1
    fusos_padrao = 0.0
    eficiencia_padrao = 85
    almoco_padrao = "Sim"
    pico_padrao = "Não"

    turnos = st.session_state.get(f"turnos_{idx}", turnos_padrao)
    maquinas = st.session_state.get(f"maq_{idx}", maq_padrao)
    fusos_parados = st.session_state.get(f"fuso_{idx}", fusos_padrao)
    eficiencia = st.session_state.get(f"efi_{idx}", eficiencia_padrao)
    almoco = st.session_state.get(f"almoco_{idx}", almoco_padrao)
    pico = st.session_state.get(f"pico_{idx}", pico_padrao)

    editado = (
        turnos != turnos_padrao or
        maquinas != maq_padrao or
        fusos_parados != fusos_padrao or
        eficiencia != eficiencia_padrao or
        almoco != almoco_padrao or
        pico != pico_padrao
    )

    with st.expander(f"{'✔️' if editado else '⚙️'} OPERAÇÃO: {operacao}", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            turnos = st.multiselect(f"Turnos - {operacao}", ["A", "B", "C"], default=turnos, key=f"turnos_{idx}")
            total_turno_horas = len(turnos) * 8
            maquinas = st.number_input(f"Máquinas - {operacao}", min_value=1, value=maquinas, key=f"maq_{idx}")
        with col2:
            almoco = st.radio(f"Almoço - {operacao}", ["Sim", "Não"], index=["Sim", "Não"].index(almoco), key=f"almoco_{idx}")
            pico = st.radio(f"Pico - {operacao}", ["Sim", "Não"], index=["Sim", "Não"].index(pico), key=f"pico_{idx}")
        with col3:
            eficiencia = st.number_input(f"Eficiência % - {operacao}", 1, 100, value=eficiencia, key=f"efi_{idx}")
            fusos_parados = st.number_input(
                f"Fusos Parados - {operacao} - Total Fusos {total_fusos}",
                min_value=0.0,
                max_value=float(total_fusos),
                value=fusos_parados,
                key=f"fuso_{idx}"
            )

        almoco_h = len(turnos) * 1.0 if almoco == "Sim" else 0.0
        pico_h = 3.0 if pico == "Sim" and "B" in turnos else 0.0

        fator_fusos = (total_fusos - fusos_parados) / total_fusos if total_fusos else 1.0
        horas_liquidas = (total_turno_horas - almoco_h - pico_h) * fator_fusos

        fator_final = (1 - absenteismo_geral / 100) * (1 - novatos_geral / 200) * (eficiencia / 100)
        horas_disp = dias_uteis * horas_liquidas * fator_final * maquinas

        resultados.append({
            "OPERAÇÃO": operacao,
            "Turnos": ", ".join(turnos),
            "Almoço": almoco,
            "Pico": pico,
            "Eficiência %": eficiencia,
            "Fusos Parados": fusos_parados,
            "Qntd Máquinas": maquinas,
            "Absenteismo %": absenteismo_geral,
            "Novatos %": novatos_geral,
            "Horas líquidas/dia": round(horas_liquidas, 2),
            "Horas Disponíveis (Total)": round(horas_disp, 2)
        })

df_resultado = pd.DataFrame(resultados)
df_resultado = df_resultado.sort_values(by="OPERAÇÃO")

st.subheader("Horas Disponiveis por Máquina")
st.dataframe(df_resultado, hide_index=True)

output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df_resultado.to_excel(writer, index=False, sheet_name="Horas_Disponiveis")

output.seek(0)
st.download_button("📥 Baixar Resultado em Excel", data=output,
                   file_name="horas_disponiveis_por_operacao.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------------- NOVA FUNCIONALIDADE: META POR PRODUTO ----------------
st.markdown("---")
st.header("Horas Necessárias por Produto")

# Agrupar produtos disponíveis
produtos_disponiveis = df_raw["PRODUTO"].drop_duplicates().tolist()

num_produtos = st.number_input("Quantidade de Produtos a Simular", min_value=1, max_value=30, value=1, step=1)

produtos_selecionados = []
for i in range(int(num_produtos)):
    with st.expander(f"🛠️ Produto {i+1}"):
        produto = st.selectbox(f"Selecione o Produto - Produto {i+1}", produtos_disponiveis, key=f"produto_{i}")
        meta_ton = st.number_input(f"Meta de Produção (toneladas) para Produto {i+1}", min_value=0.0, step=1.0, key=f"meta_{i}")
        produtos_selecionados.append({"Produto": produto, "Meta_ton": meta_ton})

# Calcular horas necessárias
resultados_produtos = []

for produto_info in produtos_selecionados:
    produto = produto_info["Produto"]
    meta = produto_info["Meta_ton"]

    df_filtrado = df_raw[df_raw["PRODUTO"] == produto]

    for _, row in df_filtrado.iterrows():
        operacao = row["OPERAÇÃO"]
        kg_mh = row["KG/MH"]

        if kg_mh > 0:
            horas_necessarias = (meta * 1000) / kg_mh
        else:
            horas_necessarias = 0.0

        resultados_produtos.append({
            "Produto": produto,
            "OPERAÇÃO": operacao,
            "KG/MH": kg_mh,
            "Meta (ton)": meta,
            "Horas Necessárias": round(horas_necessarias, 2)
        })

if resultados_produtos:
    df_produtos = pd.DataFrame(resultados_produtos)
    st.subheader("📈 Horas Necessárias por Produto e Operação")
    st.dataframe(df_produtos, hide_index=True)

    output_produtos = io.BytesIO()
    with pd.ExcelWriter(output_produtos, engine="openpyxl") as writer:
        df_produtos.to_excel(writer, index=False, sheet_name="Horas_Necessarias")
    output_produtos.seek(0)
    st.download_button(
        "📥 Baixar Resultado em Excel (Horas Necessárias)",
        data=output_produtos,
        file_name="horas_necessarias_por_operacao.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------- COMPARAÇÃO FINAL: SOMA TOTAL DE HORAS NECESSÁRIAS x HORAS DISPONÍVEIS ----------------
st.markdown("---")
st.header("Verificação Final por Ocupação")

# Agrupar horas necessárias por operação
df_necessarias_agrupadas = df_produtos.groupby("OPERAÇÃO")["Horas Necessárias"].sum().reset_index()
df_necessarias_agrupadas = df_necessarias_agrupadas.rename(columns={"Horas Necessárias": "Horas Necessárias (Total)"})

# Merge com as horas disponíveis
df_checagem = pd.merge(df_necessarias_agrupadas, df_resultado, on="OPERAÇÃO", how="left")

# Cálculo da diferença e status
df_checagem["Diferença (Disp - Nec)"] = df_checagem["Horas Disponíveis (Total)"] - df_checagem["Horas Necessárias (Total)"]
df_checagem["Status"] = df_checagem["Diferença (Disp - Nec)"].apply(
    lambda x: "✅ Viável" if x >= 0 else "❌ Inválido"
)
df_checagem["Ocupação (%)"] = ((df_checagem["Horas Necessárias (Total)"] / df_checagem["Horas Disponíveis (Total)"]) * 100).round(2)


# Exibição ordenada
colunas_exibir = [
    "OPERAÇÃO",
    "Turnos",
    "Almoço",
    "Pico",
    "Eficiência %", 
    "Fusos Parados",
    "Qntd Máquinas",
    "Absenteismo %",
    "Novatos %",
    "Horas Disponíveis (Total)",
    "Horas Necessárias (Total)",
    "Diferença (Disp - Nec)",
    "Ocupação (%)",
    "Status"
]


df_checagem = df_checagem[colunas_exibir].sort_values(by="OPERAÇÃO")

st.dataframe(df_checagem, hide_index=True)

# Exportar resultado final
output_checagem = io.BytesIO()
with pd.ExcelWriter(output_checagem, engine="openpyxl") as writer:
    df_checagem.to_excel(writer, index=False, sheet_name="Viabilidade_Final")
output_checagem.seek(0)
st.download_button(
    "📥 Baixar Verificação Final (Agrupada)",
    data=output_checagem,
    file_name="verificacao_final_viabilidade.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

