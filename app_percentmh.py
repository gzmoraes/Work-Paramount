import streamlit as st
import pandas as pd
import altair as alt
import os
import io

# Configuração da página
st.set_page_config(page_title="Paramount Têxteis - Santa Isabel", layout="wide")
st.title("Produção - Paramount SI")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    caminho = os.path.join(os.path.dirname(__file__), "Power Bi - PLANTA DE PRODUÇÃO (FIOS  INDUSTRIAIS).xlsx")
    df = pd.read_excel(caminho)
    df = df[["PRODUTO", "OPERAÇÃO", "LINHA DE PRODUÇÃO", "KG/MH", "REVISÃO", "MAQ HR", "N° OPERAÇÃO"]].dropna()
    return df

dados = carregar_dados()

# Seleção de Produtos
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧵 Produto 1")
    produto1 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto1")
    rev1 = sorted(dados[dados["PRODUTO"] == produto1]['REVISÃO'].unique())
    revisao1 = st.selectbox("⚙️ Revisão", rev1, key="revisao1")
    linha1 = sorted(dados[dados["PRODUTO"] == produto1]['LINHA DE PRODUÇÃO'].unique())
    linhaProd1 = st.multiselect("🕐 Linha de Produção", linha1, key="linhaProd1")

with col2:
    st.subheader("🧵 Produto 2")
    produto2 = st.selectbox("Item", sorted(dados["PRODUTO"].unique()), key="produto2")
    rev2 = sorted(dados[dados["PRODUTO"] == produto2]['REVISÃO'].unique())
    revisao2 = st.selectbox("⚙️ Revisão", rev2, key="revisao2")
    linha2 = sorted(dados[dados["PRODUTO"] == produto2]['LINHA DE PRODUÇÃO'].unique())
    linhaProd2 = st.multiselect("🕐 Linha de Produção", linha2, key="linhaProd2")

# Filtro dos dados
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

# Ajuste de nomes para evitar conflitos
nome1 = f"{produto1}"
nome2 = f"{produto2}"

# Preparar tabelas renomeadas
if not filtro1.empty:
    tabela1 = filtro1.rename(columns={
        "MAQ HR": f"MAQ HR - {nome1}",
        "KG/MH": f"KG/HR - {nome1}"
    })
else:
    tabela1 = pd.DataFrame(columns=["N° OPERAÇÃO", "OPERAÇÃO", f"MAQ HR - {nome1}", f"KG/HR - {nome1}"])

if not filtro2.empty:
    tabela2 = filtro2.rename(columns={
        "MAQ HR": f"MAQ HR - {nome2}",
        "KG/MH": f"KG/HR - {nome2}"
    })
else:
    tabela2 = pd.DataFrame(columns=["N° OPERAÇÃO", "OPERAÇÃO", f"MAQ HR - {nome2}", f"KG/HR - {nome2}"])

# Merge cartesiano das operações
comparativo = pd.merge(
    tabela1,
    tabela2,
    on=["N° OPERAÇÃO", "OPERAÇÃO"],
    how="outer"
)

# Preencher colunas ausentes com zero
for col in [f"MAQ HR - {nome1}", f"MAQ HR - {nome2}", f"KG/HR - {nome1}", f"KG/HR - {nome2}"]:
    if col not in comparativo.columns:
        comparativo[col] = 0
    else:
        comparativo[col] = comparativo[col].fillna(0)

if comparativo.empty:
    st.warning("⚠️ Dados insuficientes para gerar o comparativo. Verifique se selecionou corretamente Produto, Revisão e Linha de Produção.")
else:
    # Calcular a diferença percentual de MAQ HR
    comparativo["Diferença (%) MAQ HR"] = (
        (comparativo[f"MAQ HR - {nome2}"] - comparativo[f"MAQ HR - {nome1}"]) /
        comparativo[f"MAQ HR - {nome1}"].replace(0, pd.NA)
    ) * 100
    comparativo["Diferença (%) MAQ HR"] = comparativo["Diferença (%) MAQ HR"].round(2)

    # Ordenar e exibir a tabela
    comparativo = comparativo.sort_values(by="N° OPERAÇÃO", ascending=True)
    colunas_exibir = [
        "N° OPERAÇÃO",
        "OPERAÇÃO",
        f"KG/HR - {nome1}",
        f"KG/HR - {nome2}",
        f"MAQ HR - {nome1}",
        f"MAQ HR - {nome2}",
        "Diferença (%) MAQ HR"
    ]
    comparativo = comparativo[colunas_exibir]

    st.subheader("🔍 Comparativo de MAQ HR por OPERAÇÃO (%)")
    st.dataframe(comparativo, hide_index=True)

    # Diferença Total Ponderada
    soma_maq1 = comparativo[f"MAQ HR - {nome1}"].sum()
    soma_maq2 = comparativo[f"MAQ HR - {nome2}"].sum()
    if soma_maq1 != 0:
        diff_ponderada = ((soma_maq2 - soma_maq1) / soma_maq1) * 100
        diff_ponderada = round(diff_ponderada, 2)
    else:
        diff_ponderada = 0

    st.subheader("📌 Diferença Percentual Total (Ponderada)")
    st.metric(label="Diferença Total (%)", value=f"{diff_ponderada}%")

    # Explicação do gráfico
    st.markdown(
        f"""
        #### ℹ️ Interpretação do Gráfico:
        - Valores **positivos** indicam que o produto **{nome2}** consome mais MAQ HR que **{nome1}** na mesma operação.
        - Valores **negativos** indicam que o produto **{nome2}** consome menos MAQ HR que **{nome1}**.
        """
    )

    # Gráfico
    grafico = alt.Chart(comparativo).mark_bar().encode(
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

    st.altair_chart(grafico, use_container_width=True)

    # Exportar Excel
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
