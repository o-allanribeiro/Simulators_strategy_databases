import streamlit as st

st.set_page_config(layout="wide", page_title="Teoria: Sharding")

st.title("Sharding: A Teoria por Trás da Escalabilidade")

st.markdown("""
O **Sharding** (também conhecido como particionamento horizontal) é a técnica de dividir um grande banco de dados em múltiplos pedaços menores, chamados **shards**. Cada shard é um banco de dados independente, contendo um subconjunto dos dados. Quando você executa uma consulta, uma camada de roteamento direciona a sua requisição para o shard correto que contém aquele dado.

O objetivo principal é escalar o banco de dados para além dos limites de um único servidor (escalabilidade vertical), permitindo que a carga de leitura e escrita seja distribuída por vários servidores (escalabilidade horizontal).
""")

st.header("Por que o Sharding é Necessário?")
st.markdown("""
Imagine um único servidor de banco de dados. Ele tem limites físicos de:
- **CPU:** Quantas consultas ele pode processar simultaneamente.
- **RAM:** Quantos dados ele pode manter em memória para acesso rápido.
- **Armazenamento:** Quantos dados ele pode guardar no total.
- **I/O de Rede:** Quanta informação ele pode receber e enviar.

Quando uma única conta (uma *Hot Partition*) começa a receber milhares de transações por segundo, ela pode esgotar um ou mais desses recursos, tornando-se um gargalo para o sistema inteiro. O sharding resolve isso distribuindo os dados e a carga.
""")

st.header("Principais Estratégias de Sharding")

st.subheader("1. Sharding Baseado em Hash (Hash-Based Sharding)")
st.markdown("""
- **Como funciona:** Uma "chave de shard" (ex: o ID do usuário, o ID da transação) é passada por uma função de hash. O resultado do hash determina em qual shard o dado será armazenado.
- **Visualização:** Pense em um anel (Consistent Hashing). A saída do hash mapeia o dado para um ponto no anel, e o dado é armazenado no primeiro servidor que aparece no sentido horário.
- **Bancos que usam:** **DynamoDB, Cassandra, ScyllaDB**.
- **Prós:** Tende a distribuir os dados de forma muito uniforme entre os shards, evitando desbalanceamento.
- **Contras:** Consultas de intervalo (ex: "me dê todos os usuários com IDs entre 1000 e 2000") são ineficientes, pois exigiriam consultar todos os shards.
""")

st.subheader("2. Sharding Baseado em Intervalo (Range-Based Sharding)")
st.markdown("""
- **Como funciona:** Os dados são particionados com base em um intervalo contínuo da chave de shard. Por exemplo, contas de ID 1-1000 vão para o Shard A, 1001-2000 para o Shard B, e assim por diante.
- **Bancos que usam:** **CockroachDB** usa uma variação disso, onde ele automaticamente "divide" os intervalos (ranges) que ficam muito grandes ou recebem muita carga.
- **Prós:** Muito eficiente para consultas de intervalo, pois a camada de roteamento sabe exatamente quais shards consultar.
- **Contras:** Pode levar a *hot spots*. Se um intervalo específico (ex: contas criadas recentemente) for muito mais acessado, o shard correspondente se tornará um gargalo, enquanto os outros ficam ociosos.
""")

st.subheader("3. Sharding de Diretório (Directory-Based Sharding)")
st.markdown("""
- **Como funciona:** Existe uma "tabela de pesquisa" central que mapeia explicitamente cada chave de shard para um shard físico.
- **Prós:** Oferece a maior flexibilidade. Você pode mover um dado de um shard para outro simplesmente atualizando a tabela de diretório.
- **Contras:** A tabela de diretório pode se tornar um gargalo ou um ponto único de falha se não for distribuída e cacheada corretamente.
""")
