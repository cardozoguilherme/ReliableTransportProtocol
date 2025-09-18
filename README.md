# Aplicação de Transporte Confiável de Dados

Esta versão implementa apenas o handshake inicial entre cliente e servidor, na camada de aplicação, para acordar o modo de operação e o tamanho máximo de mensagem.

## Estrutura do Projeto

- `server.py` - Servidor simples que realiza handshake e encerra conexão
- `client.py` - Cliente simples que realiza handshake com o servidor
- `README.md` - Documentação do projeto

## Protocolo de Aplicação (Handshake)

O handshake é realizado na primeira comunicação entre cliente e servidor para estabelecer os parâmetros da conexão. Após o handshake, o servidor encerra a conexão.

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

### ✅ Código Simplificado

- Sem classes complexas
- Sem validações elaboradas
- Sem tratamento de erro excessivo
- Código direto e funcional

## Próximas Implementações

Serão adicionadas nas próximas etapas:

- [ ] Soma de verificação
- [ ] Temporizador
- [ ] Número de sequência
- [ ] Reconhecimento positivo/negativo
- [ ] Janela deslizante
- [ ] Simulação de perdas e erros
- [ ] Pacotes com carga útil de 4 caracteres
- [ ] Algoritmo de checagem de integridade (pontuação extra)
- [ ] Criptografia simétrica (pontuação extra)

## Exemplo de Execução

**Servidor:**

```
Servidor iniciado em localhost:8080
Aguardando conexões...
Conexão estabelecida com ('127.0.0.1', 54321)
Iniciando handshake...
Dados recebidos: {'type': 'handshake', 'max_message_size': 50, 'operation_mode': 'go_back_n'}
Handshake concluído:
  - Tamanho máximo: 50
  - Modo: go_back_n
Conexão com ('127.0.0.1', 54321) encerrada
```

**Cliente:**

```
Conectado ao servidor localhost:8080
Iniciando handshake...
Enviando: {'type': 'handshake', 'max_message_size': 50, 'operation_mode': 'go_back_n'}
Resposta recebida: {'type': 'handshake_ack', 'max_message_size': 50, 'window_size': 5, 'operation_mode': 'go_back_n', 'status': 'success'}
Handshake concluído!
Desconectado
```
