import streamlit as st

st.set_page_config(
    page_title="Simulador de Estratégias de Dados",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Simulador de Estratégias de Concorrência e Escalabilidade em Sistemas de Pagamento")
st.caption("Versão 1.0 | Autor: Allan Ribeiro")
st.divider()

# --- Abstract ---
st.header("Resumo")
st.markdown("""
Este trabalho apresenta um laboratório de experimentos computacionais interativos, desenvolvido para modelar e visualizar os trade-offs inerentes às arquiteturas de banco de dados em sistemas financeiros de alta performance. A crescente demanda por sistemas com **disponibilidade 24/7** e baixa latência, como o PIX, impõe desafios significativos de consistência e escalabilidade. Este simulador visa desmistificar tais desafios, aplicando conceitos fundamentais da Ciência da Computação — como o Teorema CAP, PACELC, Teoria das Filas e padrões de controle de concorrência — em cenários práticos e observáveis. Através de visualizações interativas, os usuários podem explorar o impacto de diferentes estratégias, como Bloqueio Pessimista e Sharding, no comportamento do sistema sob estresse.
""")
st.divider()

# --- Table of Contents ---
st.header("Índice")
st.markdown("""
- **[1. Introdução](#1-introducao)**
- **[2. Fundamentação Teórica](#2-fundamentacao-teorica)**
  - [2.1. O Trade-off Fundamental: Teorema CAP e PACELC](#2-1-o-trade-off-fundamental-teorema-cap-e-pacelc)
  - [2.2. A Matemática da Espera: Teoria das Filas](#2-2-a-matematica-da-espera-teoria-das-filas)
  - [2.3. A Solução para a "Manada Trovejante": Exponential Backoff com Jitter](#2-3-a-solucao-para-a-manada-trovejante-exponential-backoff-com-jitter)
- **[3. Metodologia (Os Experimentos)](#3-metodologia-os-experimentos)**
  - [3.1. Experimento A: Bloqueio Pessimista](#3-1-experimento-a-bloqueio-pessimista)
  - [3.2. Experimento B: Escalabilidade de Escrita com Sharding](#3-2-experimento-b-escalabilidade-de-escrita-com-sharding)
  - [3.3. Experimento C: Padrão de Write Sharding na Aplicação](#3-3-experimento-c-padrao-de-write-sharding-na-aplicacao)
- **[4. Análise Comparativa](#4-analise-comparativa)**
- **[5. Referências](#5-referencias)**
""")
st.divider()


# --- Content ---
st.header("1. Introdução")
st.markdown("""
A digitalização dos serviços financeiros e o advento de sistemas de pagamento instantâneo (SPIs), como o PIX no Brasil, revolucionaram as expectativas dos consumidores e os requisitos técnicos para as instituições financeiras. A necessidade de operar com **disponibilidade contínua (24/7)**, processando um volume massivo de transações com latência na casa dos milissegundos, colide diretamente com a necessidade de **consistência** absoluta dos dados, especialmente em um livro-razão (ledger) financeiro.

Este simulador foi criado para responder a uma pergunta central: **Quais são os trade-offs concretos ao escolher uma arquitetura de banco de dados para um sistema de pagamentos moderno?** O objetivo é fornecer uma ferramenta educacional e de análise que permita a visualização do comportamento de diferentes modelos de consistência e escalabilidade sob estresse, conectando a teoria abstrata à prática observável.
""", unsafe_allow_html=True)


st.header("2. Fundamentação Teórica")
st.markdown("""
As simulações são governadas por princípios fundamentais da ciência da computação que ditam os limites e as possibilidades de sistemas distribuídos.
""", unsafe_allow_html=True)

st.subheader("2.1. O Trade-off Fundamental: Teorema CAP e PACELC")
st.markdown("""
O **Teorema CAP**, ou Teorema de Brewer, postula que um sistema distribuído pode garantir, no máximo, duas das três seguintes propriedades simultaneamente: **C**onsistência, **A**lta Disponibilidade (Availability) e Tolerância a **P**artições de rede. Como partições de rede são uma realidade inevitável, a escolha real é quase sempre entre consistência e disponibilidade.

O **Teorema PACELC** estende essa ideia, afirmando que, na presença de uma **P**artição, um sistema deve escolher entre **A**disponibilidade e **C**onsistência; **S**enão (**E**lse), em operação normal, ele deve escolher entre **L**atência e **C**onsistência. Isso é particularmente relevante para sistemas financeiros, onde mesmo sem falhas de rede, a busca por consistência forte pode aumentar a latência das operações.
""", unsafe_allow_html=True)


st.subheader("2.2. A Matemática da Espera: Teoria das Filas")
st.markdown("""
A performance de sistemas transacionais pode ser modelada pela **Teoria das Filas**. A **Lei de Little** ($L = \lambda W$) descreve a relação entre o número de itens em um sistema ($L$, o tamanho da fila), a taxa de chegada desses itens ($\lambda$, as transações por segundo) e o tempo de espera ($W$, a latência). Em cenários de bloqueio pessimista, onde as transações são serializadas, se a taxa de chegada ($\lambda$) excede a capacidade de processamento do sistema ($\mu$), a fila ($L$) e, consequentemente, a latência ($W$), tendem ao infinito.
> Veja a demonstração deste efeito na simulação do **[Modelo Pessimista](1_A_Pessimistic_Locking)**.
""", unsafe_allow_html=True)


st.subheader("2.3. A Solução para a 'Manada Trovejante': Exponential Backoff com Jitter")
st.markdown("""
Em sistemas otimistas que podem rejeitar transações (como em "Hot Partitions" no DynamoDB), múltiplas falhas podem levar a múltiplas tentativas simultâneas, um fenômeno conhecido como "manada trovejante" (*thundering herd*), que sobrecarrega o sistema ainda mais. A solução padrão é o **Exponential Backoff com Jitter**. Em vez de tentar novamente imediatamente, o cliente espera por um tempo que aumenta exponencialmente a cada falha. O **Jitter** (uma pequena variação aleatória) é adicionado a esse tempo de espera para evitar que todos os clientes tentem novamente exatamente no mesmo instante.
> Este conceito é fundamental para a resiliência do cenário de **[Sharding no DynamoDB](2_B_DynamoDB_Sharding)**.
""", unsafe_allow_html=True)
st.divider()


st.header("3. Metodologia (Os Experimentos)")
st.markdown("""
Navegue pelas simulações no menu à esquerda para explorar cada um dos seguintes experimentos.
""", unsafe_allow_html=True)

st.subheader("3.1. Experimento A: Bloqueio Pessimista")
st.markdown("""
- **Tecnologia Modelo:** Aurora/PostgreSQL
- **Estratégia:** Uso de `SELECT FOR UPDATE` para serializar o acesso a uma conta.
- **Hipótese:** A consistência forte é garantida ao custo de um gargalo de performance.
- **Link:** **[Ir para a simulação](1_A_Pessimistic_Locking)**
""", unsafe_allow_html=True)

st.subheader("3.2. Experimento B: Escalabilidade de Escrita com Sharding")
st.markdown("""
- **Tecnologia Modelo:** Amazon DynamoDB
- **Estratégia:** Uso de *Write Sharding* para distribuir escritas em múltiplas partições lógicas.
- **Hipótese:** A capacidade de escrita pode ser escalada linearmente, mas a um custo maior de complexidade para a leitura do saldo consolidado.
- **Link:** **[Ir para a simulação](2_B_DynamoDB_Sharding)**
""", unsafe_allow_html=True)

st.subheader("3.3. Experimento C: Padrão de Write Sharding na Aplicação")
st.markdown("""
- **Tecnologia Modelo:** Cluster de Bancos Relacionais (ex: PostgreSQL, CockroachDB)
- **Estratégia:** A lógica de sharding é movida para a aplicação, que decide para qual banco de dados rotear cada escrita.
- **Hipótese:** Permite escalar bancos de dados tradicionais, mas aumenta significativamente a complexidade da aplicação e de operações cross-shard.
- **Link:** **[Ir para a simulação](3_A_Write_Sharding_Pattern)**
""", unsafe_allow_html=True)
st.divider()


st.header("4. Análise Comparativa")
st.markdown("""
A página de **Matriz de Decisão** oferece uma análise comparativa dos trade-offs de cada abordagem, consolidando os aprendizados de cada simulação em um guia de referência rápido.
- **Link:** **[Ir para a Matriz de Decisão](5_Matriz_de_Decisao)**
""", unsafe_allow_html=True)
st.divider()

st.header("5. Referências")
st.markdown("""
1.  **Brewer, E. (2000).** "Towards Robust Distributed Systems". *Symposium on Principles of Distributed Computing (PODC)*.
2.  **Gilbert, S., & Lynch, N. (2002).** "Brewer's conjecture and the feasibility of consistent, available, partition-tolerant web services". *ACM SIGACT News*.
3.  **Abadi, D. J. (2012).** "Consistency Tradeoffs in Modern Distributed Database System Design". *IEEE Computer*.
4.  **Brooker, M. (2015).** "Exponential Backoff and Jitter". *AWS Architecture Blog*.
5.  **Little, J. D. C. (1961).** "A Proof for the Queuing Formula: L = λW". *Operations Research*.
""", unsafe_allow_html=True)
