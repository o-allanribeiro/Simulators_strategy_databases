import streamlit as st

st.set_page_config(layout="wide", page_title="Análise Comparativa e Matriz de Decisão")

st.title("Análise Comparativa e Matriz de Decisão Estratégica")
st.markdown("---")
st.markdown("""
### Resumo
Esta seção final sintetiza os aprendizados dos estudos de caso anteriores em uma matriz de decisão unificada. O objetivo é prover um framework comparativo para a avaliação dos trade-offs entre as diferentes estratégias de concorrência, escalabilidade e otimização. Não existe uma "bala de prata"; a escolha da arquitetura correta é um exercício de alinhar as características de cada padrão com os requisitos específicos do negócio.
""")
st.markdown("---")

st.header("Matriz Comparativa de Estratégias Arquiteturais")

st.markdown("""
| Estratégia | Cenário Ideal de Uso | Taxa de Transferência (TPS) | Latência (Alta Carga) | Complexidade de Implementação | Principal Vantagem | Principal Desvantagem |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Controle Pessimista** | Sistemas legados; Baixa concorrência no mesmo recurso; Transações complexas que tocam muitas tabelas. | **Baixa.** Limitada pela transação mais lenta. | **Muito Alta.** A fila cresce de forma não-linear, levando ao colapso do sistema. | **Baixa.** O padrão de `LOCK` é simples e bem estabelecido. | **Garantia de consistência forte** e simplicidade de código. | **Gargalo de performance.** Não escala para "contas quentes". |
| **2. Controle Otimista** | Sistemas distribuídos; Baixa a média probabilidade de conflito; Leituras frequentes com escritas menos frequentes. | **Média a Alta.** O throughput é alto se não houver conflitos. | **Baixa a Média.** A latência é baixa, mas falhas por conflito exigem retentativas na aplicação. | **Média.** Requer versionamento dos dados e uma lógica de retentativa no lado do cliente/aplicação. | **Alto grau de concorrência.** Leitores não bloqueiam escritores. | A aplicação **deve tratar os conflitos** e o "lost update" se não houver CAS. |
| **3. Write Sharding** | Contas "baleia" com altíssimo volume de escritas; Sistemas que precisam de escalabilidade horizontal massiva. | **Muito Alta.** A capacidade de escrita escala linearmente com o número de shards. | **Baixa.** As escritas são distribuídas e independentes. | **Alta.** Exige uma lógica de roteamento (na app ou no BD) e torna as leituras agregadas complexas. | **Escalabilidade de escrita "infinita"** para um único recurso lógico. | **Leitura agregada cara** (scatter-gather) e complexidade em transações cross-shard. |
| **4. Otimização com Grafos** | Sistemas de compensação interbancária (RTGS); Otimização de processos de negócio com dependências cíclicas. | N/A (Não é uma estratégia de TPS). | N/A (Opera em lote sobre obrigações já consolidadas). | **Alta.** Requer conhecimento de teoria dos grafos e integração com o sistema de pagamentos. | **Redução drástica da necessidade de liquidez** no sistema. | Não resolve o problema de performance da transação individual. |
""")
st.markdown("---")


st.header("Como Escolher a Estratégia Certa: Um Framework de Decisão")
st.markdown("""
A matriz acima serve como um guia, mas a decisão final deve ser guiada por uma análise do seu problema de negócio específico. Faça as seguintes perguntas:

#### 1. Qual é a natureza do seu gargalo?
-   **Contenção em um único registro?** Se o problema é uma "conta quente" que recebe milhares de escritas (e.g., conta de um marketplace), o **Write Sharding** (Estratégia 3) é a solução mais indicada para escalar a escrita.
-   **Transações complexas e longas bloqueando umas às outras?** Se o problema são locks em múltiplas tabelas que geram longas filas, considere migrar para **Controle Otimista** (Estratégia 2) para permitir maior concorrência.
-   **O sistema como um todo está lento?** Se o gargalo é o hardware de um servidor monolítico, o sharding (particionamento de todo o banco, não apenas de uma conta) pode ser a solução.

#### 2. Qual a complexidade que sua equipe pode gerenciar?
-   **Equipe pequena ou projeto novo?** Comece com a solução mais simples que funciona. Um banco de dados relacional com **Controle Pessimista** (Estratégia 1) é robusto e fácil de entender. Otimize apenas quando o gargalo se tornar um problema real.
-   **Equipe experiente com cultura DevOps?** Estratégias como **Sharding na Aplicação** ou a implementação de uma arquitetura baseada em eventos (como o Padrão Agregador) oferecem performance máxima, mas exigem um investimento significativo em automação, monitoramento e complexidade de código.

#### 3. O problema é técnico (TPS) ou de negócio (eficiência de capital)?
-   Se o seu mandato é "garantir que a API de PIX nunca caia e aguente 10.000 TPS", seu foco deve estar nas Estratégias 1, 2 e 3.
-   Se o seu mandato é "reduzir a quantidade de dinheiro que o banco precisa manter em caixa para liquidar as operações do dia", seu foco é a **Otimização com Grafos** (Estratégia 4), que opera em um nível de abstração acima do processamento de transações individuais.

#### Conclusão Final
A arquitetura ideal, como vimos no Estudo de Caso 5, muitas vezes **combina múltiplas estratégias**. Usa-se o Padrão Agregador com Sharding para resolver o problema de TPS (nível micro) e, em seguida, alimenta as obrigações líquidas resultantes em um sistema de otimização de grafos para resolver o problema de liquidez (nível macro). Comece simples, identifique gargalos com dados e evolua a arquitetura de forma incremental e informada.
""")
st.markdown("---")
