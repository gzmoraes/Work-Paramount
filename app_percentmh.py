import streamlit as st
import pandas as pd
import altair as alt
import os
import io

st.set_page_config(page_title="Paramount Têxteis - Santa Isabel", layout="wide")

st.title("Produção - Paramount SI")

@st.cache_data
def carregar_dados():
    caminho = os.path.join(os.path.dirname(__file__), "Power Bi - PLANTA DE PRODUÇÃO (FIOS  INDUSTRIAIS).xlsx")
    df = pd.read_excel(caminho)
    df = df[["PRODUTO", "OPERAÇÃO", "LINHA DE PRODUÇÃO", "KG/MH", "REVISÃO", "MAQ HR", "N° OPERAÇÃO"]].dropna()
    return df

dados = carregar_dados()

# 📦 Seção de seleção dos produtos
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧵 Produto 1")
    produto1 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto1")
    rev1 = dados[dados["PRODUTO"] == produto1]['REVISÃO'].unique()
    revisao1 = st.selectbox("⚙️ Revisão", sorted(rev1), key="revisao1")
    linha1 = dados[dados["PRODUTO"] == produto1]['LINHA DE PRODUÇÃO'].unique()
    linhaProd1 = st.multiselect("🕐 Linha de Produção", linha1, key="linhaProd1")

with col2:
    st.subheader("🧵 Produto 2")
    produto2 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto2")
    rev2 = dados[dados["PRODUTO"] == produto2]['REVISÃO'].unique()
    revisao2 = st.selectbox("⚙️ Revisão", sorted(rev2), key="revisao2")
    linha2 = dados[dados["PRODUTO"] == produto2]['LINHA DE PRODUÇÃO'].unique()
    linhaProd2 = st.multiselect("🕐 Linha de Produção", linha2, key="linhaProd2")

# 🔍 Filtro dos dados
filtro1 = dados[
    (dados["PRODUTO"] == produto1) &
    (dados["REVISÃO"] == revisao1) &
    (dados["LINHA DE PRODUÇÃO"].isin(linhaProd1))
][["N° OPERAÇÃO", "OPERAÇÃO", "KG/MH", "MAQ HR"]]

filtro2 = dados[
    (dados["PRODUTO"] == produto2) &
    (dados["REVISÃO"] == revisao2) &
    (dados["LINHA DE PRODUÇÃO"].isin(linhaProd2))
][["N° OPERAÇÃO", "OPERAÇÃO", "KG/MH", "MAQ HR"]]

# 👥 Evitar conflito de nomes iguais
nome1 = f"{produto1}"
nome2 = f"{produto2}"

# 🔗 Preparar tabelas com nomes diferentes
if not filtro1.empty:
    tabela1 = filtro1.rename(columns={
        "MAQ HR": f"MAQ HR - {nome1}",
        "N° OPERAÇÃO": f"N° OPERAÇÃO - {nome1}"
    })
else:
    tabela1 = pd.DataFrame(columns=["OPERAÇÃO", f"MAQ HR - {nome1}", f"N° OPERAÇÃO - {nome1}"])

if not filtro2.empty:
    tabela2 = filtro2.rename(columns={
        "MAQ HR": f"MAQ HR - {nome2}",
        "N° OPERAÇÃO": f"N° OPERAÇÃO - {nome2}"
    })
else:
    tabela2 = pd.DataFrame(columns=["OPERAÇÃO", f"MAQ HR - {nome2}", f"N° OPERAÇÃO - {nome2}"])

# 🔗 Produto cartesiano por operação (mesmo que não tenha correspondência)
comparativo = pd.merge(
    tabela1,
    tabela2,
    on="OPERAÇÃO",
    how="outer"
)

# Garantir que as colunas de MAQ HR existam
coluna1 = f"MAQ HR - {nome1}"
coluna2 = f"MAQ HR - {nome2}"

if coluna1 not in comparativo.columns:
    comparativo[coluna1] = 0
else:
    comparativo[coluna1] = comparativo[coluna1].fillna(0)

if coluna2 not in comparativo.columns:
    comparativo[coluna2] = 0
else:
    comparativo[coluna2] = comparativo[coluna2].fillna(0)

if comparativo.empty:
    st.warning("⚠️ Dados insuficientes para gerar o comparativo. Verifique se selecionou corretamente Produto, Revisão e Linha de Produção.")
else:
    # 🔢 Calcular diferença percentual
    comparativo["Diferença (%)"] = (
        (comparativo[coluna2] - comparativo[coluna1]) /
        comparativo[coluna1].replace(0, pd.NA)
    ) * 100
    comparativo["Diferença (%)"] = comparativo["Diferença (%)"].round(2)

   # Ordenar a tabela antes de exibir
    comparativo = comparativo.sort_values(by=f"N° OPERAÇÃO - {nome1}", ascending=True)

    # Exibir a tabela
    st.subheader("🔍 Comparativo de MAQ HR por OPERAÇÃO (%)")
    st.dataframe(comparativo, hide_index=True)



    # 📌 Diferença Total Ponderada
    if comparativo[coluna1].sum() != 0:
        diferenca_total_ponderada = (
            ((comparativo[coluna2] - comparativo[coluna1]) *
             comparativo[coluna1]).sum() / 
            comparativo[coluna1].sum()
        ) * 100
        diferenca_total_ponderada = round(diferenca_total_ponderada, 2)
    else:
        diferenca_total_ponderada = 0

    st.subheader("📌 Diferença Percentual Total (Ponderada)")
    st.metric(label="Diferença Total (%)", value=f"{diferenca_total_ponderada}%")

    # 📘 Explicação do gráfico
    st.markdown(
        f"""
        #### ℹ️ Interpretação do Gráfico:
        - Valores **positivos** indicam que o produto **{nome2}** consome mais MAQ HR que **{nome1}** na mesma operação.
        - Valores **negativos** indicam que o produto **{nome2}** consome menos MAQ HR que **{nome1}**.
        """
    )
        

    # 📈 Gráfico
    grafico = alt.Chart(comparativo).mark_bar().encode(
        x=alt.X('OPERAÇÃO:N', sort=None, title='Operação'),
        y=alt.Y('Diferença (%):Q', title='Diferença (%)'),
        color=alt.condition(
            alt.datum["Diferença (%)"] > 0,
            alt.value("#28a745"),  # verde
            alt.value("#dc3545")   # vermelho
        ),
        tooltip=['OPERAÇÃO', 'Diferença (%)']
    ).properties(
        width=1000,
        height=400
    ).configure_axis(
        labelAngle=-45
    )

    st.altair_chart(grafico, use_container_width=True)

    # 💾 Exportar Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        comparativo.to_excel(writer, index=False, sheet_name='Comparativo')

    output.seek(0)

    st.download_button(
        label="📥 Baixar Comparativo em Excel",
        data=output,
        file_name=f"comparativo_{produto1}_vs_{produto2}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
