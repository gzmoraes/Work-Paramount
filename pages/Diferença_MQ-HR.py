import streamlit as st
import pandas as pd
import altair as alt
import os
import io

st.set_page_config(page_title="Diferença MQ/HR | Paramount Têxteis SI", layout="wide")

# 🎨 Sidebar personalizada
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

st.title("Diferença MQ/HR | Produção - Paramount SI")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    caminho = os.path.join(os.path.dirname(__file__), "PLANTA_DE_PRODUÇÃO(FIOS_INDUSTRIAIS).xlsx")
    df = pd.read_excel(caminho)
    df = df[["PRODUTO", "REVISÃO", "LINHA DE PRODUÇÃO", "OPERAÇÃO", "KG/MH", "MAQ HR", "N° OPERAÇÃO"]].dropna()
    return df

dados = carregar_dados()

# Padroniza as colunas
dados["OPERAÇÃO"] = dados["OPERAÇÃO"].astype(str).str.strip().str.upper()
dados["N° OPERAÇÃO"] = dados["N° OPERAÇÃO"].astype(str).str.strip()

# Remove valores nulos da coluna "LINHA DE PRODUÇÃO"
dados_sem_nulos = dados[dados["LINHA DE PRODUÇÃO"].notna()]

# Seleção de Produtos
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧵 Produto 1")
    produto1 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto1")
    rev1 = sorted(dados[dados["PRODUTO"] == produto1]['REVISÃO'].unique())
    revisao1 = st.selectbox("⚙️ Revisão da Planta de Produção", rev1, key="revisao1")
    linha1 = sorted(dados[dados["PRODUTO"] == produto1]['LINHA DE PRODUÇÃO'].unique())
    linhaProd1 = st.multiselect("🕐 Linha de Produção", linha1, key="linhaProd1")

with col2:
    st.subheader("🧵 Produto 2")
    produto2 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto2")
    rev2 = sorted(dados[dados["PRODUTO"] == produto2]['REVISÃO'].unique())
    revisao2 = st.selectbox("⚙️ Revisão da Planta de Produção", rev2, key="revisao2")
    linha2 = sorted(dados[dados["PRODUTO"] == produto2]['LINHA DE PRODUÇÃO'].unique())
    linhaProd2 = st.multiselect("🕐 Linha de Produção", linha2, key="linhaProd2")

# Filtragem de dados
filtro1 = dados_sem_nulos[
    (dados_sem_nulos["PRODUTO"] == produto1) &
    (dados_sem_nulos["REVISÃO"] == revisao1) &
    (dados_sem_nulos["LINHA DE PRODUÇÃO"].isin(linhaProd1))
][["OPERAÇÃO", "N° OPERAÇÃO", "KG/MH", "MAQ HR"]]

filtro2 = dados_sem_nulos[
    (dados_sem_nulos["PRODUTO"] == produto2) &
    (dados_sem_nulos["REVISÃO"] == revisao2) &
    (dados_sem_nulos["LINHA DE PRODUÇÃO"].isin(linhaProd2))
][["OPERAÇÃO", "KG/MH", "MAQ HR"]]

# Renomear colunas
nome1 = f"{produto1}"
nome2 = f"{produto2}"

if not filtro1.empty:
    tabela1 = filtro1.rename(columns={
        "MAQ HR": f"MAQ HR - {nome1}",
        "KG/MH": f"KG/HR - {nome1}"
    })
else:
    tabela1 = pd.DataFrame(columns=["OPERAÇÃO", "N° OPERAÇÃO", f"MAQ HR - {nome1}", f"KG/HR - {nome1}"])

if not filtro2.empty:
    tabela2 = filtro2.rename(columns={
        "MAQ HR": f"MAQ HR - {nome2}",
        "KG/MH": f"KG/HR - {nome2}"
    })
else:
    tabela2 = pd.DataFrame(columns=["OPERAÇÃO", f"MAQ HR - {nome2}", f"KG/HR - {nome2}"])

# Agrupamento de Produto 1 (mantendo menor N° OPERAÇÃO)
if not tabela1.empty:
    tabela1_grouped = tabela1.groupby(['OPERAÇÃO'], as_index=False).agg({
        "N° OPERAÇÃO": "min",
        f"MAQ HR - {nome1}": "sum",
        f"KG/HR - {nome1}": "sum"
    })
else:
    tabela1_grouped = pd.DataFrame(columns=["OPERAÇÃO", "N° OPERAÇÃO", f"MAQ HR - {nome1}", f"KG/HR - {nome1}"])

# Agrupamento de Produto 2
tabela2_grouped = tabela2.groupby(['OPERAÇÃO'], as_index=False).sum(numeric_only=True)

# Merge das tabelas agrupadas
comparativo = pd.merge(
    tabela1_grouped,
    tabela2_grouped,
    on=["OPERAÇÃO"],
    how="outer"
)

# Preencher valores ausentes com zero
for col in [f"MAQ HR - {nome1}", f"MAQ HR - {nome2}", f"KG/HR - {nome1}", f"KG/HR - {nome2}"]:
    if col not in comparativo.columns:
        comparativo[col] = 0
    else:
        comparativo[col] = comparativo[col].fillna(0)

# Converter "N° OPERAÇÃO" para numérico (ordenação correta)
comparativo["N° OPERAÇÃO"] = pd.to_numeric(comparativo["N° OPERAÇÃO"], errors='coerce')

# Calcular diferença percentual de MAQ HR
comparativo["Diferença (%) MAQ HR"] = (
    (comparativo[f"MAQ HR - {nome1}"] - comparativo[f"MAQ HR - {nome2}"]) /
    comparativo[f"MAQ HR - {nome1}"].replace(0, pd.NA)
) * 100
comparativo["Diferença (%) MAQ HR"] = comparativo["Diferença (%) MAQ HR"].round(2)

# Ordenar
comparativo = comparativo.sort_values(by=["N° OPERAÇÃO", "OPERAÇÃO"], ascending=True, na_position='last')

# Exibir tabela comparativa
colunas_exibir = [
    "N° OPERAÇÃO",
    "OPERAÇÃO",
    f"KG/HR - {nome1}",
    f"KG/HR - {nome2}",
    f"MAQ HR - {nome1}",
    f"MAQ HR - {nome2}",
    "Diferença (%) MAQ HR"
]

if comparativo.empty:
    st.warning("⚠️ Dados insuficientes para gerar o comparativo. Verifique se selecionou corretamente Produto, Revisão e Linha de Produção.")
else:
    st.subheader("🔍 Comparativo de MAQ HR por OPERAÇÃO")
    st.write("(Ordem de N° de Operação está de acordo com o Produto 1)")
    st.dataframe(comparativo[colunas_exibir], hide_index=True)

    # Diferença total ponderada
    soma_maq1 = comparativo[f"MAQ HR - {nome1}"].sum()
    soma_maq2 = comparativo[f"MAQ HR - {nome2}"].sum()
    if soma_maq1 != 0:
        diff_ponderada = ((soma_maq1 - soma_maq2) / soma_maq1) * 100
        diff_ponderada = round(diff_ponderada, 2)
    else:
        diff_ponderada = 0

    st.subheader("📌 Diferença Percentual Total (Ponderada)")
    st.metric(label="Diferença Total (%)", value=f"{diff_ponderada}%")

    # Explicação do gráfico
    st.markdown(
        f"""
        #### ℹ️ Interpretação do Gráfico:
        - Valores **positivos** indicam que o produto **{nome1}** consome mais MAQ HR que **{nome2}** na mesma operação.
        - Valores **negativos** indicam que o produto **{nome1}** consome menos MAQ HR que **{nome2}**.
        """
    )

    # Gráfico de Diferença Percentual
    grafico_diferenca = alt.Chart(comparativo).mark_bar().encode(
        x=alt.X('OPERAÇÃO:N', sort=None, title='Operação'),
        y=alt.Y('Diferença (%) MAQ HR:Q', title='Diferença (%)'),
        color=alt.condition(
            alt.datum["Diferença (%) MAQ HR"] > 0,
            alt.value("#28a745"),  # verde
            alt.value("#dc3545")   # vermelho
        ),
        tooltip=['OPERAÇÃO', 'Diferença (%) MAQ HR']
    ).properties(
        width=1000,
        height=400
    ).configure_axis(
        labelAngle=-45
    )

    st.subheader("📊 Gráfico de Diferença Percentual (MAQ HR)")
    st.altair_chart(grafico_diferenca, use_container_width=True)

    # Gráfico Comparativo Lado a Lado
    dados_plot = comparativo.melt(
        id_vars=['OPERAÇÃO', 'N° OPERAÇÃO'],
        value_vars=[f'MAQ HR - {nome1}', f'MAQ HR - {nome2}'],
        var_name='Produto',
        value_name='MAQ HR'
    )

    dados_plot['Produto'] = dados_plot['Produto'].str.replace('MAQ HR - ', '')

    grafico_comparativo = alt.Chart(dados_plot).mark_bar().encode(
        x=alt.X('OPERAÇÃO:N', title='Operação'),
        y=alt.Y('MAQ HR:Q', title='MAQ HR'),
        color=alt.Color('Produto:N',
                        scale=alt.Scale(range=['#28a745', '#dc3545']),
                        legend=alt.Legend(title="Produto")),
        tooltip=['OPERAÇÃO', 'Produto', 'MAQ HR']
    ).properties(
        width=1000,
        height=400
    ).configure_axis(
        labelAngle=-45
    )

    st.subheader("📊 Gráfico Comparativo de MAQ HR por Operação")
    st.altair_chart(grafico_comparativo, use_container_width=True)

    # Exportar Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        comparativo[colunas_exibir].to_excel(writer, index=False, sheet_name='Comparativo')

    output.seek(0)

    st.download_button(
        label="📥 Baixar Comparativo em Excel",
        data=output,
        file_name=f"comparativo_{produto1}_vs_{produto2}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
