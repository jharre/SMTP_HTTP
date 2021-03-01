import socket
from time import time, ctime
import sys
import select
from threading import Thread
import os.path #for io
if (len(sys.argv) != 2):
     print("Error: Wrong number of arguments")
     print("Example of correct usage: python2 client.py *configFile*")
     sys.exit()
#serverName, serverPort = sys.argv[1:]
#serverName = "localhost"
#serverPort = "12345"
configFile = sys.argv[1]
with open(configFile, "r") as f:
    serverName = f.readline().split('=')[1].rstrip()
    serverPort = f.readline().split('=')[1].rstrip()
#serverName = "localhost"
#serverPort = 12345
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((serverName,int(serverPort)))
socketOpen = True
save_path = 'inbox/'
if not os.path.exists(save_path):
                    os.makedirs(save_path)
def recv():
    while True:
        if socketOpen:
            data = str(clientSocket.recv(1024).decode())
            if not data:
                sys.exit()
            if 'HTTP/' in data:
                num_files = len([f for f in os.listdir(save_path)if os.path.isfile(os.path.join(save_path, f))])
                file1 = open(os.path.join(save_path, (str(num_files + 1).zfill(3)) + '.txt'), 'a')
                while 'End' not in data:
                    file1.write(data + '\n')
                    data = str(clientSocket.recv(1024).decode())
                file1.close()
            else:
                print(data)
        else:
            return

x = Thread(target=recv)
x.start()
while True:
    userInput = raw_input()
    if socketOpen:
        clientSocket.send(userInput.encode())
    if 'QUIT' in userInput:
        socketOpen = False
        clientSocket.close()
        break