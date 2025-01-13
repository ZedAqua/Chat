"""
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 TCPserver3.py localhost 12000
    coding: utf-8

    Author: Wei Song (Tutor for COMP3331/9331)
"""
from socket import *
from threading import Thread
import sys, select
import logging
import os
from datetime import datetime,timedelta
import time


if len(sys.argv)!=3:
    print()
    print("Usage: python server.py server_port number_of_consecutive_failed_attempts")
    sys.exit(1)

try:
    attempt_number = (sys.argv[2])
    if not attempt_number.isdigit():
        raise ValueError
    attempt_number = int(attempt_number)
    if attempt_number<1 or attempt_number >5:
        raise ValueError
except ValueError:
    print("Invalid number of allowed failed consecutive attempt: number. The valid value of argument number is an integer between 1 and 5")
    sys.exit(1)

block_until = {}    # username:block_end_time
cooldown_users = {} # username:attempts
active_users = {}
active_users_sequence_number = 0
group_chats = {}   # {groupname: {"members": [username1, username2, ...], "log_file": "GROUPNAME_messagelog.txt"}}
clients_id = {}
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)



#----------------------------------------------------------------------------------------
#userlog.txt
logger = logging.getLogger(__name__)
logging.basicConfig(filename='userlog.txt',level=logging.INFO,format='%(message)s')
if not os.path.exists("userlog.txt"):
    with open("userlog.txt", 'w') as f:
        pass  #
sequence_number = 0
def log_user_activity(sequence_number,username,client_ip,udp_port):
    timestamp = datetime.now().strftime('%d %b %Y %H:%M:%S')
    log_message = f"{sequence_number}; {timestamp}; {username}; {client_ip}; {udp_port}"
    logging.info(log_message)


# messagelog.txt
message_sequence_number = 0
if not os.path.exists("messagelog.txt"):
    with open("messagelog.txt", 'w') as f:
        pass  # 创建文件

def log_message_activity(message_sequence_number, username, message):
    timestamp = datetime.now().strftime('%d %b %Y %H:%M:%S')
    log_message = f"{message_sequence_number}; {timestamp}; {username}; {message}"
    with open("messagelog.txt", 'a') as f:
        f.write(log_message + "\n")

#----------------------------------------------------------------------------------------
"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
"""


class ClientThread(Thread):
    # Initialize the thread with client address and socket
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.username =None   # Username starts as None until set during login
        self.clientAlive = False   # Flag to keep track of client's connection status

        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True   # Mark the client as connected
#------------------------------------------------------------------------------------------------------
    def run(self):
        global clients_id
        message = ''

        while self.clientAlive:
            try:
                data = self.clientSocket.recv(1024)
                message = data.decode()

            except ConnectionResetError:
                # Handle cases where the client connection is reset unexpectedly
                self.clientAlive = False
                print("===== Connection reset by peer - ", self.clientAddress)
                if self.username in active_users:  #
                    self.handle_logout()
                break

            except Exception as e:
                print(f"===== An error occurred: {e} - ", self.clientAddress)
                break

            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if message == '':
                self.clientAlive = False
                print("===== the user disconnected - ", clientAddress)
                break

            # Handle different types of messages from the client
            if message == 'login':
                print("[recv] New login request")
                self.process_login()
            elif message == 'download':
                print("[recv] Download request")
                message = 'download filename'
                print("[send] " + message)
                self.clientSocket.send(message.encode())
            elif message.startswith("/msgto "):
                    print("[recv] Private message received.")
                    self.handle_msgto(message)
            elif message.startswith('/activeuser'):
                    print(f"[recv] {self.username} issued /activeuser command")
                    self.handle_activeuser_request()
            elif message =='/logout':
                    print(f'{self.username} logout')
                    self.handle_logout()
            elif message.startswith("/creategroup"):
                print(f'{self.username} issued /creategroup command')
                self.handle_creategroup(message)
            elif message.startswith("/joingroup"):
                print(f"{self.username} issued /joingroup command")
                self.handle_joingroup(message)
            elif message.startswith("/groupmsg"):
                print("[recv] groupmsg requested")
                self.handle_groupmsg(message)
            else:
                print("[recv] " + message)
                print("[send] Cannot understand this message")
                message = 'Cannot understand this message'
                self.clientSocket.send(message.encode())

    """  
        You can create more customized APIs here, e.g., logic for processing user authentication
        Each api can be used to handle one specific function, for example:
        def process_login(self):
            message = 'user credentials request'
            self.clientSocket.send(message.encode())
    """
#------------------------------------------------------------------------------------------------------
    def set_username(self, username):
        self.username = username
        clients_id[username] = self    # Set the username for the client and add to the global dictionary


    def handle_msgto(self, message):
        global message_sequence_number
        command, target_user, message_content = message.split(' ', 2)
        sender_username = self.username
        timestamp = datetime.now().strftime('%d %b %Y %H:%M:%S')
        formatted_message = f"\n{timestamp}, {sender_username}: {message_content}"
        # Check if target user is online and send the message
        if target_user in clients_id:
            target_client_thread = clients_id[target_user]
            try:
                target_client_thread.clientSocket.send(formatted_message.encode())
                # Log the message on the server console
                server_log_message = f"{timestamp}, {sender_username} message to {target_user}: \"{message_content}\""
                print(server_log_message)

            except Exception as e:
                print(f"Error sending message to {target_user}: {e}")
        else:
            self.clientSocket.send(f"User {target_user} not found or not online".encode())
        # Log the message to a file and send confirmation to the client
        message_sequence_number += 1
        with open("messagelog.txt", "a") as file:
            log_entry = f"{message_sequence_number}; {timestamp}; {target_user}; {message_content}\n"
            file.write(log_entry)
        confirmation = f" message sent at {timestamp}"
        self.clientSocket.send(confirmation.encode())


    def handle_logout(self):
        global active_users
        # Handle user logout logic...
        if self.username in active_users:
            removed_sequence = active_users[self.username]['sequence']  # Remove the user from the active_users dictionary
            del active_users[self.username]
            # Update the sequence numbers of remaining active users
            for user in active_users.values():
                if user['sequence'] > removed_sequence:
                    user['sequence'] -= 1
        # Notify the client about the logout and close the connection
        self.clientSocket.send(f' Bye, {self.username}!'.encode())
        self.clientAlive = False
        self.clientSocket.close()



    def handle_activeuser_request(self):
        global active_users
        # Compile and send active user information...
        active_users_info = [
            f"{user['sequence']}; {user['timestamp']}; {username}; {user['ip']}; {user['port']}"
            for username, user in active_users.items() if username != self.username
        ]
        print('Return message: ')
        # Print server-side information
        for username, user in active_users.items():
            if username != self.username:
                print(f"{username}, active since {user['timestamp']}")
        if not active_users_info:
            print("No other active users.")
            self.clientSocket.send("no other active user".encode())
        else:
            self.clientSocket.send("\n".join(active_users_info).encode())


    def handle_joingroup(self, command):
        parts = command.split()
        print('Return messages:')
        if len(parts) != 2:
            self.clientSocket.send(
                "Error: /joingroup command requires a group name.".encode())
            return

        groupname = parts[1]

        # check whether the group exist.
        if groupname not in group_chats:
            self.clientSocket.send(f"Error: Group chat (Name: {groupname}) does not exist.".encode())
            print(f'{self.username} tries to join to a group chat that does not exists.')
            return

        # check whether the users are initial members.
        if self.username not in group_chats[groupname]["members"]:
            self.clientSocket.send("Error: You were not added to this group chat.".encode())
            return

        # check whether the users join the group.
        if self.username in group_chats[groupname]["active_members"]:
            self.clientSocket.send(f"Error: You have already joined the group chat: {groupname}.".encode())
            return


        group_chats[groupname]["active_members"].add(self.username)

        # Get the information of other users.
        other_members = [member for member in group_chats[groupname]["members"] if member != self.username]
        other_members_str = ', '.join(other_members) if other_members else "No other members currently"
        # send the confirmation to client.
        self.clientSocket.send(f"You have joined the group chat: {groupname}".encode())
        print(
            f"Join group chat room successfully, room name: {groupname}, other users in this room: {other_members_str}")



    def handle_creategroup(self, command):

        parts = command.split()
        print('Return message:')
        if len(parts) < 3:
            self.clientSocket.send( "Please enter at least one more active users.".encode())
            print('Group chat room is not created.Please enter at least one more active users.')
            return

        groupname = parts[1]
        members = parts[2:]

        if self.username not in members:
            members.append(self.username)


        if not groupname.isalnum():
            self.clientSocket.send("Error: Group name must be alphanumeric.".encode())
            return

        if groupname in group_chats:
            self.clientSocket.send(f"Error: A group chat (Name: {groupname}) already exists.".encode())
            print(f'Groupname {groupname} already exists.')
            return


        for member in members:
            if member not in active_users:
                self.clientSocket.send(f"Error: User {member} is not valid or not online.".encode())
                return

       #create group_chats
        group_chats[groupname] = {
            "members": members,
            "active_members": set([self.username]),
            "log_file": f"{groupname}_messagelog.txt",
            "message_counter": 1  # 初始化消息计数器
        }

        with open(group_chats[groupname]["log_file"], 'w') as f:
            pass

        # reply to client
        success_message = f"Group chat room has been created, room name: {groupname}, initial users in this room: " + " ".join(
            members)
        self.clientSocket.send(success_message.encode())  # 将整个消息编码为bytes然后发送
        print(success_message)





    def handle_groupmsg(self, command):
        global group_chats
        parts = command.split(' ', 2)
        print('Return message:')
        if len(parts) < 3:
            self.clientSocket.send("Error: /groupmsg command requires a group name and a message.".encode())
            return

        groupname, message_content = parts[1], parts[2]

        # check if the group exists.
        if groupname not in group_chats:
            self.clientSocket.send("Error: The group chat does not exist.".encode())
            print('The group chat does not exist.')
            return

        # check if the user is member of group chat.
        if self.username not in group_chats[groupname]["members"]:
            self.clientSocket.send("Error: You are not a member of this group chat.".encode())
            print(f'{self.username} is not a member of {groupname}.')
            return

        # check whether the users joined in the group
        if self.username not in group_chats[groupname]["active_members"]:
            self.clientSocket.send("Please join the group before sending messages.".encode())
            print(f'{self.username} sent a message to a group chat, but {self.username} has not been joined to the group.')
            return

        # record the group message.
        timestamp = datetime.now().strftime('%d %b %Y %H:%M:%S')
        message_number = group_chats[groupname]["message_counter"]
        log_message = f"{message_number}; {timestamp}; {self.username}; {message_content}"
        print(f'{self.username} issued a message in group chat {groupname} : {log_message}')
        with open(group_chats[groupname]["log_file"], 'a') as f:
            f.write(log_message + "\n")

        # update the number
        group_chats[groupname]["message_counter"] += 1

        # reply to client
        self.clientSocket.send(f"Your message to group {groupname} has been sent.\n".encode())

        # send the group message to other users in group chat.
        for member in group_chats[groupname]["active_members"]:
            if member != self.username:
                try:
                    member_thread = clients_id.get(member)
                    if member_thread:  # check whether users online.
                        member_thread.clientSocket.send(
                            f"Group {groupname}: {self.username} says: {message_content}\n".encode())
                except Exception as e:
                    print(f"Error sending message to {member}: {e}")



    def process_login(self):
     global attempt_number
     global active_users_sequence_number
     message = 'user credentials request'
     print('[send] ' + message);
     self.clientSocket.send(message.encode())

     # authenticate
     def authenticate(username, password):
            """
               Authenticate a user based on their username and password against the credentials.txt file.
               """
            with open("credentials.txt", "r") as file:
                for line in file:
                    credentials_username, credentials_password = line.strip().split()
                    if username == credentials_username and password == credentials_password:
                        return True  # Authentication successful
            return False  # Authentication failed

     while True:
        data = self.clientSocket.recv(1024)
        credentials = data.decode()
        username, password = credentials.split(':')

        if username in block_until and datetime.now() > block_until[username]:
            del block_until[username]
            cooldown_users[username] = attempt_number
        blocked_time = block_until.get(username)
        if blocked_time and datetime.now()< blocked_time:
            response ='Your account is blocked due to multiple login failures. Please try again later'
            self.clientSocket.send(response.encode())
            print('[send] ' + response);
            return

        # Authenticate the user
        if authenticate(username, password):
            global sequence_number
            response = "Welcome to TESSENGER!"
            self.clientSocket.send(response.encode())
            self.set_username(username)
            sequence_number += 1
            udp_port = self.clientSocket.recv(1024).decode()
            client_ip = self.clientSocket.recv(1024).decode()
            log_user_activity(sequence_number, username, client_ip, udp_port)
            timestamp = datetime.now().strftime('%d %b %Y %H:%M:%S')
            #  active_user list
            active_users_sequence_number +=1
            active_users[self.username] = {
                "sequence": sequence_number,
                "timestamp": timestamp,
                "ip":    client_ip,
                "port":  udp_port
            }
            attempt_number = int(sys.argv[2])
            cooldown_users[username] = attempt_number
            print(f"{self.username} is online .")
            break
        else:
            remaining_attempts = cooldown_users.get(username,attempt_number)-1
            cooldown_users[username] = remaining_attempts
            print(remaining_attempts)
            # if attempt number comes to 0,block the User.
            if remaining_attempts ==0 :
                block_until[username] = datetime.now()+ timedelta(seconds = 10)
                response = 'Invalid Password. Your account has been blocked. Please try again later'
                self.clientSocket.send(response.encode())
                print('[send] ' + response);
                break
            else:
                response ="Invalid Password. Please try again"
                print('[send] ' + response);
                self.clientSocket.send(response.encode())


print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")
active_users.clear()  #clear the list when server close.
# Main server loop
while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()