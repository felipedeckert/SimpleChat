import sys
import socket
import message as msg
import cPickle as pickle
import threading
import time
import user as usr

# buffer size to receive a message
BUF_SIZE  = 2048
# time between heart beats
TIME_BEAT = 30
finishEvent = threading.Event()

# list of user who I have addr
myFriends = []

def heartBeat(host, port, username):
	while( not finishEvent.isSet() ):
		try:
			beatSock = socket.socket()
			beatSock.connect( (host, port) )
			beatSock.send( msg.Message(100, username, 'SERVER', 'Im alive').toString() )
			beatSock.close()
			time.sleep( TIME_BEAT )
		except KeyboardInterrupt:
			return

def login(serverSock, clientPort):
	request = msg.Message(10, socket.gethostname(), 'SERVER', clientPort).toString()
	# send login request
	serverSock.send(request)
	# wait for response
	
	in_id   = -1
	error   = False
	my_user = ''
	first   = True 
	# while user do not succed or get/is blocked
	while(True):
		
		reply = serverSock.recv(BUF_SIZE)
		reply = pickle.loads(reply)

		in_id = reply.getId()	
		# print server message
		print reply.getMsg()
		# check if it was successful login
		if(in_id == 12):
			return my_user
		# check if user is blocked
		elif(in_id == 40 or in_id == 41):
			return ''
		# check if it was an invalid login
		if(in_id == 30 or in_id == 31):
			error = True
		# if was invalid, ask credentials again
		if( error ):
			reply = serverSock.recv(BUF_SIZE)
			reply = pickle.loads(reply)

			in_id = reply.getId()	
			# print server message
			print reply.getMsg()
			error = False

		# get user input
		output = raw_input()
		
		# set id of outgoing message
		if(in_id == 20):
			out_id = 21
			my_user = output
		else:
			out_id = 23
		# send message to server
		serverSock.send(msg.Message(out_id, 'USER', 'SERVER', output).toString())

def incomingMessages(clientSock):
	#print '\nINCOMING'
	msg_id = 0

	while( msg_id != 91 and not finishEvent.isSet() ): # ):
		# waits to server to connect
		serverSock, serverAddr = clientSock.accept()
		# receive message
		server_msg = serverSock.recv(BUF_SIZE)
		if(server_msg == '' or server_msg is None):
			continue
		# from String to object
		server_msg = pickle.loads(server_msg)
		# get the ID
		msg_id = server_msg.getId()

		# if is a address requested, save it
		if( msg_id == 71 ):
			splitted = server_msg.getMsg().split()
			myFriends.append( usr.User(splitted[0], 'NULL', splitted[2], int(splitted[4])) )
		# print message
		print( server_msg.getMsg() )
		# close connection
		serverSock.close()
		if( msg_id == 13 ):
			# set evento to stop threads
			finishEvent.set()
			break

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

# this functions is running in one thread and is  
# responsible for sending messages to the server
def outgoingMessages(host, port, my_user):
	output = ['init']
	commands = ['private','getaddress', 'logout', 'unblock', 'block', 'online', 'broadcast', 'message']
	while( output[0] != 'logout' and not finishEvent.isSet() ):
		try:
			# get client input
			try:
				output = raw_input().split()
			except EOFError:
				return
			# invalid command
			if(output[0] not in commands):
				print '\nUnknown command.'
				continue
			# create and connect to the server
			serverSock = socket.socket()
			serverSock.connect((host, port))
			
			# get source and destination IP address
			source = my_user
			dest   = 'SERVER'

			if(output[0] == 'message'):
				if(len(output) < 3):
					print '\nInvalid number of arguments.\nUsage: message <user> <message>'
					continue
				outMsg = toPhrase(output[2:])
				serverSock.send( msg.Message(80, source, dest, output[1]+' '+outMsg).toString() )

			elif(output[0] == 'broadcast'):
				if(len(output) == 1):
					print '\nInvalid number of arguments.\nUsage: broadcast <message>'		
					continue
				broadMsg = toPhrase(output[1:])
				serverSock.send( msg.Message(82, source, dest, broadMsg).toString() )

			elif(output[0] == 'online'):
				if(len(output) != 1):
					print '\nInvalid number of arguments.\nUsage: online'
					continue
				serverSock.send( msg.Message(50, source, dest, 'online').toString() )

			elif(output[0] == 'block'):
				if(len(output) != 2):
					print '\nInvalid number of arguments.\nUsage: block <user>'
					continue
				serverSock.send( msg.Message(60, source, dest, output[1]).toString() )

			elif(output[0] == 'unblock'):
				if(len(output) != 2):
					print '\nInvalid number of arguments.\nUsage: unblock <user>'
					continue
				serverSock.send( msg.Message(61, source, dest, output[1]).toString() )

			elif(output[0] == 'logout'):
				if(len(output) != 1):
					print '\nInvalid number of arguments.\nUsage: logout'
					continue
				serverSock.send( msg.Message(90, source, dest, 'logout').toString() )
				# set event to finish all threads
				finishEvent.set()

			elif(output[0] == 'getaddress'):
				if(len(output) != 2):
					print '\nInvalid number of arguments.\nUsage: getaddress <user>'
					continue
				serverSock.send( msg.Message(70, source, dest, output[1]).toString() )

			elif(output[0] == 'private'):
				if(len(output) < 3):
					print '\nInvalid number of arguments.\nUsage: private <user> <message>'
					continue
				target = None
				for user in myFriends:
					if(user.getUsername() == output[1]):
						target = user
				# if you do not have the addr to the user
				if(target is None):
					print '\nYou do not have the address to private message this user.'
					continue
				# is the user online? Has he changed his addr?
				serverSock.send( msg.Message(88, source, dest, target.getUsername()+' '+target.getIp()+' '+str(target.getPort()) ).toString() )
				answer = serverSock.recv(BUF_SIZE)
				if(answer == 'Negative'):
					print'\nUnable to contact user, s/he might have gone offline or changed address.'
					continue
				try:
					friendSock = socket.socket()
					friendSock.connect((target.getIp(), target.getPort()))
					outMsg = toPhrase(output[2:])
					friendSock.send( msg.Message(81, source, target.getUsername(), source+': '+outMsg).toString() )
					friendSock.close()
				except socket.error:
					print'\nUnable to contact user, s/he might have gone offline or changed address.'

			# close connection
			serverSock.close()
		except KeyboardInterrupt:
			return

def main(argv):
	if( len(argv) != 3 ):
		print '\nUsage: python client.py <IP> <Port>'
		return

	serverSock = socket.socket()
	clientSock = socket.socket()

	# bind to a random available port
	clientSock.bind((socket.gethostname(), 0))

	# get the port
	clientPort = clientSock.getsockname()[1]

	# client will only listen to the server
	clientSock.listen(1)

	host = argv[1]
	port = int(argv[2])

	serverSock.connect((host, port))
	my_user = login(serverSock, clientPort)
	# if the login was unsuccessful
	if(my_user == ''):
		sys.exit(0)
	#close connection after successful login
	serverSock.close()

	InThread  = threading.Thread(target = incomingMessages, args = (clientSock,))
	InThread.daemon = True
	OutThread = threading.Thread(target = outgoingMessages, args = (host, port, my_user))
	OutThread.daemon = True
	HeartThread = threading.Thread(target = heartBeat, args = ( host, port, my_user ) )
	HeartThread.daemon = True
	InThread.start()
	OutThread.start()
	HeartThread.start()

	while 1 and OutThread.is_alive():
		try:
			time.sleep(1)
			if( not InThread.is_alive() ):
				return
		except KeyboardInterrupt:
			print '\nYou pressed CTRL+C\nClosing chat...'

main(sys.argv)