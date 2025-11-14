# Guia de Testes - Como Usar os Testes Implementados

Este guia ensina como usar os argumentos de teste implementados no código.

## 📋 Índice

1. [Argumentos de Teste Disponíveis](#argumentos-de-teste-disponíveis)
2. [Como Usar --drop-packets](#como-usar---drop-packets)
3. [Como Usar --corrupt-packets](#como-usar---corrupt-packets)
4. [Exemplos Práticos](#exemplos-práticos)

---

## Argumentos de Teste Disponíveis

O cliente possui dois argumentos principais para simulação de erros:

| Argumento           | Descrição                           | Exemplo               |
| ------------------- | ----------------------------------- | --------------------- |
| `--drop-packets`    | Simula perda de pacotes (não envia) | `--drop-packets 2`    |
| `--corrupt-packets` | Simula corrupção de checksum        | `--corrupt-packets 3` |

**⚠️ IMPORTANTE:** Os pacotes são numerados começando em **0** (zero).

---

## Como Usar --drop-packets

### Sintaxe

```bash
--drop-packets <valor>
```

Onde `<valor>` pode ser:

- **Número único**: `2` (perde apenas o pacote 2)
- **Lista**: `"2,5,10"` (perde pacotes 2, 5 e 10)
- **Intervalo**: `"3-7"` (perde pacotes 3, 4, 5, 6, 7)
- **Combinado**: `"2,5-7,10"` (perde pacotes 2, 5, 6, 7, 10)

### Exemplos

#### Perder um único pacote:

```bash
python client.py --drop-packets 2
```

**O que acontece:**

- Pacote 2 não é enviado
- Timer expira após 5 segundos
- Pacote 2 é retransmitido automaticamente

**Logs esperados:**

```
[SIMULATION] ⚠️  PERDA SIMULADA: Pacote 2 não será enviado
[TIMEOUT] Timeout para pacote 2 - retransmitindo...
```

---

#### Perder múltiplos pacotes (lista):

```bash
python client.py --drop-packets "2,5,10"
```

**O que acontece:**

- Pacotes 2, 5 e 10 não são enviados
- Cada um tem seu timer
- Cada um é retransmitido quando o timer expira

**Logs esperados:**

```
[SIMULATION] Simulação de erros ativada:
  - Pacotes a perder: [2, 5, 10]
[SIMULATION] ⚠️  PERDA SIMULADA: Pacote 2 não será enviado
[SIMULATION] ⚠️  PERDA SIMULADA: Pacote 5 não será enviado
[SIMULATION] ⚠️  PERDA SIMULADA: Pacote 10 não será enviado
```

---

#### Perder intervalo de pacotes:

```bash
python client.py --drop-packets "3-7"
```

**O que acontece:**

- Pacotes 3, 4, 5, 6, 7 não são enviados
- Todos são retransmitidos quando os timers expiram

**Logs esperados:**

```
[SIMULATION] Simulação de erros ativada:
  - Pacotes a perder: [3, 4, 5, 6, 7]
```

---

## Como Usar --corrupt-packets

### Sintaxe

```bash
--corrupt-packets <valor>
```

Mesma sintaxe do `--drop-packets`:

- **Número único**: `3` (corrompe apenas o pacote 3)
- **Lista**: `"3,7"` (corrompe pacotes 3 e 7)
- **Intervalo**: `"4-6"` (corrompe pacotes 4, 5, 6)
- **Combinado**: `"3,7-9,15"` (corrompe pacotes 3, 7, 8, 9, 15)

### Exemplos

#### Corromper um único pacote:

```bash
python client.py --corrupt-packets 3
```

**O que acontece:**

- Pacote 3 é enviado com checksum incorreto
- Servidor detecta o erro
- Servidor envia NACK
- Cliente retransmite com checksum correto

**Logs esperados:**

```
[SIMULATION] ⚠️  CORRUPÇÃO SIMULADA: Pacote 3 com checksum incorreto (104 -> 105)
[SEND] Enviando pacote 3: 'sta ' (checksum: 105)
Servidor: [ERROR] Pacote 3 com erro de checksum
Servidor: [NACK] NACK enviado para pacote 3
[NACK] NACK recebido para pacote 3
[RETRY] Retransmitindo pacote 3 com checksum corrigido
Servidor: [OK] Pacote 3 válido: 'sta ' (checksum: 104)
```

---

#### Corromper múltiplos pacotes:

```bash
python client.py --corrupt-packets "3,7,15"
```

**O que acontece:**

- Pacotes 3, 7 e 15 são enviados com checksum incorreto
- Cada um recebe NACK
- Cada um é retransmitido com checksum correto

---

#### Corromper intervalo de pacotes:

```bash
python client.py --corrupt-packets "4-6"
```

**O que acontece:**

- Pacotes 4, 5, 6 são enviados com checksum incorreto
- Todos recebem NACK
- Todos são retransmitidos com checksum correto

---

## Exemplos Práticos

### Exemplo 1: Teste Básico de Perda

```bash
# Terminal 1
python server.py

# Terminal 2
python client.py --drop-packets 2
```

**Resultado esperado:**

- Pacote 2 não é enviado
- Timer expira
- Retransmissão automática
- Mensagem completa no servidor

---

### Exemplo 2: Teste Básico de Corrupção

```bash
# Terminal 1
python server.py

# Terminal 2
python client.py --corrupt-packets 3
```

**Resultado esperado:**

- Pacote 3 enviado com checksum incorreto
- Servidor detecta erro e envia NACK
- Retransmissão com checksum correto
- Mensagem completa no servidor

---

### Exemplo 3: Combinar Perda e Corrupção

```bash
python client.py --drop-packets 2 --corrupt-packets 5
```

**O que acontece:**

- Pacote 2 é perdido (não enviado)
- Pacote 5 é corrompido (checksum incorreto)
- Ambos são corrigidos via retransmissão

**Logs esperados:**

```
[SIMULATION] Simulação de erros ativada:
  - Pacotes a perder: [2]
  - Pacotes a corromper: [5]
[SIMULATION] ⚠️  PERDA SIMULADA: Pacote 2 não será enviado
[SIMULATION] ⚠️  CORRUPÇÃO SIMULADA: Pacote 5 com checksum incorreto (83 -> 84)
```

---

### Exemplo 4: Teste com Go-Back-N

```bash
python client.py --operation-mode go_back_n --drop-packets 2
```

**O que observar:**

- Servidor ignora pacotes fora de ordem
- Cliente retransmite toda a janela

---

### Exemplo 5: Teste com Selective Repeat

```bash
python client.py --operation-mode selective_repeat --drop-packets 2
```

**O que observar:**

- Servidor armazena pacotes no buffer
- Cliente retransmite apenas o pacote perdido

**Logs esperados:**

```
Servidor: [BUFFER] Pacote 3 armazenado no buffer
Servidor: [BUFFER] Pacote 4 armazenado no buffer
[SR] Selective Repeat: Retransmitindo apenas pacote 2
```

---

### Exemplo 6: Teste com Criptografia

```bash
python client.py --enable-encryption --drop-packets 3
```

**O que acontece:**

- Criptografia funciona normalmente
- Perda de pacote funciona com criptografia
- Retransmissão também é criptografada

---

### Exemplo 7: Teste Completo

```bash
python client.py --operation-mode selective_repeat --enable-encryption --drop-packets "2,5" --corrupt-packets 7 --timeout 3.0 --text "Mensagem de teste muito grande para testar se funciona usada no exemplo"
```

**O que este comando faz:**

- Usa Selective Repeat
- Habilita criptografia
- Perde pacotes 2 e 5
- Corrompe pacote 7
- Timeout de 3 segundos
- Mensagem personalizada

---

## Resumo dos Comandos

### Perda de Pacotes

```bash
# Um pacote
python client.py --drop-packets 2

# Múltiplos pacotes
python client.py --drop-packets "2,5,10"

# Intervalo
python client.py --drop-packets "3-7"

# Combinado
python client.py --drop-packets "2,5-7,10"
```

### Corrupção de Checksum

```bash
# Um pacote
python client.py --corrupt-packets 3

# Múltiplos pacotes
python client.py --corrupt-packets "3,7"

# Intervalo
python client.py --corrupt-packets "4-6"
```

### Combinar Tudo

```bash
python client.py --operation-mode selective_repeat --enable-encryption --drop-packets "2,5" --corrupt-packets 7 --timeout 3.0 --text "Mensagem de teste longa para testar corretamente e validar"
```
