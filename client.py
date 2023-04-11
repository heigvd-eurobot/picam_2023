import socket
import os
import sys
import time
import signal
from cakeDetector import cakeDetector as cd
import cv2
import logging
import colorlog


class PiCam:
    mirador_ip: str
    mirador_port: str
    tcp_socket: socket
    cakeDetector: cd.CakeDetector

    def __init__(self):
        self.mirador_ip = os.getenv('MIRADOR_IP')
        self.mirador_port = os.getenv('MIRADOR_PORT')
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cakeDetector = cd.CakeDetector()
        self.calibrate_camera()

    def calibrate_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Cannot open camera")
            return
        try:
            ret, frame = cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.cakeDetector.initDetector(frame)
            logger.info("Cake Detector Initialized successfully")
        except Exception as e:
            logger.error(f"Unable to init detector : {e}")

    def connect_to_server(self, host, port):
        '''Connecter le socket au serveur'''
        try:
            self.tcp_socket.connect((host, port))
        except socket.error as e:
            logger.error(f"Erreur de connexion : {e}")
            sys.exit()

    def receive_data(self):
        '''Recevoir des données du serveur'''
        data = self.tcp_socket.recv(1024).decode()
        logger.info(f"Données reçues du serveur : {data}")

    def send_data(self, message):
        '''Envoyer des données au serveur'''
        self.tcp_socket.send(message.encode())
        logger.debug("Données envoyées au serveur")

    def close_connection(self, cap):
        if cap:
            cap.release()
        self.tcp_socket.close()
        logger.info("Connection closed")

    def watch(self):
        return self.cakeDetector.detectCakes()


def main(args):

    # Définir l'adresse IP et le port du serveur
    host = "127.0.0.1"  # Adresse IP locale
    port = 8080  # Port arbitraire

    picam = PiCam()
    picam.connect_to_server(host, port)
    picam.receive_data()

    frequency = 1  # envoi du message toutes les secondes

    signal.signal(signal.SIGTERM,
                  lambda signum, frame: picam.close_connection())

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.critical("Cannot open camera")
        return

    while True:
        # Observe le plateau de jeu
        try:
            ret, frame = cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            #data = picam.watch(frame)
            data = "COCO"
        except Exception as e:
            logger.error(f"Unable to watch : {e}")
            continue
        time.sleep(frequency)

        # Envoie les données au serveur
        try:
            picam.send_data(data)
        except KeyboardInterrupt:
            picam.close_connection(cap)
            break

# ______________________________________________________________________________
#                                   Main
# ______________________________________________________________________________

if __name__ == "__main__":
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
    main(sys.argv)
