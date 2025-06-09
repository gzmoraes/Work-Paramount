import streamlit as st
import pandas as pd
import altair as alt
import os
import io

st.set_page_config(page_title="Dias Necessarios | Paramount Têxteis SI", layout="wide")

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

st.title("Horas Disponiveis| Produção - Paramount SI")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    caminho = os.path.join(os.path.dirname(__file__), "horas_necessarias.xlsx")
    df = pd.read_excel(caminho)
    df = df[["PRODUTO", "REVISÃO", "LINHA DE PRODUÇÃO", "OPERAÇÃO", "KG/MH", "MAQ HR", "N° OPERAÇÃO", "N° FUSOS"]].dropna()
    return df

dados = carregar_dados()

coluna1, coluna2 = st.columns(2)

coluna1 