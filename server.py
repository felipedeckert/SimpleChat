import sys
import socket
import datetime
import message as msg
import cPickle as pickle
import user as usr
import threading
import time

finishEvent = threading.Event()

# buffer size to receive a message
BUF_SIZE   = 2048
MAX_USERS  = 5
BLOCK_TIME = 60
TIME_BEAT  = 30
INVALID_LOGIN = '\nInvalid username and/or possword.'
USER_BLOCKED  = '\nDue to multiple login failures, your account has been blocked.\nPlease try again after sometime.'
JUST_BLOCKED  = '\nInvalid Password. Your account has been blocked.\nPlease try again after sometime.'
SUCCESS       = '\nWelcome to simple chat server!'
BLOCK_ERROR   = '\nAn error occurred while (un)blocking user.'
BLOCK_OKAY    = '\nUser has been blocked.'
UNBLOCK_OKAY  = '\nUser has been unblocked.'
USER_OFFLINE  = '\nUser is offline.'
LOGGED_OUT    = '\nYou\'ve been logged out.'
UNKNOWN_USER  = '\nUnknown user: '
UR_BLOCKED    = '\nYour message could not be delivered \nas the recipient has blocked you.'
ACCESS_DENIED = '\nAccess denied: user has blocked you!'
ADM_KICK      = '\nSomeone logged into your account, you are being logged out.'

onlineUsers = []

def heartBeat():
	while ( not finishEvent.isSet() ):
		# sleep until it's time to check the next heart beat
		time.sleep(TIME_BEAT + 1)
		for u in onlineUsers:
			now = datetime.datetime.today()
			# if user hasnt sent heart beat, remove it
			if( (now - u.getHeartBeat()).seconds > TIME_BEAT):
				onlineUsers.remove( u )
				# anounce that user is online
				broadcastMsg(u.getUsername()+' is offline!', 'SERVER')

def fromString(input_msg):
	return pickle.loads(input_msg)

def userLogin(clientSock, credentials, clientPort):
	# get the user IP
	dest   = clientSock.getpeername()[0]
	source = 'SERVER'
	
	while True:
		# request username
		clientSock.send( msg.Message(20, source, dest, '\nUsername: ').toString() )
		# get response
		response = fromString(clientSock.recv(BUF_SIZE))
		username = response.getMsg()
		# request password
		clientSock.send( msg.Message(22, source, dest, '\nPassword: ').toString() )
		# get response
		response = fromString(clientSock.recv(BUF_SIZE))
		password = response.getMsg()

		if(username not in credentials): 
			clientSock.send( msg.Message(30, source, dest, INVALID_LOGIN).toString() )	
			continue
		# get the user object from the user whos trying to login
		currentUser = credentials[username]

		# check if the user has been blocked in the last BLOCK_TIME seconds
		if((datetime.datetime.today() - currentUser.getBlockDate()).seconds < BLOCK_TIME):
			# update user's last attempt to connect (MAY BE USELESS)
			currentUser.setLastTry(datetime.datetime.today())
			# send blocked message
			clientSock.send(msg.Message(41, source, dest, USER_BLOCKED).toString())
			return None

		# if the password is wrong
		elif(currentUser.getPassword() != password):
			# update the wrong password control
			currentUser.invalidPassword()
			# check the number of tentatives, its going to be either invalid or just blocked
			if(currentUser.getTentatives() < 3):
				clientSock.send(msg.Message(31, source, dest, INVALID_LOGIN).toString())
			else:
				currentUser.resetTentatives()
				clientSock.send(msg.Message(40, source, dest, JUST_BLOCKED).toString())
				return None

		# if it is a valid login, get ip and port
		else:
			# if user is already logged
			for u in onlineUsers:
				if(u.getUsername() == currentUser.getUsername()):
					userLogout(u.getUsername())

			currentUser.setIp(dest)
			currentUser.setPort(clientPort)
			# append current user to list fo online users
			onlineUsers.append(currentUser)
			# anounce that user is online
			broadcastMsg(currentUser.getUsername()+' is online!', 'SERVER')
			clientSock.send(msg.Message(12, source, dest, SUCCESS).toString())
			return currentUser

def getOnlineUsers():
	# list to be sent
	onlineUsersList = []
	# if the user has ip != '' it is on, so append to the list
	for user in onlineUsers:
		onlineUsersList.append( user.getUsername() )
	# serialize and return the list of users
	return (onlineUsersList)

def userLogout(user_name):
	myUser = None
	# find the user who requested logout
	for user in onlineUsers:
		if( user.getUsername() == user_name ):
			myUser = user
			break
	# send logout message
	clientSock = socket.socket()
	clientSock.connect( (myUser.getIp(), myUser.getPort()) )
	togo = msg.Message(91, 'SERVER', user_name, LOGGED_OUT).toString()
	clientSock.send ( togo )
	clientSock.close()
	
	# remove user from list of online users
	onlineUsers.remove(myUser)
	# anounce that user is online
	broadcastMsg(myUser.getUsername()+' is offline!', 'SERVER')

def blockUser(credentials, user_name, user_target):
	# check for existence of user to be blocked
	if(user_target not in credentials):
		return False
	# get the user who made the request
	for u in onlineUsers:
		if( u.getUsername() == user_name ):
			return u.addBlackList(user_target)

def unblockUser(credentials, user_name, user_target):
	# check for existence of user to be blocked
	if(user_target not in credentials):
		return False
	# get the user who made the request
	for u in onlineUsers:
		if( u.getUsername() == user_name ):
			return u.removeBlackList(user_target)

def broadcastMsg(out_msg, user):
	if(user == 'SERVER'):
		src = user
	else:
		src = user.getUsername()
	blocked = False
	# go through all online users
	for u in onlineUsers:
		# do not send message to the same user
		if( src == u.getUsername() ):
			continue
		# if user A is not blocked by B, open connection and send message
		if( src not in u.getBlackList() ):
			try:
				broadSock = socket.socket()
				broadSock.connect((u.getIp(), u.getPort()))
				broadSock.send( msg.Message(83, src, u.getIp(), src+': '+out_msg).toString() )
				broadSock.close()
			except socket.error:
				blocked = False
		else:
			blocked = True
	
	if( blocked ):
		failSock = socket.socket()
		failSock.connect((user.getIp(), user.getPort()))
		failMsg = 'Your message could not be delivered to some recipients.'
		failSock.send( msg.Message(84, 'SERVER', user.getIp(), failMsg).toString() )
		failSock.close()
# convert a list of words into a phrase
def toPhrase(wordList):
	i = len(wordList) - 1
	phrase = ''
	for word in wordList:
		phrase += word
		if( i ):
			phrase += ' '
			i -= 1
	return phrase

def sendMessage(out_msg, user_send, credentials):
    # split message 0 = username, 1 = message
	tempMsg = out_msg.split()
	outUser = None
	for u in onlineUsers:
		if(u.getUsername() == tempMsg[0]):
			outUser = u
			break

	outMsg = msg.Message( 85, user_send.getUsername(), tempMsg[0], user_send.getUsername()+': '+toPhrase( tempMsg[1:] ) ).toString()
	outSock = socket.socket()
	# unknow username
	if(tempMsg[0] not in credentials):
		outSock.connect( (user_send.getIp(), user_send.getPort()) )
		outSock.send( msg.Message( 86, 'SERVER', user_send.getUsername(), UNKNOWN_USER+tempMsg[0] ).toString() )
		outSock.close()
		return

	# send offline message
	if(outUser is None):
		credentials[tempMsg[0]].addOfflineMsg( outMsg )
	# if user is blocked
	elif(user_send.getUsername() in outUser.getBlackList() ):
		outSock.connect( (user_send.getIp(), user_send.getPort()) )
		outSock.send( msg.Message( 86, 'SERVER', user_send.getUsername(), UR_BLOCKED ).toString() )
	else:
		# send message and close connection
		outSock.connect( (outUser.getIp(), outUser.getPort()) )
		outSock.send( outMsg )

	outSock.close()

def sendOfflineMsg(outUser):
	# send all offline messages stored
	for outMsg in outUser.getOfflineMsg():
		outSock = socket.socket()
		outSock.connect( (outUser.getIp(), outUser.getPort()) )
		outSock.send( outMsg )
		outSock.close()
	# clear list of offline messages
	outUser.resetOfflineMsg()

def handleMessage(input_msg, clientSock, credentials):
	curUser = None
	# if it is a message from a logged user
	if( input_msg.getId() != 10 ):
		# find user who sent message
		for u in onlineUsers:
			if( u.getUsername() == input_msg.getSource() ):
				curUser = u
				break
		# connect with the user, in order to reply
		replySock = socket.socket()
		if(curUser != None):
			replySock.connect((curUser.getIp(), curUser.getPort()))

	# unknown client requests login
	if(input_msg.getId() == 10):
		new_user = userLogin( clientSock, credentials, input_msg.getMsg() )
		if( new_user != None ):
			sendOfflineMsg( new_user )

	# logged client request list of online users
	elif(input_msg.getId() == 50):
		onlineUsersString = getOnlineUsers()
		# send the response message
		replySock.send( msg.Message(51, 'SERVER', input_msg.getSource(), onlineUsersString).toString() )

	# block user
	elif(input_msg.getId() == 60):
		if(not blockUser(credentials, input_msg.getSource(), input_msg.getMsg()) ):
			replySock.send( msg.Message(62, 'SERVER', input_msg.getSource(), BLOCK_ERROR).toString() )
		else:
			replySock.send( msg.Message(63, 'SERVER', input_msg.getSource(), BLOCK_OKAY).toString() )
	
	# unblock user
	elif(input_msg.getId() == 61):
		if( not unblockUser(credentials, input_msg.getSource(), input_msg.getMsg() )  ):
			replySock.send( msg.Message(62, 'SERVER', input_msg.getSource(), BLOCK_ERROR).toString() )
		else:
			replySock.send( msg.Message(64, 'SERVER', input_msg.getSource(), UNBLOCK_OKAY).toString() )
	
	# get a user's address
	elif(input_msg.getId() == 70):
		userIsOnline = False
		for user in onlineUsers:
			# if user is online, return it's address
			if( user.getUsername() == input_msg.getMsg() ):
				# if user has blocked you
				if( input_msg.getSource() in user.getBlackList() ):
					replySock.send( msg.Message(73, 'SERVER', input_msg.getSource(), ACCESS_DENIED ).toString() )
				useraddr = '\n'+user.getUsername()+' IP: '+user.getIp()+' Port: '+str(user.getPort())
				replySock.send( msg.Message(71, 'SERVER', input_msg.getSource(), useraddr ).toString() )
				userIsOnline = True
		if( not userIsOnline):
			replySock.send( msg.Message(72, 'SERVER', input_msg.getSource(), USER_OFFLINE ).toString() )
	
	# user A wants to message user B
	elif(input_msg.getId() == 80):
		sendMessage( input_msg.getMsg(), u, credentials )

	# user wants to broadcast a message
	elif(input_msg.getId() == 82):
		broadcastMsg( input_msg.getMsg(), u)

	# user wants to verify if a friend is online
	elif(input_msg.getId()== 88):
		friendAddr = input_msg.getMsg().split()
		friend = credentials[friendAddr[0]]
		# if IP or Port are different, send negative message
		if(friend.getIp != friendAddr[1] or int(friendAddr[2]) != friend.getPort() ):
			clientSock.send( msg.Message( 89, 'SERVER', input_msg.getSource(), 'Negative' ).toString() )
		else:
			clientSock.send( msg.Message( 89, 'SERVER', input_msg.getSource(), 'Affirmative' ).toString() )
	
	# user requestd logout
	elif(input_msg.getId() == 90):
		userLogout( input_msg.getSource() )

	# user sends a heartbeat
	elif(input_msg.getId() == 100):
		curUser.setHeartBeat()

	# if it is a message from a logged user
	if( input_msg.getId() != 10 ):
		# close connection
		replySock.close()
	
def getDictionary(credentials_file):
	myDict = {}
	for line in credentials_file:
		l = line.split()
		myDict[l[0]] = usr.User(l[0], l[1], '', '')

	return myDict

def getCredentials():
	# get the list of users
	credentials_file = open('credentials.txt', 'r')
	# put it in a dictionary to easier use
	credentials = getDictionary(credentials_file)
	#close the file
	credentials_file.close()

	return credentials

def init_chat(argv):
	# get the credentials from 'credentials.txt'
	credentials = getCredentials()
	serverSock = socket.socket()

	if( len(argv) != 2 ):
		print '\nUsage: python server.py <Port>'
		return
	port = int(argv[1])
	host = socket.gethostname()

	# bind the port where the server is going to listen
	serverSock.bind((host, port))
	serverSock.listen(MAX_USERS)
	
	# print the address to user connect
	print '\nSERVER ADDRESS:',socket.gethostbyname(host)

	while True:
		# waits for a client to connect
		clientSock, clientAddr = serverSock.accept()
		# waits for a message 
		try:
			client_msg = clientSock.recv(BUF_SIZE)
			client_msg = fromString(client_msg)
		except EOFError:
			continue
		# handle the user request
		handleMessage(client_msg, clientSock, credentials)
		# closes the cliente socket
		clientSock.close()

def main(argv):
	threadChat  = threading.Thread( target = init_chat, args = (argv,) )
	threadChat.daemon = True
	threadHeart = threading.Thread( target = heartBeat )
	threadHeart.daemon = True
	threadChat.start()
	threadHeart.start()

	while 1:
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			print '\nChat is over!'
			return
	
main(sys.argv)