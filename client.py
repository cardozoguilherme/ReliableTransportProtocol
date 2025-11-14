import socket
import json
import time
import argparse
import datetime

# Cliente com troca de mensagens

# ===== CONFIGURAÇÕES DO CLIENTE (via CLI) =====
parser = argparse.ArgumentParser(description='Cliente do Protocolo de Transporte Confiável')
parser.add_argument('--host', type=str, default='localhost', help='Endereço do servidor (padrão: localhost)')
parser.add_argument('--port', type=int, default=8080, help='Porta do servidor (padrão: 8080)')
parser.add_argument('--max-message-size', type=int, default=100, help='Tamanho máximo da mensagem (padrão: 100)')
parser.add_argument('--operation-mode', type=str, default='go_back_n', 
                    choices=['go_back_n', 'selective_repeat'], 
                    help='Modo de operação: go_back_n ou selective_repeat (padrão: go_back_n)')
parser.add_argument('--timeout', type=float, default=5.0, help='Timeout em segundos (padrão: 5.0)')
parser.add_argument('--text', type=str, 
                    default="Olá mundo! Esta é uma mensagem de teste para o protocolo de transporte confiável.",
                    help='Texto a ser enviado')
parser.add_argument('--payload-size', type=int, default=4, 
                    help='Tamanho do segmento/payload (padrão: 4, máximo: 4)')
parser.add_argument('--enable-encryption', action='store_true',
                    help='Ativar criptografia Cifra de César para payloads')
parser.add_argument('--caesar-shift', type=int, default=1,
                    help='Número de deslocamento para Cifra de César (padrão: 1)')
parser.add_argument('--drop-packets', type=str, default='',
                    help='Pacotes a perder (ex: "2,5,10" ou "2-5" para intervalo)')
parser.add_argument('--corrupt-packets', type=str, default='',
                    help='Pacotes a corromper (ex: "3,7" ou "3-7" para intervalo)')

args = parser.parse_args()

HOST = args.host
PORT = args.port
MAX_MESSAGE_SIZE = args.max_message_size
OPERATION_MODE = args.operation_mode
TIMEOUT_DURATION = args.timeout
TEXT_TO_SEND = args.text
PAYLOAD_SIZE = min(args.payload_size, 4)  # Garantir que não exceda 4
ENABLE_ENCRYPTION = args.enable_encryption
CAESAR_SHIFT = args.caesar_shift

# Processar lista de pacotes para perder
packets_to_drop = set()
if args.drop_packets:
    for item in args.drop_packets.split(','):
        item = item.strip()
        if '-' in item:
            # Intervalo (ex: "2-5")
            start, end = map(int, item.split('-'))
            packets_to_drop.update(range(start, end + 1))
        else:
            # Número único
            packets_to_drop.add(int(item))

# Processar lista de pacotes para corromper
packets_to_corrupt = set()
if args.corrupt_packets:
    for item in args.corrupt_packets.split(','):
        item = item.strip()
        if '-' in item:
            # Intervalo (ex: "3-7")
            start, end = map(int, item.split('-'))
            packets_to_corrupt.update(range(start, end + 1))
        else:
            # Número único
            packets_to_corrupt.add(int(item))

# Estatísticas de simulação
simulation_stats = {
    'packets_dropped': 0,
    'packets_corrupted': 0,
    'total_packets': 0
}

def send_message(socket, message):
    """Envia uma mensagem com framing"""
    json_data = json.dumps(message) # Converte dicionário para JSON
    message_bytes = json_data.encode('utf-8') # Converte a stirng para bytes
    socket.send(len(message_bytes).to_bytes(4, byteorder='big')) # Envia tamanho primeiro (4 bytes)
    socket.send(message_bytes) # Envia a mensagem

def receive_message(socket, timeout=None):
    """Recebe uma mensagem com framing"""
    if timeout is not None:
        socket.settimeout(timeout)
    
    try:
        size_data = socket.recv(4) # Recebe os 4 bytes do tamanho
        if not size_data:
            raise TimeoutError("Nenhum dado recebido")
        
        size = int.from_bytes(size_data, byteorder='big') # Converte para número
        
        message_data = b'' # Buffer para a mensagem (string de bytes)
        while len(message_data) < size: # Recebe até completar o tamanho
            chunk = socket.recv(size - len(message_data))
            if not chunk:
                raise TimeoutError("Conexão fechada durante recebimento")
            message_data += chunk
        
        return json.loads(message_data.decode('utf-8')) # Converte de volta para dicionário
    except (OSError, TimeoutError) as e:
        if "timed out" in str(e).lower() or "timeout" in str(e).lower():
            raise TimeoutError("Timeout ao receber mensagem")
        raise

def caesar_encrypt(text, shift):
    """Criptografa texto usando Cifra de César"""
    result = []
    for char in text:
        if char.isalpha():
            # Determinar se é maiúscula ou minúscula
            base = ord('A') if char.isupper() else ord('a')
            # Aplicar deslocamento circular
            shifted = (ord(char) - base + shift) % 26
            result.append(chr(base + shifted))
        else:
            # Manter caracteres não-alfabéticos inalterados
            result.append(char)
    return ''.join(result)


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

def get_timestamp():
    """Retorna timestamp formatado para logs"""
    return datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]

# Variáveis globais para timer e protocolo
sent_packets = {}  # Armazenar pacotes enviados
acknowledged_packets_global = set()  # Pacotes confirmados
packet_send_times = {}  # Timestamp de quando cada pacote foi enviado (para timeout síncrono)

def start_timer(seq_num):
    """Registra timestamp de envio do pacote (para timeout síncrono)"""
    packet_send_times[seq_num] = time.time()
    print(f"\n[{get_timestamp()}] [TIMER] Timer iniciado para pacote {seq_num} ({TIMEOUT_DURATION}s)")

def stop_timer(seq_num):
    """Remove timestamp do pacote confirmado"""
    if seq_num in packet_send_times:
        del packet_send_times[seq_num]
        print(f"[{get_timestamp()}] [TIMER] Timer cancelado para pacote {seq_num}\n")

# Criar conexão com o servidor
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket TCP
s.connect((HOST, PORT)) # Conectar ao servidor

def retransmit_packet(seq_num):
    """Retransmite um pacote específico com checksum corrigido se necessário"""
    if seq_num not in sent_packets or seq_num in acknowledged_packets_global:
        return
    
    retry_packet = sent_packets[seq_num].copy()
    if 'original_checksum' in retry_packet:
        retry_packet['checksum'] = retry_packet['original_checksum']
        print(f"[{get_timestamp()}] [RETRY] Retransmitindo pacote {seq_num} com checksum corrigido")
    else:
        payload_display = retry_packet.get('payload', 'encrypted')
        print(f"[{get_timestamp()}] [RETRY] Retransmitindo pacote {seq_num}: '{payload_display}'\n")
    
    send_message(s, retry_packet)
    packet_send_times[seq_num] = time.time()
    start_timer(seq_num)

print(f"Conectado ao servidor {HOST}:{PORT}")

# Handshake - negociação inicial
print("Iniciando handshake...")

handshake_data = {
    "type": "handshake",           # Tipo da mensagem
    "max_message_size": MAX_MESSAGE_SIZE,      # Tamanho máximo da mensagem
    "operation_mode": OPERATION_MODE,  # Modo de operação (go_back_n ou selective_repeat)
    "encryption_enabled": ENABLE_ENCRYPTION  # Flag de criptografia
}

# Adicionar shift da Cifra de César se habilitada
if ENABLE_ENCRYPTION:
    print(f"[ENCRYPTION] Cifra de César ativada com deslocamento: {CAESAR_SHIFT}")
    handshake_data["caesar_shift"] = CAESAR_SHIFT

print(f"Enviando: {handshake_data}")
send_message(s, handshake_data) # Enviar handshake

# Handshake não precisa de timeout curto, usar timeout maior
s.settimeout(10.0)  # Timeout maior para handshake
response = receive_message(s) # Receber confirmação (ack do servidor)
print(f"Resposta recebida: {response}")

# Verificar se servidor confirmou criptografia
if ENABLE_ENCRYPTION:
    if response.get("encryption_enabled", False):
        print(f"[ENCRYPTION] Criptografia confirmada pelo servidor (shift: {CAESAR_SHIFT})")
    else:
        print("[WARNING] Servidor não confirmou criptografia, desabilitando...")
        ENABLE_ENCRYPTION = False

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

# Dividir texto em segmentos de até 4 caracteres
segments = [text_to_send[i:i+PAYLOAD_SIZE] for i in range(0, len(text_to_send), PAYLOAD_SIZE)]
print(f"Segmentos criados: {segments}\n")

# Implementar protocolo baseado no modo de operação
window_size = response["window_size"]  # Tamanho da janela do servidor
operation_mode = response["operation_mode"]  # Modo de operação
sent_packets.clear()  # Limpar pacotes anteriores (variável global)
acknowledged_packets_global.clear()  # Limpar pacotes confirmados (variável global)
packet_send_times.clear()  # Limpar timestamps anteriores
next_seq_to_send = 0                   # Próximo número de sequência a enviar
base_seq = 0                          # Base da janela (primeiro não confirmado)

if operation_mode == "go_back_n":
    print(f"[GBN] Iniciando Go-Back-N com janela de tamanho: {window_size}")
elif operation_mode == "selective_repeat":
    print(f"[SR] Iniciando Selective Repeat com janela de tamanho: {window_size}")
else:
    print(f"[WARNING] Modo desconhecido: {operation_mode}, usando Go-Back-N")
    operation_mode = "go_back_n"

# Mostrar configuração de simulação se houver
if packets_to_drop or packets_to_corrupt:
    print(f"\n[SIMULATION] Simulação de erros ativada:")
    if packets_to_drop:
        print(f"  - Pacotes a perder: {sorted(packets_to_drop)}")
    if packets_to_corrupt:
        print(f"  - Pacotes a corromper: {sorted(packets_to_corrupt)}")
    print()

# Enviar pacotes dentro da janela
while base_seq < len(segments):
    # Enviar pacotes até preencher a janela
    while next_seq_to_send < min(base_seq + window_size, len(segments)):
        segment = segments[next_seq_to_send]
        simulation_stats['total_packets'] += 1
        
        # SIMULAÇÃO: Verificar se deve perder este pacote
        if next_seq_to_send in packets_to_drop:
            print(f"[SIMULATION] ⚠️  PERDA SIMULADA: Pacote {next_seq_to_send} não será enviado")
            simulation_stats['packets_dropped'] += 1
            # Não enviar o pacote, mas armazenar para possível retransmissão
            # Criar o pacote normalmente para poder retransmitir depois
            payload_to_send = caesar_encrypt(segment, CAESAR_SHIFT) if ENABLE_ENCRYPTION else segment
            checksum = calculate_checksum(segment)
            packet = create_data_packet(next_seq_to_send, payload_to_send, checksum)
            if ENABLE_ENCRYPTION:
                packet["encrypted"] = True
            sent_packets[next_seq_to_send] = packet
            start_timer(next_seq_to_send)
            next_seq_to_send += 1
            continue
        
        # Preparar payload (criptografar se necessário)
        if ENABLE_ENCRYPTION:
            payload_to_send = caesar_encrypt(segment, CAESAR_SHIFT)
            print(f"[ENCRYPTION] Payload criptografado para pacote {next_seq_to_send}: '{segment}' -> '{payload_to_send}'")
        else:
            payload_to_send = segment
        
        # Calcular checksum do payload original (antes da criptografia)
        checksum = calculate_checksum(segment)
        original_checksum = checksum
        
        # SIMULAÇÃO: Corromper checksum se necessário
        if next_seq_to_send in packets_to_corrupt:
            checksum = (checksum + 1) % 256  # Corromper checksum
            print(f"[SIMULATION] ⚠️  CORRUPÇÃO SIMULADA: Pacote {next_seq_to_send} com checksum incorreto ({original_checksum} -> {checksum})")
            simulation_stats['packets_corrupted'] += 1
        
        # Criar pacote
        packet = create_data_packet(next_seq_to_send, payload_to_send, checksum)
        
        # Armazenar checksum original para retransmissão (se corrompido, retransmitir com checksum correto)
        if next_seq_to_send in packets_to_corrupt:
            packet['original_checksum'] = original_checksum
        
        # Adicionar flag de criptografia no pacote
        if ENABLE_ENCRYPTION:
            packet["encrypted"] = True
        
        print(f"\n[{get_timestamp()}] [SEND] Enviando pacote {next_seq_to_send}: '{segment}' (checksum: {checksum})")
        send_message(s, packet)
        
        # Armazenar pacote enviado
        sent_packets[next_seq_to_send] = packet
        # Iniciar timer para este pacote
        start_timer(next_seq_to_send)
        
        next_seq_to_send += 1
    
    # Aguardar ACKs até janela estar confirmada ou timeout
    while base_seq < next_seq_to_send:
        # Verificar se algum pacote expirou (timeout síncrono baseado em timestamp)
        current_time = time.time()
        timeout_occurred = False
        unacknowledged_packets = [i for i in range(base_seq, next_seq_to_send) 
                                  if i not in acknowledged_packets_global]
        
        # Verificar se algum pacote já expirou
        for seq in unacknowledged_packets:
            if seq in packet_send_times:
                elapsed = current_time - packet_send_times[seq]
                # Se passou TIMEOUT_DURATION segundos e ainda não foi confirmado
                if elapsed >= TIMEOUT_DURATION:
                    timeout_occurred = True
                    print(f"\n[{get_timestamp()}] [TIMEOUT] Timeout para pacote {seq} após {elapsed:.2f}s (esperado: {TIMEOUT_DURATION}s) - retransmitindo...")
                    
                    if operation_mode == "go_back_n":
                        print(f"[{get_timestamp()}] [GBN] Go-Back-N: Retransmitindo janela a partir de {base_seq}\n")
                        for i in range(base_seq, next_seq_to_send):
                            if i not in acknowledged_packets_global:
                                retransmit_packet(i)
                    else:
                        retransmit_packet(seq)
                    break  # Processar um timeout por vez
        
        if timeout_occurred:
            continue  # Re-avaliar o loop após retransmissão
        
        # Calcular timeout restante para o próximo pacote que pode expirar
        min_timeout = TIMEOUT_DURATION
        earliest_packet = None
        for seq in unacknowledged_packets:
            if seq in packet_send_times:
                elapsed = current_time - packet_send_times[seq]
                remaining = TIMEOUT_DURATION - elapsed
                if remaining > 0 and remaining < min_timeout:
                    min_timeout = remaining
                    earliest_packet = seq
        
        # Se não há pacotes aguardando ou todos já expiraram, aguardar o timeout completo
        if min_timeout >= TIMEOUT_DURATION or earliest_packet is None:
            # Todos os pacotes já expiraram ou não há pacotes - aguardar timeout completo
            socket_timeout = TIMEOUT_DURATION
            print(f"\n[{get_timestamp()}] [TIMER] Aguardando {socket_timeout}s para timeout...")
        else:
            # Aguardar até o próximo timeout possível
            socket_timeout = max(0.1, min_timeout)
            elapsed_for_packet = current_time - packet_send_times[earliest_packet]
            print(f"\n[{get_timestamp()}] [TIMER] Aguardando {socket_timeout:.2f}s até possível timeout do pacote {earliest_packet} (já decorridos {elapsed_for_packet:.2f}s de {TIMEOUT_DURATION}s)...")
        
        # Aguardar resposta com timeout calculado (realmente aguarda o tempo)
        try:
            response = receive_message(s, timeout=socket_timeout)
            ack_seq = response["seq_num"]
            
            if response["type"] == "ack":
                elapsed_time = time.time() - packet_send_times.get(ack_seq, time.time())
                print(f"\n[{get_timestamp()}] [ACK] ACK recebido para pacote {ack_seq} (tempo decorrido: {elapsed_time:.2f}s)")
                # Parar timer do pacote confirmado
                stop_timer(ack_seq)
                # Marcar pacote como confirmado
                acknowledged_packets_global.add(ack_seq)
                
                # Mover janela se base foi confirmada
                while base_seq in acknowledged_packets_global:
                    base_seq += 1
                    print(f"[{get_timestamp()}] [WINDOW] Janela movida. Base agora: {base_seq}\n")
                    
            elif response["type"] == "nack":
                print(f"\n[{get_timestamp()}] [NACK] NACK recebido para pacote {ack_seq}\n")
                
                if operation_mode == "go_back_n":
                    for i in range(base_seq, next_seq_to_send):
                        stop_timer(i)
                    print(f"[{get_timestamp()}] [GBN] Go-Back-N: Retransmitindo janela a partir de {base_seq}\n")
                    for i in range(base_seq, next_seq_to_send):
                        retransmit_packet(i)
                elif operation_mode == "selective_repeat":
                    print(f"[{get_timestamp()}] [SR] Selective Repeat: Retransmitindo apenas pacote {ack_seq}\n")
                    retransmit_packet(ack_seq)
                
        except (TimeoutError, OSError) as e:
            # Timeout ocorreu - continuar loop para verificar timestamps
            error_str = str(e).lower()
            if isinstance(e, TimeoutError) or "timed out" in error_str or "timeout" in error_str:
                # Continue loop to check for expired packets
                if base_seq < next_seq_to_send:
                    continue
                break
            print(f"Conexão encerrada pelo servidor: {e}")
            break
        except (ConnectionError, json.JSONDecodeError) as e:
            print(f"Conexão encerrada pelo servidor: {e}")
            break

print("\n=== TROCA DE MENSAGENS CONCLUÍDA ===")

# Mostrar estatísticas de simulação
if packets_to_drop or packets_to_corrupt:
    print(f"\n[SIMULATION] Estatísticas de simulação:")
    print(f"  - Total de pacotes: {simulation_stats['total_packets']}")
    print(f"  - Pacotes perdidos: {simulation_stats['packets_dropped']}")
    print(f"  - Pacotes corrompidos: {simulation_stats['packets_corrupted']}")

s.close() # Fechar conexão
print("Desconectado")