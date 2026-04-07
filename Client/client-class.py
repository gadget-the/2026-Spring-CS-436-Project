import json
from socket import socket, AF_INET, SOCK_DGRAM

class socket_client():
    serverName = None
    serverPort = None
    clientSocket = None
    SERVER_CLOSE_MESSAGE = "STOP"
    SERVER_CLOSE_ACK = "CLOSE_ACK"

    def __init__(self, givenName = 'localhost', givenPort = 12000):
        self.serverName = givenName
        self.serverPort = givenPort
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)

    def send_message(self, message = ""):
        try:
            self.clientSocket.sendto(message.encode(), (self.serverName, self.serverPort))
        except Exception as e:
            self.stop()
            print("message not succesful, error returned :", e)

    def send_dict(self, data):
        data_string = json.dumps(data) # serialize the data (turn it into a string)
        # data_loaded = json.loads(data) # load the data (turn it back into a dict)

        self.clientSocket.sendto(data_string.encode(), (self.serverName, self.serverPort))

    def receive_message(self):
        modifiedMessage, serverAddress = self.clientSocket.recvfrom(2048)
        print(modifiedMessage.decode())

    def stop(self):
        self.clientSocket.close()

if __name__ == "__main__":
    client1 = socket_client()

    message = input('Input lowercase sentence:')
    client1.send_message(message)
    # client1.send_dict({"test": True})

    client1.stop()

    '''
    doesn't work for some reason??
    '''