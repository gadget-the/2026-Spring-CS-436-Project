import sys
import os
import json
from socket import socket, AF_INET, SOCK_DGRAM

CHUNK_SIZE = 1024
SERVER_CLOSE_MESSAGE = "STOP"
SERVER_CLOSE_ACK = "CLOSE_ACK"

class socket_client():
    serverName = None
    serverPort = None
    clientSocket = None

    def __init__(self, givenName='localhost', givenPort=12000):
        self.serverName = givenName
        self.serverPort = givenPort
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)
        self.clientSocket.settimeout(10)

    def send_message(self, message=""):
        self.clientSocket.sendto(message.encode(), (self.serverName, self.serverPort))

    def receive_message(self):
        data, serverAddress = self.clientSocket.recvfrom(65535)
        return data.decode()

    def send_json(self, obj):
        self.send_message(json.dumps(obj))

    def receive_json(self):
        return json.loads(self.receive_message())

    def send_file(self, filepath):
        with open(filepath, "rb") as f:
            data = f.read()
        total = len(data)
        self.send_message(f"FILESTART:{total}") # tell server how many bytes are coming
        ack = self.receive_message()
        if ack != "FILESTART_ACK":
            return False
        offset = 0
        while offset < total:
            chunk = data[offset:offset + CHUNK_SIZE]
            self.clientSocket.sendto(chunk, (self.serverName, self.serverPort))
            self.receive_message() # wait for ack
            offset += CHUNK_SIZE
        self.send_message("FILEEND")
        ack = self.receive_message()
        return ack == "FILEEND_ACK"

    def receive_file(self, save_path):
        header = self.receive_message()
        if not header.startswith("FILESTART:"):
            return False
        total = int(header.split(":")[1]) 
        self.send_message("FILESTART_ACK")
        received = b""
        while len(received) < total:
            chunk, _ = self.clientSocket.recvfrom(CHUNK_SIZE + 64)
            received += chunk
            self.send_message("CHUNK_ACK")
        end_marker = self.receive_message()
        if end_marker == "FILEEND":
            with open(save_path, "wb") as f:
                f.write(received)
            self.send_message("FILEEND_ACK")
            return True
        return False

    def stop(self):
        self.clientSocket.close()

if __name__ == "__main__":
    client1 = socket_client()
    message = input('Input lowercase sentence:')
    client1.send_message(message)
    client1.stop()