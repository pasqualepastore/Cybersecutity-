import socket

# Lasciando "" (stringa vuota), il server ascolta su TUTTE le interfacce di rete
IP = "0.0.0.0" 
PORT = 4444

def main():
    # Creazione socket e impostazione opzione per riutilizzare la porta subito dopo la chiusura
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    address = (IP, PORT)

    try:
        sock.bind(address)
        sock.listen(1)
        print(f"[*] In ascolto su {IP}:{PORT}...")

        # Accetta la connessione
        conn, addr_victim = sock.accept()
        print(f"[+] Connessione stabilita da: {addr_victim[0]}:{addr_victim[1]}")

        # Invio messaggio
        msg = "Messaggio dal server: Connessione riuscita!"
        conn.send(msg.encode('utf-8'))

        # Chiusura connessione specifica con la vittima
        conn.close()
        
    except Exception as e:
        print(f"[-] Errore: {e}")
    finally:
        # Chiusura del socket principale
        sock.close()

if __name__ == "__main__":
    main()
