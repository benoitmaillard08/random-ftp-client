import socket

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


	def getResponse(self, decode=True):
		"""
		Returns the response from the server after a request
		"""
		response = self.commandChannel.recv(1024)

		# Response is converted from Byte to String if needed
		if decode:
			response = response.decode()

		print(response)

		return response


	def transfer(self, request, type, dataToSend=""):
		"""
		"""
		# Preparing data TCP channel (like port number) for passive or active mode
		dataTransfer = self.prepareTransfer()

		# Setting type
		self.sendRequest("TYPE " + type)

		# Response argument must be False because the response is not expected right after the request
		self.sendRequest(request, False)

		# Opening data TCP channel
		dataTransfer.openTCP()

		# A response from the server is expected after data channel opening
		# In the case of RETR, the response may contain file size in bytes
		response = self.getResponse()

		# Actual data transfer, from client to server or the other way
		if dataToSend:
			dataTransfer.sendData(dataToSend)
			
		else:
			size = self.getSize(response)
			dataTransfer.receiveData(size)

		# Closing data channel
		dataTransfer.closeTCP()

		self.getResponse()

		return response

	def getSize(self, response):
		"""
		Returns the size of a file in bytes contained in response of type :
		"150 Opening BINARY mode data connection for download of file.ext (xxxx bytes)"
		"""

		try:
			# Finding text inside parenthesis
			parenthesis = response[response.find("(")+1 : response.find(")")]

		# In case size is not specified by server
		except IndexError:
			size = -1

		else:
			size = int(parenthesis.split(" ")[0])

		print("# File size : {}".format(size))

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
		self.commandChannel.close()


class DataTransfer(object):
	def __init__(self, parentChannel):
		"""
		"""
		# Reference to parent of type 'CommandConnect' used to send requests on command channel
		self.parentChannel = parentChannel


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

		print("# Last bytes : ")
		print(response[-100:])
		print("# Response wize : " + str(len(response)))

		return response


class PassiveTransfer(DataTransfer):
	def prepareTCP(self):
		"""
		"""
		# Entering pasive mode
		response = self.parentChannel.sendRequest("PASV")

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


	def closeTCP(self):
		"""
		"""
		self.dataChannel.close()


class ActiveTransfer(DataTransfer):
	def prepareTCP(self):
		"""
		"""
		self.dataChannel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.dataChannel.bind((''))

		self.domain = "127,0,0,1"
		self.port = self.dataChannel.getsockname()[1]

		self.parentChannel.sendRequest("PORT {},{},{}".format(self.domain, self.port / 256, self.port % 256))

	def openTCP(self):
		"""
		"""
		pass


class FileSystemEntity(object):
	def __init__(self, name, permissions, modifDateTime, size, isDirectory):
		"""
		"""
		self.name = name # name of file or folder
		self.permissions = permissions # permissions string
		self.modifDateTime = modifDateTime # date time of modification
		self.size = size # size in bytes
		self.isDirectory = isDirectory # True if directory // False if file


c = CommandConnect("127.0.0.1", "ftp-user", "ftp-pass")
c.transfer("RETR tp9.pdf", "I")
c.quit()