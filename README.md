# Protocolo de Transporte Confiável

## Visão Geral

Este projeto implementa um protocolo de transporte confiável que simula a camada de transporte de redes de computadores. O sistema permite a troca de mensagens entre cliente e servidor usando dois protocolos diferentes: **Go-Back-N** e **Selective Repeat**.

### Objetivo

Demonstrar os conceitos fundamentais de protocolos de transporte confiável, incluindo:

- Janela deslizante
- Controle de fluxo
- Detecção e correção de erros
- Retransmissão automática
- Reconhecimento positivo e negativo

### Arquitetura

```
Cliente ←→ Servidor
   ↓         ↓
Go-Back-N  ou  Selective Repeat
   ↓         ↓
Timer + NACK + Checksum
```

## Estrutura do Projeto

- **`client.py`** - Cliente que inicia conexão, negocia parâmetros e envia mensagens
- **`server.py`** - Servidor que aceita conexões, processa mensagens e reconstrói dados
- **`README.md`** - Documentação completa do projeto

## Entregáveis do Projeto

### ✅ **Entrega 1 - Handshake Inicial** (CONCLUÍDA)

**Objetivo:** Aplicações cliente e servidor devem se conectar via socket e realizar o handshake inicial.

#### **Implementado:**

- ✅ **Conexão via Socket**: Cliente conecta ao servidor via TCP
- ✅ **Handshake Inicial**: Negociação de parâmetros entre cliente e servidor
- ✅ **Modo de Operação**: Cliente escolhe entre Go-Back-N ou Selective Repeat
- ✅ **Tamanho Máximo**: Negociação do limite de caracteres da mensagem
- ✅ **Confirmação**: Servidor confirma parâmetros com handshake_ack

#### **Características:**

- **Protocolo de Aplicação**: JSON com campos `type`, `max_message_size`, `operation_mode`
- **Framing**: Tamanho da mensagem (4 bytes) + dados JSON
- **Validação**: Servidor confirma parâmetros recebidos

### ✅ **Entrega 2 - Troca de Mensagens** (CONCLUÍDA)

**Objetivo:** Troca de mensagens entre cliente e servidor considerando um canal de comunicação sem erros e perdas.

#### **Implementado:**

- ✅ **Segmentação**: Mensagem dividida em segmentos de até 4 caracteres (configurável)
- ✅ **Janela Deslizante**: Tamanho configurável (1-5 pacotes)
- ✅ **Go-Back-N**: Retransmissão em lote com janela deslizante
- ✅ **Selective Repeat**: Retransmissão seletiva com buffer
- ✅ **Controle de Fluxo**: Paralelismo controlado por janela
- ✅ **Verificação de Limite**: Cliente verifica tamanho máximo da mensagem

#### **Características do Transporte Confiável:**

- ✅ **Soma de Verificação**: Checksum simples (soma ASCII % 256)
- ✅ **Temporizador**: Timer de 5 segundos para detecção de perdas
- ✅ **Número de Sequência**: Identificação única de pacotes
- ✅ **Reconhecimento Positivo**: ACK para pacotes válidos
- ✅ **Reconhecimento Negativo**: NACK para pacotes corrompidos
- ✅ **Janela/Paralelismo**: Envio simultâneo de múltiplos pacotes
- ✅ **Algoritmo de Integridade**: Checksum para detecção de corrupção

### ✅ **Entrega 3 - Simulação de Erros** (CONCLUÍDA)

**Objetivo:** Inserção de erros e perdas simulados, bem como a implementação do correto comportamento dos processos.

#### **Implementado:**

- ✅ **Simulação de Perdas**: Perda determinística de pacotes específicos
- ✅ **Simulação de Corrupção**: Corrupção determinística de checksums
- ✅ **Configuração de Erros**: Argumentos CLI para definir pacotes a perder/corromper
- ✅ **Modo de Teste**: Ativado via argumentos `--drop-packets` e `--corrupt-packets`
- ✅ **Estatísticas**: Relatório de erros inseridos ao final da transmissão

#### **Funcionalidades Implementadas:**

- **Perda de Pacotes**: Simular perda de pacotes específicos via `--drop-packets`
- **Corrupção de Checksum**: Simular checksums incorretos via `--corrupt-packets`
- **Intervalos**: Suporte a intervalos (ex: `"2-5"`) e listas (ex: `"2,5,10"`)
- **Retransmissão Inteligente**: Pacotes corrompidos são retransmitidos com checksum correto
- **Estatísticas**: Contador de pacotes perdidos e corrompidos

**Uso:**

```bash
# Perder pacote 2
python client.py --drop-packets 2

# Corromper pacote 3
python client.py --corrupt-packets 3

# Perder múltiplos pacotes
python client.py --drop-packets "2,5,10"

# Perder intervalo de pacotes
python client.py --drop-packets "3-7"

# Combinar perda e corrupção
python client.py --drop-packets 2 --corrupt-packets 5
```

### 🎯 **Pontuação Extra** (OPCIONAL)

#### **Algoritmo de Integridade** (0,5 pontos)

- ✅ **Algoritmo de checagem de integridade** (checksum implementado)

**Implementação:**

```python
def calculate_checksum(data):
    """Calcula soma de verificação simples"""
    return sum(ord(c) for c in data) % 256

def verify_checksum(payload, received_checksum):
    """Verifica se a soma de verificação está correta"""
    calculated_checksum = calculate_checksum(payload)
    return calculated_checksum == received_checksum
```

**Características:**

- **Método**: Soma dos valores ASCII módulo 256
- **Detecção**: Identifica corrupção de dados
- **Aplicação**: Cliente calcula, servidor verifica
- **Integração**: Usado em todos os pacotes de dados

#### **Criptografia Simétrica** (0,5 pontos)

- ✅ **Criptografia simétrica** (implementada)

**Implementação:**

A criptografia simétrica foi implementada usando o algoritmo **Fernet** (baseado em AES-128 em modo CBC) da biblioteca `cryptography`. O sistema criptografa apenas o payload dos pacotes de dados, mantendo os metadados (número de sequência, checksum, tipo) em texto claro para garantir o funcionamento correto do protocolo.

**Características:**

- **Algoritmo**: Fernet (AES-128 em modo CBC com HMAC)
- **Geração de Chave**: Chave gerada automaticamente no cliente durante o handshake
- **Troca de Chave**: Chave compartilhada via handshake (codificada em base64)
- **Escopo**: Apenas o payload é criptografado (dados de 4 caracteres)
- **Checksum**: Calculado sobre o payload original (antes da criptografia)
- **Ativação**: Opcional via flag `--enable-encryption` no cliente

**Uso:**

```bash
# Cliente com criptografia habilitada
python client.py --enable-encryption

# Servidor (suporta criptografia automaticamente)
python server.py
```

**Fluxo de Criptografia:**

1. Cliente gera chave Fernet durante o handshake
2. Chave é enviada ao servidor no handshake (codificada em base64)
3. Cliente criptografa cada payload antes de enviar
4. Servidor descriptografa cada payload ao receber
5. Checksum é calculado/verificado sobre o payload original

**Segurança:**

- Chave única por sessão (gerada aleatoriamente)
- Criptografia autenticada (Fernet inclui HMAC)
- Payloads são codificados em base64 para transmissão via JSON

### 📊 **Status Atual do Projeto**

| Entrega                  | Status           | Progresso | Observações                              |
| ------------------------ | ---------------- | --------- | ---------------------------------------- |
| **Entrega 1**            | ✅ **Concluída** | 100%      | Handshake implementado                   |
| **Entrega 2**            | ✅ **Concluída** | 100%      | Go-Back-N e Selective Repeat funcionais  |
| **Entrega 3**            | ✅ **Concluída** | 100%      | Simulação de erros e perdas implementada |
| **Extra - Integridade**  | ✅ **Concluída** | 100%      | Algoritmo de checagem de integridade     |
| **Extra - Criptografia** | ✅ **Concluída** | 100%      | Criptografia simétrica (Fernet/AES)      |

### 🚀 **Próximos Passos**

1. **Implementar Entrega 3**: Simulação de erros e perdas
2. **Testes Extensivos**: Validar comportamento com erros
3. **Documentação**: Atualizar manual com simulação
4. **Pontuação Extra**: Considerar implementação opcional

## Conceitos Fundamentais

### Janela Deslizante

A janela deslizante é um conjunto de pacotes que podem ser enviados simultaneamente sem aguardar confirmação individual. Permite melhor utilização da largura de banda e paralelismo na transmissão.

### Segmentos vs Pacotes

- **Segmento**: Pedaço da mensagem original (até 4 caracteres)
- **Pacote**: Segmento + metadados (número de sequência, checksum, tipo)

### Checksum

Soma de verificação simples que detecta corrupção de dados:

```python
checksum = sum(ord(c) for c in data) % 256
```

### Número de Sequência

Identificador único para cada pacote, usado para:

- Controle de ordem
- Detecção de duplicatas
- Controle de janela

### Go-Back-N vs Selective Repeat

| Característica    | Go-Back-N                  | Selective Repeat            |
| ----------------- | -------------------------- | --------------------------- |
| **Retransmissão** | Todos os pacotes da janela | Apenas pacote específico    |
| **Buffer**        | Não usa                    | Usa buffer para reordenação |
| **Eficiência**    | Menor com perdas           | Maior com perdas            |
| **Complexidade**  | Simples                    | Mais complexo               |

## Especificação do Protocolo

### Mensagem de Handshake (Cliente → Servidor)

```json
{
  "type": "handshake",
  "max_message_size": 100,
  "operation_mode": "go_back_n"
}
```

### Resposta do Handshake (Servidor → Cliente)

```json
{
  "type": "handshake_ack",
  "max_message_size": 100,
  "window_size": 5,
  "operation_mode": "go_back_n",
  "status": "success"
}
```

### Pacote de Dados (Cliente → Servidor)

```json
{
  "type": "data",
  "seq_num": 0,
  "payload": "Olá ",
  "checksum": 188
}
```

### Pacote de Reconhecimento (Servidor → Cliente)

```json
{
  "type": "ack",
  "seq_num": 0
}
```

### Pacote de Reconhecimento Negativo (Servidor → Cliente)

```json
{
  "type": "nack",
  "seq_num": 0
}
```

## Características Implementadas

### ✅ Handshake Inicial

- Negociação de parâmetros entre cliente e servidor
- Definição do modo de operação (Go-Back-N ou Selective Repeat)
- Configuração do tamanho máximo de mensagem
- Confirmação de configurações

### ✅ Janela Deslizante

- Tamanho configurável (padrão: 5 pacotes)
- Envio paralelo de múltiplos pacotes
- Controle de fluxo eficiente

### ✅ Go-Back-N

- Retransmissão em lote quando NACK é recebido
- Simplicidade de implementação
- Controle de janela deslizante

### ✅ Selective Repeat

- Buffer de recebimento para pacotes fora de ordem
- Retransmissão seletiva de pacotes específicos
- Reordenação automática de pacotes
- Entrega em ordem para a aplicação

### ✅ Controle de Erros

- Checksum para detecção de corrupção
- NACK para pacotes com erro
- Timer para detecção de perdas
- Retransmissão automática

### ✅ Verificação de Limite

- Limite máximo configurável (padrão: 100 caracteres)
- Verificação no cliente antes do envio
- Truncamento automático se exceder limite

## Manual de Execução

Para instruções detalhadas sobre como executar o servidor e cliente, incluindo todos os argumentos de linha de comando disponíveis, consulte o **[Guia de Uso](GUIDE.md)**.

## Fluxos Passo a Passo

### 7.1 Go-Back-N - Cenário de Sucesso

**Situação:** Todos os pacotes são enviados e recebidos corretamente, sem perdas ou corrupções.

**Cliente:**

- Passo 1: Inicia handshake (linhas 105-109 em client.py)

  ```python
  handshake_data = {
      "type": "handshake",           # Tipo da mensagem
      "max_message_size": MAX_MESSAGE_SIZE,      # Tamanho máximo da mensagem
      "operation_mode": OPERATION_MODE  # Modo de operação (go_back_n ou selective_repeat)
  }
  send_message(s, handshake_data) # Enviar handshake
  ```

- Passo 2: Recebe confirmação do servidor (linha 114 em client.py)

  ```python
  response = receive_message(s) # Receber confirmação (ack do servidor)
  ```

- Passo 3: Envia primeira janela [0,1,2,3,4] (linhas 162-176 em client.py)

  ```python
  while next_seq_to_send < min(base_seq + window_size, len(segments)):
      segment = segments[next_seq_to_send]
      checksum = calculate_checksum(segment)
      packet = create_data_packet(next_seq_to_send, segment, checksum)

      print(f"[SEND] Enviando pacote {next_seq_to_send}: '{segment}' (checksum: {checksum})")
      send_message(s, packet)

      # Armazenar pacote enviado
      sent_packets[next_seq_to_send] = packet

      # Iniciar timer para este pacote
      start_timer(next_seq_to_send, packet, s)

      next_seq_to_send += 1
  ```

- Passo 4: Aguarda ACKs sequenciais (linhas 179-195 em client.py)

  ```python
  while base_seq < next_seq_to_send:
      try:
          response = receive_message(s)
          ack_seq = response["seq_num"]

          if response["type"] == "ack":
              print(f"[ACK] ACK recebido para pacote {ack_seq}")
              # Parar timer do pacote confirmado
              stop_timer(ack_seq)
              # Marcar pacote como confirmado
              acknowledged_packets.add(ack_seq)

              # Mover janela se base foi confirmada
              while base_seq in acknowledged_packets:
                  base_seq += 1
                  print(f"[WINDOW] Janela movida. Base agora: {base_seq}")
  ```

**Servidor:**

- Passo 1: Recebe handshake (linha 69 em server.py)

  ```python
  handshake_data = receive_message(client_socket) # Receber handshake do cliente
  ```

- Passo 2: Envia confirmação (linhas 73-81 em server.py)

  ```python
  response = {
      "type": "handshake_ack",                                # Confirmação do handshake
      "max_message_size": handshake_data["max_message_size"], # Confirmar tamanho
      "window_size": WINDOW_SIZE,                             # Tamanho da janela
      "operation_mode": handshake_data["operation_mode"],     # Confirmar modo
      "status": "success"                                     # Status de sucesso
  }
  send_message(client_socket, response) # Enviar confirmação (handshake_ack)
  ```

- Passo 3: Processa pacotes em ordem (linhas 120-130 em server.py)

  ```python
  if operation_mode == "go_back_n":
      # Go-Back-N: Armazenar segmento se for o próximo esperado
      if seq_num == expected_seq:
          received_segments.append(payload)  # Adicionar à lista
          expected_seq += 1  # Próximo número esperado
          print(f"[OK] Segmento {seq_num} adicionado à mensagem")

          # Enviar ACK para pacote válido
          ack = create_ack_packet(seq_num)
          send_message(client_socket, ack)
          print(f"[ACK] ACK enviado para pacote {seq_num}")
  ```

**Estado das Variáveis:**

- base_seq: 0 → 1 → 2 → 3 → 4 → 5
- next_seq_to_send: 0 → 5
- acknowledged_packets: {} → {0} → {0,1} → {0,1,2} → {0,1,2,3} → {0,1,2,3,4}

**Resultado:** Janela movida completamente, próxima janela [5,6,7,8,9] é enviada.

### 7.2 Go-Back-N - Cenário de Perda de Pacote

**Situação:** Pacote 2 é perdido durante a transmissão, servidor não recebe.

**Cliente:**

- Passo 1: Envia janela [0,1,2,3,4] (linhas 162-176 em client.py)
- Passo 2: Recebe ACKs 0 e 1 (linhas 184-195 em client.py)
- Passo 3: Não recebe ACK 2, timer expira (linhas 65-80 em client.py)
  ```python
  def timeout_handler():
      print(f"[TIMEOUT] Timeout para pacote {seq_num} - retransmitindo...")
      # Para timeout, sempre retransmitir apenas o pacote específico
      # A lógica de Go-Back-N vs Selective Repeat é tratada no NACK
      send_message(socket_conn, packet)
      print(f"Pacote {seq_num} retransmitido por timeout")
  ```
- Passo 4: Retransmite todos os pacotes da janela [2,3,4] (linhas 199-214 em client.py)

  ```python
  if operation_mode == "go_back_n":
      # Go-Back-N: Parar todos os timers da janela
      for i in range(base_seq, next_seq_to_send):
          stop_timer(i)

      # Go-Back-N: Retransmitir todos os pacotes da janela
      print(f"[GBN] Go-Back-N: Retransmitindo janela a partir de {base_seq}")
      for i in range(base_seq, next_seq_to_send):
          if i in sent_packets:
              packet = sent_packets[i]
              print(f"[RETRY] Retransmitindo pacote {i}: '{packet['payload']}'")
              send_message(s, packet)
              # Reiniciar timer para retransmissão
              start_timer(i, packet, s)
  ```

**Servidor:**

- Passo 1: Recebe pacotes 0 e 1, envia ACKs
- Passo 2: Não recebe pacote 2
- Passo 3: Recebe pacotes 3 e 4, mas ignora (fora de ordem)
  ```python
  else:
      print(f"[WARNING] Pacote {seq_num} fora de ordem (esperado: {expected_seq}) - ignorando")
      # Go-Back-N: NÃO enviar ACK para pacotes fora de ordem
  ```
- Passo 4: Recebe retransmissão [2,3,4], processa em ordem

**Estado das Variáveis:**

- base_seq: 0 → 1 → 2 (após retransmissão)
- expected_seq: 0 → 1 → 2 (no servidor)

**Resultado:** Pacotes 2, 3, 4 são retransmitidos e processados corretamente.

### 7.3 Go-Back-N - Cenário de Pacote Corrompido

**Situação:** Pacote 2 chega ao servidor com checksum incorreto.

**Cliente:**

- Passo 1: Envia janela [0,1,2,3,4]
- Passo 2: Recebe ACKs 0 e 1
- Passo 3: Recebe NACK 2 (linhas 196-214 em client.py)
  ```python
  elif response["type"] == "nack":
      if operation_mode == "go_back_n":
          for i in range(base_seq, next_seq_to_send):
              stop_timer(i)
          for i in range(base_seq, next_seq_to_send):
              packet = sent_packets[i]
              send_message(s, packet)
              start_timer(i, packet, s)
  ```

**Servidor:**

- Passo 1: Recebe pacotes 0 e 1, processa corretamente
- Passo 2: Recebe pacote 2 corrompido (linhas 116-164 em server.py)

  ```python
  if verify_checksum(payload, checksum):
      print(f"[OK] Pacote {seq_num} válido: '{payload}' (checksum: {checksum})")
      # Processa pacote válido
  else:
      print(f"[ERROR] Pacote {seq_num} com erro de checksum")

      # Enviar NACK para pacote com erro
      nack = create_nack_packet(seq_num)
      send_message(client_socket, nack)
      print(f"[NACK] NACK enviado para pacote {seq_num}")
  ```

- Passo 3: Envia NACK 2
- Passo 4: Recebe retransmissão [2,3,4], processa corretamente

**Estado das Variáveis:**

- base_seq: 0 → 1 → 2 (após retransmissão)
- acknowledged_packets: {0,1} → {0,1,2,3,4}

**Resultado:** Pacotes corrompidos são detectados e retransmitidos em lote.

### 7.4 Go-Back-N - Cenário de Timeout

**Situação:** ACK 2 é perdido, cliente não recebe confirmação.

**Cliente:**

- Passo 1: Envia janela [0,1,2,3,4]
- Passo 2: Recebe ACKs 0 e 1
- Passo 3: Timer do pacote 2 expira (5 segundos) (linhas 65-80 em client.py)
  ```python
  def timeout_handler():
      print(f"[TIMEOUT] Timeout para pacote {seq_num} - retransmitindo...")
      # Para timeout, sempre retransmitir apenas o pacote específico
      # A lógica de Go-Back-N vs Selective Repeat é tratada no NACK
      send_message(socket_conn, packet)
      print(f"Pacote {seq_num} retransmitido por timeout")
  ```
- Passo 4: Retransmite pacote 2 automaticamente

**Servidor:**

- Passo 1: Processa pacotes 0 e 1
- Passo 2: Não recebe ACK 2 (perdido)
- Passo 3: Recebe retransmissão do pacote 2
- Passo 4: Processa pacote 2 e envia ACK

**Estado das Variáveis:**

- base_seq: 0 → 1 → 2 (após retransmissão)
- timers: {2: timer2} → {} (após ACK)

**Resultado:** Timeout detecta perda de ACK e retransmite automaticamente.

### 7.5 Selective Repeat - Cenário de Sucesso

**Situação:** Todos os pacotes são enviados e recebidos corretamente, com buffer para reordenação.

**Cliente:**

- Passo 1: Inicia handshake com modo "selective_repeat" (linha 108 em client.py)
  ```python
  "operation_mode": "selective_repeat"
  ```
- Passo 2: Envia janela [0,1,2,3,4] (mesmo processo do Go-Back-N)
- Passo 3: Recebe ACKs individuais (linhas 184-195 em client.py)

**Servidor:**

- Passo 1: Configura buffer para Selective Repeat (linhas 93-103 em server.py)

  ```python
  operation_mode = handshake_data.get("operation_mode", "go_back_n")
  window_size = handshake_data.get("window_size", WINDOW_SIZE)
  buffer = {}  # Buffer para armazenar pacotes fora de ordem
  buffer_size = window_size * 2  # Buffer maior que a janela

  if operation_mode == "selective_repeat":
      print(f"[SR] Iniciando Selective Repeat com janela de tamanho: {window_size}")
      print(f"[BUFFER] Buffer de recebimento: {buffer_size} pacotes")
  ```

- Passo 2: Armazena pacotes no buffer (linhas 138-150 em server.py)

  ```python
  elif operation_mode == "selective_repeat":
      # Selective Repeat: Armazenar pacote no buffer
      if seq_num not in buffer:
          buffer[seq_num] = payload
          print(f"[BUFFER] Pacote {seq_num} armazenado no buffer")

      # Verificar se podemos entregar pacotes em ordem
      while expected_seq in buffer:
          received_segments.append(buffer[expected_seq])
          del buffer[expected_seq]  # Remover do buffer
          print(f"[DELIVER] Segmento {expected_seq} entregue em ordem")
          expected_seq += 1

      # Enviar ACK para pacote válido
      ack = create_ack_packet(seq_num)
      send_message(client_socket, ack)
      print(f"[ACK] ACK enviado para pacote {seq_num}")
  ```

- Passo 3: Envia ACK para cada pacote recebido

**Estado das Variáveis:**

- buffer: {} → {0: "Olá "} → {} → {1: "mund"} → {} → ...
- expected_seq: 0 → 1 → 2 → 3 → 4 → 5

**Resultado:** Pacotes são armazenados no buffer e entregues em ordem para a aplicação.

### 7.6 Selective Repeat - Cenário de Perda de Pacote

**Situação:** Pacote 2 é perdido, mas pacotes 3 e 4 chegam ao servidor.

**Cliente:**

- Passo 1: Envia janela [0,1,2,3,4]
- Passo 2: Recebe ACKs 0, 1, 3, 4
- Passo 3: Timer do pacote 2 expira
- Passo 4: Retransmite apenas pacote 2 (linhas 213-222 em client.py)
  ```python
  elif operation_mode == "selective_repeat":
      # Selective Repeat: Retransmitir apenas o pacote específico
      print(f"[SR] Selective Repeat: Retransmitindo apenas pacote {ack_seq}")
      if ack_seq in sent_packets:
          packet = sent_packets[ack_seq]
          print(f"[RETRY] Retransmitindo pacote {ack_seq}: '{packet['payload']}'")
          send_message(s, packet)
          # Reiniciar timer apenas para este pacote
          start_timer(ack_seq, packet, s)
  ```

**Servidor:**

- Passo 1: Recebe pacotes 0, 1, 3, 4
- Passo 2: Armazena pacotes 3 e 4 no buffer (linhas 138-150 em server.py)
  ```python
  # Buffer armazena pacotes fora de ordem
  buffer = {3: "sta ", 4: "é um"}
  print(f"[BUFFER] Buffer atual: {list(buffer.keys())")
  ```
- Passo 3: Recebe retransmissão do pacote 2
- Passo 4: Entrega pacotes 2, 3, 4 em ordem
  ```python
  # Verificar se podemos entregar pacotes em ordem
  while expected_seq in buffer:
      received_segments.append(buffer[expected_seq])
      del buffer[expected_seq]  # Remover do buffer
      print(f"[DELIVER] Segmento {expected_seq} entregue em ordem")
      expected_seq += 1
  ```

**Estado das Variáveis:**

- buffer: {} → {3: "sta ", 4: "é um"} → {} (após entrega)
- expected_seq: 0 → 1 → 2 → 3 → 4 → 5

**Resultado:** Apenas pacote perdido é retransmitido, pacotes válidos são preservados no buffer.

### 7.7 Selective Repeat - Cenário de Pacote Corrompido

**Situação:** Pacote 2 chega corrompido, pacotes 3 e 4 chegam válidos.

**Cliente:**

- Passo 1: Envia janela [0,1,2,3,4]
- Passo 2: Recebe ACKs 0, 1, 3, 4
- Passo 3: Recebe NACK 2
- Passo 4: Retransmite apenas pacote 2 (linhas 213-222 em client.py)

**Servidor:**

- Passo 1: Processa pacotes 0, 1, 3, 4 corretamente
- Passo 2: Detecta corrupção no pacote 2 (linhas 116-164 em server.py)
  ```python
  if verify_checksum(payload, checksum):
      # Processa pacote válido
  else:
      nack = create_nack_packet(seq_num)
      send_message(client_socket, nack)
  ```
- Passo 3: Envia NACK apenas para pacote 2
- Passo 4: Recebe retransmissão do pacote 2, processa corretamente

**Estado das Variáveis:**

- buffer: {3: "sta ", 4: "é um"} (preservado)
- expected_seq: 0 → 1 → 2 → 3 → 4 → 5

**Resultado:** Apenas pacote corrompido é retransmitido, pacotes válidos permanecem no buffer.

### 7.8 Selective Repeat - Cenário de Timeout

**Situação:** ACK 2 é perdido, mas pacotes 3 e 4 chegam ao servidor.

**Cliente:**

- Passo 1: Envia janela [0,1,2,3,4]
- Passo 2: Recebe ACKs 0, 1, 3, 4
- Passo 3: Timer do pacote 2 expira (5 segundos)
- Passo 4: Retransmite apenas pacote 2 (linhas 65-80 em client.py)

**Servidor:**

- Passo 1: Processa pacotes 0, 1, 3, 4
- Passo 2: Armazena pacotes 3 e 4 no buffer
- Passo 3: Recebe retransmissão do pacote 2
- Passo 4: Entrega pacotes 2, 3, 4 em ordem

**Estado das Variáveis:**

- buffer: {3: "sta ", 4: "é um"} → {} (após entrega)
- timers: {2: timer2} → {} (após ACK)

**Resultado:** Timeout detecta perda de ACK e retransmite apenas pacote específico.

## Exemplo de Execução

### Output do Servidor

```
Servidor iniciado em localhost:8080
Aguardando conexões...
Conexão estabelecida com ('127.0.0.1', 64768)
Iniciando handshake...
Dados recebidos: {'type': 'handshake', 'max_message_size': 100, 'operation_mode': 'selective_repeat'}
Handshake concluído:
  - Tamanho máximo: 100
  - Modo: selective_repeat

=== INICIANDO TROCA DE MENSAGENS ===
[SR] Iniciando Selective Repeat com janela de tamanho: 5
[BUFFER] Buffer de recebimento: 10 pacotes
Pacote recebido: {'type': 'data', 'seq_num': 0, 'payload': 'Olá ', 'checksum': 188}
[OK] Pacote 0 válido: 'Olá ' (checksum: 188)
[BUFFER] Pacote 0 armazenado no buffer
[DELIVER] Segmento 0 entregue em ordem
[ACK] ACK enviado para pacote 0
[BUFFER] Buffer vazio

=== MENSAGEM COMPLETA RECEBIDA ===
Texto: Olá mundo! Esta é uma mensagem de teste para o protocolo de transporte confiável.
Total de segmentos: 21
Tamanho total: 81 caracteres

=== TROCA DE MENSAGENS CONCLUÍDA ===
Conexão com ('127.0.0.1', 64768) encerrada
```

### Output do Cliente

```
Conectado ao servidor localhost:8080
Iniciando handshake...
Enviando: {'type': 'handshake', 'max_message_size': 100, 'operation_mode': 'selective_repeat'}
Resposta recebida: {'type': 'handshake_ack', 'max_message_size': 100, 'window_size': 5, 'operation_mode': 'selective_repeat', 'status': 'success'}
Handshake concluído!

=== INICIANDO TROCA DE MENSAGENS ===
Texto a ser enviado: Olá mundo! Esta é uma mensagem de teste para o protocolo de transporte confiável.
Tamanho da mensagem: 81 caracteres
[OK] Mensagem dentro do limite de 100 caracteres
Segmentos criados: ['Olá ', 'mund', 'o! E', 'sta ', 'é um', 'a me', 'nsag', 'em d', 'e te', 'ste ', 'para', ' o p', 'roto', 'colo', ' de ', 'tran', 'spor', 'te c', 'onfi', 'ável', '.']

[SR] Iniciando Selective Repeat com janela de tamanho: 5
[SEND] Enviando pacote 0: 'Olá ' (checksum: 188)
[TIMER] Timer iniciado para pacote 0 (5.0s)
[SEND] Enviando pacote 1: 'mund' (checksum: 180)
[TIMER] Timer iniciado para pacote 1 (5.0s)
[SEND] Enviando pacote 2: 'o! E' (checksum: 245)
[TIMER] Timer iniciado para pacote 2 (5.0s)
[SEND] Enviando pacote 3: 'sta ' (checksum: 104)
[TIMER] Timer iniciado para pacote 3 (5.0s)
[SEND] Enviando pacote 4: 'é um' (checksum: 235)
[TIMER] Timer iniciado para pacote 4 (5.0s)
[ACK] ACK recebido para pacote 0
[TIMER] Timer cancelado para pacote 0
[WINDOW] Janela movida. Base agora: 1
[ACK] ACK recebido para pacote 1
[TIMER] Timer cancelado para pacote 1
[WINDOW] Janela movida. Base agora: 2

=== TROCA DE MENSAGENS CONCLUÍDA ===
[TIMER] Todos os timers cancelados
Desconectado
```
