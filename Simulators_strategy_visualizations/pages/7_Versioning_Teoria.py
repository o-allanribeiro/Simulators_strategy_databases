import streamlit as st

st.set_page_config(layout="wide", page_title="Teoria: Versionamento de Dados")

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
- **Visualização:** Pense em cada linha do banco de dados como uma lista encadeada de versões, onde cada versão tem um "válido de" e "válido até" associado a IDs de transação.
""")

st.subheader("2. Log-Structured Merge-Trees (LSM-Trees)")
st.markdown("""
- **Como funciona:** Esta abordagem, comum em bancos NoSQL otimizados para escrita, leva o conceito de "nunca modificar no local" ao extremo. Todas as escritas e atualizações são simplesmente adicionadas a uma estrutura em memória (`Memtable`). Quando a `Memtable` está cheia, ela é despejada em um arquivo imutável no disco (`SSTable`).
- **Versionamento Implícito:** A versão mais recente de um dado é simplesmente a que está no arquivo mais recente (ou na `Memtable`). Para ler um dado, o sistema procura da fonte mais nova para a mais velha. As atualizações são apenas novas escritas. As deleções são "marcadores de deleção" (tombstones).
- **Bancos que usam:** **Cassandra, ScyllaDB, DynamoDB (internamente), RocksDB/Pebble (usado pelo CockroachDB)**.
- **Visualização:** É exatamente o que o **Cenário de Versioning com LSM-Tree** (que eu havia criado anteriormente) demonstrava: o fluxo de dados da `Memtable` para múltiplos `SSTables` e o processo de compactação que limpa as versões antigas.
""")

st.header("Benefícios do Versionamento")
st.markdown("""
- **Leitores não bloqueiam escritores (e vice-versa):** Em muitos casos (especialmente com MVCC), uma transação que está lendo dados não precisa esperar por uma transação que está escrevendo nos mesmos dados, pois ela simplesmente lê uma versão mais antiga. Isso melhora drasticamente a concorrência.
- **Consistência de Leitura (Snapshot Isolation):** Garante que uma transação leia uma "fotografia" consistente do banco de dados, prevenindo anomalias de leitura.
- **Time-Travel Queries:** Em alguns bancos (como o CockroachDB), o versionamento permite executar consultas "como se fosse em um ponto no tempo" no passado (`AS OF SYSTEM TIME`), o que é extremamente poderoso para auditoria e depuração.
""")
