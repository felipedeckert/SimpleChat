import datetime
class User:

	def __init__(self, username, password, ip, port):
		self.username = username
		self.password = password
		self.ip   = ip
		self.port = port
		self.blockDate  = datetime.datetime.min
		self.lastTry    = datetime.datetime.min
		self.lastBeat   = datetime.datetime.min
		self.blackList  = []
		self.tentatives = 0
		self.offlineMsg = []

	def getHeartBeat(self):
		return self.lastBeat

	def setHeartBeat(self):
		self.lastBeat = datetime.datetime.today()

	def invalidPassword(self):
		self.tentatives += 1
		self.lastTry     = datetime.datetime.today()
		if(self.tentatives == 3):
			self.blockDate = datetime.datetime.today()

	def getBlockDate(self):
		return self.blockDate

	def getLastTry(self):
		return self.lastTry

	def setLastTry(self, new_date):
		self.lastTry = new_date

	def resetTentatives(self):
		self.tentatives = 0

	def getTentatives(self):
		return self.tentatives

	def getUsername(self):
		return self.username

	def getPassword(self):
		return self.password

	def setIp(self, ip_addr):
		self.ip = ip_addr

	def getIp(self):
		return self.ip

	def setPort(self, port_number):
		self.port = port_number

	def getPort(self):
		return self.port
	
	def addBlackList(self, user_target):
		# check if the user already is blocked
		if(user_target not in self.blackList):
			self.blackList.append( user_target )
			return True
		return False

	def removeBlackList(self, user_target):
		# check if the user is not blocked
		if(user_target in self.blackList):
			self.blackList.remove( user_target )
			return True
		return False

	def getBlackList(self):
		return self.blackList

	def addOfflineMsg(self, in_msg):
		self.offlineMsg.append(in_msg)

	def getOfflineMsg(self):
		return self.offlineMsg

	def resetOfflineMsg(self):
		self.offlineMsg = []