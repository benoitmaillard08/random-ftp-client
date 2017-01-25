import ftp
import transfer
import sys
import os
import getpass

# explorer = ftp.FTPExplorer("127.")

def getCallbackArg(commandName):
	return (lambda session, argument: ftp.FTPClient.genericRequest(session, commandName, argument))

def getCallback(commandName):
	return (lambda session: ftp.FTPClient.genericRequest(session, commandName))


COMMANDS = {
	"list" : ftp.FTPClient.list,
	"retr" : ftp.FTPClient.download,
	"stor" : ftp.FTPClient.upload,
	"rnfr" : ftp.FTPClient.rename,
	"togglemode" : ftp.FTPClient.toggleMode,
	"cwd" : getCallbackArg("CWD"),
	"dele" : getCallbackArg("DELE"),
	"mkd" : getCallbackArg("MKD"),
	"rmd" : getCallbackArg("RMD"),
	"pwd" : getCallback("PWD"),
	"cdup" : getCallback("CDUP"),
}

ERROR_STRING = "Please use following syntax : <l / d>.<action>\nExample : d.list"

class FTPCommandLine(object):
	def __init__(self):
		self.session = None

		domain = input("Enter domain name : ")
		port = input("Enter port number (can be left empty) : ")

		# in case no port is specified
		if port == "" or port == " ":
			port = 21

		# making sure port is an integer
		port = int(port)

		# Opening FTP session with server
		self.session = ftp.FTPClient(domain, port)

		self.authenticated = False

		while (not self.authenticated):
			username = input("Enter username : ")
			password = getpass.getpass("Enter password : ")

			# self.authenticated is set to True if authentication is successful
			response = self.session.authenticate(username, password)
			self.authenticated = response[0] == "230"


		self.prompt()

	def prompt(self):
		userInput = input("ftp# ")

		try:
			location, instruction = userInput.split(".", 1)

		# in case there was no "." or other character than "d" or "l" as location
		except ValueError:
			print(ERROR_STRING)
		else:
			if location == "l":
				# executing command as bash instruction
				os.system(instruction)
			elif location == "d":
				self.distantAction(instruction)
			else:
				print(ERROR_STRING)

		self.prompt()

	def distantAction(self, instruction):
		# quit instruction close the program immediately
		if instruction[0:4] == "quit":
			self.session.quit()
			sys.exit(0)

		splitInstruction = instruction.split(" ")

		# command name is the first part
		commandName = splitInstruction[0]

		# command arguments are the followings words (separated by spaces)
		arguments = splitInstruction[1:]

		try:
			commandMethod = COMMANDS[commandName]

		# in case the command doesn't exist (in this program's list, not in RFC)
		except KeyError:
			print("Unknown command")

		else:
			# calling chosen method with arguments
			try:
				response = commandMethod(self.session, *arguments)
			except TypeError as t:
				print(t)
				print("Wrong number of arguments for command {}".format(commandName))


FTPCommandLine()