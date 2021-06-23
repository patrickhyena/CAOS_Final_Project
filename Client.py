import socket
import select
import errno

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234
my_username = input("Username: ")

#We first create a socket
# socket.AF_INET - address family, IPv4
# socket.SOCK_STREAM - TCP, conection-based
# socket.SOCK_DGRAM - UDP, connectionless, datagrams
# socket.SOCK_RAW - raw IP packets
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#We connect the client to the given IP and PORT
client_socket.connect((IP, PORT))

# Set the connection to the non-blocking state, so when .recv() call happen it won't block. It will just return some exception
client_socket.setblocking(False)

# Prepare and send the username and header
# We need to encode the username to bytes. And then we count number of bytes and  prepare header of fixed size so we can encode to it to bytes as well
username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)

while True:

    # user will input the message
    message = input(f'{my_username} > ')

    # Check if the message is empty or not, if its not empty send it
    if message:

        # Prepare the header and convert the header into bytes, for example : username
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)

    try:
        # Now we loop over the received messages and it can be more than one
        while True:

            # Get our header containing username length and its size is defined and constant
            username_header = client_socket.recv(HEADER_LENGTH)

            # If we didn't receive any data the server will close its connection, server close its connection for example using socket.close() or socket.shutdown(socket.SHUT RDWR)
            if not len(username_header):
                print('Connection closed by the server')
                sys.exit()

            # Convert the header into int value
            username_length = int(username_header.decode('utf-8').strip())

            # Receive the username and decode it
            username = client_socket.recv(username_length).decode('utf-8')

            # We do the same for message, as we receive username we will receive the whole message so there is no need to check if it has any length
            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            # Print message
            print(f'{username} > {message}')

    except IOError as e:
        # Its normal on non blocking connections, and when there are no incoming data error its going to be raised
        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
        # We are going to check for error using AGAIN and WOULDBLOCK if one of them expected it means no data is coming
        # If we get neither AGAIN and WOULDBLOCK error code or something else happen the code below will run
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

        # If we did not receive anything
        continue

    except Exception as e:
        # Other exception or something happen it will exit
        print('Reading error: '.format(str(e)))
        sys.exit()