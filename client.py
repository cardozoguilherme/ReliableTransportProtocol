import socket
import json
import time

# Cliente com troca de mensagens
HOST = 'localhost'  # Endereço do servidor
PORT = 8080        # Porta do servidor

def send_message(socket, message):
    """Envia uma mensagem com framing"""
    json_data = json.dumps(message) # Converte dicionário para JSON
    message_bytes = json_data.encode('utf-8') # Converte a stirng para bytes
    socket.send(len(message_bytes).to_bytes(4, byteorder='big')) # Envia tamanho primeiro (4 bytes)
    socket.send(message_bytes) # Envia a mensagem

def receive_message(socket):
    """Recebe uma mensagem com framing"""
    size_data = socket.recv(4) # Recebe os 4 bytes do tamanho
    size = int.from_bytes(size_data, byteorder='big') # Converte para número
    
    message_data = b'' # Buffer para a mensagem (string de bytes)
    while len(message_data) < size: # Recebe até completar o tamanho
        chunk = socket.recv(size - len(message_data))
        message_data += chunk
    
    return json.loads(message_data.decode('utf-8')) # Converte de volta para dicionário

def calculate_checksum(data):
    """Calcula soma de verificação simples"""
    return sum(ord(c) for c in data) % 256 # Soma valores ASCII e pega resto da divisão por 256

def create_data_packet(seq_num, payload, checksum):
    """Cria um pacote de dados"""
    return {
        "type": "data",      # Tipo da mensagem
        "seq_num": seq_num,  # Número de sequência
        "payload": payload,  # Dados (4 caracteres)
        "checksum": checksum # Soma de verificação
    }

def create_ack_packet(seq_num):
    """Cria um pacote de reconhecimento"""
    return {
        "type": "ack",     # Tipo de confirmação
        "seq_num": seq_num # Número do pacote confirmado
    }

# Criar conexão com o servidor
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket TCP
s.connect((HOST, PORT)) # Conectar ao servidor

print(f"Conectado ao servidor {HOST}:{PORT}")

# Handshake - negociação inicial
print("Iniciando handshake...")

handshake_data = {
    "type": "handshake",           # Tipo da mensagem
    "max_message_size": 50,        # Tamanho máximo da mensagem
    "operation_mode": "go_back_n"  # Modo de operação
}

print(f"Enviando: {handshake_data}")
send_message(s, handshake_data) # Enviar handshake

response = receive_message(s) # Receber confirmação (ack do servidor)
print(f"Resposta recebida: {response}")

print("Handshake concluído!")

# Troca de mensagens - envio dos dados
print("\n=== INICIANDO TROCA DE MENSAGENS ===")

# Texto para enviar (dividido em segmentos de 4 caracteres)
text_to_send = "Olá mundo! Esta é uma mensagem de teste para o protocolo de transporte confiável."
print(f"Texto a ser enviado: {text_to_send}")

# Dividir texto em segmentos de 4 caracteres
segments = [text_to_send[i:i+4] for i in range(0, len(text_to_send), 4)] # Cortar em pedaços de 4 caracteres
print(f"Segmentos criados: {segments}\n")

# Enviar cada segmento como um pacote
seq_num = 0                           # Número de sequência inicial (número do pacote)
window_size = response["window_size"] # Tamanho da janela do servidor
sent_packets = {}                     # Armazenar pacotes enviados

for i, segment in enumerate(segments):
    # Criar pacote para este segmento
    checksum = calculate_checksum(segment) # Calcular verificação
    packet = create_data_packet(seq_num, segment, checksum) # Montar pacote
    
    print(f"Enviando pacote {seq_num}: '{segment}' (checksum: {checksum})")
    send_message(s, packet)  # Enviar pacote
    
    # Armazenar pacote enviado (para possível retransmissão)
    sent_packets[seq_num] = packet
    
    # Aguardar confirmação (ACK) do servidor
    try:
        ack_response = receive_message(s)
        print(f"ACK recebido: {ack_response}")
    except:
        print("Conexão encerrada pelo servidor")
        break
    
    seq_num += 1 # Próximo número de sequência
    
    # Simular pequena pausa entre pacotes
    time.sleep(0.1)

print("\n=== TROCA DE MENSAGENS CONCLUÍDA ===")
s.close() # Fechar conexão
print("Desconectado")