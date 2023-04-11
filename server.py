import socket
from _thread import *
import logging
import colorlog
import os
from dotenv import load_dotenv


def client_handler(connection):
    connection.send(
        str.encode(
            'You are now connected to the replay server... Type BYE to stop'))
    client_info = connection.getpeername()
    while True:
        try:
            data = connection.recv(2048)
            message = data.decode('utf-8')
            if message == 'BYE':
                break
            else:
                logger.debug(f'Client: {message}')
            reply = f'Server: {message}'
            connection.sendall(str.encode(reply))
        except:
            logger.error(f"Client disconnected {client_info}")
            break
    connection.close()


def accept_connections(ServerSocket):
    client, address = ServerSocket.accept()
    logger.info('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(client_handler, (client, ))


# ______________________________________________________________________________
#                                   Main
# ______________________________________________________________________________

if __name__ == '__main__':
    load_dotenv()

    # Définir l'adresse IP et le port du serveur
    host = os.getenv('MIRADOR_IP')  # Adresse IP locale
    port = os.getenv('MIRADOR_PORT')  # Port arbitraire

    # configure logger
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%')
    handler.setFormatter(formatter)
    logger = colorlog.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    ServerSocket = socket.socket()
    try:
        ServerSocket.bind((host, port))
    except socket.error as e:
        print(str(e))
    logger.info(f'Server is listing on the port {port}...')
    ServerSocket.listen()

    while True:
        accept_connections(ServerSocket)
