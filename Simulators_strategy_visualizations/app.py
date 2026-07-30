import streamlit as st

st.set_page_config(
    page_title="Análise de Arquiteturas para Sistemas Financeiros",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Análise Comparativa de Arquiteturas para Sistemas de Pagamento de Alta Frequência")
st.caption("Trabalho Apresentado como Requisito para Modelagem de Sistemas Distribuídos")
st.divider()

# --- Abstract ---
st.header("Resumo")
st.markdown("""
O presente trabalho explora, através de um laboratório de simulação computacional, os trade-offs críticos entre diferentes estratégias de controle de concorrência e escalabilidade em sistemas de pagamento de alta frequência (HFT). Com a ascensão de sistemas de pagamento instantâneo (SPIs), a demanda por baixa latência e alta disponibilidade colide com a necessidade de consistência estrita dos dados, um dilema governado por princípios como os teoremas CAP e PACELC. Este simulador modela cenários práticos, permitindo a análise visual e quantitativa do desempenho de arquiteturas monolíticas com **bloqueio pessimista** frente a arquiteturas distribuídas que utilizam **versionamento otimista**, **write sharding**, e **otimização de liquidez com teoria de grafos**. O objetivo é prover um framework didático para a tomada de decisão arquitetural, fundamentada em evidências empíricas geradas pelas simulações.
""")
st.divider()

# --- Table of Contents ---
st.header("Estrutura do Estudo")
st.markdown("""
- **[1. Introdução](#1-introducao)**: Definição do problema e a questão de pesquisa.
- **[2. Fundamentação Teórica](#2-fundamentacao-teorica)**: Os pilares científicos que governam os sistemas distribuídos.
  - [2.1. O Dilema da Distribuição: Teoremas CAP e PACELC](#2-1-o-dilema-da-distribuicao-teoremas-cap-e-pacelc)
  - [2.2. A Física da Performance: Teoria das Filas e Lei de Little](#2-2-a-fisica-da-performance-teoria-das-filas-e-lei-de-little)
- **[3. Metodologia: Estudo de Casos Simulados](#3-metodologia-estudo-de-casos-simulados)**: Descrição dos experimentos.
  - [3.1. Caso 1: Controle de Concorrência Pessimista](#3-1-caso-1-controle-de-concorrencia-pessimista)
  - [3.2. Caso 2: Controle de Concorrência Otimista](#3-2-caso-2-controle-de-concorrencia-otimista)
  - [3.3. Caso 3: Escalabilidade com Write Sharding](#3-3-caso-3-escalabilidade-com-write-sharding)
  - [3.4. Caso 4: Otimização de Liquidez com Grafos](#3-4-caso-4-otimizacao-de-liquidez-com-grafos)
  - [3.5. Caso 5: Arquitetura de Referência Agregadora](#3-5-caso-5-arquitetura-de-referencia-agregadora)
- **[4. Análise Comparativa e Conclusões](#4-analise-comparativa-e-conclusoes)**
- **[5. Referências Bibliográficas](#5-referencias-bibliograficas)**
""")
st.divider()


# --- Content ---
st.header("1. Introdução")
st.markdown("""
A proliferação de sistemas de pagamento instantâneo (SPIs) impôs um novo paradigma para a engenharia de software no setor financeiro. A questão deixou de ser apenas *se* uma transação pode ser processada de forma segura, mas *se* milhões de transações concorrentes podem ser processadas de forma segura, com latência de milissegundos e disponibilidade contínua (24/7). Este desafio expõe uma tensão fundamental entre consistência, disponibilidade e latência.

A questão central que este estudo busca responder é: **Quais são os trade-offs quantificáveis entre os diferentes padrões arquiteturais para a gestão de um livro-razão (ledger) distribuído sob alta carga?** Para tal, desenvolveu-se uma suíte de simulações interativas que modelam o comportamento de diferentes estratégias, desde o bloqueio pessimista tradicional até padrões de sharding e otimização de liquidez.
""", unsafe_allow_html=True)


st.header("2. Fundamentação Teórica")
st.markdown("""
As simulações apresentadas são a manifestação prática de teorias consolidadas da Ciência da Computação.
""", unsafe_allow_html=True)

st.subheader("2.1. O Dilema da Distribuição: Teoremas CAP e PACELC")
st.markdown("""
O **Teorema CAP (Brewer, 2000)** estabelece que um sistema distribuído pode, no máximo, satisfazer duas de três garantias: Consistência (todos os nós veem os mesmos dados ao mesmo tempo), Disponibilidade (todas as requisições recebem uma resposta) e Tolerância a Partições de rede. Dado que partições de rede são uma certeza em sistemas de larga escala, a escolha de projeto recai sobre sacrificar a consistência ou a disponibilidade durante uma falha.

O **Teorema PACELC (Abadi, 2012)** refina essa noção para o mundo real, argumentando que, mesmo na ausência de partições (**E**lse), existe um trade-off entre **L**atência e **C**onsistência. Para sistemas financeiros, esta segunda parte do teorema é crucial: a busca por consistência forte (e.g., através de protocolos de consenso ou locks) inerentemente introduz latência.
""", unsafe_allow_html=True)


st.subheader("2.2. A Física da Performance: Teoria das Filas e Lei de Little")
st.markdown(r"""
A performance de sistemas transacionais pode ser modelada pela **Teoria das Filas**. A **Lei de Little (1961)**, expressa como $L = \lambda W$, é particularmente poderosa. Ela afirma que o número médio de itens em um sistema ($L$, o "tamanho da fila") é igual à taxa média de chegada desses itens ($\lambda$, transações por segundo) multiplicada pelo tempo médio de permanência de um item no sistema ($W$, a latência).

Em um modelo de **bloqueio pessimista**, onde o acesso a um recurso é serializado, o sistema se comporta como uma fila M/D/1. Se a taxa de chegada ($\lambda$) se aproxima da taxa de serviço ($\mu$), a latência ($W$) e, consequentemente, o tamanho da fila ($L$), crescem de forma não-linear, tendendo ao infinito.
> A demonstração deste colapso de performance é o foco do **[Caso 1: Controle de Concorrência Pessimista](1_Controle_de_Concorr_ncia_Pessimista)**.
""", unsafe_allow_html=True)
st.divider()


st.header("3. Metodologia: Estudo de Casos Simulados")
st.markdown("""
Navegue pelas páginas no menu à esquerda para interagir com cada estudo de caso. A metodologia adotada foi a de simulação de eventos discretos para modelar o comportamento de cada arquitetura sob carga variável.
""", unsafe_allow_html=True)
st.divider()


st.header("4. Análise Comparativa e Conclusões")
st.markdown("""
A página de **Matriz de Decisão Estratégica** consolida os resultados observados, oferecendo uma análise comparativa dos trade-offs de cada arquitetura em eixos como taxa de transferência (TPS), latência, complexidade de implementação e custo operacional.
- **Link:** **[Ir para a Matriz de Decisão](6_Matriz_de_Decisao_Estrategica)**
""", unsafe_allow_html=True)
st.divider()

st.header("5. Referências Bibliográficas")
st.markdown("""
1.  **Abadi, D. J. (2012).** "Consistency Tradeoffs in Modern Distributed Database System Design". *IEEE Computer*.
2.  **Brewer, E. (2000).** "Towards Robust Distributed Systems". *Symposium on Principles of Distributed Computing (PODC)*.
3.  **Gilbert, S., & Lynch, N. (2002).** "Brewer's conjecture and the feasibility of consistent, available, partition-tolerant web services". *ACM SIGACT News*.
4.  **Kleppmann, M. (2017).** *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems*. O'Reilly Media.
5.  **Little, J. D. C. (1961).** "A Proof for the Queuing Formula: L = λW". *Operations Research*.
6.  **Bernstein, P. A., & Newcomer, E. (2009).** *Principles of Transaction Processing*. Morgan Kaufmann.
""", unsafe_allow_html=True)