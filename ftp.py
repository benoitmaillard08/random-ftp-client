import transfer
import os


class FTPClient(object):
    def __init__(self, domain, port):
        self.session = transfer.CommandConnect(domain, port)
        self.passiveMode = transfer.PASSIVE

    def authenticate(self, user, password):
        """
        """
        # Authentication
        self.session.sendRequest("USER " + user)
        response = self.session.sendRequest("PASS " + password)

        # Return True if authentication was successful
        return response

    def toggleMode(self):
        if self.passiveMode:
            self.passiveMode = False
        else:
            self.passiveMode = True

    def list(self):
        response = self.session.transfer("LIST", transfer.ASCII, self.passiveMode)
        
        # print directory list
        print(response[2].decode())

        return response

    def download(self, file):
        response = self.session.transfer("RETR " + file, transfer.BINARY, self.passiveMode)
        self.writeFile(file, response[2])

        return response

    def upload(self, file):
        content = self.getFile(file)
        return self.session.transfer("STOR " + file, transfer.BINARY, self.passiveMode, content)

    def rename(self, file, newname):
        status = self.session.sendRequest("RNFR "+file)[0]

        # RNFR was successful
        if status == "350":
            response = self.session.sendRequest("RNTO " + newname)

        return response

    def writeFile(self, file, content):
        file = open(file, "wb")
        file.write(content)
        file.close()

    def getFile(self, file):
        file = open(file, "rb")
        content = file.read()
        file.close()

        return content

    def genericRequest(self, command, argument=""):
        return self.session.sendRequest(command + " " + argument)

    def quit(self):
        self.session.quit()