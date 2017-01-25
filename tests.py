import unittest

import ftp

class TestFTP(unittest.TestCase):

	def setUp(self):
		self.session = ftp.FTPClient("localhost", 21)
		self.authResponse = self.session.authenticate("ftp-user", "ftp-pass")

	def test_authenticate(self):
		self.assertEqual(self.authResponse[0], "230")

	def test_list(self):
		status = self.session.list()[0]

		self.assertEqual(status, "226")

	def test_pwd(self):
		status = self.session.genericRequest("PWD")[0]

		self.assertEqual(status, "257")

	def test_cwd(self):
		status = self.session.genericRequest("CWD", "testdir")[0]
		self.session.genericRequest("CWD", "..")

		self.assertEqual(status, "250")

	def test_stor(self):
		status = self.session.upload("test.pdf")[0]

		self.assertEqual(status, "226")

	def test_retr(self):
		status = self.session.download("test.pdf")[0]

		self.assertEqual(status, "226")

	def test_file_integrity(self):
		f1 = self.session.getFile("test.pdf")

		self.session.upload("test.pdf")
		self.session.download("test.pdf")

		f2 = self.session.getFile("test.pdf")

		self.assertEqual(f1, f2)

	def test_dele(self):
		status = self.session.genericRequest("DELE", "test.pdf")[0]

		self.assertEqual(status, "250")

	def test_rename(self):
		status = self.session.rename("test.pdf", "test2.pdf")[0]

		self.session.rename("test2.pdf", "test.pdf")

		self.assertEqual(status, "250")

	def tearDown(self):
		self.session.quit()

class ActiveTest(TestFTP):
	def setUp(self):
		self.session = ftp.FTPClient("localhost", 21)
		self.authResponse = self.session.authenticate("ftp-user", "ftp-pass")
		self.session.passiveMode = False


unittest.main()