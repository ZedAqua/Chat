#python3
# coding: utf-8
import time
from socket import *
from random import randint

# Define connection (socket) parameters
serverName = 'localhost'
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_DGRAM)

# Start sequence number randomly between 10000 and 20000
sequence_number = randint(10000, 20000)

rtts = []

# Send 20 pings to the server
for i in range(20):
    message = f"PING {sequence_number} {time.time()} CRLF"

    start_time = time.time()
    clientSocket.sendto(message.encode('utf-8'), (serverName, serverPort))

    clientSocket.settimeout(0.6)  # Set timeout to 600ms

    try:
        modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
        end_time = time.time()
        rtt = (end_time - start_time) * 1000  # Convert RTT to ms
        rtts.append(rtt)
        print(f"ping to {serverName}, seq = {sequence_number}, rtt = {rtt:.2f} ms")
    except timeout:
        print(f"ping to {serverName}, seq = {sequence_number}, time out")

    sequence_number += 1

if rtts:
    print(f"Minimum RTT: {min(rtts):.2f} ms")
    print(f"Maximum RTT: {max(rtts):.2f} ms")
    print(f"Average RTT: {sum(rtts) / len(rtts):.2f} ms")

clientSocket.close()
