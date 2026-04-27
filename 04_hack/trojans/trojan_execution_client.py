#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import subprocess
import tempfile
import os

def start_client(server_ip: str, server_port: int) -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print(f"[*] Tentativo di connessione a {server_ip}:{server_port}...")
            sock.settimeout(10.0) # Evita che il client rimanga bloccato all'infinito
            sock.connect((server_ip, server_port))
            print("[+] Connessione stabilita. Ricezione script...")

            # Ricezione sicura dei dati
            response_data = b''
            while True:
                data_chunk = sock.recv(4096)
                if not data_chunk:
                    break
                response_data += data_chunk
                # Se il server chiude dopo l'invio, usciamo dal ciclo

            if not response_data or response_data.decode('utf-8').strip() == "SCRIPT_NOT_FOUND":
                print("[!] Il server non ha fornito alcuno script valido.")
                return

            script_content = response_data.decode('utf-8')

            # Salvataggio in file temporaneo
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".sh") as script_file:
                script_file.write(script_content)
                temp_script_path = script_file.name

            # Rende lo script eseguibile
            os.chmod(temp_script_path, 0o755)

            print(f"[*] Eseguo lo script ricevuto tramite Bash...\n")
            
            # --- RISOLUZIONE ERRORI SINTASSI ---
            # Forziamo l'uso di Bash invece di Python per eseguire lo script ricevuto
            subprocess.run(["/bin/bash", temp_script_path], check=False)

            # Pulizia
            os.remove(temp_script_path)
            print("\n[+] Script eseguito e rimosso con successo.")

    except ConnectionRefusedError:
        print(f"[!] Errore: Il server è spento su {server_ip}:{server_port}.")
    except socket.timeout:
        print("[!] Errore: Timeout della connessione.")
    except Exception as e:
        print(f"[!] Errore imprevisto: {e}")
    finally:
        print("[*] Client terminato.")

def main():
    # --- CONFIGURAZIONE AUTOMATICA ---
    # Cambia questi due valori con quelli del tuo server
    DEFAULT_IP = "192.168.142.128" 
    DEFAULT_PORT = 8000

    # Se scrivi IP e Porta nel terminale usa quelli, altrimenti usa i DEFAULT
    if len(sys.argv) == 3:
        server_ip = sys.argv[1]
        try:
            server_port = int(sys.argv[2])
        except ValueError:
            print("La porta deve essere un numero intero.")
            sys.exit(1)
    else:
        server_ip = DEFAULT_IP
        server_port = DEFAULT_PORT
        print(f"[*] Modalità automatica: mi connetto a {server_ip}:{server_port}")

    start_client(server_ip, server_port)

if __name__ == "__main__":
    main()
