from socket import socket, AF_INET, SOCK_DGRAM#, SOL_SOCKET, SO_REUSEADDR

class socket_server():
    # serverPort = 12000
    # serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverPort = None
    serverSocket = None
    SERVER_CLOSE_MESSAGE = "STOP"
    SERVER_CLOSE_ACK = "CLOSE_ACK"

    def __init__(self, given_port = 12000):
        # self.serverPort = 12000
        # self.serverSocket = socket(AF_INET, SOCK_DGRAM)
        self.serverPort = given_port
        self.serverSocket = socket(AF_INET, SOCK_DGRAM)

    # def __del__(self):
    #     self.stop()

    def stop(self):
        # unbind the port?
        print ('Stopping Server...')
        # self.serverSocket.shutdown() # shutdown then close?
        self.serverSocket.close() # close the socket; might not unbind the port...

    def start(self):
        # self.serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # https://docs.python.org/3.3/library/socket.html and https://docs.python.org/3.3/library/socket.html
        self.serverSocket.bind(('', self.serverPort)) # bind the socket to the port specified(12000)

        print ('The server is ready to receive')

        while True:
            try:
                message, clientAddress = self.serverSocket.recvfrom(2048) # 
                decoded_message = message.decode() # decode the message received from the client

                if decoded_message == self.SERVER_CLOSE_MESSAGE: # check for close message
                    self.serverSocket.sendto(self.SERVER_CLOSE_ACK.encode(), clientAddress) # send ACK to client; want to have this in stop fxn, but not sure how w/o making clientaddress (more) global...
                    self.stop()
                    break

                modifiedMessage = decoded_message.upper() # change message to uppercase
                self.serverSocket.sendto(modifiedMessage.encode(), clientAddress) # send the modified message back to the client
            except Exception as e:
                self.stop()
                print("message not succesful, error returned :", e)
                break

if __name__ == "__main__":
    server1 = socket_server()

    server1.start()