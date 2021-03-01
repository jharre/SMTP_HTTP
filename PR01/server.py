from socket import *
from datetime import datetime
from threading import Thread
import select
import re #regular expressions for input
import os.path #for io
import sys

userQueue = []
threads = []
if (len(sys.argv) != 2):
     print("Error: Wrong number of arguments")
     print("Example of correct usage: python2 server.py *configFile*")
     sys.exit()

configFile = sys.argv[1]
#configFile = "server.conf"
with open(configFile, "r") as f:
    SMTP_PORT = f.readline().split('=')[1].rstrip()
    HTTP_PORT = f.readline().split('=')[1].rstrip()

httpSocket = socket(AF_INET, SOCK_STREAM)
#httpSocket.setblocking(False)
httpSocket.bind(('', int(HTTP_PORT)))
httpSocket.listen(5)

SMTPSocket = socket(AF_INET, SOCK_STREAM)
#SMTPSocket.setblocking(False)
SMTPSocket.bind(('', int(SMTP_PORT)))
SMTPSocket.listen(5)

userDict = {}
save_path = 'db/'

print("The server is ready to recieve")
#if not os.path.exists('db'):
#    os.makedirs("db")

def getReadableUsers():
    ready_to_read = []
    readableUsers = {}
    if len(userDict) < 1:
        return readableUsers
    for addr in userDict.keys():
        ready_to_read.append(userDict[addr]['socket'])

    for user in userDict.values():
        for socket in ready_to_read:
            if user['socket'] == socket:
                readableUsers[user['address']] = user
    return readableUsers
    
def handleNewConnections_SMTP():
    while True:
        connectionSocket, addr = SMTPSocket.accept()

        #x = Thread(target=handleNewConnections_SMTP)
        #x.start()
        #threads.append(x)
        userQueue.append((connectionSocket,addr))
        connectionSocket.send("220 Connection accepted from " + gethostname())
        if addr not in userDict.keys():
            userDict[addr] = {  'address': addr,
                                'socket':connectionSocket,
                                'helod':False,
                                'connected': False}
    

def handleNewConnections_HTTP():
    while True:
        connectionSocket, addr = httpSocket.accept()
        userQueue.append((connectionSocket,addr))
        #connectionSocket.setblocking(0)
        if addr not in userDict.keys():
            userDict[addr] = {  'address': addr,
                                'socket':connectionSocket,
                                'helod':False,
                                'connected': False}

def smtpHandler(addr):
    boolean = True
    
    connectionSocket = userDict[addr]['socket']

    try:
        helo = connectionSocket.recv(1024)
        if helo[:4] == 'HELO':
            connectionSocket.send("250 Hello " + gethostname() + '. Pleased to meet you.')
            userDict[addr]['helod'] = True
            boolean = True
    except:
        connectionSocket.send('HELO error. Try again.')
    while boolean:
        #recieve mail from
        cmd = connectionSocket.recv(1024)
        if 'HELP' in cmd:
            if 'MAIL' in cmd:
                connectionSocket.send('Correct usage: MAIL FROM: <user@test.com>')
                continue
            if 'RCPT' in cmd:
                connectionSocket.send('Correct usage: RCPT TO: <user@test.com>')
                continue
            if 'DATA' in cmd:
                connectionSocket.send("Correct usage: DATA\n*type your message here*\n Then type a single period to finish data entry.")
                continue
         # check if cmd input is out of order
        _check1 = re.match(r'RCPT(\s+|$)TO:', cmd)
        _check2 = re.match(r'DATA', cmd)
        # checks for valid MAIL FROM cmd 
        _cmd = re.match(r'MAIL(\s+|$)FROM:' , cmd)
        # checks for valid path
        _path = re.match(r'MAIL(.+)FROM:(\s*)<[^\s](.+)@(.+)[^\s]>', cmd)
        # checks for valid mailbox
        _mb = re.match(r'MAIL(.+)FROM:(\s*)<([\+/\'!\?\w-]+)@[^\s](.+)[^\s]>', cmd)
        # checks for valid local-part
        _lp = re.match(r'MAIL(.+)FROM:(\s*)<([\+/\'!\?\w-]+)@(.+)>', cmd)
        # checks for valid url domain 
        _domain = re.search(r'MAIL(.+)FROM:(\s*)<(.+)@([\w.]+)>', cmd)
        if _check1:
            connectionSocket.send('503 Bad sequence of cmds')
            continue
        if _check2:
            connectionSocket.send('503 Bad sequence of cmds')
            continue
        elif not _cmd:
            connectionSocket.send('500 Syntax error: cmd unrecognized')
            continue
        elif not _path:
            connectionSocket.send('501 Syntax error in parameters or arguments')
            continue
        elif not _mb:
            connectionSocket.send('501 Syntax error in parameters or arguments')
            continue
        elif not _lp:
            connectionSocket.send('501 Syntax error in parameters or arguments')
            continue
        elif not _domain:
            connectionSocket.send('501 Syntax error in parameters or arguments')
            continue
        else:
            From = cmd.replace("MAIL FROM", "From")
            connectionSocket.send('250 OK')
        _bool = True
        toList = []
        rcptList = []
        while boolean:
            # recieve rcpt to
            receipt = connectionSocket.recv(1024)
            check = re.match(r'DATA', receipt)
            # if check:
            # _bool=False   
            check2 = re.match(r'MAIL(\s+|$)FROM:' , receipt)
            # checks for valid RECEIPT TO command 
            rcpt = re.match(r'RCPT(\s+|$)TO:', receipt)
            # checks for valid path
            fpath = re.match(r'RCPT(.+)TO:(\s*)<([\+/\'!\?\w-]+)@([\w.]+)>', receipt)
            if receipt[:7] == 'Subject':
                receipt = 'DATA'
                _bool = False
                continue
            if _bool is False:
                if check:
                    break
                if check2:
                    connectionSocket.send('503 Bad sequence of commands')
                    continue
            if not rcpt:
                connectionSocket.send('501 Syntax error in parameters or arguments')
                continue
            elif not fpath:
                connectionSocket.send('501 Syntax error in parameters or arguments')
                continue
            else:
                _bool = False
                # make save names from recipients
                name_of_file = receipt.replace("RCPT TO: ", "")
                name_of_file = name_of_file.strip('>')
                name_of_file = name_of_file[1:]
                name_of_file = name_of_file.split('@', 1)[0]
                to = receipt.replace("RCPT TO: ", "")
                rcptList.append(to)
                save_name = os.path.join(save_path, name_of_file)
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                if not os.path.exists(save_name):
                    os.mkdir(save_name)
                num_files = len([f for f in os.listdir(save_name)if os.path.isfile(os.path.join(save_name, f))])
                file1 = open(os.path.join(save_name, (str(num_files + 1).zfill(3)) + '.email'), 'a')
                toList.append(file1)

                connectionSocket.send('250 OK')
                for files in toList:
                    file1 = files
                    size = len(rcptList)
                    file1.write("Date: " + str(datetime.now()) + '\n')
                    file1.write(From + "\n")
                    file1.write("To: ")
                    for rcpt in rcptList:
                        size = size - 1
                        if size is 0:
                            file1.write(rcpt + "\n")
                        else:
                            file1.write(rcpt + ", ")
                continue
            

        while boolean:
            if not check:
                # receive DATA cmd 
                datacmd = connectionSocket.recv(1024)
                check = re.match(r'DATA', datacmd)

            if not check:
                connectionSocket.send('500 Syntax error: command unrecognized')
                continue
            else:
                connectionSocket.send('354 Start mail input; end with <CRLF>.<CRLF>')
            
            while boolean:
                # receive msg until QUIT      
                data = connectionSocket.recv(1024)
                if data == '.':
                    connectionSocket.send('250 OK')
                    boolean = False
                
                    for files in toList:
                        file1 = files
                        file1.close()

                    quitCmd = connectionSocket.recv(1024)
                    if re.match(r'QUIT', quitCmd):
                        connectionSocket.send('221 Bye')
                        boolean = False
                        del(userDict[addr])
                        break

                else:
                    #connectionSocket.send(data)
                    for files in toList:
                        file1 = files
                        file1.write(data + "\n")
                        continue

def httpHandler(addr):
    connectionSocket = userDict[addr]['socket']
    connectionSocket.send("HTTP Connected.\n")
    
    while True:
        connectionSocket.send("Enter username:")
        username = connectionSocket.recv(1024)
        connectionSocket.send("Enter number of Emails to retrieve:")
        count = connectionSocket.recv(1024)

        try:
            get = connectionSocket.recv(1024)
            if get[:3] == 'GET':
                #connectionSocket.send("250 Hello " + gethostname() + '. Pleased to meet you.')
                #userDict[addr]['helod'] = True
                #boolean = True
                get = get.split(' ')
                filepath = get[1]
                filepath = filepath[1:]
                httpVersion = get [2]
                if not os.path.exists(filepath):
                    connectionSocket.send('404 (Path not found.)')
                    continue
                num_files = len([f for f in os.listdir(filepath)if os.path.isfile(os.path.join(filepath, f))]) 
                #if count > num_files:
                #    connectionSocket.send('404 (Files not found.)')
        except:
            connectionSocket.send('400 (Bad Request)')
            continue
        connectionSocket.send('HTTP/1.1 200 OK')
        connectionSocket.send('Server: ' + str(gethostname()))
        mod_time = os.path.getmtime(filepath)
        local_time = datetime.fromtimestamp(mod_time)
        connectionSocket.send('Last modified: ' + str(local_time))
        connectionSocket.send('Count: ' + str(count))
        connectionSocket.send('Content-Type: text/plain')
        connectionSocket.send('Messages: ' + str(count))
        num = 0
        messages = 0
        for f in os.listdir(filepath):
            num = num + 1
            if num < count:
                messages = messages + 1
                with open((filepath + f), 'r') as readFile:
                    lines = readFile.readlines()
                    for line in lines:
                        connectionSocket.send(line.rstrip())
        connectionSocket.send('\nEnd of messages.')
        quitMsg = connectionSocket.recv(1024)
        if 'QUIT' in quitMsg:
            del(userDict[addr])
            connectionSocket.close()
            break
            

#def queueHandler():    
#    while True:
#        if len(userQueue) > 0:
#            connectionSocket, addr = userQueue.pop()
#            if addr not in userDict.keys():
#                userDict[addr] = {  'address': addr,
#                                    'socket':connectionSocket,
#                                    'helod':False}

x = Thread(target=handleNewConnections_SMTP)
x.start()
    
y = Thread(target=handleNewConnections_HTTP)
y.start()

#z = Thread(target=queueHandler)
#z.start()

#handleNewConnections_SMTP()
while True:
    
    readableUsers = getReadableUsers()
    if len(readableUsers) < 1:
        continue
    for addr in readableUsers.keys():
        #print(userDict[addr]['socket'].getsockname())
        #print(SMTPSocket.getsockname())
        try:
            if userDict[addr]['connected']:
                continue
        except:
            continue
        if userDict[addr]['socket'].getsockname()[1] == SMTPSocket.getsockname()[1]:
            
            userDict[addr]['connected'] = True
            #smtpHandler(addr)
            z = Thread(target=smtpHandler, args = (addr,))
            z.start()
            del(readableUsers[addr])
            continue
        elif userDict[addr]['socket'].getsockname()[1] == httpSocket.getsockname()[1]:
            
            userDict[addr]['connected'] = True
            #httpHandler(addr)
            z = Thread(target=httpHandler, args = (addr,))
            z.start()
            del(readableUsers[addr])
            continue
        else:
            print("wrong hole")
