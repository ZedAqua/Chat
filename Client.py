"""
    Python 3
    Usage: python3 TCPClient3.py localhost 12000
    coding: utf-8

    Author: Wei Song (Tutor for COMP3331/9331)
"""
from socket import *
import sys
from threading import Thread
import queue
import re
import socket
import os

# Server would be running on the same host as Client
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT UDP_PORT ======\n")
    exit(0)
serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
udpPort = int(sys.argv[3])
serverAddress = (serverHost, serverPort)
udp_socket = socket.socket(AF_INET,SOCK_DGRAM)
udp_socket.bind(('127.0.0.1', udpPort))

# create a queue to save the message from server.
messages_queue = queue.Queue()
# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket.socket(AF_INET, SOCK_STREAM)
# build connection with the server and send message to it
clientSocket.connect(serverAddress)
user_status = {}  # Format: {username: (ip, port)}
running = True
udp_running = True
print('Please login')
#--------------------------------------------------------------------------------------------
def receive_messages(socket):
    global running
    while running:
        try:
            message = socket.recv(1024).decode()
            if message:
                # match the format of msgto.
                private_msg_match = re.match(r"\s*\d{2} \w+ \d{4} \d{2}:\d{2}:\d{2}, (.*?): (.*)", message)
                # match the format of groupmsg.
                group_msg_match = re.match(r"Group (\w+): (.*?) says: (.*)", message)

                if private_msg_match:
                    username, content = private_msg_match.groups()
                    print(message)
                elif group_msg_match:
                    groupname, username, content = group_msg_match.groups()
                    print(message)
                else:
                    messages_queue.put(message)
            else:
                break
        except OSError:
            break


# send_file function adjusted to use the global udp_socket
def send_file(presenter_username, audience_username, filename, audience_address, audience_port):
    global udp_socket
    if not os.path.exists(filename):
        print(f"File {filename} does not exist.")
        return
    # No need to create a new socket, use the global udp_socket instead
    # Send the information about the user and the file name as the start of the file transfer
    start_of_file_marker = "START_OF_FILE"
    info_message = f"{start_of_file_marker},{presenter_username},{filename}"
    udp_socket.sendto(info_message.encode(), (audience_address, audience_port))
    # Read and send the file content
    with open(filename, "rb") as file:
        while True:
            bytes_read = file.read(1024)
            if not bytes_read:
                # End of file
                break
            udp_socket.sendto(bytes_read, (audience_address, audience_port))
    # Send the end of file marker
    end_of_file_marker = "END_OF_FILE"
    udp_socket.sendto(end_of_file_marker.encode(), (audience_address, audience_port))

    print(f"File {filename} has been sent to {audience_username}.")




# receive_file function adjusted to use the global udp_socket
def receive_file():
    global udp_socket,udp_running
    while udp_running:


        try:
            # Receive the information about the file

            data, address = udp_socket.recvfrom(1024)
            # Check if this is the end of file marker or start of file marker
            message = data.decode('utf-8')  # Try to decode the data as utf-8
            if message.startswith("START_OF_FILE"):
                _, presenter_username, filename = message.split(',')
                # Maintain the original file extension
                original_extension = os.path.splitext(filename)[1]
                save_filename = f"{presenter_username}_{os.path.splitext(filename)[0]}{original_extension}"
                file = open(save_filename, "wb")  # Open the file to write binary data
            elif message == "END_OF_FILE":
                file.close()  # Close the file as we have finished writing data
                print(f"A file has been received from {presenter_username} and saved as {save_filename}")
                continue  # Continue to the next iteration of the loop to wait for new files
        except UnicodeDecodeError:
            # If a UnicodeDecodeError occurs, this means the data is binary and should be written directly to the file
            if 'file' in locals():
                file.write(data)
        except OSError as e:
                if e.winerror == 10038:
                    break
                else:
                    raise
#-------------------------------------------------------------------------------------------
while True:
    message = input("===== Please type any message you want to send to server: =====\n")
    clientSocket.sendall(message.encode())

    # receive response from the server
    # 1024 is a suggested packet size, you can specify it as 2048 or others
    data = clientSocket.recv(1024)
    receivedMessage = data.decode()

    # parse the message received from server and take corresponding actions
    if receivedMessage == "":
        print("[recv] Message from server is empty!")
    elif receivedMessage == "user credentials request":
     print("[recv] You need to provide username and password to login")
     login_success = False  #Mark whether login success.
     while not login_success:
        username = input('Username: ')
        password = input('Password: ')
        # Create the credentials message in the format "username:password"
        credentials_msg = f"{username}:{password}"
        clientSocket.send(credentials_msg.encode())
        # Wait and receive the response for the login attempt
        login_response = clientSocket.recv(1024).decode()
        print("[recv]", login_response)  # Display the result to the user

        if "Welcome" in login_response:
            host, udp_port = udp_socket.getsockname()
            clientSocket.send(str(udpPort).encode())
            clientSocket.send(str(host).encode())
            login_success = True  # Mark True if login successfully.
            break
        elif "blocked" in login_response:
            break
        elif "Invalid Password" in login_response:
            continue  # If password is invalid, continue asking for credentials

    elif receivedMessage == "download filename":
        print("[recv] You need to provide the file name you want to download")

    else:
        print("[recv] Message makes no sense")
    if login_success:
       break
receive_messages_thread = Thread(target=receive_messages, args=(clientSocket,))
receive_messages_thread.start()
receive_file_thread = Thread(target=receive_file)
receive_file_thread.start()
#-----------------------------------------------------------------------------------------------------------------
while True:

    command_input = input('Enter one of the following commands(/msgto, /activeuser, ...):')
    if command_input.startswith("/msgto "):
        parts = command_input.split(' ', 2)
        if len(parts) < 3 or not parts[1].strip():
            print("Error: /msgto command requires a username and a message.")
            continue
        clientSocket.send(command_input.encode())

        try:
            confirmation = messages_queue.get(timeout=20)
            print('[recv] ' + confirmation)
        except queue.Empty:
            print("[recv] No confirmation received from server.")

    elif command_input == '/activeuser':
        clientSocket.send(command_input.encode())
        try:

            response = messages_queue.get(timeout=20)
            if response.strip():
             print("[recv] Active users:\n" + response)
             user_status.clear()  # clear the original status info.
             users_info = response.strip().split('\n')
             for user_info in users_info:
                 user_detail = user_info.split(';')
                 if len(user_detail) == 5:
                     _, _, username, ip, port = user_detail
                     user_status[username.strip()] = (ip.strip(), int(port.strip()))
            else:
              pass
        except queue.Empty:
             print("[recv] No response received from server.")

    elif command_input =='/logout':

        clientSocket.send(command_input.encode())

        try:

            response = messages_queue.get(timeout=20)
            print(response)
        except queue.Empty:
             print("[recv] No response received from server.")
        running = False  # terminate the thread.
        break  # break the loop,prepare to terminate the client.

    elif command_input.startswith('/creategroup'):
        parts = command_input.split()

        if len(parts) < 2:
            print("Error: /creategroup command requires a groupname and optionally usernames.")
            continue
        clientSocket.send(command_input.encode())

        try:
            confirmation = messages_queue.get(timeout=20)
            print('[recv] ' + confirmation)
        except queue.Empty:
            print("[recv] No confirmation received from server.")

    elif command_input.startswith('/p2pvideo'):

        parts = command_input.split(' ', 2)
        if len(parts) != 3:
            print("Error: /p2pvideo command requires a username and a filename.")
            continue

        target_username, filename = parts[1], parts[2]

        if target_username not in user_status:
            print(f"Error: No active user {target_username} found.")
            continue

        target_address = user_status[target_username]   #get the target users'information.
        presenter_username =username
        audience_username  =target_username
        audience_address   =target_address[0]
        audience_port      =target_address[1]
        send_file(presenter_username, audience_username, filename, audience_address, audience_port)


    elif command_input.startswith('/joingroup'):
        parts = command_input.split()
        if len(parts)<2:
            print('Error,/joingroup command need groupname')
            continue
        else:
            clientSocket.send(command_input.encode())
        try:

            confirmation = messages_queue.get(timeout=20)
            print('[recv] ' + confirmation)
        except queue.Empty:
            print("[recv] No confirmation received from server.")


    elif command_input.startswith('/groupmsg'):

        parts = command_input.split(' ', 2)
        if len(parts) < 3 or not parts[1].strip():
            print("Error: /groupmsg command requires a group name and a message.")
            continue

        clientSocket.send(command_input.encode())

        try:
            confirmation = messages_queue.get(timeout=20)
            print('[recv] ' + confirmation)
        except queue.Empty:
            print("[recv] No confirmation received from server.")
    else:
        print(' Error.Invalid command!')

#-------------------------------------------------------------------------------------------------------------------
# close the socket
udp_running = False
clientSocket.close()
udp_socket.close()
receive_messages_thread.join()
receive_file_thread.join()

