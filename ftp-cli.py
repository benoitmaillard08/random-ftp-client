import ftp
import transfer
import sys
import os
import getpass

# explorer = ftp.FTPExplorer("127.")

def getCallback(commandName):
	return (lambda session, argument="": ftp.FTPClient.genericRequest(session, commandName, argument))


COMMANDS = {
	"list" : ftp.FTPClient.list,
	"retr" : ftp.FTPClient.download,
	"stor" : ftp.FTPClient.upload,
	"rnfr" : ftp.FTPClient.rename,
	"togglemode" : ftp.FTPClient.toggleMode,
	"cwd" : getCallback("CWD"),
	"dele" : getCallback("DELE"),
	"mkd" : getCallback("MKD"),
	"rmd" : getCallback("RMD"),
	"pwd" : getCallback("PWD"),
	"cdup" : getCallback("CDUP"),
}
ERROR_STRING = "Please use following syntax : <l / d>.<action>\nExample : d.list"
HELP_STRING = """
User inputs must use the following syntax : <l / d>.<action>
Prefix "l." can be used to execute bash actions, while "d." is used for actual FTP actions

Here is a list of FTP actions (commands with prefix "d.") :
- list : list content of current directory
- retr <file> : download a file from current directory
- stor <file> : upload a file to current directory
- renfr <oldname> <newname> : rename a file
- togglemode : change mode from passive to active or active from passive (passive is default)
- cwd <relative path> : change current directory
- dele <file> : remove a file from current directory
- mkd <directory> : create a directory
- rmd <directory> : remove a directory
- pwd : print path of current directory
- cdup : change working directory to parent directory

Enter "quit" (without prefix) to close the program
"""

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

		print('Enter "help" to display user manual')
		self.prompt()

	def prompt(self):
		userInput = input("ftp# ")

		if userInput == "help":
			print(HELP_STRING)

		# quit instruction close the program immediately
		elif userInput == "quit":
			self.session.quit()
			sys.exit(0)
		else:
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
			except TypeError:
				print("Wrong number of arguments for command {}".format(commandName))
			except transfer.TransferException:
				print("Unable to transfer data : check logs for more information")

FTPCommandLine()