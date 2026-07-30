import streamlit as st
import graphviz
import random
import time
from datetime import datetime

# A lógica principal da simulação (funções de estado, processamento e desenho) permanece a mesma.
# As alterações estão na camada de apresentação do Streamlit (textos, títulos, análises).

def inicializar_estado():
    if 'fila_requisicoes' not in st.session_state:
        st.session_state.fila_requisicoes = []
    if 'transacao_atual' not in st.session_state:
        st.session_state.transacao_atual = None
    if 'transacoes_comitadas' not in st.session_state:
        st.session_state.transacoes_comitadas = []
    if 'log_eventos' not in st.session_state:
        st.session_state.log_eventos = ["Simulação iniciada."]
    if 'lock_adquirido' not in st.session_state:
        st.session_state.lock_adquirido = False
    if 'pockets' not in st.session_state:
        st.session_state.pockets = {'total': 1000.00, 'bloqueado': 0.00}

def resetar_simulacao():
    st.session_state.fila_requisicoes = []
    st.session_state.transacao_atual = None
    st.session_state.transacoes_comitadas = []
    st.session_state.log_eventos = ["Simulação reiniciada."]
    st.session_state.lock_adquirido = False
    st.session_state.pockets = {'total': 1000.00, 'bloqueado': 0.00}

def adicionar_requisicao():
    valor = round(random.uniform(10.0, 250.0), 2)
    req_id = f"pix_{int(time.time())}_{random.randint(100,999)}"
    nova_req = {'id': req_id, 'valor': valor, 'status': 'pendente'}
    st.session_state.fila_requisicoes.append(nova_req)
    log(f"Nova requisição (λ) de R$ {valor:.2f} chegou ao sistema.", "INFO")

def adicionar_rajada(quantidade=10):
    for _ in range(quantidade):
        adicionar_requisicao()
    log(f"Rajada de {quantidade} transações geradas de uma vez.", "WARN")

def adicionar_transacao_alto_valor():
    saldo_disponivel = st.session_state.pockets['total'] - st.session_state.pockets['bloqueado']
    valor = round(saldo_disponivel + 100, 2) if saldo_disponivel > 0 else 999.99
    req_id = f"pix_{int(time.time())}_{random.randint(100,999)}"
    nova_req = {'id': req_id, 'valor': valor, 'status': 'pendente'}
    st.session_state.fila_requisicoes.append(nova_req)
    log(f"Transação de alto valor (R$ {valor:.2f}) adicionada — excede o saldo disponível de propósito.", "WARN")

def log(mensagem, tipo="DEBUG"):
    agora = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_eventos.insert(0, f"[{agora}] {tipo}: {mensagem}")

def desenhar_motor_postgres():
    dot = graphviz.Digraph('PostgresEngine', comment='PostgreSQL Pessimistic Locking')
    dot.attr('graph', rankdir='TB', splines='ortho')
    dot.attr('node', shape='box', style='rounded,filled')

    with dot.subgraph(name='cluster_queue') as q:
        q.attr(label="Fila de Requisições (Buffer de Entrada)", style="dashed")
        q.node("fila_label", f"Itens na Fila (Lq): {len(st.session_state.fila_requisicoes)}", shape="plaintext")
        reqs_para_mostrar = st.session_state.fila_requisicoes[:5]
        for i, req in enumerate(reqs_para_mostrar):
            q.node(req['id'], f"ID: ...{req['id'][-6:]}\nValor: R$ {req['valor']:.2f}", fillcolor="lightyellow")
            if i > 0:
                q.edge(reqs_para_mostrar[i-1]['id'], req['id'], style="invis")
    
    with dot.subgraph(name='cluster_engine') as e:
        e.attr(label="Servidor de Banco de Dados (M/D/1)", style="filled", color="lightgrey")
        lock_label = "ADQUIRIDO" if st.session_state.lock_adquirido else "LIVRE"
        lock_color = "salmon" if st.session_state.lock_adquirido else "lightgreen"
        e.node("lock_status", f"Recurso Crítico: CONTA-123\nLock de Transação\n\nStatus: {lock_label}", shape="doubleoctagon", fillcolor=lock_color)

        if st.session_state.transacao_atual:
            req = st.session_state.transacao_atual
            e.node("processing", f"Processando (Taxa μ):\nID: ...{req['id'][-6:]}", fillcolor="lightblue")
            dot.edge("fila_label", "processing", style="dashed", label="Dequeue")
            dot.edge("processing", "lock_status", label="SELECT FOR UPDATE")
        elif st.session_state.fila_requisicoes:
            dot.edge(reqs_para_mostrar[0]['id'], "lock_status", style="dashed", label="Tenta adquirir lock")

    with dot.subgraph(name='cluster_committed') as c:
        c.attr(label="Ledger (Estado Consistente)", style="dashed")
        c.node("ledger_label", f"Transações Comitadas: {len(st.session_state.transacoes_comitadas)}", shape="plaintext")
        if st.session_state.transacoes_comitadas:
            last_commit = st.session_state.transacoes_comitadas[-1]
            c.node("committed", f"Último Commit:\nID: ...{last_commit['id'][-6:]}", fillcolor="palegreen")
            if st.session_state.transacao_atual:
                 dot.edge("processing", "committed", style="dashed", label="COMMIT")

    return dot
    
def processar_proximo():
    if st.session_state.lock_adquirido:
        log("COMMIT da transação. Liberação do lock.", "SUCCESS")
        req_anterior = st.session_state.transacao_atual
        st.session_state.pockets['total'] -= req_anterior['valor']
        st.session_state.pockets['bloqueado'] -= req_anterior['valor']
        st.session_state.transacoes_comitadas.append(req_anterior)
        st.session_state.transacao_atual = None
        st.session_state.lock_adquirido = False
        log(f"Recurso CONTA-123 liberado. Saldo: R$ {st.session_state.pockets['total']:.2f}", "INFO")

    elif st.session_state.fila_requisicoes:
        st.session_state.lock_adquirido = True
        log("Adquiriu lock exclusivo sobre o recurso CONTA-123.", "WARN")
        req = st.session_state.fila_requisicoes.pop(0)
        st.session_state.transacao_atual = req
        valor = req['valor']
        saldo_disponivel = st.session_state.pockets['total'] - st.session_state.pockets['bloqueado']
        if saldo_disponivel >= valor:
            st.session_state.pockets['bloqueado'] += valor
            log(f"Reserva de R$ {valor:.2f} efetuada (BEGIN TX).", "INFO")
        else:
            log(f"FALHA: Saldo insuficiente (R$ {saldo_disponivel:.2f}) para R$ {valor:.2f}. ROLLBACK.", "ERROR")
            st.session_state.transacao_atual = None 
            st.session_state.lock_adquirido = False
            log("Transação falhou. Lock liberado.", "WARN")
    else:
        log("Fila vazia.", "INFO")

# --- Início da Renderização da Página ---
inicializar_estado()

st.title("Estudo de Caso 1: Controle de Concorrência Pessimista")
st.markdown("---")

st.markdown(f"""
### Resumo
Este experimento modela o comportamento de um sistema de banco de dados relacional (como PostgreSQL ou Oracle) que emprega uma estratégia de **Controle de Concorrência Pessimista (PCC)**. Sob este paradigma, assume-se que conflitos de transação são prováveis. Portanto, para garantir a consistência, o sistema bloqueia preventivamente os recursos de dados no início de uma transação (`SELECT FOR UPDATE`), forçando outras transações que requerem o mesmo recurso a esperar. Esta simulação visualiza o efeito de tal serialização sob uma carga de trabalho concorrente.
""")

st.info(
    "**Como funciona:** clique em \"Nova transação chegou\" para simular um cliente enviando um Pix para a fila. "
    "Clique em \"Processar 1 transação\" para o banco atender a fila, uma de cada vez — ele precisa travar "
    "(\"lock\") o recurso antes de processar e só libera no fim. Gere transações mais rápido do que processa e "
    "veja a fila crescer."
)
st.markdown("---")


col_controles, col_viz, col_log = st.columns([1, 2, 1])

# --- Coluna de Controles e Saldos ---
with col_controles:
    st.header("Controles")
    if st.button(
        "Nova transação chegou",
        help="Na Teoria das Filas, isso representa a taxa de chegada (λ): uma nova requisição entra no sistema.",
    ):
        adicionar_requisicao()

    if st.button(
        "Processar 1 transação",
        help="Representa um ciclo de serviço (μ): o banco processa a transação do início da fila e libera o lock ao final.",
        disabled=not st.session_state.fila_requisicoes and not st.session_state.lock_adquirido,
    ):
        processar_proximo()

    st.markdown("**Cenários prontos:**")
    if st.button(
        "Simular rajada (10 chegadas de uma vez)",
        help="Adiciona 10 transações na fila de uma só vez, sem precisar clicar 10 vezes — útil para ver a fila crescer rápido.",
    ):
        adicionar_rajada(10)

    if st.button(
        "Forçar transação de alto valor (vai falhar)",
        help="Adiciona uma transação maior que o saldo disponível atual, garantindo que o próximo processamento resulte em ROLLBACK por saldo insuficiente.",
    ):
        adicionar_transacao_alto_valor()

    if st.button("Reiniciar simulação", help="Limpa a fila, o log e o saldo — útil para começar cada cenário do zero."):
        resetar_simulacao()

    st.header("Estado do Recurso (Conta-123)")
    saldo_disponivel = st.session_state.pockets['total'] - st.session_state.pockets['bloqueado']
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; border: 1px solid #ccc; background-color: #f8f9fa;">
        <p style="font-size: 16px; margin: 0;"><b>Saldo Contábil:</b> R$ {st.session_state.pockets['total']:.2f}</p>
        <p style="font-size: 16px; margin: 0; color: #E55;"><b>Saldo Bloqueado (em Tx):</b> R$ {st.session_state.pockets['bloqueado']:.2f}</p>
        <p style="font-size: 16px; margin: 0; color: #007BFF;"><b>Saldo Disponível:</b> R$ {saldo_disponivel:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

# --- Coluna de Visualização ---
with col_viz:
    st.header("O que está acontecendo agora")
    st.graphviz_chart(desenhar_motor_postgres())
    st.caption(
        "Amarelo: transações esperando na fila · Verde: recurso livre · Vermelho: recurso travado (em uso) · "
        "Verde claro: já processado e registrado no ledger."
    )

# --- Coluna de Log ---
with col_log:
    st.header("Log de Eventos (Trace)")
    log_container = st.container()
    log_html = "".join([
        f'<p style="color: #28a745; margin: 0; font-family: monospace;">{evento}</p>' if "SUCCESS" in evento else
        f'<p style="color: #ffc107; margin: 0; font-family: monospace;">{evento}</p>' if "WARN" in evento else
        f'<p style="color: #dc3545; margin: 0; font-family: monospace;">{evento}</p>' if "ERROR" in evento else
        f'<p style="color: #6c757d; margin: 0; font-family: monospace;">{evento}</p>'
        for evento in st.session_state.log_eventos
    ])
    log_container.markdown(f'<div style="height: 600px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f8f9fa;">{log_html}</div>', unsafe_allow_html=True)

st.markdown("---")

st.subheader("Cenários para Explorar")
st.markdown("""
Dica: clique em "Reiniciar simulação" antes de cada cenário abaixo para começar do zero.

**Cenário 1 — Fluxo Normal (sem fila):**
1. Clique em "Nova transação chegou".
2. Clique em "Processar 1 transação" logo em seguida.
3. A transação é comitada sem nunca formar fila — é o caso feliz, sem contenção.

**Cenário 2 — Colapso da Fila (alta concorrência):**
1. Clique em "Simular rajada (10 chegadas de uma vez)".
2. Repare na Fila de Requisições (Lq) do diagrama saltando para 10 itens de uma vez.
3. Clique em "Processar 1 transação" repetidamente e note quanto tempo leva pra fila esvaziar — é exatamente o efeito da Lei de Little: com λ muito maior que μ, a fila cresce muito mais rápido do que o sistema consegue drenar.

**Cenário 3 — Saldo Insuficiente (falha e rollback):**
1. Clique em "Forçar transação de alto valor (vai falhar)".
2. Clique em "Processar 1 transação".
3. Veja no log, em vermelho, a falha: o sistema tenta reservar o valor, detecta saldo insuficiente e faz ROLLBACK — o lock é liberado imediatamente, sem comitar nada.
""")

st.subheader("Conclusão")
st.markdown("""
O bloqueio pessimista garante consistência de forma simples e robusta, mas ao custo de criar um gargalo (um único ponto de serialização) que impede a escalabilidade horizontal para um recurso de alta contenção. É uma estratégia eficaz quando o volume de transações concorrentes para o mesmo recurso é baixo — o problema aparece quando a fila cresce mais rápido do que o sistema consegue processar.
""")

with st.expander("Aprofundar: por que a fila cresce (Lei de Little e filas M/D/1)"):
    st.markdown(r"""
**Interpretação da Simulação:**
- **Taxa de Chegada (λ):** Cada clique no botão "Nova transação chegou" simula uma nova transação chegando ao sistema.
- **Taxa de Serviço (μ):** O clique em "Processar 1 transação" representa um único ciclo de processamento do banco de dados (o tempo para executar a lógica de negócio e o COMMIT).

**Observação Empírica:**
A simulação demonstra um princípio fundamental da **Teoria das Filas**. O sistema se comporta como uma fila do tipo **M/D/1** (Chegadas de Markov, Tempo de Serviço Determinístico, 1 Servidor). O "servidor" é o lock da conta, que só pode atender uma transação por vez.

Ao aumentar a frequência de chegadas (clicar em "Nova transação chegou" mais rápido do que em "Processar 1 transação"), a **Fila de Requisições (Lq)** começa a crescer. Este é o efeito previsto pela **Lei de Little ($L = \lambda W$)**:
1.  Quando a taxa de chegada ($\lambda$) é significativamente menor que a taxa de serviço ($\mu$), a fila permanece vazia ou pequena.
2.  À medida que $\lambda$ se aproxima de $\mu$, o tempo de espera no sistema ($W$) para cada transação aumenta drasticamente. Como $L = \lambda W$, o tamanho da fila ($L$) também cresce de forma não-linear.
3.  Se $\lambda \ge \mu$, a fila teoricamente cresce ao infinito, e o sistema colapsa em termos de latência.
""")

with st.expander("Aprofundar: alternativas ao bloqueio e referências"):
    st.markdown("""
**Alternativas ao Bloqueio: Arquiteturas Lock-Free (LMAX Disruptor)**

A principal conclusão do modelo pessimista é que **locks são gargalos**. Em sistemas de altíssima frequência (HFT), a contenção por locks é inaceitável. A arquitetura **LMAX Disruptor**, desenvolvida para uma bolsa de valores de Londres, popularizou o **"Single Writer Principle"** (Princípio do Escritor Único).
A ideia é redesenhar a arquitetura para que, por design, apenas **uma única thread** tenha permissão para modificar um recurso crítico. Se não há múltiplos escritores, não há concorrência pela escrita, e, portanto, **não há necessidade de locks**.
Isto é frequentemente alcançado com filas em memória e particionamento de dados, onde cada partição é "possuída" por uma thread. Este conceito é a base para o "Padrão Agregador" que veremos mais adiante, onde o Kafka garante que todas as transações de uma conta sejam processadas por um único consumidor.

---

**Referências e Leitura Adicional**
- **Bernstein, P. A., & Newcomer, E. (2009).** *Principles of Transaction Processing*. Morgan Kaufmann. (Capítulos sobre Two-Phase Locking).
- **Gray, J., & Reuter, A. (1992).** *Transaction Processing: Concepts and Techniques*. Morgan Kaufmann.
- **Thompson, M. et al.** "LMAX Disruptor: High Performance Inter-Thread Messaging Library". *LMAX Exchange*. (Apresenta o conceito de design mecânico e o Single Writer Principle).
""")