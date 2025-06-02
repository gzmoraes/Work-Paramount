import streamlit as st

st.set_page_config(page_title="Paramount Têxteis - Santa Isabel", layout="wide")

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


# Conteúdo principal
st.image("https://cdn-app-privally-io.s3.amazonaws.com/env/suite/images/treatment/central/0001/00000436/darkLogo/20210824193610.png", width= 700)

st.subheader("👈 Selecione uma página no menu lateral")

st.markdown("""
### 📄 Descrição:
Este aplicativo possui duas funcionalidades principais:

1. **🔍 Comparativo de Produção**  
Compare a produtividade de dois produtos distintos com base na quantidade de MAQ HR e KG/HR por operação.

2. **🧮 Simulador de Produção**  
Simule a quantidade de dias necessários para atingir uma meta de produção, considerando variáveis como quantidade de máquinas, fusos parados, turnos, pausas e eficiência.
""")

