#                                                                    #
# #                                                                # #
# # #                                                            # # #
# # #  RELIABLE UDP (SERVER PROGRAM)                             # # #
# # #  BY: ZAIN AMIR ZAMAN (237677), KHAN MOEEN DANISH (XXXXXX)  # # #
# # #                                                            # # #
# #                                                                # #
#                                                                    #

import socket
import select
import random
from itertools import imap, chain
from operator import sub

# # #  GLOBAL VARIABLES  # # #

ip = "127.0.0.1"
port = 50000
time_out = 6  # In seconds
fragment_size = 500
window_size = 10
received_file_name = "recieved_sound_file.mp4"
client_list = []  # List of connected UDP clients (only connected clients can send data)

global f, re_order, rec_index_buffer, rec_data_buffer, client_addr, response_buffer, rec_seq_num

# # #  ERROR SIMULATION SWITCHES  # # #

sim_ack_loss = True  # Switch on to simulate loss of first ACK packet during file transfer
sim_packet_order_mix = True  # Causes client to mix up order of packets sent, can be used to test re-ordering at server

# # #  FUNCTIONS  # # #

def process_final_window_packet():
    global f, re_order, rec_index_buffer, rec_data_buffer, client_addr, response_buffer, sim_ack_loss, sim_packer_order_mix, rec_seq_num

    # If simulation of packet order randomization is switched on, randomize packet order
    if sim_packet_order_mix:
        re_order = True
        random.shuffle(rec_index_buffer)

        # Shuffle data buffer in the same pattern as index buffer
        temp_data_buffer = rec_data_buffer[:]
        temp_index_buffer = rec_index_buffer[:]
        for k in range(len(rec_index_buffer)):
            mod = divmod(temp_index_buffer[k], window_size)
            temp_index_buffer[k] = mod[1]
            rec_data_buffer[k] = temp_data_buffer[temp_index_buffer[k]]

    # Show index buffer
    print "Obtained payload!"
    print "Received packet indices: " + str(rec_index_buffer)

    # Re-order buffer if needed
    if re_order:
        # Convert packet numbers into sequence numbers in temporary index buffer
        temp_data_buffer = rec_data_buffer[:]
        temp_index_buffer = rec_index_buffer[:]
        for k in range(len(rec_index_buffer)):
            mod = divmod(temp_index_buffer[k], window_size)
            temp_index_buffer[k] = mod[1]

        # Re-order data buffer using index buffer
        for k in range(len(rec_index_buffer)):
            rec_data_buffer[k] = temp_data_buffer[temp_index_buffer.index(k)]

        # Sort index buffer
        rec_index_buffer.sort()

        print "Re-order?: True, sorting: " + str(rec_index_buffer)
        re_order = False
    else:
        print "Re-order?: Not required"

    # Write re-ordered data from buffer into file
    for k in rec_data_buffer:
        f.write(k)

    # Re-initialize sequence number and buffers
    rec_seq_num = 0
    rec_data_buffer = []
    rec_index_buffer = []

    # Do not send first ACK_ALL if simulation for ACK loss is switched on
    if sim_ack_loss:
        sim_ack_loss = False
    else:
        UDP_socket.sendto("ACK_ALL", client_addr)  # All packets were received

    response_buffer.append("ACK_ALL")

# # #  MAIN PROGRAM  # # #

# Create UDP socket and bind it to IP address and port
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind((ip, port))
print "\n** UDP SERVER LOG **\n"
print "Simulate ACK loss: " + str(sim_ack_loss)
print "Simulate packet order randomization: " + str(sim_packet_order_mix) + "\n"
print "Starting server on %s:%s" % (ip, port)

# Server loop
while True:
    print "Waiting..."

    # Listen to socket
    msg, client_addr = UDP_socket.recvfrom(fragment_size)
    print "Message received from %s:%s: " % (client_addr[0], client_addr[1]) + msg

    # Check for contents
    if msg == "CONN_REQ":  # Establish connection
        client_list.append(client_addr)  # Add client to list (authorisation)
        UDP_socket.sendto("ACK", client_addr)  # Send ACK to confirm connection
        print "Connection established with %s:%s!" % (client_addr[0], client_addr[1])
    elif msg == "REQ_TO_SEND":
        # Authentication protocol (to prevent unauthorised clients from sending data)
        print "Authenticating client..."
        if client_addr in client_list:
            UDP_socket.sendto("ACK", client_addr)
            print "Authentication confirmed. Receiving file..."

            # Get window size
            # If window sizes do not match, reject transfer

            client_window_size = UDP_socket.recvfrom(fragment_size)
            if int(client_window_size[0]) != window_size:
                UDP_socket.sendto("NACK", client_addr)  # Reject file transfer
                print "File transfer failed! Window sizes do not match."
                break
            else:
                UDP_socket.sendto("ACK", client_addr)
                print "Window sizes match. Beginning transfer..."

            UDP_socket.settimeout(time_out)  # Set default time-out

            # # #  START FILE RECEPTION  # # #

            f = open(received_file_name, 'ab')
            rec_seq_num = 0  # Sequence number in a given window (resets each time window slides)
            rec_data_buffer = []  # Packet data buffer
            rec_index_buffer = []  # Packet index buffer
            response_buffer = []  # Store ACK / NACK packets (for recovery during loss)
            cont_iter_last = False  # Enables an extra iteration for the last window
            re_order = False

            while True or cont_iter_last:
                if cont_iter_last:  # Runs for last window
                    process_final_window_packet()
                    cont_iter_last = False
                    print "\nSaving file. Please wait..."

                else:  # Runs for first to second-last windows
                    ready = select.select([UDP_socket], [], [], time_out)  # Check status of socket
                    if ready[0]:
                        try:
                            data, sender_addr = UDP_socket.recvfrom(fragment_size)

                            if data == "REQ_ACK":
                                # Check if all packets have been received or not
                                if rec_seq_num != window_size and rec_seq_num != 0:
                                    # A function that calculates all the index numbers missing from index buffer
                                    list_of_packets_not_received = list(chain.from_iterable(
                                        (rec_index_buffer[i] + d for d in xrange(1, diff)) for i, diff in
                                        enumerate(imap(sub, rec_index_buffer[1:], rec_index_buffer)) if diff > 1))

                                    i = len(list_of_packets_not_received)
                                    while i:
                                        i = i - 1
                                        UDP_socket.sendto("NACK" + str(list_of_packets_not_received[i]),
                                                          client_addr)  # Sends a NAK
                                        print "Packet Number #" + str(list_of_packets_not_received[
                                                                          i]) + " lost. Requesting to be sent again..."  # Displaying which packets lost.
                                        data, sender_addr = UDP_socket.recvfrom(
                                            fragment_size)  # Receives the missing packet.

                                        rec_data_buffer.insert(int(list_of_packets_not_received[i]),
                                                               data)  # Stores in the data buffer in the right order.
                                        rec_seq_num = rec_seq_num + 1  # Appending sequence number.
                                        if i < rec_index_buffer[-1]:
                                            re_order = True
                                        rec_index_buffer.append(
                                            list_of_packets_not_received[i])  # Appending index buffer

                                    process_final_window_packet()

                                else:
                                    # Resend last ACK/NACK in case client doesn't receive ACK/NACK packet
                                    UDP_socket.sendto(response_buffer[-1], client_addr)
                            else:
                                # Receive packet (data)
                                rec_data_buffer.append(data)
                                rec_seq_num = rec_seq_num + 1

                                # Receive packet number (index)
                                data, sender_addr = UDP_socket.recvfrom(fragment_size)

                                # The data sent by the client is encoded as: [<1 CHAR LETTER>, <PACKET NUMBER>]
                                # The first char denotes whether the packet is the final one or not
                                # "N" -> NOT FINAL PACKET, "F" -> FINAL PACKET
                                # e.g. "N102" means the client has sent packet number 102, which is NOT the final packet
                                #      However "F115" means that packet number 115 is the final packet

                                # Store packet number in buffer...
                                rec_packet_num = int(data[1:])

                                # Check if re-ordering is necessary...
                                if rec_index_buffer:
                                    if rec_packet_num < rec_index_buffer[-1]:
                                        re_order = True

                                rec_index_buffer.append(rec_packet_num)

                                # Get 1 char letter
                                if data[0] == "F":
                                    cont_iter_last = True

                                # If final packet in window is received...
                                if rec_seq_num >= window_size:
                                    process_final_window_packet()
                        except:  # Runs if there is a time-out from recvfrom() or some other error
                            print "Time-out reached. File transfer failed."
                            f.close()
                            print "Closing file..."
                            break
                    else:  # No further packets received...
                        print "File %s saved successfully!" % received_file_name
                        f.close()
                        print "Closing file..."
                        break

            # # #  END FILE RECEPTION  # # #

            break
        else:
            UDP_socket.sendto("NACK", client_addr)  # Reject client
            print "Authentication failed! Client must first establish connection with server."

print "Closing server..."
UDP_socket.close()