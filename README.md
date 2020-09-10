# Reliable UDP using Python Socket Programming

UDP on its own is unreliable because none of the datagrams sent back and forth between the server and client are acknowledged. This makes it difficult for the sender to ensure that the recipient received the packet or not. Therefore, by taking inspiration from TCP, we decided to improve the reliability of UDP in the following ways:
* **Sequencing of packets**: The client sends the packet number along with the packet itself; this allows the server to recognise un-ordered or missing packets.
* Stop-and-wait for window: After sending all the packets in a given window, the client waits for the server's acknowledgment before sending the remaining packets. The server, meanwhile, re-orders the packets (if necessary) and checks for missing packets.
* **Retransmission of lost packets (selective-repeat)**: The server requests the client to re-transmit one or more missing packets.
* **Retransmission of lost ACK packets**: The client sends the server a 'request for acknowledgement', which the server re-sends if all packets have been received.
* **Re-ordering of packets**: Un-ordered packets are re-ordered on the server end once all the packets in a given window are received. This is discussed in more detail in Behaviour, design and development.
* **Client authentication**: The client must first establish a connection with the server before it is able to send files. The server achieves this by storing the client IP address and port number in a list when the client first connects to the server. When it receives a request-to-send packet, it cross-checks the client details with its list of clients. If a match is found, it sends an ACK packet to confirm authentication, otherwise it denies the request by sending a NACK packet. The server refuses to accept files from unauthenticated clients.
* **Window size check**: The server ensures that the window size is matched with that of the client. 

The program offers three simulation modes:
* Loss of first ACK packet
* Loss of one or more datagrams
* Packet order randomisation

**Instructions**: First run <code>server_reliableUDP.py</code> to open server, then run <code>client_reliableUDP.py</code> to begin transfer.  
</br  >
*Note: There is no need to add in your IP address as the client and server addresses are set to to 127.0.0.1 (the loop-back address).*

Python version: 2.7  
IDE: PyCharm Community Edition  
Date of creation: May 2020  
Type of project: Semester project
Group members: Zain Amir Zaman, Khan Moeen Danish
