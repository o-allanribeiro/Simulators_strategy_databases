# Simulators: Strategies for High-Frequency Payment Databases

Laboratório interativo (Streamlit) que compara estratégias de **controle de concorrência e
escalabilidade** em sistemas de pagamento de alta frequência, como o Pix: quando muitas
transações disputam a mesma conta ("hot account"), qual arquitetura se sustenta e a que custo.

> As simulações são **didáticas**: modelam o comportamento de cada estratégia para fins de
> estudo e não substituem benchmarks em bancos reais. Os números mostrados vêm de parâmetros
> configuráveis na própria interface.

## O que o laboratório mostra

| Página | Tema | Ideia central |
|---|---|---|
| 1. Controle Pessimista | Locking em banco relacional (estilo PostgreSQL) | Cada escrita na mesma linha espera o lock da anterior: a fila cresce e a latência explode |
| 2. Controle Otimista | OCC com versionamento e escritas condicionais | Sem lock, mas conflitos viram retentativas; simulação de colisões e retry |
| 3. Write Sharding | Partição quente em NoSQL (estilo DynamoDB) | Dividir a chave em shards distribui a escrita, ao custo de leituras scatter-gather |
| 4. Netting com Grafos | Compensação multilateral | Detecção de ciclos de dívidas cruzadas para cancelar obrigações e reduzir a liquidez necessária |
| 5. Arquitetura Agregadora | API, Kafka, processamento em lote, banco | Transformar N escritas em uma atualização atômica de saldo, preservando o extrato |
| 6. Matriz de Decisão | Síntese | Como combinar as estratégias e 3 perguntas para escolher uma |

## Como executar

Requisitos: Python 3.10+.

```bash
cd Simulators_strategy_visualizations
python -m venv .venv
# Windows: .\.venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Os diagramas usam o pacote Python `graphviz` e são renderizados pelo navegador; instalar o
Graphviz do sistema é opcional.

## Estrutura

```
Simulators_strategy_visualizations/
  app.py        # ponto de entrada (st.navigation)
  nav.py        # definição central das páginas
  views/        # uma página por estudo de caso
docs/           # relatórios de pesquisa e resumo técnico
```

## Documentação

- [`docs/RESUMO_TECNICO_AGGREGATOR_PATTERN.md`](docs/RESUMO_TECNICO_AGGREGATOR_PATTERN.md): resumo técnico da arquitetura agregadora.
- [`docs/Estudo de Trade-offs em Arquitetura de Dados.md`](<docs/Estudo de Trade-offs em Arquitetura de Dados.md>), [`docs/Otimização Financeira e Bancária em TPS.md`](<docs/Otimização Financeira e Bancária em TPS.md>) e [`docs/Arquitetura Híbrida_ Síncrono vs. Assíncrono.md`](<docs/Arquitetura Híbrida_ Síncrono vs. Assíncrono.md>): relatórios de pesquisa que fundamentam as simulações. Foram elaborados com apoio de ferramentas de IA e revisados pelo autor.

## Projeto relacionado

[`calculator_aws_DBs_tradeoff_cost`](https://github.com/o-allanribeiro/calculator_aws_DBs_tradeoff_cost):
calculadora de custo e viabilidade entre Aurora, DynamoDB, CockroachDB e Cassandra/ScyllaDB
para as mesmas cargas de alto TPS.

## Autor

Allan Ribeiro da Silva, [LinkedIn](https://www.linkedin.com/in/allanribeirosilva/).
