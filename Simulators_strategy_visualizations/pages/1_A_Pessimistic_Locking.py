import streamlit as st
import graphviz
import random
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="Modelo Físico: Aurora/PostgreSQL")

# --- Funções do State ---
def inicializar_estado():
    if 'fila_requisicoes' not in st.session_state:
        st.session_state.fila_requisicoes = []
    if 'transacao_atual' not in st.session_state:
        st.session_state.transacao_atual = None
    if 'transacoes_comitadas' not in st.session_state:
        st.session_state.transacoes_comitadas = []
    if 'log_eventos' not in st.session_state:
        st.session_state.log_eventos = ["Simulação iniciada. Adicione requisições."]
    if 'lock_adquirido' not in st.session_state:
        st.session_state.lock_adquirido = False
    if 'pockets' not in st.session_state:
        st.session_state.pockets = {'total': 1000.00, 'bloqueado': 0.00}

def adicionar_requisicao():
    valor = round(random.uniform(10.0, 250.0), 2)
    req_id = f"pix_{int(time.time())}_{random.randint(100,999)}"
    nova_req = {'id': req_id, 'valor': valor, 'status': 'pendente'}
    st.session_state.fila_requisicoes.append(nova_req)
    log(f"Nova requisição PIX de R$ {valor:.2f} adicionada à fila.", "INFO")

def log(mensagem, tipo="DEBUG"):
    agora = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_eventos.insert(0, f"[{agora}] {tipo}: {mensagem}")

# --- Funções de Visualização ---
def desenhar_motor_postgres():
    dot = graphviz.Digraph('PostgresEngine', comment='PostgreSQL Pessimistic Locking')
    dot.attr('graph', rankdir='TB', splines='ortho', label="Motor: Aurora/PostgreSQL (Pessimista)")
    dot.attr('node', shape='box', style='rounded,filled')

    # 1. Cluster da Fila de Requisições
    with dot.subgraph(name='cluster_queue') as q:
        q.attr(label="Fila de Requisições (Limite Visual: 5)", style="dashed")
        q.node("fila_label", "Requisições Pendentes", shape="plaintext")
        
        # Limita a visualização para as primeiras 5 requisições
        reqs_para_mostrar = st.session_state.fila_requisicoes[:5]
        for i, req in enumerate(reqs_para_mostrar):
            q.node(req['id'], f"ID: {req['id'][-8:]}\nValor: R$ {req['valor']:.2f}", fillcolor="lightyellow")
            if i > 0:
                q.edge(reqs_para_mostrar[i-1]['id'], req['id'], style="invis") # Mantém a ordem vertical
    
    # 2. Cluster do Motor de Banco de Dados
    with dot.subgraph(name='cluster_engine') as e:
        e.attr(label="Engine de Banco de Dados", style="filled", color="lightgrey")
        
        lock_label = "LOCK ADQUIRIDO" if st.session_state.lock_adquirido else "LOCK LIVRE"
        lock_color = "salmon" if st.session_state.lock_adquirido else "lightgreen"
        e.node("lock_status", f"pg_advisory_xact_lock\n(CONTA-123)\n\nStatus: {lock_label}", shape="doubleoctagon", fillcolor=lock_color)

        if st.session_state.transacao_atual:
            req = st.session_state.transacao_atual
            e.node("processing", f"Processando...\nID: {req['id'][-8:]}\nValor: R$ {req['valor']:.2f}", fillcolor="lightblue")
            dot.edge(reqs_para_mostrar[0]['id'], "processing", style="dashed", label="Dequeue")
            dot.edge("processing", "lock_status", label="Adquire Lock")
        elif st.session_state.fila_requisicoes:
            dot.edge(reqs_para_mostrar[0]['id'], "lock_status", style="dashed", label="Tenta Adquirir Lock")


    # 3. Cluster de Transações Comitadas
    with dot.subgraph(name='cluster_committed') as c:
        c.attr(label="Ledger (Transações Comitadas)", style="dashed")
        c.node("ledger_label", "Registros no Banco", shape="plaintext")
        if st.session_state.transacoes_comitadas:
            last_commit = st.session_state.transacoes_comitadas[-1]
            c.node("committed", f"Último Commit:\nID: {last_commit['id'][-8:]}\nValor: R$ {last_commit['valor']:.2f}", fillcolor="palegreen")
            if st.session_state.transacao_atual:
                 dot.edge("processing", "committed", style="dashed", label="COMMIT")

    return dot
    
# --- Lógica da Simulação ---
def processar_proximo():
    if st.session_state.lock_adquirido:
        log("COMMIT da transação anterior.", "SUCCESS")
        req_anterior = st.session_state.transacao_atual
        
        # Efetivação (Baixa Real)
        st.session_state.pockets['total'] -= req_anterior['valor']
        st.session_state.pockets['bloqueado'] -= req_anterior['valor']

        st.session_state.transacoes_comitadas.append(req_anterior)
        st.session_state.transacao_atual = None
        st.session_state.lock_adquirido = False
        log(f"Lock da CONTA-123 liberado. Saldo Atual: R$ {st.session_state.pockets['total']:.2f}", "INFO")

    elif st.session_state.fila_requisicoes:
        st.session_state.lock_adquirido = True
        log("Lock da CONTA-123 adquirido pela próxima transação.", "WARN")
        
        req = st.session_state.fila_requisicoes.pop(0)
        st.session_state.transacao_atual = req
        
        # Fase de Bloqueio (Reserva)
        valor = req['valor']
        saldo_disponivel = st.session_state.pockets['total'] - st.session_state.pockets['bloqueado']
        if saldo_disponivel >= valor:
            st.session_state.pockets['bloqueado'] += valor
            log(f"Reserva de R$ {valor:.2f} efetuada. Saldo Bloqueado agora é R$ {st.session_state.pockets['bloqueado']:.2f}", "INFO")
        else:
            log(f"FALHA: Saldo disponível (R$ {saldo_disponivel:.2f}) insuficiente para reserva de R$ {valor:.2f}", "ERROR")
            # Em um cenário real, a transação falharia e seria movida para uma DLQ.
            # Aqui, vamos apenas cancelar a reserva e liberar o lock.
            st.session_state.transacao_atual = None 
            st.session_state.lock_adquirido = False
            log("Transação falhou e foi removida. Lock liberado.", "WARN")

    else:
        log("Fila de requisições vazia. Nada a processar.", "INFO")

# --- Renderização da Página ---
inicializar_estado()

st.title("Modelo Físico: Aurora/PostgreSQL (Bloqueio Pessimista)")

col_controles, col_viz, col_log = st.columns([1, 2, 1])

# --- Coluna de Controles e Saldos ---
with col_controles:
    st.header("Painel de Controle")
    if st.button("Adicionar Requisição PIX"):
        adicionar_requisicao()

    proximo_label = "Commit & Processar Próximo" if st.session_state.lock_adquirido else "Processar Próximo da Fila"
    if st.button(proximo_label, disabled=not st.session_state.fila_requisicoes and not st.session_state.lock_adquirido):
        processar_proximo()
    
    st.header("Modelo Conceitual (Saldos)")
    saldo_disponivel = st.session_state.pockets['total'] - st.session_state.pockets['bloqueado']
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; border: 1px solid #ccc;">
        <h4 style="margin-bottom: 10px;">🟢 Saldo Contábil (Total)</h4>
        <p style="font-size: 24px; font-weight: bold; margin: 0;">R$ {st.session_state.pockets['total']:.2f}</p>
        <hr>
        <h4 style="margin-bottom: 10px;">🔴 Saldo Bloqueado</h4>
        <p style="font-size: 24px; font-weight: bold; margin: 0; color: #E55;">R$ {st.session_state.pockets['bloqueado']:.2f}</p>
        <hr>
        <h4 style="margin-bottom: 10px;">🔵 Saldo Disponível (Calculado)</h4>
        <p style="font-size: 24px; font-weight: bold; margin: 0; color: #007BFF;">R$ {saldo_disponivel:.2f}</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Disponível = Total - Bloqueado")

# --- Coluna de Visualização ---
with col_viz:
    st.header("Visualização do Motor")
    st.graphviz_chart(desenhar_motor_postgres())

# --- Coluna de Log ---
with col_log:
    st.header("Log de Eventos da Simulação")
    log_container = st.container()
    log_html = ""
    for evento in st.session_state.log_eventos:
        if "SUCCESS" in evento or "Commit" in evento:
            log_html += f'<p style="color: #28a745; margin: 0; font-family: monospace;">{evento}</p>'
        elif "WARN" in evento:
            log_html += f'<p style="color: #ffc107; margin: 0; font-family: monospace;">{evento}</p>'
        elif "ERROR" in evento or "FALHA" in evento:
            log_html += f'<p style="color: #dc3545; margin: 0; font-family: monospace;">{evento}</p>'
        else:
            log_html += f'<p style="color: #6c757d; margin: 0; font-family: monospace;">{evento}</p>'
    log_container.markdown(f'<div style="height: 600px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f8f9fa;">{log_html}</div>', unsafe_allow_html=True)

st.markdown("---")
st.subheader("Análise da Estratégia")
st.markdown("""
**Bloqueio Pessimista (`SELECT FOR UPDATE` ou `pg_advisory_xact_lock`):**
- **O que é?** A primeira transação que acessa a "linha" da conta (ou um lock abstrato que a representa) a bloqueia exclusivamente. Nenhuma outra transação pode sequer ler o dado (na forma mais estrita) até que a primeira termine (faça `COMMIT` ou `ROLLBACK`).
- **Comportamento:** As transações são serializadas. Elas formam uma fila ordenada, garantindo consistência forte. É como um pedágio com uma única cabine.
- **Vantagens:** Simplicidade de implementação e garantia total de que não haverá *race conditions*. O estado do saldo é sempre consistente.
- **Desvantagens:** **Gargalo de performance**. A taxa de transferência (TPS) é limitada pela latência de uma única transação. Não escala horizontalmente para uma única conta "quente". Se uma transação demorar, todas as outras esperam.
""")
