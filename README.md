# Aplicação de Transporte Confiável de Dados

Esta versão implementa o handshake inicial e a troca de mensagens entre cliente e servidor, na camada de aplicação, considerando um canal de comunicação sem erros e perdas.

## Estrutura do Projeto

- `server.py` - Servidor que realiza handshake e troca de mensagens
- `client.py` - Cliente que realiza handshake e envia mensagens
- `README.md` - Documentação do projeto

## Protocolo de Aplicação

O protocolo implementa um sistema de transporte confiável com duas fases: handshake inicial e troca de mensagens. O handshake estabelece os parâmetros da conexão, e em seguida inicia-se a troca de mensagens divididas em segmentos de 4 caracteres.

### Mensagem de Handshake (Cliente → Servidor)

```json
{
  "type": "handshake",
  "max_message_size": 50,
  "operation_mode": "go_back_n"
}
```

**Campos:**

- `type`: Tipo da mensagem (sempre "handshake")
- `max_message_size`: Tamanho máximo de caracteres por mensagem
- `operation_mode`: Modo de operação ("go_back_n" ou "selective_repeat")

### Resposta do Handshake (Servidor → Cliente)

```json
{
  "type": "handshake_ack",
  "max_message_size": 50,
  "window_size": 5,
  "operation_mode": "go_back_n",
  "status": "success"
}
```

**Campos:**

- `type`: Tipo da mensagem (sempre "handshake_ack")
- `max_message_size`: Tamanho máximo confirmado pelo servidor
- `window_size`: Tamanho da janela (fixo em 5)
- `operation_mode`: Modo de operação confirmado
- `status`: Status do handshake ("success")

### Fluxo do Protocolo

1. **Handshake**: Cliente e servidor negociam parâmetros
2. **Divisão**: Cliente divide mensagem em segmentos de 4 caracteres
3. **Envio**: Cliente envia cada segmento como pacote separado
4. **Verificação**: Servidor verifica checksum e número de sequência
5. **Confirmação**: Servidor envia ACK para cada pacote válido
6. **Reconstrução**: Servidor reconstrói mensagem original

## Protocolo de Troca de Mensagens

Após o handshake, o cliente envia mensagens divididas em segmentos de 4 caracteres, cada um em um pacote separado.

### Pacote de Dados (Cliente → Servidor)

```json
{
  "type": "data",
  "seq_num": 0,
  "payload": "Olá ",
  "checksum": 123
}
```

**Campos:**

- `type`: Tipo da mensagem (sempre "data")
- `seq_num`: Número de sequência do pacote
- `payload`: Carga útil (máximo 4 caracteres)
- `checksum`: Soma de verificação do payload

### Pacote de Reconhecimento (Servidor → Cliente)

```json
{
  "type": "ack",
  "seq_num": 0
}
```

**Campos:**

- `type`: Tipo da mensagem (sempre "ack")
- `seq_num`: Número de sequência reconhecido

## Características do Protocolo

### ✅ Soma de Verificação

- Cálculo simples: soma dos valores ASCII dos caracteres módulo 256
- Verificação de integridade dos dados

### ✅ Número de Sequência

- Cada pacote possui um número de sequência sequencial
- Controle de ordem dos pacotes

### ✅ Reconhecimento Positivo (ACK)

- Servidor envia ACK para cada pacote recebido
- Cliente aguarda ACK antes de enviar próximo pacote

### ✅ Carga Útil de 4 Caracteres

- Cada pacote contém no máximo 4 caracteres
- Texto dividido automaticamente em segmentos

## Como Usar

### 1. Executar o Servidor

```bash
python server.py
```

O servidor será iniciado em `localhost:8080` e aguardará conexões.

### 2. Executar o Cliente (em outro terminal)

```bash
python client.py
```

O cliente se conectará automaticamente ao servidor, realizará o handshake e encerrará.

### 3. Configurações Personalizadas

Para modificar as configurações do cliente, edite as variáveis no arquivo `client.py`:

```python
# Configurações do cliente
HOST = 'localhost'  # ou IP do servidor
PORT = 8080

# Configurações do handshake
handshake_data = {
    "type": "handshake",
    "max_message_size": 50,  # Altere aqui
    "operation_mode": "go_back_n"  # ou "selective_repeat"
}
```

## Características Implementadas

### ✅ Handshake Inicial

- Troca de modo de operação (Go-Back-N ou Selective Repeat)
- Definição do tamanho máximo de mensagem
- Confirmação de configurações

### ✅ Comunicação via Sockets

- Suporte a localhost e IP
- Protocolo TCP confiável
- Framing com prefixo de 4 bytes

### ✅ Troca de Mensagens

- Divisão de texto em segmentos de 4 caracteres
- Número de sequência para cada pacote
- Soma de verificação simples
- Reconhecimento positivo (ACK)
- Reconstrução da mensagem completa no servidor

### ✅ Código Simplificado

- Sem classes complexas
- Sem validações elaboradas
- Sem tratamento de erro excessivo
- Código direto e funcional

## Próximas Implementações

Serão adicionadas nas próximas etapas:

- [ ] Janela deslizante (Go-Back-N e Selective Repeat)
- [ ] Temporizador
- [ ] Reconhecimento negativo (NACK)
- [ ] Simulação de perdas e erros
- [ ] Algoritmo de checagem de integridade (pontuação extra)
- [ ] Criptografia simétrica (pontuação extra)

## Exemplo de Execução

**Servidor:**

```
Servidor iniciado em localhost:8080
Aguardando conexões...
Conexão estabelecida com ('127.0.0.1', 64768)
Iniciando handshake...
Dados recebidos: {'type': 'handshake', 'max_message_size': 50, 'operation_mode': 'go_back_n'}
Handshake concluído:
  - Tamanho máximo: 50
  - Modo: go_back_n

=== INICIANDO TROCA DE MENSAGENS ===
Pacote recebido: {'type': 'data', 'seq_num': 0, 'payload': 'Olá ', 'checksum': 188}
✓ Pacote 0 válido: 'Olá ' (checksum: 188)
✓ Segmento 0 adicionado à mensagem
ACK enviado para pacote 0
Metadados do pacote 0:
  - Payload: 'Olá '
  - Checksum: 188
  - Número de sequência: 0
  - Status: Válido

Pacote recebido: {'type': 'data', 'seq_num': 1, 'payload': 'mund', 'checksum': 180}
✓ Pacote 1 válido: 'mund' (checksum: 180)
✓ Segmento 1 adicionado à mensagem
ACK enviado para pacote 1
...

=== MENSAGEM COMPLETA RECEBIDA ===
Texto: Olá mundo! Esta é uma mensagem de teste para o protocolo de transporte confiável.
Total de segmentos: 20
Tamanho total: 81 caracteres

=== TROCA DE MENSAGENS CONCLUÍDA ===
Conexão com ('127.0.0.1', 64768) encerrada
```

**Cliente:**

```
Conectado ao servidor localhost:8080
Iniciando handshake...
Enviando: {'type': 'handshake', 'max_message_size': 50, 'operation_mode': 'go_back_n'}
Resposta recebida: {'type': 'handshake_ack', 'max_message_size': 50, 'window_size': 5, 'operation_mode': 'go_back_n', 'status': 'success'}
Handshake concluído!

=== INICIANDO TROCA DE MENSAGENS ===
Texto a ser enviado: Olá mundo! Esta é uma mensagem de teste para o protocolo de transporte confiável.
Segmentos criados: ['Olá ', 'mund', 'o! E', 'sta ', 'é um', 'a me', 'nsag', 'em d', 'e te', 'ste ', 'para', ' o p', 'roto', 'colo', ' de ', 'tran', 'spor', 'te c', 'onfi', 'ável', '.']

Enviando pacote 0: 'Olá ' (checksum: 188)
ACK recebido: {'type': 'ack', 'seq_num': 0}
Enviando pacote 1: 'mund' (checksum: 180)
ACK recebido: {'type': 'ack', 'seq_num': 1}
...

=== TROCA DE MENSAGENS CONCLUÍDA ===
Desconectado
```
