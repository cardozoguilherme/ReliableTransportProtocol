import socket
import json
import time
import threading

# Cliente com troca de mensagens

# ===== CONFIGURAÇÕES DO CLIENTE =====
HOST = 'localhost'                    # Endereço do servidor
PORT = 8080                           # Porta do servidor
MAX_MESSAGE_SIZE = 100                # Tamanho máximo da mensagem
OPERATION_MODE = 'go_back_n'          # Modo de operação ('go_back_n' ou 'selective_repeat')
TIMEOUT_DURATION = 5.0                # Timeout em segundos
TEXT_TO_SEND = "Olá mundo! Esta é uma mensagem de teste para o protocolo de transporte confiável."  # Texto a ser enviado
PAYLOAD_SIZE = 4                      # Tamanho do segmento (máximo 4, conforme especificação)

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

def create_nack_packet(seq_num):
    """Cria um pacote de reconhecimento negativo"""
    return {
        "type": "nack",    # Tipo de rejeição
        "seq_num": seq_num # Número do pacote rejeitado
    }

# Variáveis globais para timer
timers = {}  # Dicionário para armazenar timers ativos

def start_timer(seq_num, packet, socket_conn):
    """Inicia timer para um pacote específico"""
    def timeout_handler():
        print(f"[TIMEOUT] Timeout para pacote {seq_num} - retransmitindo...")
        # Para timeout, sempre retransmitir apenas o pacote específico
        # A lógica de Go-Back-N vs Selective Repeat é tratada no NACK
        send_message(socket_conn, packet)
        print(f"Pacote {seq_num} retransmitido por timeout")
    
    # Cancelar timer anterior se existir
    if seq_num in timers:
        timers[seq_num].cancel()
    
    # Criar novo timer
    timer = threading.Timer(TIMEOUT_DURATION, timeout_handler)
    timers[seq_num] = timer
    timer.start()
    print(f"[TIMER] Timer iniciado para pacote {seq_num} ({TIMEOUT_DURATION}s)")

def stop_timer(seq_num):
    """Para timer de um pacote específico"""
    if seq_num in timers:
        timers[seq_num].cancel()
        del timers[seq_num]
        print(f"[TIMER] Timer cancelado para pacote {seq_num}")

def stop_all_timers():
    """Para todos os timers ativos"""
    for timer in timers.values():
        timer.cancel()
    timers.clear()
    print("[TIMER] Todos os timers cancelados")

# Criar conexão com o servidor
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket TCP
s.connect((HOST, PORT)) # Conectar ao servidor

print(f"Conectado ao servidor {HOST}:{PORT}")

# Handshake - negociação inicial
print("Iniciando handshake...")

handshake_data = {
    "type": "handshake",           # Tipo da mensagem
    "max_message_size": MAX_MESSAGE_SIZE,      # Tamanho máximo da mensagem
    "operation_mode": OPERATION_MODE  # Modo de operação (go_back_n ou selective_repeat)
}

print(f"Enviando: {handshake_data}")
send_message(s, handshake_data) # Enviar handshake

response = receive_message(s) # Receber confirmação (ack do servidor)
print(f"Resposta recebida: {response}")

print("Handshake concluído!")

# Troca de mensagens - envio dos dados
print("\n=== INICIANDO TROCA DE MENSAGENS ===")

# Texto para enviar (dividido em segmentos de 4 caracteres)
text_to_send = TEXT_TO_SEND
print(f"Texto a ser enviado: {text_to_send}")
print(f"Tamanho da mensagem: {len(text_to_send)} caracteres")

# Verificar se a mensagem excede o limite máximo
max_message_size = response["max_message_size"]
if len(text_to_send) > max_message_size:
    print(f"[WARNING] ATENÇÃO: Mensagem excede limite de {max_message_size} caracteres!")
    print(f"[INFO] Tamanho atual: {len(text_to_send)} caracteres")
    print(f"[INFO] Truncando mensagem para {max_message_size} caracteres...")
    text_to_send = text_to_send[:max_message_size]
    print(f"[INFO] Nova mensagem: {text_to_send}")
    print(f"[INFO] Novo tamanho: {len(text_to_send)} caracteres")
else:
    print(f"[OK] Mensagem dentro do limite de {max_message_size} caracteres")

# Dividir texto em segmentos de até 4 caracteres (configurável por PAYLOAD_SIZE)
effective_payload = PAYLOAD_SIZE if PAYLOAD_SIZE <= 4 else 4
segments = [text_to_send[i:i+effective_payload] for i in range(0, len(text_to_send), effective_payload)] # Cortar em pedaços de até 4 caracteres
print(f"Segmentos criados: {segments}\n")

# Implementar protocolo baseado no modo de operação
window_size = response["window_size"]  # Tamanho da janela do servidor
operation_mode = response["operation_mode"]  # Modo de operação
sent_packets = {}                      # Armazenar pacotes enviados
acknowledged_packets = set()           # Pacotes confirmados
next_seq_to_send = 0                   # Próximo número de sequência a enviar
base_seq = 0                          # Base da janela (primeiro não confirmado)

if operation_mode == "go_back_n":
    print(f"[GBN] Iniciando Go-Back-N com janela de tamanho: {window_size}")
elif operation_mode == "selective_repeat":
    print(f"[SR] Iniciando Selective Repeat com janela de tamanho: {window_size}")
else:
    print(f"[WARNING] Modo desconhecido: {operation_mode}, usando Go-Back-N")
    operation_mode = "go_back_n"

# Enviar pacotes dentro da janela
while base_seq < len(segments):
    # Enviar pacotes até preencher a janela
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
    
    # Aguardar ACKs até janela estar confirmada ou timeout
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
                    
            elif response["type"] == "nack":
                print(f"[NACK] NACK recebido para pacote {ack_seq}")
                
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
                
                elif operation_mode == "selective_repeat":
                    # Selective Repeat: Retransmitir apenas o pacote específico
                    print(f"[SR] Selective Repeat: Retransmitindo apenas pacote {ack_seq}")
                    if ack_seq in sent_packets:
                        packet = sent_packets[ack_seq]
                        print(f"[RETRY] Retransmitindo pacote {ack_seq}: '{packet['payload']}'")
                        send_message(s, packet)
                        # Reiniciar timer apenas para este pacote
                        start_timer(ack_seq, packet, s)
                
        except:
            print("Conexão encerrada pelo servidor")
            break
    
    # Pequena pausa
    time.sleep(0.1)

print("\n=== TROCA DE MENSAGENS CONCLUÍDA ===")
stop_all_timers()  # Parar todos os timers ativos
s.close() # Fechar conexão
print("Desconectado")