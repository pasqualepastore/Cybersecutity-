#!/usr/bin/env python3
import socket, threading, time

# --- CONFIGURAZIONE MULTI-PORTA ---
# Ogni riga rappresenta una macchina: (IP, PORTA)
WORKERS_CONFIG = [
    ("192.168.142.141", 8000),  # Lubuntu
    ("192.168.142.146", 8082),  # Ubuntu (porta diversa per evitare blocchi)
]

class KaliMaster:
    def __init__(self):
        self.workers = []

    def connect_to_workers(self):
        for ip, porta in WORKERS_CONFIG:
            threading.Thread(target=self.attempt_connection, args=(ip, porta), daemon=True).start()

    def attempt_connection(self, ip, porta):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((ip, porta))
                self.workers.append(s)
                print(f"\n[+] Collegato al Worker: {ip} sulla porta {porta}")
                break
            except:
                # Silenzioso per non intasare il terminale, riprova ogni 5 secondi
                time.sleep(5)

    def send_command(self, cmd):
        print(f"[*] Inviando ordine a {len(self.workers)} macchine...")
        for w in self.workers[:]:
            try:
                w.sendall(cmd.encode())
            except:
                try:
                    peer_info = w.getpeername()
                    print(f"[!] Connessione persa con {peer_info}")
                except:
                    print(f"[!] Connessione persa con un worker.")
                self.workers.remove(w)

    def run(self):
        self.connect_to_workers()
        print("[*] Kali Master pronto. Comandi: send <cmd>, stop, list, exit")
        while True:
            try:
                cmd = input("KALI MASTER > ").strip()
                if not cmd: continue
                
                if cmd.startswith("send "):
                    self.send_command(cmd[5:])
                elif cmd == "stop":
                    self.send_command("STOP")
                elif cmd == "list":
                    print(f"[*] Macchine attualmente connesse: {len(self.workers)}")
                    for w in self.workers:
                        print(f"  - {w.getpeername()}")
                elif cmd == "exit":
                    break
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    KaliMaster().run()
