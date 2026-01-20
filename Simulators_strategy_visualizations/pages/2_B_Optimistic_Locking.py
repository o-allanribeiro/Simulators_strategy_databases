import streamlit as st
import graphviz
import random
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Cenário B: Bloqueio Otimista com DynamoDB")

# --- Funções de Simulação e Visualização ---
def generate_optimistic_locking_graph(concurrency, winner_thread, failed_threads, use_buffer):
    dot = graphviz.Digraph('OptimisticLock', comment='Compare-and-Swap')
    dot.attr('graph', rankdir='TB', splines='ortho')

    with dot.subgraph(name='cluster_app') as c:
        c.attr(label='Aplicação (Threads processando PIX)', style='dashed')
        c.node_attr.update(shape='circle')
        for i in range(concurrency):
            if i == winner_thread:
                c.node(f'thread_{i}', f'Thread {i+1}', style='filled', fillcolor='lightgreen')
            elif i in failed_threads:
                c.node(f'thread_{i}', f'Thread {i+1}', style='filled', fillcolor='salmon')
            else:
                 c.node(f'thread_{i}', f'Thread {i+1}')
    
    with dot.subgraph(name='cluster_db') as c:
        c.attr(label='Banco de Dados (DynamoDB)', style='filled', color='lightblue')
        c.node('db_record', '{<pk> PK: CONTA-123 | Saldo: R$90 | Versão: 2}', shape='record')

    if use_buffer:
        dot.node('buffer', 'Fila SQS por Conta\n(Garante 1 Thread por Vez)', shape='box', style='filled', fillcolor='lightyellow')
        dot.edge(f'thread_{winner_thread}', 'buffer', style='solid', label='Consome da fila')
        dot.edge('buffer', 'db_record', label=' Acesso Ordenado')
        for i in failed_threads:
            dot.edge(f'thread_{i}', 'buffer', style='dashed', label='Enfileirando')
    
    else: # Modo "corrida livre"
        for i in range(concurrency):
            label = 'Lendo Saldo (R$100, Versão 1)'
            style = 'dotted'
            color = 'black'
            if i == winner_thread:
                label = 'SUCESSO!\n(CAS: Versão 1 == 1)'
                style = 'solid'
                color = 'green'
            elif i in failed_threads:
                label = 'FALHA!\n(CAS: Versão 1 != 2)\nRETRY'
                style = 'dashed'
                color = 'red'
            dot.edge(f'thread_{i}', 'db_record', label=label, color=color, fontcolor=color)

    return dot

# --- Interface do Streamlit ---
def render_optimistic_locking_page():
    st.title("Cenário B: O Bloqueio Otimista com DynamoDB")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Painel de Controle")
        st.markdown("**Simulação: Black Friday em um Marketplace**")
        concurrency = st.slider("Requisições PIX por segundo (TPS)", 2, 1000, 500)
        use_buffer = st.checkbox("Usar Fila de Buffer (SQS) por Conta", value=False)
        run_simulation = st.button("Executar Simulação de Concorrência")

    with col2:
        st.header("Visualização da Disputa pelo Saldo")
        if run_simulation:
            winner_thread = random.randint(0, concurrency - 1)
            failed_threads = [i for i in range(concurrency) if i != winner_thread]
            
            st.write(f"1. **Cenário:** {concurrency} PIX Débito chegam **no mesmo instante** para a conta do marketplace.")
            st.write(f"2. **Leitura Concorrente:** Todas as {concurrency} threads da aplicação leem o saldo da conta no DynamoDB: `(Saldo: R$100, Versão: 1)`. Elas fazem o cálculo do novo saldo em memória.")
            st.write(f"3. **Disputa (Race Condition):** Todas tentam executar a escrita condicional. A **Thread {winner_thread + 1}** é a mais rápida e sua escrita é aceita, atualizando a versão para 2.")
            st.write(f"4. **Falha e Retentativa:** As outras {concurrency - 1} threads recebem o erro `ConditionalCheckFailedException` e precisam reiniciar o ciclo: reler, recalcular e tentar escrever de novo.")

            graph = generate_optimistic_locking_graph(concurrency, winner_thread, failed_threads, use_buffer)
            st.graphviz_chart(graph)
        else:
            st.info("Ajuste os controles e clique em 'Executar' para simular a disputa.")

    st.header("Análise Técnica e de Escalabilidade")
    st.markdown("""
    **O Problema:** Como escalar uma conta de alto volume (ex: um marketplace na Black Friday com **500 TPS**), onde o bloqueio pessimista (Cenário A) é inviável?

    **A Solução com DynamoDB (Otimista):** O DynamoDB não usa bloqueios, permitindo leituras massivamente paralelas. A consistência é garantida na escrita através de **Escritas Condicionais** (Compare-and-Swap). A aplicação tenta atualizar o item, mas adiciona uma `ConditionExpression` que verifica se o atributo de versão não mudou.

    **Disrupção Matemática/Física (Latência vs. Carga):**
    Sem uma fila, a performance se degrada com o aumento da concorrência. A probabilidade de uma transação falhar aumenta, levando a mais retentativas. Isso não só aumenta a latência média (cada retry é uma nova chamada de API), mas também o **custo**, pois cada tentativa de escrita consome WCUs (Write Capacity Units) no DynamoDB, mesmo que falhe.
    """)

    # --- Gráfico de Escalabilidade Simulado ---
    tps_range = np.arange(10, 1001, 20)
    # Latência sem buffer: cresce exponencialmente com a concorrência devido a retries
    latency_no_buffer = 10 + (tps_range / 100) ** 2 
    # Latência com buffer: estável, pois não há retries no DB
    latency_with_buffer = np.full_like(tps_range, 15)

    chart_data = pd.DataFrame({
        "TPS Concorrente na Mesma Conta": tps_range,
        "Latência Média (ms) - Sem Fila de Buffer": latency_no_buffer,
        "Latência Média (ms) - Com Fila de Buffer (SQS)": latency_with_buffer
    }).set_index("TPS Concorrente na Mesma Conta")

    st.line_chart(chart_data)

    st.header("Deep Dive: Estrutura e Configuração no DynamoDB")
    st.markdown("""
    Para implementar esta solução, a tabela no DynamoDB seria estruturada assim:
    - **Partition Key (PK):** `ID da Conta` (ex: `CONTA-12345`). Garante que todos os dados de uma conta fiquem juntos na mesma partição física, otimizando a busca.
    - **Atributos:**
        - `saldo`: (Number) O valor do saldo.
        - `versao`: (Number) O número de versão, incrementado a cada atualização.
        - `ultima_atualizacao`: (String) Timestamp da modificação.

    **Como o DynamoDB Funciona:**
    - **Threads:** O DynamoDB é um serviço gerenciado. As "threads" que mencionamos são na sua **aplicação** (ex: Lambdas, contêineres ECS) que rodam em paralelo. O DynamoDB é construído para lidar com milhões de requisições simultâneas.
    - **Capacidade (RCU/WCU):** Você provisiona (ou usa o modo On-Demand) a capacidade de leitura e escrita. Uma `Hot Partition` (muitas requisições para a mesma PK, como no nosso cenário) pode esgotar a capacidade provisionada para aquela partição física, causando `ThrottlingException`. A fila de buffer na aplicação ajuda a mitigar isso, suavizando os picos de escrita.
    - **Escrita Condicional (A Mágica):** A API `UpdateItem` do DynamoDB permite a `ConditionExpression`. Nossa chamada seria algo como: `UpdateItem(TableName='...', Key={'PK': 'CONTA-123'}, UpdateExpression='SET saldo = :novo_saldo, versao = versao + 1', ConditionExpression='versao = :versao_antiga', ...)`
    """)
    
render_optimistic_locking_page()