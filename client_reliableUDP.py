#                                                                    #
# #                                                                # #
# # #                                                            # # #
# # #  RELIABLE UDP (CLIENT PROGRAM)                             # # #
# # #  BY: ZAIN AMIR ZAMAN, KHAN MOEEN DANISH                    # # #
# # #                                                            # # #
# #                                                                # #
#                                                                    #

import socket
import time
import os  # Needed for os.path.getsize() to get size of file

# # #  GLOBAL VARIABLES  # # #

server_ip = "127.0.0.1"
server_port = 50000
fragment_size = 500  # In bytes
window_size = 10  # In frames (for SRP)
time_out = 4  # Default time out for packets (in seconds)
file_name = "sound_file.mp4"

global sender_data_buffer, sender_index_buffer, time_out_tries, seq_num, cont_iter_last, cont_iter_timeout, max_time_out_tries

# # #  ERROR SIMULATION SWITCHES  # # #

sim_packet_loss = False  # Switch on to incur loss of one packet in each window
packets_lost = [12, 55]  # Packets to simulate as lost

# # #  FUNCTIONS  # # #

# Receive, display and return server message
def get_response():
    try:
        rec_msg = UDP_socket.recvfrom(fragment_size)
        print "Server response: %s" % rec_msg[0]
        return rec_msg[0]
    except:
        return "TIMEOUT"

# Display window and and reset variables for subsequent windows
def process_final_window_packet():
    global sender_data_buffer, sender_index_buffer, time_out_tries, seq_num, cont_iter_last, cont_iter_timeout, max_time_out_tries

    # Show index buffer
    print "Sent packet indices: " + str(sender_index_buffer)
    print "Waiting for server acknowledgment..."

    server_response = get_response()

    if server_response == "ACK_ALL":

        # Reset time-out tries
        if time_out_tries != 0:
            time_out_tries = 0

        # Reset sequence number and buffers
        seq_num = 0
        sender_data_buffer = []
        sender_index_buffer = []

        # Reset extra iterations
        cont_iter_last = False
        if cont_iter_timeout:
            cont_iter_timeout = False

    elif server_response[0:4] == "NACK":
        index_of_packet_not_received = server_response[4:]  # Getting the index number of lost packet
        print "Packet Number #" + str(index_of_packet_not_received) + " was lost. Resending the lost packet"  # Displaying which packets to resend.
        seq_of_packet_not_received = int(index_of_packet_not_received) % window_size  # Taking remainder by window size so index number is converted to sequence number.
        UDP_socket.sendto(sender_data_buffer[int(seq_of_packet_not_received)], (server_ip, server_port))  # Resending the lost packet.

    elif server_response == "TIMEOUT":  # When server response is not received
        cont_iter_timeout = True
        # Retransmit packet until tries run out
        if time_out_tries < max_time_out_tries:
            time_out_tries += 1
            print "Request timed-out. Requesting acknowledgement again... (Tries left: %i/%i)" % (max_time_out_tries - time_out_tries, max_time_out_tries)
            UDP_socket.sendto("REQ_ACK", (server_ip, server_port))
        else:
            if cont_iter_last:
                cont_iter_last = False
            cont_iter_timeout = False
            print "Server is not responding."
            return True
    return False


# # #  MAIN PROGRAM  # # #

print "\n** UDP CLIENT PROGRAM **"

# Create UDP socket and establish connection
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.settimeout(time_out)  # Set default time-out

print "\nConnecting to UDP server %s:%s..." % (server_ip, server_port)

# Send connection request
UDP_socket.sendto("CONN_REQ", (server_ip, server_port))
print "Waiting for server response..."

server_response = get_response()
if server_response == "ACK":
    print "Connection established!"
    print "\nEnter 0 to send " + file_name + " to server.\nEnter 1 to terminate connection.\n"

    while True:
        UDP_socket.sendto("REQ_TO_SEND", (server_ip, server_port))  # Ask for transfer permission

        server_response = get_response()
        if server_response == "ACK":
            print "Sending " + file_name + "..."
            print "Fragment size: %i bytes" % fragment_size
            print "Window size: %i packets" % window_size
            file_size = os.path.getsize("sound_file.mp4")
            print "File size: " + str(file_size) + " bytes"

            # Send window size for verification
            UDP_socket.sendto(str(window_size), (server_ip, server_port))
            server_response = get_response()
            if server_response == "NACK":
                print "File transfer failed! Window sizes do not match."
                break

            # # #  START FILE TRANSFER  # # #

            f = open("sound_file.mp4", "rb")
            data = f.read(fragment_size)

            packet_num = -1  # Packet index
            final_packet = int(file_size / fragment_size)  # Index of final packet
            seq_num = 0  # Sequence number in a given window (resets each time window slides)
            sender_data_buffer = []  # Stores data for a given window
            sender_index_buffer = []  # Stores indices for the data buffer
            time_out_tries = 0  # Number of tries left until client shuts down in wait of server response
            cont_iter_last = False  # Allows an extra iteration for the last window
            cont_iter_timeout = False  # Required in case last packet reaches time-out
            max_time_out_tries = 3  # Maximum tries allowed for re-transmission

            # Transfer loop
            while data or cont_iter_last or cont_iter_timeout:
                if cont_iter_last:  # Runs for last window
                    if process_final_window_packet():
                        break

                else:
                    if seq_num < window_size:
                        if sim_packet_loss and (packet_num == packets_lost[0]-1 or packet_num == packets_lost[1]-1):
                            packet_num += 1
                            seq_num += 1

                            data = f.read(fragment_size)
                            sender_data_buffer.append(data)  # Save packet data in buffer
                            sender_index_buffer.append(packet_num)  # Save packet index in buffer

                            time.sleep(0.02)  # Allow server to receive file
                        else:
                            if UDP_socket.sendto(data, (server_ip, server_port)):
                                packet_num += 1
                                seq_num += 1

                                data = f.read(fragment_size)
                                sender_data_buffer.append(data)  # Save packet data in buffer
                                sender_index_buffer.append(packet_num)  # Save packet index in buffer

                                time.sleep(0.02)  # Allow server to receive file

                                # Send packet number
                                if packet_num == final_packet:
                                    msg = "F" + str(packet_num)  # "F" denotes FINAL PACKET
                                    UDP_socket.sendto(msg, (server_ip, server_port))
                                    cont_iter_last = True
                                else:
                                    msg = "N" + str(packet_num)  # "N" denotes NOT FINAL PACKET
                                    UDP_socket.sendto(msg, (server_ip, server_port))

                    else:  # Runs when final packet in window is sent...
                        if process_final_window_packet():
                            break

            # # #  END FILE TRANSFER  # # #

        elif server_response == "NACK":
            print "Request denied! Establish connection with server before file transfer."

        break
else:
    print "Connection failed. Try again."

# Close socket
print "Shutting down client."
UDP_socket.close()