import socket
import json
import argparse
import base64
from cryptography.fernet import Fernet

# Servidor com troca de mensagens

# ===== CONFIGURAÇÕES DO SERVIDOR (via CLI) =====
parser = argparse.ArgumentParser(description='Servidor do Protocolo de Transporte Confiável')
parser.add_argument('--host', type=str, default='localhost', help='Endereço do servidor (padrão: localhost)')
parser.add_argument('--port', type=int, default=8080, help='Porta do servidor (padrão: 8080)')
parser.add_argument('--window-size', type=int, default=5, help='Tamanho da janela (padrão: 5)')

args = parser.parse_args()

HOST = args.host
PORT = args.port
WINDOW_SIZE = args.window_size

def send_message(socket, message):
    """Envia uma mensagem com framing"""
    json_data = json.dumps(message) # Converte dicionário para JSON
    message_bytes = json_data.encode('utf-8') # Converte a string para bytes
    socket.send(len(message_bytes).to_bytes(4, byteorder='big')) # Envia tamanho primeiro (4 bytes)
    socket.send(message_bytes) # Envia a mensagem

def receive_message(socket):
    """Recebe uma mensagem com framing"""
    size_data = socket.recv(4) # Recebe os 4 bytes do tamanho
    
    # Verificar se a conexão foi fechada
    if not size_data or len(size_data) == 0:
        raise ConnectionError("Conexão fechada pelo cliente")
    
    # Verificar se recebemos os 4 bytes completos
    if len(size_data) < 4:
        raise ConnectionError("Conexão fechada antes de receber tamanho completo")
    
    size = int.from_bytes(size_data, byteorder='big') # Converte para número
    
    # Verificar se o tamanho é válido
    if size <= 0:
        raise ValueError("Tamanho de mensagem inválido")
    
    message_data = b'' # Buffer para a mensagem (string de bytes)
    while len(message_data) < size: # Recebe até completar o tamanho
        chunk = socket.recv(size - len(message_data))
        if not chunk:  # Conexão fechada durante recebimento
            raise ConnectionError("Conexão fechada durante recebimento de dados")
        message_data += chunk
    
    # Verificar se recebemos dados válidos
    if not message_data:
        raise ValueError("Mensagem vazia recebida")
    
    return json.loads(message_data.decode('utf-8')) # Converte de volta para dicionário

def decrypt_payload(encrypted_payload, key):
    """Descriptografa o payload usando a chave fornecida"""
    fernet = Fernet(key)
    # Decodificar de base64
    encrypted_bytes = base64.b64decode(encrypted_payload.encode('utf-8'))
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode('utf-8')

def calculate_checksum(data):
    """Calcula soma de verificação simples"""
    return sum(ord(c) for c in data) % 256 # Soma valores ASCII e pega resto da divisão por 256

def verify_checksum(payload, received_checksum):
    """Verifica se a soma de verificação está correta"""
    calculated_checksum = calculate_checksum(payload) # Calcula checksum do payload
    return calculated_checksum == received_checksum # Compara com o recebido

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

# Configurar servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket TCP
server_socket.bind((HOST, PORT)) # Associar ao endereço e porta
server_socket.listen(1) # Aguardar conexões (1 cliente por vez)

print(f"Servidor iniciado em {HOST}:{PORT}")
print("Aguardando conexões...")

while True:
    # Aguardar conexão de cliente
    client_socket, client_address = server_socket.accept()
    print(f"Conexão estabelecida com {client_address}") 
    
    # Handshake - negociação inicial
    print("Iniciando handshake...")
    
    handshake_data = receive_message(client_socket) # Receber handshake do cliente
    print(f"Dados recebidos: {handshake_data}")
    
    # Verificar se cliente solicitou criptografia
    encryption_enabled = handshake_data.get("encryption_enabled", False)
    encryption_key = None
    
    if encryption_enabled:
        # Receber chave de criptografia do cliente
        if "encryption_key" in handshake_data:
            encryption_key_b64 = handshake_data["encryption_key"]
            encryption_key = base64.b64decode(encryption_key_b64.encode('utf-8'))
            print("[ENCRYPTION] Chave de criptografia recebida e configurada")
        else:
            print("[WARNING] Criptografia solicitada mas chave não fornecida")
            encryption_enabled = False
    
    # Enviar resposta do handshake
    response = {
        "type": "handshake_ack",                                # Confirmação do handshake
        "max_message_size": handshake_data["max_message_size"], # Confirmar tamanho
        "window_size": WINDOW_SIZE,                             # Tamanho da janela
        "operation_mode": handshake_data["operation_mode"],     # Confirmar modo
        "encryption_enabled": encryption_enabled,               # Confirmar criptografia
        "status": "success"                                     # Status de sucesso
    }
    
    send_message(client_socket, response) # Enviar confirmação (handshake_ack)
    
    print(f"Handshake concluído:")
    print(f"  - Tamanho máximo: {handshake_data['max_message_size']}")
    print(f"  - Modo: {handshake_data['operation_mode']}")
    if encryption_enabled:
        print(f"  - Criptografia: Habilitada")
    
    # Troca de mensagens - recebimento dos dados
    print("\n=== INICIANDO TROCA DE MENSAGENS ===")
    
    received_segments = [] # Lista para armazenar segmentos recebidos
    expected_seq = 0       # Próximo número de sequência esperado
    
    # Variáveis para Selective Repeat
    operation_mode = handshake_data.get("operation_mode", "go_back_n")
    buffer = {}  # Buffer para armazenar pacotes fora de ordem
    
    if operation_mode == "selective_repeat":
        print(f"[SR] Iniciando Selective Repeat com janela de tamanho: {WINDOW_SIZE}")
        print(f"[BUFFER] Buffer de recebimento: {WINDOW_SIZE * 2} pacotes")
    else:
        print(f"[GBN] Iniciando Go-Back-N com janela de tamanho: {WINDOW_SIZE}")
    
    try:
        while True:
            # Receber pacote de dados do cliente
            try:
                packet = receive_message(client_socket)
            except (ConnectionError, ValueError) as e:
                # Conexão fechada pelo cliente ou dados inválidos
                print(f"[INFO] Cliente encerrou a conexão: {e}")
                break
            except json.JSONDecodeError as e:
                # Erro ao decodificar JSON (conexão pode ter sido fechada)
                print(f"[INFO] Erro ao decodificar mensagem (conexão pode ter sido fechada): {e}")
                break
            
            print(f"Pacote recebido: {packet}")
            
            if packet["type"] == "data": # Se for pacote de dados
                seq_num = packet["seq_num"]   # Número de sequência
                payload_encrypted = packet["payload"]   # Dados (pode estar criptografado)
                checksum = packet["checksum"] # Soma de verificação
                is_encrypted = packet.get("encrypted", False)  # Verificar se está criptografado
                
                # Descriptografar payload se necessário
                payload = payload_encrypted
                if is_encrypted and encryption_key:
                    try:
                        payload = decrypt_payload(payload_encrypted, encryption_key)
                        print(f"[ENCRYPTION] Payload descriptografado para pacote {seq_num}")
                    except Exception as e:
                        print(f"[ERROR] Falha ao descriptografar pacote {seq_num}: {e}")
                        payload = payload_encrypted  # Usar payload original em caso de erro
                
                # Verificar se a soma de verificação está correta
                # O checksum é calculado sobre o payload original (antes da criptografia)
                is_valid = verify_checksum(payload, checksum)
                if is_valid:
                    print(f"[OK] Pacote {seq_num} válido: '{payload}' (checksum: {checksum})")
                    
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
                        else:
                            print(f"[WARNING] Pacote {seq_num} fora de ordem (esperado: {expected_seq}) - ignorando")
                            # Go-Back-N: NÃO enviar ACK para pacotes fora de ordem
                    
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
                        
                        # Mostrar estado do buffer
                        if buffer:
                            print(f"[BUFFER] Buffer atual: {list(buffer.keys())}")
                        else:
                            print(f"[BUFFER] Buffer vazio")
                else:
                    print(f"[ERROR] Pacote {seq_num} com erro de checksum")
                    
                    # Enviar NACK para pacote com erro
                    nack = create_nack_packet(seq_num)
                    send_message(client_socket, nack)
                    print(f"[NACK] NACK enviado para pacote {seq_num}")
                
                # Mostrar informações do pacote
                print(f"Metadados do pacote {seq_num}:")
                print(f"  - Payload: '{payload}'")
                print(f"  - Checksum: {checksum}")
                print(f"  - Número de sequência: {seq_num}")
                print(f"  - Status: {'Válido' if is_valid else 'Inválido'}")
                print()
                
    except Exception as e:
        # Erros inesperados (erros de conexão já tratados no loop interno)
        print(f"[ERROR] Erro inesperado na comunicação: {e}")
    
    # Reconstruir mensagem completa juntando todos os segmentos
    if received_segments:
        complete_message = ''.join(received_segments) # Juntar segmentos
        print(f"\n=== MENSAGEM COMPLETA RECEBIDA ===")
        print(f"Texto: {complete_message}")
        print(f"Total de segmentos: {len(received_segments)}")
        print(f"Tamanho total: {len(complete_message)} caracteres")
        
    print("\n=== TROCA DE MENSAGENS CONCLUÍDA ===")
    client_socket.close() # Fechar conexão com cliente
    print(f"Conexão com {client_address} encerrada")