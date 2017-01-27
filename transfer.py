import socket

BINARY = "I"
ASCII = "A"
PASSIVE = True
ACTIVE = False

class FTPCommand(object):
    def __init__(self, domain, port):
        """
        Opens TCP COMMAND channel with server on port 21 and authenticates the user
        """

        # Opening command TCP channel on port 21
        self.commandChannel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.commandChannel.connect((domain, port))

        # A message is sent by the server at session opening
        self.getResponse()

    def sendRequest(self, request, response=True):
        """
        Sends a FTP request to the server
        """

        print(request)

        # Request must end with a line return character
        request += "\n"

        # String must be converted to Byte for TCP transfer
        self.commandChannel.send(request.encode())

        if response:
            return self.getResponse()


    def getResponse(self):
        """
        Returns the response from the server after a request
        """
        response = self.commandChannel.recv(1024)

        response = response.decode()

        print(response)

        # Status code and message are separated
        status, message = response.split(" ", 1)

        return status, message


    def transfer(self, request, type, passiveMode=True, dataToSend=""):
        """
        Opens data channel and sends / receives byte array
        """
        # Setting type
        self.sendRequest("TYPE " + type)

        # Instancing appropriate mode
        if passiveMode:
            dataTransfer = PassiveTransfer(self)
        else:
            dataTransfer = ActiveTransfer(self)

        # Preparing data TCP channel (like port number) for passive or active mode
        dataTransfer.prepareTCP()

        data = None # content received from the server

        # Response argument must be False because the response is not expected right after the request
        self.sendRequest(request, False)

        # Opening data TCP channel
        dataTransfer.openTCP()

        # A response from the server is expected after data channel opening
        # In the case of RETR, the response may contain file size in bytes
        status, message = self.getResponse()

        # 150 --> server ready to receive/send file
        if status == "150":
            # Actual data transfer, from client to server or the other way
            if dataToSend:
                dataTransfer.sendData(dataToSend)
                
            else:
                size = self.getSize(message)
                data = dataTransfer.receiveData(size)
                

        else:
            dataTransfer.closeTCP()
            raise TransferException(status, message, "Unable to transfer data")

        # Closing data channel
        dataTransfer.closeTCP()

        if status == "150":
            status, message = self.getResponse()

        return status, message, data

    def getSize(self, response):
        """
        Returns the size of a file in bytes contained in response of type :
        "150 Opening BINARY mode data connection for download of file.ext (xxxx bytes)"
        """

        # Finding text inside parenthesis
        p1 = response.find("(")
        p2 = response.find(")")

        if p1 >= 0:
            parenthesis = response[p1+1 : p2]
            size = int(parenthesis.split(" ")[0])

        else:
            size = -1

        return size

    def quit(self):
        """
        Closes command channel
        """
        self.commandChannel.close()


class FTPData(object):
    def __init__(self, parentChannel):
        """
        """
        # Reference to parent of type 'CommandConnect' used to send requests on command channel
        self.parentChannel = parentChannel
        self.dataChannel = None


    def sendData(self, bytesArray):
        """
        Send bytes array on data channel
        """
        # String must be converted to Byte for TCP transfer
        self.dataChannel.send(bytesArray)


    def receiveData(self, fileSize):
        """
        Receives bytes array on data channel
        """
        currentSize = 0 # Number of bytes received so far
        response = b"" # Data recevied so far
        

        # Data is received by chunk of 4096 bytes
        while True:
            response += self.dataChannel.recv(4096)
            currentSize += 4096
            

            # Loop breaks when all the bytes have been received
            if currentSize >= fileSize:
                break


        
        return response


class PassiveTransfer(FTPData):
    def prepareTCP(self):
        """
        Prepares transfer in passive mode
        """
        # Entering pasive mode
        response = self.parentChannel.sendRequest("PASV")[1]

        # Finding text inside parenthesis
        parenthesis = response[response.find("(")+1 : response.find(")")]

        # Various parameters are separated by ","
        params = parenthesis.split(",")

        # Finding IP and port
        self.domain = ".".join(params[0:4])
        self.port = int(params[4]) * 256 + int(params[5])


    def openTCP(self):
        """
        Initialize data channel on port given by server
        """
        # Opening TCP channel on port specified by the server
        self.dataChannel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dataChannel.connect((self.domain, self.port))

    def closeTCP(self):
        """
        Close data channel
        """
        self.dataChannel.close()


class ActiveTransfer(FTPData):
    def prepareTCP(self):
        """
        Sends port information to server
        """
        self.mainChannel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mainChannel.bind(('', 0)) # 0 means OS chooses the port

        self.domain = "127,0,0,1"
        # Port chosen by OS
        self.port = self.mainChannel.getsockname()[1]

        portString = "PORT {},{},{}".format(self.domain, self.port // 256, self.port % 256)

        self.parentChannel.sendRequest(portString)


    def openTCP(self):
        """
        Makes data channel ready to accepts connections
        """
        self.mainChannel.listen(5)

    def sendData(self, bytesArray):
        """
        Accepts connection from server and sends bytes array
        """
        self.dataChannel, data = self.mainChannel.accept()

        FTPData.sendData(self, bytesArray)


    def receiveData(self, size):
        """
        Accepts connection from server and receives bytes array
        """
        self.dataChannel, data = self.mainChannel.accept()

        return FTPData.receiveData(self, size)


    def closeTCP(self):
        """
        Closes data channel
        """
        # In case there was an actual connection with server
        if self.dataChannel:
            self.dataChannel.close()

        self.mainChannel.close()

class TransferException(Exception):
    def __init__(self, status, message, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.status = status
        self.message = message