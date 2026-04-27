import socket

# Configurazione
IP = "192.168.188.130" 
PORT = 4444

def main():
    # Creazione del socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = (IP, PORT)

    try:
        # Tentativo di connessione
        sock.connect(address)
        
        # Ricezione del messaggio
        msg = sock.recv(1024)
        if msg:
            print(f"Messaggio ricevuto: {msg.decode('utf-8')}")
        
    except ConnectionRefusedError:
        print("Errore: Impossibile connettersi. Il server è attivo?")
    except Exception as e:
        print(f"Errore imprevisto: {e}")
    finally:
        # Chiusura sempre garantita
        sock.close()

if __name__ == "__main__":
    main() # Rimosso l'errore di sintassi qui
