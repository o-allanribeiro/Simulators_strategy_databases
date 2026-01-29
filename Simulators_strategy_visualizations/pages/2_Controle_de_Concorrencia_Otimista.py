import streamlit as st
import graphviz

st.set_page_config(layout="wide", page_title="Estudo de Caso 2: Controle de Concorrência Otimista")

# --- Estado da Simulação ---
def inicializar_estado_occ():
    if 'server_state' not in st.session_state:
        st.session_state.server_state = {'saldo': 1000, 'versao': 1}
    if 'client_a' not in st.session_state:
        st.session_state.client_a = {'saldo_lido': None, 'versao_lida': None, 'status': 'Não iniciado'}
    if 'client_b' not in st.session_state:
        st.session_state.client_b = {'saldo_lido': None, 'versao_lida': None, 'status': 'Não iniciado'}
    if 'occ_log' not in st.session_state:
        st.session_state.occ_log = ["Simulação OCC iniciada."]

def occ_log(msg):
    st.session_state.occ_log.insert(0, msg)

# --- Lógica da Simulação ---
def client_read(client_id):
    client = st.session_state[client_id]
    server = st.session_state.server_state
    client['saldo_lido'] = server['saldo']
    client['versao_lida'] = server['versao']
    client['status'] = 'Leu Saldo e Versão'
    occ_log(f"CLIENTE {client_id[-1].upper()}: LEU saldo R$ {client['saldo_lido']} na versão {client['versao_lida']}.")

def client_commit(client_id, valor_debito):
    client = st.session_state[client_id]
    server = st.session_state.server_state
    
    if client['versao_lida'] is None:
        client['status'] = 'ERRO: Deve ler antes de comitar.'
        occ_log(f"CLIENTE {client_id[-1].upper()}: TENTATIVA DE COMMIT SEM LEITURA PRÉVIA.")
        return

    occ_log(f"CLIENTE {client_id[-1].upper()}: Tenta comitar débito de R$ {valor_debito} com a versão {client['versao_lida']}.")
    
    # Compare-and-Swap (CAS)
    if client['versao_lida'] == server['versao']:
        # Sucesso! A versão não mudou desde a leitura.
        server['saldo'] -= valor_debito
        server['versao'] += 1
        client['status'] = f'SUCESSO: Commit do débito de R$ {valor_debito} aceito.'
        occ_log(f"SERVIDOR: Versão bate ({client['versao_lida']}). COMMIT ACEITO. Novo saldo R$ {server['saldo']}, nova versão {server['versao']}.")
    else:
        # Falha! O dado mudou.
        client['status'] = f'FALHA: Conflito de versão detectado (versão do servidor: {server['versao']})'
        occ_log(f"SERVIDOR: Versão não bate (esperava {client['versao_lida']}, mas é {server['versao']}). COMMIT REJEITADO.")

def reset_occ():
    inicializar_estado_occ()
    st.session_state.server_state = {'saldo': 1000, 'versao': 1}
    st.session_state.occ_log = ["Simulação OCC reiniciada."]


# --- Visualização ---
def desenhar_occ_diagram():
    dot = graphviz.Digraph('OCC_Simulation')
    dot.attr('graph', rankdir='TB', splines='ortho')
    dot.attr('node', shape='box', style='rounded,filled')

    # Server
    server = st.session_state.server_state
    dot.node('server', f"SERVIDOR (Banco de Dados)\nSaldo: R$ {server['saldo']}\nVersão: {server['versao']}", fillcolor='lightgreen', shape='octagon')

    # Clients
    client_a = st.session_state.client_a
    client_b = st.session_state.client_b
    
    dot.node('client_a', f"CLIENTE A\nLido: Saldo R$ {client_a['saldo_lido']}, Versão {client_a['versao_lida']}\nStatus: {client_a['status']}", fillcolor='lightblue')
    dot.node('client_b', f"CLIENTE B\nLido: Saldo R$ {client_b['saldo_lido']}, Versão {client_b['versao_lida']}\nStatus: {client_b['status']}", fillcolor='lightyellow')
    
    # Arestas
    dot.edge('server', 'client_a', label='1. READ', style='dashed')
    dot.edge('server', 'client_b', label='2. READ', style='dashed')
    dot.edge('client_a', 'server', label='3. COMMIT?', dir='back', style='dotted')
    dot.edge('client_b', 'server', label='4. COMMIT?', dir='back', style='dotted')

    return dot

# --- Início da Renderização da Página ---
st.set_page_config(layout="wide", page_title="Estudo de Caso 2: Controle de Concorrência Otimista")
inicializar_estado_occ()

st.title("Estudo de Caso 2: Controle de Concorrência Otimista (OCC)")
st.markdown("---")
st.markdown("""
### Resumo
Este estudo de caso analisa o **Controle de Concorrência Otimista (OCC)**, um paradigma alternativo ao bloqueio pessimista. O OCC parte do pressuposto de que conflitos entre transações concorrentes são raros. Em vez de bloquear recursos preventivamente, as transações executam suas lógicas sobre uma "fotografia" dos dados e, no momento do `COMMIT`, o sistema verifica se os dados subjacentes foram alterados por outra transação. Se uma modificação (um "conflito") for detectada, a transação é abortada e cabe à aplicação decidir como lidar com o erro (geralmente, tentando novamente). Esta técnica é a base para o isolamento de snapshot (MVCC) em muitos bancos de dados modernos.
""")
st.markdown("---")

st.header("Simulação Interativa de OCC")
st.markdown("Use os botões para simular uma 'race condition' entre dois clientes tentando debitar da mesma conta.")

col_sim, col_log = st.columns([3, 1])

with col_sim:
    st.graphviz_chart(desenhar_occ_diagram())
    
    st.markdown("#### Painel de Ações")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Cliente A**")
        if st.button("Cliente A: Ler Saldo/Versão"):
            client_read('client_a')
        if st.button("Cliente A: Comitar Débito de R$ 100"):
            client_commit('client_a', 100)
    with c2:
        st.markdown("**Cliente B**")
        if st.button("Cliente B: Ler Saldo/Versão"):
            client_read('client_b')
        if st.button("Cliente B: Comitar Débito de R$ 50"):
            client_commit('client_b', 50)
    with c3:
        st.markdown("**Sistema**")
        if st.button("Resetar Simulação"):
            reset_occ()

with col_log:
    st.markdown("#### Log de Operações")
    log_html = "".join([f'<p style="color: #333; margin: 0; font-family: monospace; font-size: 12px;">{evento}</p>' for evento in st.session_state.occ_log])
    st.markdown(f'<div style="height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f8f9fa;">{log_html}</div>', unsafe_allow_html=True)


st.markdown("---")
st.header("Análise dos Resultados")
st.markdown("""
**Cenário de Sucesso (Sem Conflito):**
1.  Clique em "Cliente A: Ler". Ele lê Saldo 1000, Versão 1.
2.  Clique em "Cliente A: Comitar". O commit é aceito, pois a versão lida (1) é a mesma do servidor. O servidor atualiza o saldo para 900 e a versão para 2.

**Cenário de Falha (Race Condition):**
1.  Clique em "Cliente A: Ler". Ele lê Saldo 1000, Versão 1.
2.  Clique em "Cliente B: Ler". Ele também lê Saldo 1000, Versão 1.
3.  Clique em "Cliente A: Comitar". O commit é aceito. O saldo vira 900 e a versão do servidor vira 2.
4.  Clique em "Cliente B: Comitar". O commit **falha**. O Cliente B tenta comitar usando a versão 1, mas o servidor já está na versão 2. O sistema detectou a "race condition" e preveniu a inconsistência de dados (um "lost update").

**Conclusão:** A Concorrência Otimista oferece maior throughput que a Pessimista em cenários de baixa contenção, pois "leitores não bloqueiam escritores e vice-versa". No entanto, a complexidade é movida para a aplicação, que deve ser capaz de tratar as falhas de commit e implementar uma estratégia de retentativa (ex: exponential backoff).
""")

st.markdown("---")
st.header("Fundamentação: Versionamento e Escritas Condicionais")
st.markdown("""
O OCC depende de dois conceitos fundamentais implementados por bancos de dados modernos.
""")

st.subheader("1. Controle de Concorrência Multiversão (MVCC)")
st.markdown("""
- **Como funciona:** Em vez de sobrescrever dados, cada `UPDATE` cria uma nova versão do registro. As transações que leem os dados recebem uma "fotografia" (snapshot) do banco de dados, vendo apenas as versões que foram comitadas antes do seu início.
- **Benefício:** Permite que transações de leitura de longa duração não bloqueiem transações de escrita rápidas, e vice-versa.
- **Bancos que usam:** **PostgreSQL, CockroachDB, Oracle**.
""")

st.subheader("2. Implementação no Mundo Real: 'Conditional Writes' do DynamoDB")
st.markdown("""
A lógica `if client_version == server_version` simulada aqui é implementada na prática através de **escritas condicionais**. O **paper do Dynamo (2007)** foi um dos precursores a popularizar esta técnica em larga escala.
No DynamoDB, a operação `UpdateItem` pode incluir uma `ConditionExpression`. Esta expressão deve ser verdadeira para que a escrita seja efetuada. Para implementar o OCC, a chamada de API seria:
`UpdateItem(..., ConditionExpression="version = :expected_version")`
Onde `:expected_version` é a versão que o cliente leu. Se outro cliente atualizou o item nesse meio tempo, a versão no servidor será diferente, a condição falhará, e a API retornará um erro `ConditionalCheckFailedException`. Isso permite que a aplicação detecte o conflito e tente a operação novamente, exatamente como em nossa simulação.
""")


st.markdown("---")
st.subheader("Referências e Leitura Adicional")
st.markdown("""
- **Kung, H. T., & Robinson, J. T. (1981).** "On Optimistic Methods for Concurrency Control". *ACM Transactions on Database Systems*. (O artigo seminal sobre OCC).
- **DeCandia, G., et al. (2007).** "Dynamo: Amazon's Highly Available Key-value Store". *Symposium on Operating Systems Principles (SOSP)*.
- **Kleppmann, M. (2017).** *Designing Data-Intensive Applications*. O'Reilly Media. (Capítulos 7 e 8).
""")
