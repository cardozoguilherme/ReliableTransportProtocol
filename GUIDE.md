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

| Argumento             | Padrão            | Exemplo                              |
| --------------------- | ----------------- | ------------------------------------ |
| `--host`              | `localhost`       | `--host 192.168.1.100`               |
| `--port`              | `8080`            | `--port 9090`                        |
| `--operation-mode`    | `go_back_n`       | `--operation-mode selective_repeat`  |
| `--max-message-size`  | `100`             | `--max-message-size 200`             |
| `--timeout`           | `5.0`             | `--timeout 3.0`                      |
| `--text`              | (mensagem padrão) | `--text "Minha mensagem"`            |
| `--payload-size`      | `4`               | `--payload-size 2`                   |
| `--enable-encryption` | (desabilitado)    | `--enable-encryption`                |
| `--caesar-shift`      | `1`               | `--caesar-shift 3`                   |
| `--drop-packets`      | (nenhum)          | `--drop-packets "2,5"` ou `"3-7"`    |
| `--corrupt-packets`   | (nenhum)          | `--corrupt-packets "3,7"` ou `"4-6"` |

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

### Com criptografia (Cifra de César)

```bash
# Servidor (suporta criptografia automaticamente)
python server.py

# Cliente com criptografia habilitada (shift padrão = 1)
python client.py --enable-encryption

# Cliente com criptografia e shift customizado
python client.py --enable-encryption --caesar-shift 3
```

**Exemplo de Cifra de César:**

- Shift = 1: "SUKAR" → "TVLBS"
- Shift = 3: "ABC" → "DEF"
- Apenas letras (A-Z, a-z) são deslocadas, outros caracteres permanecem iguais

### Com simulação de erros

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
- **Criptografia:** Use `--enable-encryption` no cliente para criptografar payloads usando Cifra de César. Use `--caesar-shift` para definir o deslocamento (padrão: 1)
- **Simulação de Erros:** Use `--drop-packets` para simular perdas e `--corrupt-packets` para simular corrupção
- **Intervalos:** Suporte a intervalos (`"2-5"`) e listas (`"2,5,10"`) para simulação de erros

## Instalação de Dependências

O projeto usa apenas bibliotecas padrão do Python. Não são necessárias dependências externas.
