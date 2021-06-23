#code inspiration from https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/

import socket
import select

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234

# We first create a socket
# socket.AF_INET - address family, IPv4
# socket.SOCK_STREAM - TCP, conection-based
# socket.SOCK_DGRAM - UDP, connectionless, datagrams
# socket.SOCK_RAW - raw IP packets
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# We bind so that the operating system gets informed by the server that it's going to use given IP and port
# Using 0.0.0.0 on a server indicates that it will listen on all accessible interfaces, which is beneficial for connecting locally to 127.0.0.1 and remotely to the LAN interface IP.
server_socket.bind((IP, PORT))

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR to 1 on socket as a socket option
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# List of sockets for select.select()
sockets_list = [server_socket]

# Makes the server listen to new connections
server_socket.listen()

# The socket is used as a key, and the user header and name are used as data in a list of connected clients.
clients = {}

print(f'Listening for connections on {IP}:{PORT}...')

# Handles message receiving
def message_get(client_socket):

    try:

        # Receive a "header" containing the length of the message, which is defined and constant.
        message_header = client_socket.recv(HEADER_LENGTH)

        # Client gently ended a connection if no data was received, for example using socket. socket.shutdown(socket.SHUT RDWR) or close()
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:

        # If we're here, the client either forcibly ended the connection (for example, by pressing ctrl+c on their script) or just lost the connection socket. socket is also invoked by close(). 
        # socket.shutdown(socket.SHUT RDWR) transmits information about closing the socket (shutdown read/write), and it's also one of the reasons why we get an empty message.
        return False

while True:

    # Calls Unix select() system call or Windows select() WinSock call with three parameters:
    #   - rlist - sockets to be monitored for incoming data
    #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
    #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
    # Returns lists:
    #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
    #   - writing - sockets ready for data to be send thru them
    #   - errors  - sockets with some exceptions
    # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)


    # notified sockets iterated over
    for notified_socket in read_sockets:

        # If notified socket is a server socket, accept new connection
        if notified_socket == server_socket:

            # This creates a new socket - a client socket that is only connected to this specific client and is unique to that client.
            # The other object returned is ip/port set.
            client_socket, client_address = server_socket.accept()

            # Client should give their name as soon as possible, and it should be received
            user = message_get(client_socket)

            # If False, the client disconnected before sending their name.
            if user is False:
                continue

            # Accepted socket is added to select.select() list
            sockets_list.append(client_socket)

            # Saves username and username header
            clients[client_socket] = user

            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))

        # Else existing socket is sending a message
        else:

            # Receive message
            message = message_get(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Removed from list of users
                del clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            # Iterate over the clients who are connected and send out a message.
            for client_socket in clients:

                # However, we do not send it back to the sender.
                if client_socket != notified_socket:

                    # Send a message to the user (both with their headers)
                    # We're reusing the sender's message header and saving the user's username header from when he connected.
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

    # This isn't absolutely necessary, but it will handle some socket exceptions just in case.
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]