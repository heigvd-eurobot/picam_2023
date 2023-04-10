import socket
import os
import sys
import time 
import signal
from cakeDetector import cakeDetector as cd
import cv2

class PiCam:
    mirador_ip: str
    mirador_port: str
    tcp_socket: socket
    cakeDetector: cd.CakeDetector
    videoStream: any

    def __init__(self):
        self.mirador_ip = os.getenv('MIRADOR_IP')
        self.mirador_port = os.getenv('MIRADOR_PORT')
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cakeDetector = cd.CakeDetector()
        self.videoStream = cv2.VideoCapture(0)
        self.calibrate_camera()


    def calibrate_camera(self):
        try:
            # Read a frame from the video stream
            ret, frame = self.videoStream.read()
            self.cakeDetector.initDetector(frame)
            print("GOTCHA")
        except Exception as e:
            print("Unable to init detector",e)

    def connect_to_server(self, host, port):
        '''Connecter le socket au serveur'''
        try:
            self.tcp_socket.connect((host, port))
        except socket.error as e:
            print("Erreur de connexion : ", e)
            sys.exit()

    def receive_data(self):
        '''Recevoir des données du serveur'''
        data = self.tcp_socket.recv(1024).decode()
        print("Données reçues du serveur : ", data)

    def send_data(self, message):
        '''Envoyer des données au serveur'''
        self.tcp_socket.send(message.encode())

    def close_connection(self):
        self.tcp_socket.close()

def main(args):

    # Définir l'adresse IP et le port du serveur
    host = "127.0.0.1"  # Adresse IP locale
    port = 8080  # Port arbitraire

    picam = PiCam()
    picam.connect_to_server(host, port)
    picam.receive_data()


    # Envoyer des données au serveur à une fréquence définie
    message = "Hello server, this is client !"
    frequency = 1  # envoi du message toutes les secondes

    def send_message():
        picam.send_data(message)

    signal.signal(signal.SIGTERM, lambda signum, frame: picam.close_connection())

    while True:
        try:
            send_message()
            time.sleep(frequency)
        except KeyboardInterrupt:
            picam.close_connection()
            break


if __name__ == "__main__":
    main(sys.argv)