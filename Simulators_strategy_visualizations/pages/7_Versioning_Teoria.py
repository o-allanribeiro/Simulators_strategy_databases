import streamlit as st
import graphviz

st.set_page_config(layout="wide", page_title="Teoria: Versionamento de Dados")

# --- Funções de Desenho ---

def draw_mvcc_diagram():
    dot = graphviz.Digraph('MVCC', comment='Multi-Version Concurrency Control')
    dot.attr('graph', rankdir='LR', splines='ortho', label="Visualização de MVCC", labelloc="t", fontsize="16")
    dot.attr('node', shape='box', style='rounded,filled')

    with dot.subgraph(name='cluster_db') as c:
        c.attr(label="Banco de Dados (Linha da Conta)", style="dashed")
        c.node('row_v1', 'Versão 1\nSaldo: R$1000\n(Válida até TXN 90)', fillcolor="lightgrey")
        c.node('row_v2', 'Versão 2\nSaldo: R$1200\n(Criada pela TXN 91)', fillcolor="lightgreen")
        c.edge('row_v1', 'row_v2', label="Atualização")

    with dot.subgraph(name='cluster_txn') as c:
        c.attr(label="Transações", color="white")
        c.node('txn1', 'TXN 90 (Relatório - Leitura Longa)\nIniciada às 10:00:01', fillcolor="lightblue")
        c.node('txn2', 'TXN 91 (PIX Crédito - Escrita Rápida)\nIniciada às 10:00:02', fillcolor="lightyellow")

    dot.edge('txn1', 'row_v1', label="1. Lê o saldo (R$1000)")
    dot.edge('txn2', 'row_v2', label="2. Credita R$200 e comita")
    dot.edge('txn1', 'row_v1', label="3. Continua vendo R$1000\n(lendo de sua 'fotografia')", style="dashed", constraint='false')
    
    return dot

def draw_lsm_tree_diagram():
    dot = graphviz.Digraph('LSMTree', comment='Log-Structured Merge-Tree')
    dot.attr('graph', rankdir='TB', splines='ortho', label="Visualização de LSM-Tree", labelloc="t", fontsize="16")
    dot.attr('node', shape='box', style='rounded,filled')

    dot.node('writes', 'Requisições de Escrita\n(INSERT, UPDATE, DELETE)', shape='ellipse', fillcolor='lightblue')
    dot.node('memtable', 'Memtable\n(em memória, ordenado)', fillcolor='lightyellow')
    dot.edge('writes', 'memtable', label="1. Escritas vão para memória")

    with dot.subgraph(name="cluster_disk") as c:
        c.attr(label="Armazenamento em Disco (Imutável)", style="dashed")
        with dot.subgraph(name="cluster_l0") as l0:
            l0.attr(label="Level 0 (desordenado entre arquivos)", color="lightgrey")
            l0.node('sstable1', 'SSTable 1\n(Flush 1)', fillcolor='whitesmoke')
            l0.node('sstable2', 'SSTable 2\n(Flush 2)', fillcolor='whitesmoke')
        
        with dot.subgraph(name="cluster_l1") as l1:
            l1.attr(label="Level 1 (ordenado)", color="darkgrey")
            l1.node('sstable3', 'SSTable 3\n(Merge de L0)', fillcolor='whitesmoke')
        
        c.edge('sstable1', 'sstable3', style='invis')


    dot.edge('memtable', 'sstable1', label="2. Flush para Disco (quando cheio)")

    dot.node('compaction', 'Processo de Compactação', shape='cylinder', fillcolor='salmon')
    dot.edge('sstable1', 'compaction', style='dashed', dir='none')
    dot.edge('sstable2', 'compaction', style='dashed', dir='none', label="3. Lê múltiplos SSTables")
    dot.edge('compaction', 'sstable3', label="4. Escreve novo SSTable,\nremovendo dados antigos/deletados")


    return dot

# --- Conteúdo da Página ---

st.title("Versionamento de Dados: A Base da Consistência e Concorrência")

st.markdown("""
O **versionamento de dados** é uma técnica onde, em vez de sobrescrever dados antigos quando uma atualização ocorre, o banco de dados mantém múltiplas versões do mesmo dado. Cada transação que modifica um dado, na verdade, cria uma nova versão dele.

Esta abordagem é a espinha dorsal de como bancos de dados modernos lidam com dois grandes desafios:
1.  **Controle de Concorrência:** Permitir que múltiplas transações leiam e escrevam no banco de dados ao mesmo tempo sem corromper os dados.
2.  **Isolamento:** Garantir que cada transação veja uma "fotografia" consistente do banco de dados, como se ela estivesse sendo executada sozinha, sem ver as alterações parciais e não confirmadas de outras transações.
""")

st.header("Principais Estratégias de Versionamento")

st.subheader("1. Controle de Concorrência Multiversão (MVCC)")
st.markdown("""
- **Como funciona:** Este é o modelo mais comum em bancos de dados relacionais. Cada transação recebe um ID de transação e um timestamp. Quando uma transação lê um dado, o banco de dados encontra a versão correta daquele dado que era "visível" no momento em que a transação começou. As alterações feitas por transações ainda não confirmadas são invisíveis.
- **Exemplo:** Se uma transação de **PIX Débito** começa, ela vê o saldo como estava no início da sua execução. Mesmo que um **PIX Crédito** chegue e seja confirmado *durante* a execução do débito, a transação de débito continuará vendo o saldo antigo, garantindo uma visão estável e consistente.
- **Bancos que usam:** **PostgreSQL, CockroachDB, Oracle**.
""")
st.graphviz_chart(draw_mvcc_diagram())


st.subheader("2. Log-Structured Merge-Trees (LSM-Trees)")
st.markdown("""
- **Como funciona:** Esta abordagem, comum em bancos NoSQL otimizados para escrita, leva o conceito de "nunca modificar no local" ao extremo. Todas as escritas e atualizações são simplesmente adicionadas a uma estrutura em memória (`Memtable`). Quando a `Memtable` está cheia, ela é despejada em um arquivo imutável no disco (`SSTable`).
- **Versionamento Implícito:** A versão mais recente de um dado é simplesmente a que está no arquivo mais recente (ou na `Memtable`). Para ler um dado, o sistema procura da fonte mais nova para a mais velha. As atualizações são apenas novas escritas. As deleções são "marcadores de deleção" (tombstones).
- **Bancos que usam:** **Cassandra, ScyllaDB, DynamoDB (internamente), RocksDB/Pebble (usado pelo CockroachDB)**.
""")
st.graphviz_chart(draw_lsm_tree_diagram())


st.header("Benefícios do Versionamento")
st.markdown("""
- **Leitores não bloqueiam escritores (e vice-versa):** Em muitos casos (especialmente com MVCC), uma transação que está lendo dados não precisa esperar por uma transação que está escrevendo nos mesmos dados, pois ela simplesmente lê uma versão mais antiga. Isso melhora drasticamente a concorrência.
- **Consistência de Leitura (Snapshot Isolation):** Garante que uma transação leia uma "fotografia" consistente do banco de dados, prevenindo anomalias de leitura.
- **Time-Travel Queries:** Em alguns bancos (como o CockroachDB), o versionamento permite executar consultas "como se fosse em um ponto no tempo" no passado (`AS OF SYSTEM TIME`), o que é extremamente poderoso para auditoria e depuração.
""")
