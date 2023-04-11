import socket
import os
import sys
import time
import signal
from cakeDetector import cakeDetector as cd
import cv2
import logging
import colorlog
import json
from picamera2 import Picamera2
from dotenv import load_dotenv


class PiCam:
    mirador_ip: str
    mirador_port: str
    tcp_socket: socket
    cakeDetector: cd.CakeDetector

    def __init__(self):
        self.mirador_ip = os.getenv("MIRADOR_IP")
        self.mirador_port = os.getenv("MIRADOR_PORT")
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cakeDetector = cd.CakeDetector()

    def calibrate_camera(self, camera):
        try:
            camera.start()
        except Exception as e:
            logger.error(f"{e}")
            return

        try:
            # ret, frame = cap.read()
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.cakeDetector.initDetector(frame)
            camera.close()
            logger.info("Cake Detector Initialized successfully")
        except Exception as e:
            logger.error(f"Unable to init detector : {e}")

    def connect_to_server(self, host, port):
        """Connecter le socket au serveur"""
        try:
            self.tcp_socket.connect((host, port))
        except socket.error as e:
            logger.error(f"Erreur de connexion à {host} sur le port {port} : {e}")
            sys.exit()

    def receive_data(self):
        """Recevoir des données du serveur"""
        data = self.tcp_socket.recv(1024).decode()
        logger.info(f"Données reçues du serveur : {data}")

    def send_data(self, message):
        """Envoyer des données au serveur"""
        self.tcp_socket.send(message.encode())
        logger.debug("Données envoyées au serveur")

    def close_connection(self):
        self.tcp_socket.close()
        logger.info("Connection closed")

    def watch(self, frame):
        # return self.cakeDetector.detectCakes()
        return [
            {"cake": "1"},
            {"cake": "2"},
        ]


def main(args):
    load_dotenv()
    host = os.getenv("MIRADOR_IP")  # Adresse IP locale
    port = int(os.getenv("MIRADOR_PORT"))  # Port arbitraire

    # Configuration de la camera
    camera = Picamera2()
    config = camera.create_preview_configuration()
    camera.configure(config)
    try:
        camera.start()
    except Exception as e:
        logger.critical(f"Cannot open camera {e}")
        return
    
    # Lancement du client
    picam = PiCam()
    picam.connect_to_server(host, port)
    picam.receive_data()
    frequency = 1  # envoi du message toutes les secondes
    signal.signal(signal.SIGTERM, lambda signum, frame: picam.close_connection())
    picam.calibrate_camera(camera)

    # Observe le plateau de jeu
    while True:
        try:
            frame = camera.capture_array()
            #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            data = picam.watch(frame)
            payload = json.dumps(data)
        except Exception as e:
            logger.error(f"Unable to watch : {e}")
            continue
        time.sleep(frequency)

        # Envoie les données au serveur
        try:
            picam.send_data(payload)
        except KeyboardInterrupt:
            camera.close()
            picam.close_connection()
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
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )
    handler.setFormatter(formatter)
    logger = colorlog.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    main(sys.argv)
