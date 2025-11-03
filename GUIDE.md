# Guia Rápido - Como Usar

Para ver todos os argumentos disponíveis e suas descrições, use `--help`:

```bash
python server.py --help
python client.py --help
```

## Execução Rápida

### Servidor

```bash
python server.py
```

### Cliente

```bash
python client.py
```

## Argumentos Disponíveis

### Servidor (`server.py`)

| Argumento       | Padrão      | Exemplo            |
| --------------- | ----------- | ------------------ |
| `--host`        | `localhost` | `--host 0.0.0.0`   |
| `--port`        | `8080`      | `--port 9090`      |
| `--window-size` | `5`         | `--window-size 10` |

### Cliente (`client.py`)

| Argumento            | Padrão            | Exemplo                             |
| -------------------- | ----------------- | ----------------------------------- |
| `--host`             | `localhost`       | `--host 192.168.1.100`              |
| `--port`             | `8080`            | `--port 9090`                       |
| `--operation-mode`   | `go_back_n`       | `--operation-mode selective_repeat` |
| `--max-message-size` | `100`             | `--max-message-size 200`            |
| `--timeout`          | `5.0`             | `--timeout 3.0`                     |
| `--text`             | (mensagem padrão) | `--text "Minha mensagem"`           |
| `--payload-size`     | `4`               | `--payload-size 2`                  |

**Nota:** O `--payload-size` tem limite máximo de **4 caracteres** conforme especificação. Valores maiores serão automaticamente limitados a 4.

## Exemplos Práticos

### Básico (valores padrão)

```bash
# Terminal 1
python server.py

# Terminal 2
python client.py
```

### Servidor em rede local

```bash
python server.py --host 0.0.0.0
python client.py --host <IP_SERVIDOR>
```

### Selective Repeat

```bash
python client.py --operation-mode selective_repeat
```

### Mensagem personalizada

```bash
python client.py --text "Sua mensagem aqui"
```

### Configuração completa

```bash
# Servidor
python server.py --port 9090 --window-size 7

# Cliente
python client.py --port 9090 --operation-mode selective_repeat --timeout 3.0 --max-message-size 150
```

## Ajuda

```bash
python server.py --help
python client.py --help
```

## Dicas

- **Portas devem coincidir:** Cliente e servidor devem usar a mesma porta
- **Strings com espaços:** Use aspas: `--text "mensagem com espaços"`
- **Modos:** `go_back_n` (padrão) ou `selective_repeat`
- **Payload máximo:** 4 caracteres (conforme especificação - valores maiores são limitados automaticamente)
