import graphviz
import streamlit as st

from nav import pg_interbancaria, pg_matriz, pg_netting, pg_otimista, pg_pessimista, pg_sharding

st.title("Análise Comparativa de Arquiteturas para Sistemas de Pagamento de Alta Frequência")
st.caption("Trabalho Apresentado como Requisito para Modelagem de Sistemas Distribuídos")
st.divider()

# --- Abstract ---
st.header("Resumo")
st.markdown("""
O presente trabalho explora, através de um laboratório de simulação computacional, os trade-offs críticos entre diferentes estratégias de controle de concorrência e escalabilidade em sistemas de pagamento de alta frequência (HFT). Com a ascensão de sistemas de pagamento instantâneo (SPIs), a demanda por baixa latência e alta disponibilidade colide com a necessidade de consistência estrita dos dados, um dilema governado por princípios como os teoremas CAP e PACELC. Este simulador modela cenários práticos, permitindo a análise visual e quantitativa do desempenho de arquiteturas monolíticas com **bloqueio pessimista** frente a arquiteturas distribuídas que utilizam **versionamento otimista**, **write sharding**, e **otimização de liquidez com teoria de grafos**. O objetivo é prover um framework didático para a tomada de decisão arquitetural, fundamentada em evidências empíricas geradas pelas simulações.
""")
st.divider()

# --- Organograma: como os 6 estudos de caso se relacionam ---
st.header("Como os Estudos de Caso se Relacionam")
st.markdown("""
Os seis estudos de caso não são independentes: os três primeiros atacam o problema no **nível micro** (como uma transação individual é processada), os dois seguintes atacam o problema no **nível macro** (como o conjunto de obrigações do sistema é liquidado), e a Matriz de Decisão sintetiza os dois níveis num framework único.
""")

dot = graphviz.Digraph()
dot.attr(rankdir="TB", bgcolor="white")
dot.attr("node", shape="box", style="rounded,filled", fontname="Helvetica", fontsize="11")
dot.attr("edge", color="#94a3b8")

dot.node("problema", "Sistema de Pagamento\nde Alta Frequência", fillcolor="#1f2937", fontcolor="white")

with dot.subgraph(name="cluster_micro") as c:
    c.attr(label="Nível Micro — por transação", style="dashed", color="#2563eb", fontsize="11")
    c.node("c1", "1. Controle\nPessimista", fillcolor="#bfdbfe")
    c.node("c2", "2. Controle\nOtimista", fillcolor="#bfdbfe")
    c.node("c3", "3. Write\nSharding", fillcolor="#bfdbfe")

with dot.subgraph(name="cluster_macro") as c:
    c.attr(label="Nível Macro — liquidez agregada", style="dashed", color="#b45309", fontsize="11")
    c.node("c4", "4. Netting\ncom Grafos", fillcolor="#fde68a")
    c.node("c5", "5. Arquitetura\nAgregadora", fillcolor="#fde68a")

dot.node("c6", "6. Matriz de Decisão\n(Síntese)", fillcolor="#86efac")

for micro in ("c1", "c2", "c3"):
    dot.edge("problema", micro)
for macro in ("c4", "c5"):
    dot.edge("problema", macro)
for caso in ("c1", "c2", "c3", "c4", "c5"):
    dot.edge(caso, "c6")

st.graphviz_chart(dot, use_container_width=True)
st.divider()

# --- Table of Contents ---
st.header("Estrutura do Estudo")
st.markdown("""
- **1. Introdução**: Definição do problema e a questão de pesquisa.
- **2. Fundamentação Teórica**: Os pilares científicos que governam os sistemas distribuídos.
- **3. Metodologia: Estudo de Casos Simulados**: navegue pelos 5 casos abaixo.
""")

nav_cols = st.columns(5)
case_pages = [pg_pessimista, pg_otimista, pg_sharding, pg_netting, pg_interbancaria]
for col, page in zip(nav_cols, case_pages):
    with col:
        st.page_link(page, width="stretch")

st.markdown("")
st.markdown("- **4. Análise Comparativa e Conclusões**")
st.page_link(pg_matriz, label="Ir para a Matriz de Decisão")
st.divider()

# --- Content ---
st.header("1. Introdução")
st.markdown("""
A proliferação de sistemas de pagamento instantâneo (SPIs) impôs um novo paradigma para a engenharia de software no setor financeiro. A questão deixou de ser apenas *se* uma transação pode ser processada de forma segura, mas *se* milhões de transações concorrentes podem ser processadas de forma segura, com latência de milissegundos e disponibilidade contínua (24/7). Este desafio expõe uma tensão fundamental entre consistência, disponibilidade e latência.

A questão central que este estudo busca responder é: **Quais são os trade-offs quantificáveis entre os diferentes padrões arquiteturais para a gestão de um livro-razão (ledger) distribuído sob alta carga?** Para tal, desenvolveu-se uma suíte de simulações interativas que modelam o comportamento de diferentes estratégias, desde o bloqueio pessimista tradicional até padrões de sharding e otimização de liquidez.
""")


st.header("2. Fundamentação Teórica")
st.markdown("""
As simulações apresentadas são a manifestação prática de teorias consolidadas da Ciência da Computação.
""")

st.subheader("2.1. O Dilema da Distribuição: Teoremas CAP e PACELC")
st.markdown("""
O **Teorema CAP (Brewer, 2000)** estabelece que um sistema distribuído pode, no máximo, satisfazer duas de três garantias: Consistência (todos os nós veem os mesmos dados ao mesmo tempo), Disponibilidade (todas as requisições recebem uma resposta) e Tolerância a Partições de rede. Dado que partições de rede são uma certeza em sistemas de larga escala, a escolha de projeto recai sobre sacrificar a consistência ou a disponibilidade durante uma falha.

O **Teorema PACELC (Abadi, 2012)** refina essa noção para o mundo real, argumentando que, mesmo na ausência de partições (**E**lse), existe um trade-off entre **L**atência e **C**onsistência. Para sistemas financeiros, esta segunda parte do teorema é crucial: a busca por consistência forte (e.g., através de protocolos de consenso ou locks) inerentemente introduz latência.
""")


st.subheader("2.2. A Física da Performance: Teoria das Filas e Lei de Little")
st.markdown(r"""
A performance de sistemas transacionais pode ser modelada pela **Teoria das Filas**. A **Lei de Little (1961)**, expressa como $L = \lambda W$, é particularmente poderosa. Ela afirma que o número médio de itens em um sistema ($L$, o "tamanho da fila") é igual à taxa média de chegada desses itens ($\lambda$, transações por segundo) multiplicada pelo tempo médio de permanência de um item no sistema ($W$, a latência).

Em um modelo de **bloqueio pessimista**, onde o acesso a um recurso é serializado, o sistema se comporta como uma fila M/D/1. Se a taxa de chegada ($\lambda$) se aproxima da taxa de serviço ($\mu$), a latência ($W$) e, consequentemente, o tamanho da fila ($L$), crescem de forma não-linear, tendendo ao infinito.
""")
st.page_link(pg_pessimista, label="Ver a demonstração deste colapso de performance: Caso 1 — Controle de Concorrência Pessimista")
st.divider()


st.header("3. Metodologia: Estudo de Casos Simulados")
st.markdown("""
Navegue pelas páginas no menu à esquerda para interagir com cada estudo de caso. A metodologia adotada foi a de simulação de eventos discretos para modelar o comportamento de cada arquitetura sob carga variável.
""")
st.divider()


st.header("4. Análise Comparativa e Conclusões")
st.markdown("""
A página de **Matriz de Decisão Estratégica** consolida os resultados observados, oferecendo uma análise comparativa dos trade-offs de cada arquitetura em eixos como taxa de transferência (TPS), latência, complexidade de implementação e custo operacional.
""")
st.page_link(pg_matriz, label="Ir para a Matriz de Decisão")
st.divider()

st.header("5. Referências Bibliográficas")
st.markdown("""
1.  **Abadi, D. J. (2012).** "Consistency Tradeoffs in Modern Distributed Database System Design". *IEEE Computer*.
2.  **Brewer, E. (2000).** "Towards Robust Distributed Systems". *Symposium on Principles of Distributed Computing (PODC)*.
3.  **Gilbert, S., & Lynch, N. (2002).** "Brewer's conjecture and the feasibility of consistent, available, partition-tolerant web services". *ACM SIGACT News*.
4.  **Kleppmann, M. (2017).** *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems*. O'Reilly Media.
5.  **Little, J. D. C. (1961).** "A Proof for the Queuing Formula: L = λW". *Operations Research*.
6.  **Bernstein, P. A., & Newcomer, E. (2009).** *Principles of Transaction Processing*. Morgan Kaufmann.
""")
