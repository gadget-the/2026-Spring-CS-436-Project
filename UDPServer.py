# from socket import *
from socket import socket, AF_INET, SOCK_DGRAM

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

def start_server():
    SERVER_CLOSE_MESSAGE = "STOP"
    SERVER_CLOSE_ACK = "CLOSE_ACK"
    print ('The server is ready to receive')
    
    while True:
        message, clientAddress = serverSocket.recvfrom(2048)
        decoded_message = message.decode()

        if decoded_message == SERVER_CLOSE_MESSAGE:
            serverSocket.sendto(SERVER_CLOSE_ACK.encode(), clientAddress)
            print ('Stopping Server...')
            break

        modifiedMessage = decoded_message.upper()
        serverSocket.sendto(modifiedMessage.encode(), clientAddress)

if __name__ == "__main__":
    start_server()