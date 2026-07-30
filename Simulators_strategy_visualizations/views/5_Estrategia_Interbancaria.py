import streamlit as st
import graphviz


st.title("Arquitetura de Referência: Padrão Agregador em um Sistema de Pagamentos")
st.markdown("---")
st.markdown("""
### Resumo
Este capítulo final consolida os conceitos explorados nos estudos de caso anteriores — controle de concorrência, escalabilidade de escrita e otimização de liquidez — em uma **arquitetura de referência de duas camadas**. Esta arquitetura é projetada para resolver simultaneamente (1) o desafio técnico de processar um volume massivo de transações em uma única conta (escalabilidade de micro-nível) e (2) o desafio de negócio de otimizar a liquidez em todo o sistema de pagamento (eficiência de macro-nível).
""")
st.markdown("---")

def create_architecture_diagram():
    dot = graphviz.Digraph(comment='Arquitetura de Referência')
    dot.attr('graph', rankdir='TB', splines='ortho', compound='true')
    dot.attr('node', shape='box', style='rounded,filled', fontname="Arial", fontsize="10")
    dot.attr('edge', fontname="Arial", fontsize="9")

    # --- Nível Macro ---
    with dot.subgraph(name='cluster_macro') as macro:
        macro.attr(label='Nível Macro: Otimização de Liquidez Sistêmica (Interbanco)', style='dashed', color='darkgreen')
        macro.node('clearing_house', 'Câmara de Compensação\n(Aplica Algoritmo de Grafos - LSM)', shape='octagon', fillcolor='darkseagreen1')
    
    # --- Nível Micro ---
    with dot.subgraph(name='cluster_micro') as micro:
        micro.attr(label='Nível Micro: Escalabilidade de Conta (Intrabanco)', style='dashed')

        # Fluxo de Ingestão
        micro.node('api', 'API Gateway\n(Recebe 10.000 TPS)', shape='ellipse', fillcolor='lightblue')
        micro.node('kafka', 'Apache Kafka\n(Tópico particionado por `account_id`)', fillcolor='lightyellow')
        micro.edge('api', 'kafka', label='1. Publica eventos de transação')

        # Fluxo de Processamento
        with micro.subgraph(name='cluster_ecs') as ecs:
            ecs.attr(label='ECS / Kubernetes', style='dotted')
            ecs.node('aggregator', 'Serviço Agregador (Java/Go/Python)\n(Consumidor em Lote)', fillcolor='lightgoldenrodyellow')
        micro.edge('kafka', 'aggregator', label='2. Consome lote de eventos\n(Netting em memória)')

        # Fluxo de Persistência
        with micro.subgraph(name='cluster_db') as db:
            db.attr(label='Banco de Dados Distribuído', style='dotted')
            db.node('dynamodb', 'DynamoDB / ScyllaDB\n(Tabela Sharded)', fillcolor='lightgrey')
        micro.edge('aggregator', 'dynamodb', label='3. Escrita ÚNICA do saldo líquido\n+ Múltiplas escritas de extrato')

    # --- Conexão Micro -> Macro ---
    dot.edge('aggregator', 'clearing_house', lhead='cluster_macro', label='4. Reporta Obrigação Líquida\n(e.g., "Banco A deve $5M ao Banco D")', style='dashed', color='darkgreen', fontsize='10')

    return dot

st.header("Diagrama da Arquitetura de Duas Camadas")
st.graphviz_chart(create_architecture_diagram())
st.markdown("---")


st.header("Análise Detalhada das Camadas")

st.subheader("Nível 1 (Micro): Escalabilidade Intrabanco com o Padrão Agregador")
st.markdown("""
O primeiro desafio é técnico: como evitar que o banco de dados se torne um gargalo ao processar milhares de escritas por segundo em uma única "conta quente"? A solução é o **Padrão Agregador (The Aggregator Pattern)**, que combina as técnicas dos estudos de caso anteriores:

1.  **Ingestão e Enfileiramento (API Gateway + Kafka):** As requisições de API não atingem o banco de dados diretamente. Elas são transformadas em eventos e publicadas em um tópico Kafka, que atua como um buffer massivamente escalável. O uso do `account_id` como **chave de partição** é crucial, pois garante que todas as transações para uma mesma conta sejam processadas em ordem pelo mesmo consumidor.

2.  **Processamento em Lote (ECS Consumer):** Um serviço consumidor (rodando no ECS ou Kubernetes) não processa uma mensagem de cada vez. Ele consome um **lote** de centenas ou milhares de eventos do Kafka de uma só vez. Ele então realiza a agregação (netting) em memória: `saldo_final = saldo_atual + Σ(créditos) - Σ(débitos)`.

3.  **Persistência Otimizada (Banco de Dados Distribuído):** Após o cálculo em memória, o serviço realiza uma **única operação de escrita** para atualizar o saldo consolidado no banco de dados, utilizando **Controle de Concorrência Otimista** (versionamento) para garantir a consistência. As transações individuais são salvas de forma assíncrona para fins de extrato. O banco de dados em si já é horizontalmente escalável usando **Write Sharding** (Estudo de Caso 3) para evitar "hot partitions".

**Resultado do Nível 1:** O sistema transforma 10.000 requisições de API em apenas 1 operação de atualização de saldo no banco de dados, alcançando uma escalabilidade de escrita quase infinita no nível da conta.
""")

st.subheader("Nível 2 (Macro): Otimização de Liquidez Interbanco com Grafos")
st.markdown("""
O segundo desafio é de negócio: como reduzir a quantidade de capital (liquidez) que um banco precisa manter para liquidar suas obrigações diárias?

1.  **Geração da Obrigação Líquida:** O resultado final de todo o processamento no Nível 1 é uma obrigação líquida. Por exemplo, após processar 5.000 PIX da `Conta Power-User` do `Banco A` para várias contas no `Banco D`, o `Banco A` não precisa transferir 5.000 pequenos valores. Ele simplesmente calcula que agora tem uma obrigação líquida total de, digamos, `$5M` para o `Banco D`.

2.  **Entrada para o Sistema de Compensação:** Esta obrigação líquida (`A -> D: $5M`) é então enviada para a **Câmara de Compensação Interbancária (Clearing House)**.

3.  **Aplicação do Mecanismo de Economia de Liquidez (LSM):** A Câmara de Compensação executa o algoritmo de detecção de ciclos em grafos, exatamente como visto no Estudo de Caso 4. Ela usa a obrigação `A -> D` como uma aresta em seu grafo, procurando por ciclos de compensação com outras obrigações de outros bancos (e.g., `D -> E -> A`).

**Resultado do Nível 2:** O sistema de pagamento, como um todo, reduz drasticamente a necessidade de liquidez. O capital que seria "travado" para cobrir cada transação individual é liberado, pois apenas as obrigações líquidas finais (pós-netting) precisam ser liquidadas com dinheiro real.
""")
st.markdown("---")

st.header("Conclusão Geral")
st.markdown("""
A arquitetura de referência proposta demonstra uma solução holística para os desafios dos sistemas de pagamento modernos. Ela combina padrões de arquitetura de software (Event Sourcing, Micro-batching) com técnicas de banco de dados (Sharding, OCC) e algoritmos de otimização (Teoria dos Grafos) para criar um sistema que é simultaneamente:

-   **Massivamente Escalável:** No nível da transação individual (graças ao Padrão Agregador).
-   **Eficiente em Capital:** No nível do sistema financeiro (graças ao Netting por Grafos).

Esta abordagem em duas camadas permite que cada componente se especialize em resolver um problema específico, resultando em um todo coeso, robusto e performático.
""")
st.markdown("---")

st.header("Justificativa da Stack Tecnológica")
st.subheader("Apache Kafka: O Ledger como um Log")
st.markdown("""
- **Papel:** O Kafka atua como a **fonte da verdade (Source of Truth)** em um design de *Event Sourcing*. Ele não é apenas uma fila, mas um log de eventos distribuído, imutável e auditável que garante a ordem causal das transações.
- **Recurso Chave:** Particionamento por `account_id` para garantir o *Single Writer Principle*. O `Log Compaction` permite manter um histórico completo das transações de forma eficiente.
""")

st.subheader("Amazon DynamoDB: O Estado Materializado")
st.markdown("""
- **Papel:** Armazena o **estado atual (snapshot)** do saldo de cada conta e serve como a trava de segurança para o processamento.
- **Recurso Chave:** `Conditional Writes` (Escritas Condicionais).
- **Justificativa:** Permite a implementação do Controle de Concorrência Otimista. A lógica `UPDATE saldo WHERE versao = X` é a primitiva que garante que o processamento em lote pelo consumidor não sobrescreva um estado inconsistente.
""")

st.subheader("AWS ECS (ou Kubernetes): O Cérebro do LSM")
st.markdown("""
- **Papel:** Executa a lógica de negócio do Mecanismo de Economia de Liquidez (LSM), ou seja, o "Padrão Agregador".
- **Justificativa:** Diferente de uma função Lambda (efêmera e sem estado), um container de longa duração no ECS é ideal para esta tarefa. Ele pode manter estado em memória, otimizar conexões e, mais importante, consumir **micro-batches** do Kafka de forma eficiente, o que é essencial para a performance do algoritmo de netting.
""")

st.markdown("---")
st.subheader("Referências e Leitura Adicional")
st.markdown("""
- **Kleppmann, M. (2017).** *Designing Data-Intensive Applications*. O'Reilly Media. (Referência fundamental para os padrões de arquitetura discutidos).
- **DeCandia, G., et al. (2007).** "Dynamo: Amazon's Highly Available Key-value Store". *SOSP*. (Paper seminal sobre bancos de dados distribuídos e sharding).
- **Bech, M. L., & Soramäki, K. (2001).** "Gridlock Resolution in Payment Systems". *Bank of Finland Discussion Paper*. (Referência sobre a aplicação de grafos em sistemas financeiros).
""")