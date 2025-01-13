# **Messenger Application**

## **Project Overview**

This project implements a client-server-based messaging application inspired by platforms like Messenger and WhatsApp. The application allows multiple clients to connect to a server for real-time messaging and peer-to-peer video file sharing using TCP and UDP protocols. Key functionalities include authentication, private messaging, group chat, active user listing, and peer-to-peer video file transfer.

---

## **Features**

### **1. Authentication**

- Users must log in with valid credentials stored in `credentials.txt`.
- Accounts are blocked for 10 seconds after a specified number of failed login attempts (configurable via command-line arguments).

### **2. Private Messaging**

- Send direct messages to other active users.
- Messages are logged in `messagelog.txt` with timestamps.

### **3. Group Chat**

- Create unique group chat rooms and invite other active users.
- Send messages within a group.
- Group activities are logged in group-specific log files (e.g., `GROUPNAME_messagelog.txt`).

### **4. Active User Listing**

- View the list of active users with details such as IP address and UDP port (for CSE students).

### **5. Peer-to-Peer Video File Sharing (CSE Students Only)**

- Transfer video files between clients using UDP.
- File transfers include metadata like the sender’s username and file name.

---

## **File Structure**

### **Server**

- **File**: `Server.py`
- **Description**: Handles client connections, authentication, logging, and managing group chat and private messaging functionalities.

### **Client**

- **File**: `Client.py`
- **Description**: Provides a command-line interface for users to interact with the server and perform various actions like sending messages, joining groups, and transferring files.

### **Log Files**

- `userlog.txt`: Logs user activity (login/logout, IP, UDP port).
- `messagelog.txt`: Logs private and group messages with timestamps.
- `GROUPNAME_messagelog.txt`: Logs messages specific to a group.

---

## **Usage Instructions**

### **1. Prerequisites**

- Python 3.9 or higher.
- Ensure `credentials.txt` exists in the same directory as the server.
- Install required libraries:
  ```bash
  pip install socket threading
  ```

### **2. Starting the Server**

Run the server with the following command:

```bash
python Server.py <server_port> <number_of_consecutive_failed_attempts>
```

- `server_port`: Port for server to listen on (e.g., 12000).
- `number_of_consecutive_failed_attempts`: Integer (1-5) specifying allowed failed login attempts before blocking a user.

Example:

```bash
python Server.py 12000 3
```

### **3. Starting the Client**

Run the client with the following command:

```bash
python Client.py <server_IP> <server_port> <udp_port>
```

- `server_IP`: IP address of the server (e.g., `127.0.0.1` for localhost).
- `server_port`: Port the server is listening on (same as above).
- `udp_port`: Port the client will use for UDP communication.

Example:

```bash
python Client.py 127.0.0.1 12000 13000
```

### **4. Available Commands**

- **`/msgto <username> <message>`**: Send a private message to a user.
- **`/activeuser`**: List active users.
- **`/creategroup <groupname> <username1> <username2>`**: Create a group chat.
- **`/joingroup <groupname>`**: Join an existing group chat.
- **`/groupmsg <groupname> <message>`**: Send a message to a group chat.
- **`/p2pvideo <username> <filename>`**: Transfer a video file to another user (UDP, CSE only).
- **`/logout`**: Log out.

---

## **Sample Workflow**

1. **Starting the Server**:

   ```bash
   python Server.py 12000 3
   ```

2. **Starting a Client**:

   ```bash
   python Client.py 127.0.0.1 12000 13000
   ```

3. **Client Commands**:
   - **Login**:
     ```
     Username: Yoda
     Password: comp9331
     ```
   - **Private Message**:
     ```
     /msgto Obi-Wan Hello there!
     ```
   - **List Active Users**:
     ```
     /activeuser
     ```
   - **Group Chat**:
     ```
     /creategroup JediOrder Obi-Wan Anakin
     /groupmsg JediOrder May the Force be with you.
     ```
   - **Video Transfer**:
     ```
     /p2pvideo Obi-Wan lecture.mp4
     ```
   - **Logout**:
     ```
     /logout
     ```

---

## **Notes**

- Ensure log files have write permissions (`chmod +w`).
- The server should be started before any clients connect.
- Video file transfer uses UDP for low latency.
- Test the application on a reliable network to ensure accurate performance.

---

## **Author**

This project was implemented as part of the COMP9331/3331 course by Patrick.

---

For additional support or queries, please contact via GitHub repository: [Repository Link].
