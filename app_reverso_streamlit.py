import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Paramount Têxteis - Santa Isabel", layout="centered")

st.title("Produção - Paramount SI")

# === Carrega dados ===
@st.cache_data
def carregar_dados():
    df = pd.read_excel("Power Bi - PLANTA DE PRODUÇÃO (FIOS  INDUSTRIAIS).xlsx")
    df = df[["PRODUTO", "OPERAÇÃO", "N° FUSOS", "KG/MH"]].dropna()
    return df

dados = carregar_dados()

diasMax = st.number_input("📆 Max Dias Úteis", min_value=1, max_value=31, step=1)

# === Seleção de produtos e metas (lado a lado) ===
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧵 Produto 1")
    produto1 = st.selectbox("Produto 1", sorted(dados["PRODUTO"].unique()), key="produto1")
    meta1 = st.number_input("Meta Produto 1 (kg)", min_value=1, step=1000, key="meta1")
    operacoes1 = dados[dados["PRODUTO"] == produto1]["OPERAÇÃO"].unique()
    operacao1 = st.selectbox("⚙️ Operação Produto 1", sorted(operacoes1), key="operacao1")
    maquinas1 = st.number_input("🏭 Quantidade de máquinas Produto 1", min_value=1, step=1, key="maquinas1")

with col2:
    st.subheader("🧵 Produto 2")
    produto2 = st.selectbox("Produto 2", sorted(dados["PRODUTO"].unique()), key="produto2")
    meta2 = st.number_input("Meta Produto 2 (kg)", min_value=1, step=1000, key="meta2")
    operacoes2 = dados[dados["PRODUTO"] == produto2]["OPERAÇÃO"].unique()
    operacao2 = st.selectbox("⚙️ Operação Produto 2", sorted(operacoes2), key="operacao2")
    maquinas2 = st.number_input("🏭 Quantidade de máquinas Produto 2", min_value=1, step=1, key="maquinas2")

# === Dados da operação para cada produto ===
linha1 = dados[(dados["PRODUTO"] == produto1) & (dados["OPERAÇÃO"] == operacao1)].iloc[0]
fusos_total1 = int(linha1["N° FUSOS"])
kg_por_hora1 = float(str(linha1["KG/MH"]).replace(",", "."))

linha2 = dados[(dados["PRODUTO"] == produto2) & (dados["OPERAÇÃO"] == operacao2)].iloc[0]
fusos_total2 = int(linha2["N° FUSOS"])
kg_por_hora2 = float(str(linha2["KG/MH"]).replace(",", "."))

# === Fusos e Eficiência ===
colf1, colf2 = st.columns(2)

with colf1:
    fusos_parados1 = st.slider(f"🛑 Fusos parados {produto1} (máx: {fusos_total1})", 0, fusos_total1, step=1, key="fuso1")
    eficiencia_maquina1 = st.slider(f"🛠️ Eficiência Máquina {produto1} (%)", 0, 100, 100, step=1, key="ef1")

with colf2:
    fusos_parados2 = st.slider(f"🛑 Fusos parados {produto2} (máx: {fusos_total2})", 0, fusos_total2, step=1, key="fuso2")
    eficiencia_maquina2 = st.slider(f"🛠️ Eficiência Máquina {produto2} (%)", 0, 100, 100, step=1, key="ef2")

# === Pausas e pico ===
almoco = st.radio("🍽️ Pausa para almoço?", ["Sim", "Não"]) == "Sim"
pico = st.radio("📈 Pico no turno B?", ["Sim", "Não"]) == "Sim"

# === Função de simulação ===
def simular(meta, produto, operacao, fusos_total, kg_por_hora, fusos_parados, eficiencia_maquina, maquinas):
    fusos_ativos = fusos_total - fusos_parados
    eficiencia = fusos_ativos / fusos_total
    percent_maquina = eficiencia_maquina / 100

    turnos_possiveis = [["A"], ["B"], ["C"],
                        ["A", "B"], ["A", "C"], ["B", "C"],
                        ["A", "B", "C"]]

    resultados = []

    for dias in range(1, diasMax + 1):
        for turnos in turnos_possiveis:
            total_horas = 0
            for t in turnos:
                h = 8
                if almoco:
                    h -= 1
                if t == "B" and pico:
                    h -= 3
                total_horas += h
            total_horas *= dias * maquinas
            producao = total_horas * kg_por_hora * eficiencia * percent_maquina
            if producao >= meta:
                resultados.append({
                    "Turnos": "".join(turnos),
                    "Dias": dias,
                    "Horas Totais": total_horas,
                    "Produção Estimada": round(producao, 2)
                })

    if resultados:
        melhor = sorted(resultados, key=lambda x: (x["Dias"], len(x["Turnos"])))[0]
        return {
            "dados": pd.DataFrame([{
                "Produto": produto,
                "Operação": operacao,
                "Meta (kg)": meta,
                "Fusos Parados": fusos_parados,
                "Máquinas": maquinas,
                "Eficiência Máquina(%)": percent_maquina * 100,
                "Almoço": "Sim" if almoco else "Não",
                "Pico no Turno B": "Sim" if pico else "Não",
                "Eficiência Fusos(%)": round(eficiencia * 100, 2),
                "Turnos Necessários": melhor["Turnos"],
                "Dias Necessários": melhor["Dias"],
                "Produção Estimada (kg)": melhor["Produção Estimada"]
            }]),
            "metricas": {
                "Eficiência Fusos (%)": eficiencia * 100,
                "Eficiência Máquina (%)": percent_maquina * 100,
                "Turnos": melhor["Turnos"],
                "Dias": melhor["Dias"],
                "Produção (kg)": melhor["Produção Estimada"]
            }
        }
    else:
        return None

# === Cálculo e Exibição ===
if st.button("🔍 Calcular Simulações"):
    resultado1 = simular(meta1, produto1, operacao1, fusos_total1, kg_por_hora1, fusos_parados1, eficiencia_maquina1, maquinas1)
    resultado2 = simular(meta2, produto2, operacao2, fusos_total2, kg_por_hora2, fusos_parados2, eficiencia_maquina2, maquinas2)

    if resultado1 or resultado2:
        colres1, colres2 = st.columns(2)

        if resultado1:
            with colres1:
                st.subheader(f"✅ Resultado: {produto1}")
                st.metric("Eficiência Fusos (%)", f"{resultado1['metricas']['Eficiência Fusos (%)']:.2f}%")
                st.metric("Eficiência Máquina (%)", f"{resultado1['metricas']['Eficiência Máquina (%)']:.2f}%")
                st.metric("Turnos Necessários", resultado1["metricas"]["Turnos"])
                st.metric("Dias de Produção", resultado1["metricas"]["Dias"])
                st.metric("Produção Estimada (kg)", f"{resultado1['metricas']['Produção (kg)']:.0f}")

        if resultado2:
            with colres2:
                st.subheader(f"✅ Resultado: {produto2}")
                st.metric("Eficiência Fusos (%)", f"{resultado2['metricas']['Eficiência Fusos (%)']:.2f}%")
                st.metric("Eficiência Máquina (%)", f"{resultado2['metricas']['Eficiência Máquina (%)']:.2f}%")
                st.metric("Turnos Necessários", resultado2["metricas"]["Turnos"])
                st.metric("Dias de Produção", resultado2["metricas"]["Dias"])
                st.metric("Produção Estimada (kg)", f"{resultado2['metricas']['Produção (kg)']:.0f}")

        dias_total = (resultado1["metricas"]["Dias"] if resultado1 else 0) + \
                     (resultado2["metricas"]["Dias"] if resultado2 else 0) + 1

        total_df = pd.DataFrame([{
            "Produto": "TOTAL",
            "Dias Necessários": dias_total
        }])

        if dias_total > diasMax:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin-top: 2em;">
                    <div style="background-color: #ff4d4d; padding: 20px 40px; border-radius: 10px; text-align: center; color: white;">
                        <h2 style="margin: 0;">⚠️ Limite Excedido</h2><br>
                        <p style="margin: 0;">Dias úteis necessários ultrapassam o máximo definido ({diasMax})</p>
                        <p style="font-size: 36px; font-weight: bold; margin: 10px 0 0 0;">{dias_total} dias</p>
                    </div>
                </div><br>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin-top: 2em;">
                    <div style="background-color: #29a329; padding: 20px 40px; border-radius: 10px; text-align: center; color: white;">
                        <h2 style="margin: 0;">✅ Dentro do Limite</h2>
                        <p style="margin: 0;">Dias úteis necessários</p>
                        <p style="font-size: 36px; font-weight: bold; margin: 10px 0 0 0;">{dias_total} dias</p>
                    </div>
                </div><br>
                """,
                unsafe_allow_html=True
            )


        # === Exportação Excel ===
        output = io.BytesIO()
        frames = []
        if resultado1:
            frames.append(resultado1["dados"])
        if resultado2:
            frames.append(resultado2["dados"])
        frames.append(total_df)

        resultado_final = pd.concat(frames, ignore_index=True)

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado_final.to_excel(writer, index=False, sheet_name="Simulação Total")

        st.download_button(
            label="📥 Exportar resultados em Excel",
            data=output.getvalue(),
            file_name=f"simulacao_producao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Nenhum dos produtos atinge a meta com os parâmetros fornecidos.")
