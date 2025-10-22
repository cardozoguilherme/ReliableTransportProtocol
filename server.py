import socket
import json

# Servidor com troca de mensagens
HOST = 'localhost'  # Endereço do servidor
PORT = 8080        # Porta do servidor

def send_message(socket, message):
    """Envia uma mensagem com framing"""
    json_data = json.dumps(message) # Converte dicionário para JSON
    message_bytes = json_data.encode('utf-8') # Converte a string para bytes
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
    
    # Enviar resposta do handshake
    response = {
        "type": "handshake_ack",                                # Confirmação do handshake
        "max_message_size": handshake_data["max_message_size"], # Confirmar tamanho
        "window_size": 5,                                       # Tamanho da janela
        "operation_mode": handshake_data["operation_mode"],     # Confirmar modo
        "status": "success"                                     # Status de sucesso
    }
    
    send_message(client_socket, response) # Enviar confirmação (handshake_ack)
    
    print(f"Handshake concluído:")
    print(f"  - Tamanho máximo: {handshake_data['max_message_size']}")
    print(f"  - Modo: {handshake_data['operation_mode']}")
    
    # Troca de mensagens - recebimento dos dados
    print("\n=== INICIANDO TROCA DE MENSAGENS ===")
    
    received_segments = [] # Lista para armazenar segmentos recebidos
    expected_seq = 0       # Próximo número de sequência esperado
    
    try:
        while True:
            # Receber pacote de dados do cliente
            packet = receive_message(client_socket)
            print(f"Pacote recebido: {packet}")
            
            if packet["type"] == "data": # Se for pacote de dados
                seq_num = packet["seq_num"]   # Número de sequência
                payload = packet["payload"]   # Dados (4 caracteres)
                checksum = packet["checksum"] # Soma de verificação
                
                # Verificar se a soma de verificação está correta
                if verify_checksum(payload, checksum):
                    print(f"✓ Pacote {seq_num} válido: '{payload}' (checksum: {checksum})")
                    
                    # Armazenar segmento se for o próximo esperado
                    if seq_num == expected_seq:
                        received_segments.append(payload)  # Adicionar à lista
                        expected_seq += 1  # Próximo número esperado
                        print(f"✓ Segmento {seq_num} adicionado à mensagem")
                    else:
                        print(f"⚠ Pacote {seq_num} fora de ordem (esperado: {expected_seq})")
                else:
                    print(f"✗ Pacote {seq_num} com erro de checksum")
                
                # Enviar confirmação (ACK) para o cliente
                ack = create_ack_packet(seq_num)
                send_message(client_socket, ack)
                print(f"ACK enviado para pacote {seq_num}")
                
                # Mostrar informações do pacote
                print(f"Metadados do pacote {seq_num}:")
                print(f"  - Payload: '{payload}'")
                print(f"  - Checksum: {checksum}")
                print(f"  - Número de sequência: {seq_num}")
                print(f"  - Status: {'Válido' if verify_checksum(payload, checksum) else 'Inválido'}")
                print()
                
    except Exception as e:
        print(f"Erro na comunicação: {e}")
    
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