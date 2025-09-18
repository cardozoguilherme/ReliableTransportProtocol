import socket
import json

# Servidor (apenas handshake)
HOST = 'localhost'
PORT = 8080

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Cria um socket TCP
socket.bind((HOST, PORT)) # Associa o socket a um endereço e porta
socket.listen(1) # Inicia a escuta por conexões

print(f"Servidor iniciado em {HOST}:{PORT}")
print("Aguardando conexões...")

while True:
    client_socket, client_address = socket.accept() # Aceita uma conexão
    print(f"Conexão estabelecida com {client_address}") 
    
    # Handshake
    print("Iniciando handshake...")
    
    # Recebe dados do cliente
    size_data = client_socket.recv(4) # Lê os 4 bytes que representam o tamanho da mensagem JSON
    size = int.from_bytes(size_data, byteorder='big') # Converte os 4 bytes para um inteiro
    
    message_data = b'' # Inicializa a variável que armazenará a mensagem JSON
    while len(message_data) < size:
        chunk = client_socket.recv(size - len(message_data)) # Lê o restante da mensagem JSON
        message_data += chunk
    
    handshake_data = json.loads(message_data.decode('utf-8')) # Converte os bytes para string e depois para um dicionário
    print(f"Dados recebidos: {handshake_data}")
    
    # Envia resposta
    response = {
        "type": "handshake_ack",
        "max_message_size": handshake_data["max_message_size"],
        "window_size": 5,
        "operation_mode": handshake_data["operation_mode"],
        "status": "success"
    }
    
    response_json = json.dumps(response) # Converte o dicionário para uma mensagem JSON
    response_bytes = response_json.encode('utf-8') # Converte a mensagem JSON para bytes
    
    client_socket.send(len(response_bytes).to_bytes(4, byteorder='big')) # Envia os 4 bytes que representam o tamanho da mensagem JSON
    client_socket.send(response_bytes) # Envia a mensagem JSON
    
    print(f"Handshake concluído:")
    print(f"  - Tamanho máximo: {handshake_data['max_message_size']}")
    print(f"  - Modo: {handshake_data['operation_mode']}")
    
    client_socket.close() # Fecha a conexão
    print(f"Conexão com {client_address} encerrada")