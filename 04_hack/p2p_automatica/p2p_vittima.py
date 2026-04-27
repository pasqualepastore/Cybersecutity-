#!/usr/bin/env python3
import socket, subprocess

PORTA = 8000

def worker():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", PORTA))
        s.listen(1)
        print(f"[*] Lubuntu pronto. In attesa di Kali...")
        
        conn, addr = s.accept()
        print(f"[+] Kali collegato! Pronto a mostrare l'attacco.")
        
        with conn:
            while True:
                data = conn.recv(1024)
                if not data: break
                cmd = data.decode().strip()
                
                if cmd == "STOP":
                    subprocess.run("pkill -f ping hping3", shell=True)
                    print("\n[!] ATTACCO INTERROTTO.")
                else:
                    print(f"\n[!] AVVIO ATTACCO: {cmd}")
                    # Esegue l'attacco e mostra i pacchetti qui su Lubuntu
                    subprocess.Popen(cmd, shell=True)

worker()
