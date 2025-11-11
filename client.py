import socket
import json
import time
import threading
import argparse
import base64
from cryptography.fernet import Fernet

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
                    help='Ativar criptografia simétrica para payloads')
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
        # socket.timeout é uma subclasse de OSError em Python 3.3+
        # Verificar se é um timeout
        if "timed out" in str(e).lower() or "timeout" in str(e).lower():
            raise TimeoutError("Timeout ao receber mensagem")
        raise  # Re-raise outros erros

def generate_encryption_key():
    """Gera uma chave de criptografia simétrica usando Fernet"""
    return Fernet.generate_key()

def encrypt_payload(payload, key):
    """Criptografa o payload usando a chave fornecida"""
    fernet = Fernet(key)
    encrypted = fernet.encrypt(payload.encode('utf-8'))
    # Codificar em base64 para transmissão via JSON
    return base64.b64encode(encrypted).decode('utf-8')

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

# Variáveis globais para timer e protocolo
timers = {}  # Dicionário para armazenar timers ativos
sent_packets = {}  # Armazenar pacotes enviados (acessível por timers)
acknowledged_packets_global = set()  # Pacotes confirmados (acessível por timers)
retransmission_lock = threading.Lock()  # Lock para evitar retransmissões concorrentes
protocol_state = {
    'operation_mode': 'go_back_n',
    'base_seq': 0,
    'next_seq_to_send': 0,
    'window_size': 5
}

def start_timer(seq_num, packet, socket_conn):
    """Inicia timer para um pacote específico"""
    def timeout_handler():
        # Verificar se o pacote já foi confirmado ou adquirir lock
        if seq_num in acknowledged_packets_global or not retransmission_lock.acquire(blocking=False):
            return
        
        try:
            # Verificar novamente após adquirir o lock
            if seq_num in acknowledged_packets_global:
                return
            
            print(f"[TIMEOUT] Timeout para pacote {seq_num} - retransmitindo...")
            op_mode = protocol_state['operation_mode']
            base = protocol_state['base_seq']
            next_seq = protocol_state['next_seq_to_send']
            
            if op_mode == "go_back_n":
                # Go-Back-N: Retransmitir toda a janela a partir do base
                print(f"[GBN] Go-Back-N: Retransmitindo janela a partir de {base}")
                for i in range(base, next_seq):
                    if i not in acknowledged_packets_global and i in sent_packets:
                        retry_packet = sent_packets[i].copy()
                        if 'original_checksum' in retry_packet:
                            retry_packet['checksum'] = retry_packet['original_checksum']
                        send_message(socket_conn, retry_packet)
                        print(f"Pacote {i} retransmitido por timeout (Go-Back-N)")
                        start_timer(i, sent_packets[i], socket_conn)
            else:
                # Selective Repeat: Retransmitir apenas o pacote específico
                if seq_num in sent_packets and seq_num not in acknowledged_packets_global:
                    retry_packet = sent_packets[seq_num].copy()
                    if 'original_checksum' in retry_packet:
                        retry_packet['checksum'] = retry_packet['original_checksum']
                    send_message(socket_conn, retry_packet)
                    print(f"Pacote {seq_num} retransmitido por timeout")
                    start_timer(seq_num, sent_packets[seq_num], socket_conn)
        except (ConnectionError, OSError) as e:
            print(f"[ERROR] Erro ao retransmitir pacote {seq_num}: {e}")
        finally:
            retransmission_lock.release()
    
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
s.settimeout(0.5)  # Timeout de 0.5s para permitir verificação de timers
s.connect((HOST, PORT)) # Conectar ao servidor

print(f"Conectado ao servidor {HOST}:{PORT}")

# Handshake - negociação inicial
print("Iniciando handshake...")

# Gerar chave de criptografia se habilitado
encryption_key = None
if ENABLE_ENCRYPTION:
    encryption_key = generate_encryption_key()
    print(f"[ENCRYPTION] Chave de criptografia gerada")

handshake_data = {
    "type": "handshake",           # Tipo da mensagem
    "max_message_size": MAX_MESSAGE_SIZE,      # Tamanho máximo da mensagem
    "operation_mode": OPERATION_MODE,  # Modo de operação (go_back_n ou selective_repeat)
    "encryption_enabled": ENABLE_ENCRYPTION  # Flag de criptografia
}

# Adicionar chave de criptografia se habilitada
if ENABLE_ENCRYPTION and encryption_key:
    # Codificar chave em base64 para transmissão via JSON
    handshake_data["encryption_key"] = base64.b64encode(encryption_key).decode('utf-8')

print(f"Enviando: {handshake_data}")
send_message(s, handshake_data) # Enviar handshake

# Handshake não precisa de timeout curto, usar timeout maior
s.settimeout(10.0)  # Timeout maior para handshake
response = receive_message(s) # Receber confirmação (ack do servidor)
s.settimeout(0.5)  # Voltar ao timeout curto para loop principal
print(f"Resposta recebida: {response}")

# Verificar se servidor confirmou criptografia
if ENABLE_ENCRYPTION:
    if response.get("encryption_enabled", False):
        print("[ENCRYPTION] Criptografia confirmada pelo servidor")
    else:
        print("[WARNING] Servidor não confirmou criptografia, desabilitando...")
        ENABLE_ENCRYPTION = False
        encryption_key = None

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
sent_packets.clear()  # Limpar pacotes anteriores (variável global)
acknowledged_packets_global.clear()  # Limpar pacotes confirmados (variável global)
next_seq_to_send = 0                   # Próximo número de sequência a enviar
base_seq = 0                          # Base da janela (primeiro não confirmado)

# Atualizar estado global para timers
protocol_state['operation_mode'] = operation_mode
protocol_state['window_size'] = window_size

if operation_mode == "go_back_n":
    print(f"[GBN] Iniciando Go-Back-N com janela de tamanho: {window_size}")
elif operation_mode == "selective_repeat":
    print(f"[SR] Iniciando Selective Repeat com janela de tamanho: {window_size}")
else:
    print(f"[WARNING] Modo desconhecido: {operation_mode}, usando Go-Back-N")
    operation_mode = "go_back_n"
    protocol_state['operation_mode'] = operation_mode

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
    # Atualizar estado global
    protocol_state['base_seq'] = base_seq
    protocol_state['next_seq_to_send'] = next_seq_to_send
    
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
            payload_to_send = segment
            if ENABLE_ENCRYPTION and encryption_key:
                payload_to_send = encrypt_payload(segment, encryption_key)
            checksum = calculate_checksum(segment)
            packet = create_data_packet(next_seq_to_send, payload_to_send, checksum)
            if ENABLE_ENCRYPTION:
                packet["encrypted"] = True
            sent_packets[next_seq_to_send] = packet
            # Iniciar timer mesmo sem enviar (para detectar perda)
            start_timer(next_seq_to_send, packet, s)
            next_seq_to_send += 1
            continue  # Pular o envio deste pacote
        
        # Criptografar payload se criptografia estiver habilitada
        payload_to_send = segment
        if ENABLE_ENCRYPTION and encryption_key:
            payload_to_send = encrypt_payload(segment, encryption_key)
            print(f"[ENCRYPTION] Payload criptografado para pacote {next_seq_to_send}")
        
        # Calcular checksum do payload original (antes da criptografia)
        checksum = calculate_checksum(segment)
        
        # SIMULAÇÃO: Verificar se deve corromper o checksum deste pacote
        original_checksum = checksum
        if next_seq_to_send in packets_to_corrupt:
            checksum = (checksum + 1) % 256  # Corromper checksum
            print(f"[SIMULATION] ⚠️  CORRUPÇÃO SIMULADA: Pacote {next_seq_to_send} com checksum incorreto ({original_checksum} -> {checksum})")
            simulation_stats['packets_corrupted'] += 1
        
        packet = create_data_packet(next_seq_to_send, payload_to_send, checksum)
        
        # Armazenar checksum original para retransmissão (se corrompido, retransmitir com checksum correto)
        if next_seq_to_send in packets_to_corrupt:
            packet['original_checksum'] = original_checksum
        
        # Adicionar flag de criptografia no pacote
        if ENABLE_ENCRYPTION:
            packet["encrypted"] = True
        
        print(f"[SEND] Enviando pacote {next_seq_to_send}: '{segment}' (checksum: {checksum})")
        send_message(s, packet)
        
        # Armazenar pacote enviado
        sent_packets[next_seq_to_send] = packet
        
        # Iniciar timer para este pacote
        start_timer(next_seq_to_send, packet, s)
        
        next_seq_to_send += 1
    
    # Aguardar ACKs até janela estar confirmada ou timeout
    # Atualizar estado global antes de entrar no loop de ACKs
    protocol_state['base_seq'] = base_seq
    protocol_state['next_seq_to_send'] = next_seq_to_send
    
    while base_seq < next_seq_to_send:
        try:
            # Tentar receber mensagem com timeout curto para não bloquear indefinidamente
            response = receive_message(s, timeout=0.5)
            ack_seq = response["seq_num"]
            
            if response["type"] == "ack":
                print(f"[ACK] ACK recebido para pacote {ack_seq}")
                # Parar timer do pacote confirmado
                stop_timer(ack_seq)
                # Marcar pacote como confirmado
                acknowledged_packets_global.add(ack_seq)
                
                # Mover janela se base foi confirmada
                while base_seq in acknowledged_packets_global:
                    base_seq += 1
                    protocol_state['base_seq'] = base_seq  # Atualizar estado global
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
                            packet = sent_packets[i].copy()  # Copiar para não modificar o original
                            # Se o pacote foi corrompido, usar checksum correto na retransmissão
                            if 'original_checksum' in packet:
                                packet['checksum'] = packet['original_checksum']
                                print(f"[RETRY] Retransmitindo pacote {i} com checksum corrigido")
                            else:
                                print(f"[RETRY] Retransmitindo pacote {i}: '{packet['payload']}'")
                            send_message(s, packet)
                            # Reiniciar timer para retransmissão
                            start_timer(i, packet, s)
                
                elif operation_mode == "selective_repeat":
                    # Selective Repeat: Retransmitir apenas o pacote específico
                    print(f"[SR] Selective Repeat: Retransmitindo apenas pacote {ack_seq}")
                    if ack_seq in sent_packets:
                        packet = sent_packets[ack_seq].copy()  # Copiar para não modificar o original
                        # Se o pacote foi corrompido, usar checksum correto na retransmissão
                        if 'original_checksum' in packet:
                            packet['checksum'] = packet['original_checksum']
                            print(f"[RETRY] Retransmitindo pacote {ack_seq} com checksum corrigido")
                        else:
                            print(f"[RETRY] Retransmitindo pacote {ack_seq}: '{packet['payload']}'")
                        send_message(s, packet)
                        # Reiniciar timer apenas para este pacote
                        start_timer(ack_seq, packet, s)
                
        except (TimeoutError, OSError) as e:
            # Tratar timeouts: continuar esperando se ainda há pacotes não confirmados
            error_str = str(e).lower()
            if isinstance(e, TimeoutError) or "timed out" in error_str or "timeout" in error_str:
                if base_seq < next_seq_to_send:
                    continue
                break
            # Outro erro (conexão fechada, etc)
            print(f"Conexão encerrada pelo servidor: {e}")
            break
        except (ConnectionError, json.JSONDecodeError) as e:
            print(f"Conexão encerrada pelo servidor: {e}")
            break
    
    # Pequena pausa
    time.sleep(0.1)

print("\n=== TROCA DE MENSAGENS CONCLUÍDA ===")

# Mostrar estatísticas de simulação
if packets_to_drop or packets_to_corrupt:
    print(f"\n[SIMULATION] Estatísticas de simulação:")
    print(f"  - Total de pacotes: {simulation_stats['total_packets']}")
    print(f"  - Pacotes perdidos: {simulation_stats['packets_dropped']}")
    print(f"  - Pacotes corrompidos: {simulation_stats['packets_corrupted']}")

stop_all_timers()  # Parar todos os timers ativos
s.close() # Fechar conexão
print("Desconectado")