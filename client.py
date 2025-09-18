import socket
import json

# Cliente simples (apenas handshake
HOST = 'localhost'
PORT = 8080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Cria um socket TCP
s.connect((HOST, PORT)) # Conecta ao servidor

print(f"Conectado ao servidor {HOST}:{PORT}")

# Handshake
print("Iniciando handshake...")

# Enviar dados
handshake_data = {
    "type": "handshake",
    "max_message_size": 50,
    "operation_mode": "go_back_n"
}

print(f"Enviando: {handshake_data}")

json_data = json.dumps(handshake_data) # Converte o dicionário para uma mensagem JSON
message = json_data.encode('utf-8') # Converte a mensagem JSON para bytes

s.send(len(message).to_bytes(4, byteorder='big')) # Envia os 4 bytes que representam o tamanho da mensagem JSON
s.send(message) # Envia a mensagem JSON

# Receber resposta
size_data = s.recv(4) # Lê os 4 bytes que representam o tamanho da mensagem JSON
size = int.from_bytes(size_data, byteorder='big') # Converte os 4 bytes para um inteiro

response_data = b'' # Inicializa a variável que armazenará a mensagem JSON
while len(response_data) < size:
    chunk = s.recv(size - len(response_data)) # Lê o restante da mensagem JSON
    response_data += chunk

response = json.loads(response_data.decode('utf-8')) # Converte os bytes para string e depois para um dicionário
print(f"Resposta recebida: {response}")

print("Handshake concluído!")
s.close()
print("Desconectado")