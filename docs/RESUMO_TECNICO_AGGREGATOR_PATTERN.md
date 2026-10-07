# Resumo Técnico: Arquitetura de Alta Performance para Sistemas de Pagamento

**Autores:** Allan Ribeiro & Gemini

## RESUMO

Este documento detalha uma arquitetura de sistema de pagamentos projetada para alcançar altíssima performance e escalabilidade, especificamente em cenários de alta concorrência de transações (1:N), como um único "PIX" recebendo milhares de créditos simultâneos. A solução proposta, denominada "The Aggregator Pattern", desvia do paradigma tradicional de processamento individual de requisições API, implementando um modelo baseado em mensageria e processamento em lote. O fluxo desacopla a camada de ingestão (API) da camada de processamento (lógica de negócio), utilizando o Apache Kafka como um buffer de ordenação e o AWS ECS para a execução da lógica de "Netting" (compensação). Este mecanismo de economia de liquidez (LSM) agrupa múltiplas transações em memória antes de consolidá-las em uma única operação atômica no banco de dados (DynamoDB), transformando, por exemplo, 5.000 requisições de escrita em uma única atualização de saldo, garantindo consistência, idempotência e performance.

---

## 1. INTRODUÇÃO: O DESAFIO DO TPS EM UMA ÚNICA CONTA

Sistemas de pagamento modernos, como o PIX, exigem respostas de baixa latência (sub-segundo) e alta disponibilidade. O desafio se intensifica quando uma única conta se torna um "hotspot" de transações, recebendo milhares de operações de débito e crédito por segundo. Uma abordagem síncrona tradicional, onde cada requisição de API resulta em uma transação de banco de dados (e.g., `UPDATE an account...`), invariavelmente leva a contenção de recursos, "locks" de linha e, por fim, à falha do sistema. A presente arquitetura foi concebida para resolver este gargalo.

## 2. ARQUITETURA PROPOSTA: "THE AGGREGATOR PATTERN"

O conceito central é transformar o fluxo de N requisições individuais em uma única atualização de saldo atômica no banco de dados, sem perder o registro de cada transação (extrato).

**Fluxo de Dados:** `API (Entrada) -> Kafka (Ordenação) -> ECS (Netting/Inteligência) -> DynamoDB (Persistência)`

### 2.1. Camada de Ingestão e Ordenação (API Gateway & Kafka)

-   **Interface Externa (API):** Para o mundo externo (Apps, Parceiros, Open Finance), a entrada ocorre via APIs REST ou gRPC expostas por um API Gateway. A API valida a requisição, autentica e publica o evento de transação em um tópico Kafka.
-   **Buffer e Ordenação (Kafka):** O Kafka atua como um "shock absorber", absorvendo picos de carga e garantindo a ordem de processamento. A chave de partição do tópico (`financial-transactions-events`) é o `account_id`. Isso garante que todas as transações para uma mesma conta sejam direcionadas para a mesma partição e, consequentemente, processadas pelo mesmo consumidor, eliminando condições de corrida distribuídas.

### 2.2. A "Inteligência" no ECS (Java Spring Boot)

O núcleo da lógica de negócio (LSM) reside em consumidores Kafka rodando no AWS ECS.

-   **Processamento em Lote (Micro-batching):** Utilizando o `BatchMessageListener` do Spring Kafka, o serviço não processa transações uma a uma. Ele consome um lote de mensagens da partição, agrupa-as por conta e aplica a lógica de netting em memória: `Saldo Final = Saldo Atual + Soma(Créditos) - Soma(Débitos)`.
-   **Ganho de Performance:** Se 5.000 transações chegam em um segundo, o consumidor as lê de uma vez, calcula o saldo final em microssegundos e executa apenas uma chamada ao banco de dados para persistir o resultado consolidado. Isso transforma 5.000 escritas em 1.

### 2.3. Modelo de Dados e Persistência (DynamoDB)

A persistência é realizada no DynamoDB utilizando o padrão de "Single-Table Design" e transações atômicas (`TransactWriteItems`) para garantir a integridade.

-   **Estrutura da Tabela "Ledger":**
    -   **Item de Saldo (Snapshot):** `PK: ACCOUNT#<id>, SK: BALANCE#CURRENT` com o saldo atual e um número de versão para concorrência otimista.
    -   **Item de Transação (Extrato):** `PK: ACCOUNT#<id>, SK: TX#<timestamp>#<uuid>` para cada transação individual.
    -   **Item de Idempotência:** `PK: IDEMPOTENCY#<transaction_id>` para prevenir processamento duplicado.
-   **Transação Atômica:** Ao commitar um lote, o serviço Java executa uma única transação no DynamoDB que inclui:
    1.  **Checagem de Idempotência** para cada transação do lote.
    2.  **Atualização do Saldo** com uma `ConditionExpression` que garante que a conta não ficará negativa.
    3.  **Gravação do Extrato** com um `PutItem` para cada transação individual.

## 3. INSTALAÇÃO E EXECUÇÃO DO SIMULADOR

Este repositório contém um simulador visual interativo construído com Streamlit para demonstrar os conceitos acima.

### 3.1. Pré-requisitos
- Instale o **Graphviz** em seu sistema para a visualização dos grafos.
  - **Windows:** `choco install graphviz`
  - **macOS:** `brew install graphviz`
  - **Linux (Debian/Ubuntu):** `sudo apt-get install graphviz`

### 3.2. Passos de Instalação
1. Clone o repositório e navegue até a pasta `Simulators_strategy_visualizations`.
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   # Windows: .\.venv\Scripts\activate
   # Linux/macOS: source .venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### 3.3. Executando a Aplicação
Para iniciar o painel de simulação, execute:
```bash
streamlit run app.py
```
A aplicação abrirá em seu navegador, onde você poderá explorar as diferentes simulações de arquitetura.
