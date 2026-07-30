import graphviz
import pandas as pd
import streamlit as st


def desenhar_diagrama_micro_macro():
    dot = graphviz.Digraph()
    dot.attr(rankdir="LR", bgcolor="white")
    dot.attr("node", shape="box", style="rounded,filled", fontname="Helvetica", fontsize="11")
    dot.attr("edge", fontname="Helvetica", fontsize="9", color="#94a3b8")

    with dot.subgraph(name="cluster_micro") as c:
        c.attr(label="Nível Micro — escalar por transação", style="dashed", color="#2563eb", fontsize="11")
        c.node("p1", "1. Pessimista", fillcolor="#bfdbfe")
        c.node("p2", "2. Otimista", fillcolor="#bfdbfe")
        c.node("p3", "3. Write Sharding", fillcolor="#bfdbfe")

    dot.node("agg", "Serviço Agregador\n(Padrão Agregador)", fillcolor="#fef3c7")

    with dot.subgraph(name="cluster_macro") as c:
        c.attr(label="Nível Macro — otimizar liquidez", style="dashed", color="#b45309", fontsize="11")
        c.node("p4", "4. Netting com Grafos", fillcolor="#fde68a")

    dot.node("resultado", "Sistema escalável\n+ eficiente em capital", fillcolor="#86efac")

    for micro in ("p1", "p2", "p3"):
        dot.edge(micro, "agg")
    dot.edge("agg", "p4", label="obrigação líquida")
    dot.edge("p4", "resultado")

    return dot


st.title("Síntese: Matriz de Decisão Estratégica")
st.markdown("---")

st.info(
    "Não existe bala de prata: as quatro estratégias resolvem problemas diferentes. A arquitetura "
    "de referência combina as três primeiras (nível micro, escala por transação) com a quarta "
    "(nível macro, eficiência de capital)."
)

st.header("Como as camadas se conectam")
st.graphviz_chart(desenhar_diagrama_micro_macro(), width="stretch")
st.caption(
    "As três primeiras estratégias resolvem 'como escalar a escrita de uma conta'. A quarta resolve "
    "'como usar menos capital para liquidar o sistema como um todo' — e recebe como entrada o resultado "
    "já agregado das três primeiras."
)
st.markdown("---")

st.header("Comparação Rápida")
st.caption(
    "Avaliação qualitativa (Baixa/Média/Alta/Muito Alta) de cada estudo de caso, convertida em escala "
    "numérica só para leitura visual — não é um benchmark medido."
)

col_tps, col_lat, col_cmplx = st.columns(3)

with col_tps:
    st.markdown("**Capacidade de TPS** (nível micro)")
    tps_scores = pd.DataFrame({
        "Estratégia": ["1. Pessimista", "2. Otimista", "3. Sharding"],
        "Score": [1, 3, 4],
    }).set_index("Estratégia")
    st.bar_chart(tps_scores, height=220)

with col_lat:
    st.markdown("**Latência sob carga alta** (menor é melhor)")
    lat_scores = pd.DataFrame({
        "Estratégia": ["1. Pessimista", "2. Otimista", "3. Sharding"],
        "Score": [4, 2, 1],
    }).set_index("Estratégia")
    st.bar_chart(lat_scores, height=220)

with col_cmplx:
    st.markdown("**Complexidade de Implementação**")
    complexity_scores = pd.DataFrame({
        "Estratégia": ["1. Pessimista", "2. Otimista", "3. Sharding", "4. Grafos"],
        "Score": [1, 2, 3, 3],
    }).set_index("Estratégia")
    st.bar_chart(complexity_scores, height=220)

st.markdown("---")

st.header("Como Escolher: 3 Perguntas Rápidas")
q1, q2, q3 = st.columns(3)
with q1:
    st.markdown("**1. Qual é o gargalo?**")
    st.markdown("""
- Conta quente com muita escrita → **Write Sharding**
- Locks longos travando tudo → **Controle Otimista**
- Servidor monolítico saturado → sharding do banco inteiro
""")
with q2:
    st.markdown("**2. Que complexidade a equipe aguenta?**")
    st.markdown("""
- Equipe pequena / projeto novo → **Controle Pessimista** (comece simples)
- Equipe com cultura DevOps forte → Sharding + Padrão Agregador
""")
with q3:
    st.markdown("**3. O problema é técnico ou de negócio?**")
    st.markdown("""
- "A API não pode cair, precisa aguentar 10k TPS" → Estratégias 1, 2 ou 3
- "Precisamos de menos capital parado em caixa" → **Estratégia 4 (Grafos)**
""")

st.success(
    "**Conclusão:** a arquitetura ideal geralmente combina as duas camadas — Write Sharding + Padrão "
    "Agregador resolvem o problema técnico (TPS) no nível micro, e alimentam as obrigações líquidas "
    "resultantes num sistema de otimização por grafos para resolver o problema de negócio (liquidez) "
    "no nível macro. Comece simples, meça os gargalos reais, e evolua de forma incremental."
)

with st.expander("Ver a matriz completa, com todos os detalhes"):
    st.markdown("""
| Estratégia | Cenário Ideal de Uso | Taxa de Transferência (TPS) | Latência (Alta Carga) | Complexidade de Implementação | Principal Vantagem | Principal Desvantagem |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Controle Pessimista** | Sistemas legados; Baixa concorrência no mesmo recurso; Transações complexas que tocam muitas tabelas. | **Baixa.** Limitada pela transação mais lenta. | **Muito Alta.** A fila cresce de forma não-linear, levando ao colapso do sistema. | **Baixa.** O padrão de `LOCK` é simples e bem estabelecido. | **Garantia de consistência forte** e simplicidade de código. | **Gargalo de performance.** Não escala para "contas quentes". |
| **2. Controle Otimista** | Sistemas distribuídos; Baixa a média probabilidade de conflito; Leituras frequentes com escritas menos frequentes. | **Média a Alta.** O throughput é alto se não houver conflitos. | **Baixa a Média.** A latência é baixa, mas falhas por conflito exigem retentativas na aplicação. | **Média.** Requer versionamento dos dados e uma lógica de retentativa no lado do cliente/aplicação. | **Alto grau de concorrência.** Leitores não bloqueiam escritores. | A aplicação **deve tratar os conflitos** e o "lost update" se não houver CAS. |
| **3. Write Sharding** | Contas "baleia" com altíssimo volume de escritas; Sistemas que precisam de escalabilidade horizontal massiva. | **Muito Alta.** A capacidade de escrita escala linearmente com o número de shards. | **Baixa.** As escritas são distribuídas e independentes. | **Alta.** Exige uma lógica de roteamento (na app ou no BD) e torna as leituras agregadas complexas. | **Escalabilidade de escrita "infinita"** para um único recurso lógico. | **Leitura agregada cara** (scatter-gather) e complexidade em transações cross-shard. |
| **4. Otimização com Grafos** | Sistemas de compensação interbancária (RTGS); Otimização de processos de negócio com dependências cíclicas. | N/A (Não é uma estratégia de TPS). | N/A (Opera em lote sobre obrigações já consolidadas). | **Alta.** Requer conhecimento de teoria dos grafos e integração com o sistema de pagamentos. | **Redução drástica da necessidade de liquidez** no sistema. | Não resolve o problema de performance da transação individual. |
""")
