import streamlit as st
import pandas as pd
import altair as alt
import os
import io

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


# Configuração da página
st.title("📊Produção - Paramount SI")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    caminho = os.path.join(os.path.dirname(__file__), "PLANTA_DE_PRODUÇÃO(FIOS_INDUSTRIAIS).xlsx")
    df = pd.read_excel(caminho)
    df = df[["PRODUTO", "REVISÃO", "OPERAÇÃO", "N_ROTEIRO", "N° OPERAÇÃO"]].dropna()
    return df

dados = carregar_dados()

# Padroniza as colunas
dados["OPERAÇÃO"] = dados["OPERAÇÃO"].astype(str).str.strip().str.upper()
dados["N° OPERAÇÃO"] = dados["N° OPERAÇÃO"].astype(str).str.strip()
dados["N_ROTEIRO"] = dados["N_ROTEIRO"].astype(str).str.strip().str.upper()


st.subheader("🧵 Produto 1")
produto1 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto1")
rev1 = sorted(dados[dados["PRODUTO"] == produto1]['REVISÃO'].unique())
revisao1 = st.selectbox("⚙️ Revisão da Planta de Produção", rev1, key="revisao1")



# Filtragem de dados
filtro1 = dados[
    (dados["PRODUTO"] == produto1) &
    (dados["REVISÃO"] == revisao1) 
][["OPERAÇÃO", "N° OPERAÇÃO", "N_ROTEIRO"]]


# Renomear colunas
nome1 = f"{produto1}"


if not filtro1.empty:
    tabela1 = filtro1.rename(columns={
        "N_ROTEIRO": f"ROTEIRO - {nome1}"
    })
else:
    tabela1 = pd.DataFrame(columns=["OPERAÇÃO", "N° OPERAÇÃO", f"ROTEIRO - {nome1}"])

# Exibir tabela comparativa
colunas_exibir = [
    "N° OPERAÇÃO",
    "OPERAÇÃO",
    f"ROTEIRO - {nome1}"
]

if tabela1.empty:
    st.warning("⚠️ Dados insuficientes para gerar o comparativo. Verifique se selecionou corretamente Produto, Revisão e Linha de Produção.")
else:
    st.subheader("🔍 Comparativo de MAQ HR por OPERAÇÃO")
    st.write("(Ordem de N° de Operação está de acordo com o Produto 1)")
    st.dataframe(tabela1[colunas_exibir], hide_index=True)

    
    # Exportar Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        tabela1[colunas_exibir].to_excel(writer, index=False, sheet_name='Comparativo')

    output.seek(0)

    st.download_button(
        label="📥 Baixar Comparativo em Excel",
        data=output,
        file_name=f"roteiro_{produto1}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
