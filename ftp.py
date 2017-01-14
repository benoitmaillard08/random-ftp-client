import socket

ACTIVE = False
PASSIVE = True
BINARY = "I"
ASCII = "A"

class CommandConnect(object):
	def __init__(self, domain, user, password):
		"""
		Opens TCP COMMAND channel with server on port 21 and authenticates the user
		"""
		# Opening command TCP channel on port 21
		self.commandChannel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.commandChannel.connect((domain, 21))

		# A message is sent by the server at session opening
		self.getResponse()

		# Authentication
		self.sendRequest("USER " + user)
		self.sendRequest("PASS " + password)

		# Passive mode is set by default
		self.passiveMode = True


	def sendRequest(self, request, response=True):
		"""
		Sends a FTP request to the server
		"""

		# Request must end with a line return character
		request += "\n"

		print(request)

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


	def transfer(self, request, type, dataToSend=""):
		"""
		"""
		# Setting type
		print("TRANSFER #############################################")
		self.sendRequest("TYPE " + type)

		# Preparing data TCP channel (like port number) for passive or active mode
		dataTransfer = self.prepareTransfer()

		data = None

		# Response argument must be False because the response is not expected right after the request
		self.sendRequest(request, False)

		# Opening data TCP channel
		dataTransfer.openTCP()

		# A response from the server is expected after data channel opening
		# In the case of RETR, the response may contain file size in bytes
		status, response = self.getResponse()

		# 150 --> server ready to receive/send file
		if status == "150":
			# Actual data transfer, from client to server or the other way
			if dataToSend:
				dataTransfer.sendData(dataToSend)
				
			else:
				size = self.getSize(response)
				data = dataTransfer.receiveData(size)

		else:
			print("# UNABLE TO START TRANSFER")

		# Closing data channel
		dataTransfer.closeTCP()
		print("# Data connection closed")

		if status == "150":
			self.getResponse()

		print("END ##################################################")

		return data

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

		print("# Expected size : {}".format(size))

		return size


	def prepareTransfer(self):
		"""
		"""
		# Creating an instance from the appropriate class
		if self.passiveMode:
			dataTransfer = PassiveTransfer(self)

		else:
			dataTransfer = ActiveTransfer(self)

		dataTransfer.prepareTCP()

		return dataTransfer

	def quit(self):
		"""
		"""
		self.commandChannel.close()

	def setMode(self, mode):
		"""
		mode = False for Active Mode
		mode = True for Passive Mode
		"""
		if mode:
			self.passiveMode = True

		else:
			self.passiveMode = False


class DataTransfer(object):
	def __init__(self, parentChannel):
		"""
		"""
		# Reference to parent of type 'CommandConnect' used to send requests on command channel
		self.parentChannel = parentChannel
		self.dataChannel = None


	def sendData(self, bytesArray):
		"""
		"""
		# String must be converted to Byte for TCP transfer
		self.dataChannel.send(bytesArray)


	def receiveData(self, fileSize):
		"""
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

		print("# Response size : " + str(len(response)))

		return response


class PassiveTransfer(DataTransfer):
	def prepareTCP(self):
		"""
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
		"""
		# Opening TCP channel on port specified by the server
		self.dataChannel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.dataChannel.connect((self.domain, self.port))

		# print("Passive data channel opened !")
		# print("LOCAL PORT  : {}".format(self.dataChannel.laddr))
		# print("SERVER PORT : {}".format(self.dataChannel.raddr))


	def closeTCP(self):
		"""
		"""
		self.dataChannel.close()


class ActiveTransfer(DataTransfer):

	def prepareTCP(self):
		"""
		"""
		self.mainChannel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.mainChannel.bind(('', 0)) # 0 means OS chooses the port

		self.domain = "127,0,0,1"
		# Port chosen by OS
		self.port = self.mainChannel.getsockname()[1]

		portString = "PORT {},{},{}".format(self.domain, self.port // 256, self.port % 256)
		print("# Port request : " + portString)

		self.parentChannel.sendRequest(portString)


	def openTCP(self):
		"""
		"""
		self.mainChannel.listen(5)
		print("# Listening ...")

		# print("Active data channel opened !")
		# print("LOCAL PORT  : {}".format(self.dataChannel.laddr))
		# print("SERVER PORT : {}".format(self.dataChannel.raddr))

	def sendData(self, bytesArray):
		"""
		"""
		self.dataChannel, data = self.mainChannel.accept()

		DataTransfer.sendData(self, bytesArray)


	def receiveData(self, size):
		"""
		"""
		self.dataChannel, data = self.mainChannel.accept()

		DataTransfer.receiveData(self, size)


	def closeTCP(self):
		"""
		"""
		# In case 
		if self.dataChannel:
			self.dataChannel.close()

		self.mainChannel.close()


# Move to --> interface.py
class FileSystemEntity(object):
	def __init__(self, name, permissions, modifDateTime, size, isDirectory):
		"""
		"""
		self.name = name # name of file or folder
		self.permissions = permissions # permissions string
		self.modifDateTime = modifDateTime # date time of modification
		self.size = size # size in bytes
		self.isDirectory = isDirectory # True if directory // False if file


# c = CommandConnect("127.0.0.1", "ftp-user", "ftp-pass")

# c.setMode(ACTIVE)
# c.transfer("RETR tp.pdf", BINARY)
# c.transfer("RETR tpx.pdf", BINARY)
# c.transfer("STOR test.txt", BINARY, b"abc"*100000)
# c.transfer("RETRR tpx.pdf", BINARY)

# c.setMode(PASSIVE)
# c.transfer("RETR tp.pdf", BINARY)
# c.transfer("RETR tpx.pdf", BINARY)
# c.transfer("LIST", ASCII)
# c.transfer("STOR test.txt", BINARY, b"abc"*100000)
# c.transfer("RETRR tpx.pdf", BINARY)

# c.sendRequest("RNFR test.txt")
# c.sendRequest("RNTO TO test2.txt")

# c.sendRequest("MKD testdir")

# c.sendRequest("RMD testdir")

# c.transfer("LIST", ASCII)

# c.quit()

c = CommandConnect("185.28.188.151", "blm08.594891", "hynbedUdyem7")
print(c.transfer("LIST", ASCII).decode())
c.quit()