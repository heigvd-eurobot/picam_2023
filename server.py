import socket
from _thread import *

host = '127.0.0.1'
port = 8080

def client_handler(connection):
    connection.send(str.encode('You are now connected to the replay server... Type BYE to stop'))
    client_info = connection.getpeername()
    while True:
        try:
            data = connection.recv(2048)
            message = data.decode('utf-8')
            if message == 'BYE':
                break
            else:
                print(f'Client: {message}')
            reply = f'Server: {message}'
            connection.sendall(str.encode(reply))
        except:
            print(f"Client disconnected {client_info}")
            break
    connection.close()

def accept_connections(ServerSocket):
    client, address = ServerSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(client_handler, (client, ))

# ______________________________________________________________________________
#                                   Main
# ______________________________________________________________________________

if __name__ == '__main__':
    ServerSocket = socket.socket()
    try:
        ServerSocket.bind((host, port))
    except socket.error as e:
        print(str(e))
    print(f'Server is listing on the port {port}...')
    ServerSocket.listen()

    while True:
        accept_connections(ServerSocket)
