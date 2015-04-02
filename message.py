import cPickle as pickle

class Message:
	def __init__(self, msg_id, source, dest, msg):
		self.msg_id = msg_id
		self.source = source
		self.dest   = dest
		self.msg    = msg

	#Serialize the message object into a String
	def toString(self):
		return pickle.dumps(self)

	def getId(self):
		return self.msg_id

	def getMsg(self):
		return self.msg

	def getSource(self):
		return self.source

# This class is our Protocol, it is responsible for organizing data in a way
# we can retrive information about the message echange. 
	# Kinds of messages:
		
		# 10 User request login
		# 12 Login successful
		# 13 Your were kicked

		# 20 Server asks for username
		# 21 User sends username
		# 22 Server asks for password
		# 23 User sends password
		
		# 30 Invalid username
		# 31 Invalid password
		
		# 40 User has just been blocked
		# 41 User is blocked
		
		# 50 User request list of online users
		# 51 Server returns the list of online users
		
		# 60 User A wants to block user B
		# 61 User A wants to unblock user B
		# 62 Error (un)blocking user
		# 63 Success Blocking
		# 64 Success Unblocking
		
		# 70 User A wants the address of user B
		# 71 Server returns the requested address
		# 72 User not online
		# 73 Access denied: user has blocked you!

		# 80 User A wants to message user B
		# 81 User A wants to PRIVATE message user
		# 82 User wants to broadcast a message
		# 83 Server broadcasts message
		# 84 Fail to send message to some recipients
		# 85 Server deliver message from user A to user B
		# 86 Unknow user <username>
		# 87 Your message could not be delivered as the recipient has blocked you
		# 88 Is that user still online / have the same address?
		# 89 Server response

		# 90 User request logout
		# 91 Server tells user he is going to be logged out