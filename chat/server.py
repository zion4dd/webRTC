import socket
import threading

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"Сообщение от клиента: {message}", client_socket)
            broadcast(message, client_socket)
        except:
            break

    client_socket.close()

def broadcast(message, client_socket):
    for client in clients:
        if client != client_socket:
            try:
                client.send(message.encode('utf-8'))
            except:
                client.close()
                clients.remove(client)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5555))
server.listen(5)
print("Сервер запущен и ожидает подключения...")

clients = []

while True:
    client_socket, addr = server.accept()
    print(f"Подключен клиент: {addr}")
    clients.append(client_socket)
    thread = threading.Thread(target=handle_client, args=(client_socket,))
    thread.start()
