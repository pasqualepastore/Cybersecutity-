#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
 p2p_chat_node.py - Versione STABILE con send_script e status
============================================================================
"""

import socket
import threading
import sys
import subprocess
import shlex
import os
import time


class P2PNode:
    def __init__(self, listen_host: str, listen_port: int) -> None:
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.server_socket: socket.socket | None = None
        self.peers: dict[tuple[str, int], socket.socket] = {}
        self.peers_lock = threading.Lock()
        self.running = True

    def start(self) -> None:
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.listen_host, self.listen_port))
            self.server_socket.listen(5)
        except OSError as e:
            print(f"[ERRORE] Impossibile avviare il nodo su {self.listen_host}:{self.listen_port} -> {e}")
            sys.exit(1)

        print(f"[INFO] Nodo in ascolto su {self.listen_host}:{self.listen_port}")
        print(f"[INFO] Directory di lavoro: {os.getcwd()}")

        listener = threading.Thread(target=self._listen_loop, name="ListenerThread", daemon=True)
        listener.start()

    def _listen_loop(self) -> None:
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
            except OSError:
                break

            print(f"\n[CONNESSIONE IN INGRESSO] da {client_address[0]}:{client_address[1]}")

            with self.peers_lock:
                self.peers[client_address] = client_socket

            handler = threading.Thread(
                target=self._handle_peer,
                args=(client_socket, client_address),
                name=f"PeerHandler-{client_address}",
                daemon=True,
            )
            handler.start()

            self._prompt()

    def _handle_peer(self, peer_socket: socket.socket, peer_address: tuple[str, int]) -> None:
        try:
            while self.running:
                data = peer_socket.recv(8192)
                if not data:
                    break

                # === GESTIONE UPLOAD BINARIO ===
                if data.startswith(b"UPLOAD:"):
                    try:
                        # Estrai dimensione dal header
                        header = data[:data.find(b"\n") + 1].decode("utf-8", errors="ignore")
                        size = int(header.split(":")[-1].strip())
                        file_data = data[data.find(b"\n") + 1:]
                        self._receive_file(peer_socket, file_data, size, peer_address)
                        continue
                    except Exception as e:
                        print(f"[ERRORE] Formato UPLOAD non valido da {peer_address}: {e}")
                        continue

                # === Messaggi normali (testo) ===
                raw = data.decode("utf-8", errors="replace").rstrip()

                if raw.startswith("EXEC:"):
                    parts = raw.split(":", 2)
                    if len(parts) < 3:
                        continue
                    _, target, cmd = parts
                    print(f"\n[EXEC da {peer_address[0]}:{peer_address[1]}] {cmd}")
                    self._execute_command(cmd, peer_socket, peer_address)

                else:
                    print(f"\n[MSG da {peer_address[0]}:{peer_address[1]}] {raw}")
                    if raw != raw.upper():
                        try:
                            peer_socket.sendall(raw.upper().encode("utf-8"))
                        except OSError:
                            break

                self._prompt()

        except (ConnectionResetError, OSError):
            pass
        finally:
            self._remove_peer(peer_address)

    def _execute_command(self, cmd: str, peer_socket: socket.socket, peer_address: tuple[str, int]):
        try:
            dangerous = ["rm -rf", "dd if=", "> /dev/", "mkfs", "shutdown", "reboot"]
            if any(kw in cmd.lower() for kw in dangerous):
                output = "[ERRORE DI SICUREZZA] Comando bloccato."
            else:
                exec_list = shlex.split(cmd)
                result = subprocess.run(
                    exec_list,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd="/tmp"
                )
                output = result.stdout + result.stderr
                if not output.strip():
                    output = f"[OK] Eseguito (exit code: {result.returncode})"
                else:
                    output = f"[OUTPUT]\n{output}"
        except subprocess.TimeoutExpired:
            output = "[ERRORE] Timeout 120s"
        except FileNotFoundError:
            output = "[ERRORE] File o comando non trovato"
        except Exception as e:
            output = f"[ERRORE] {type(e).__name__}: {e}"

        try:
            peer_socket.sendall(output.encode("utf-8"))
        except OSError:
            pass

    def _receive_file(self, peer_socket: socket.socket, received_data: bytes, size: int, peer_address: tuple[str, int]):
        """Salva SEMPRE come /tmp/command.sh"""
        try:
            data = received_data
            while len(data) < size:
                chunk = peer_socket.recv(min(8192, size - len(data)))
                if not chunk:
                    break
                data += chunk

            save_path = "/tmp/command.sh"
            with open(save_path, "wb") as f:
                f.write(data)

            os.chmod(save_path, 0o755)

            print(f"[UPLOAD SUCCESS] Script salvato come {save_path} ({len(data)} bytes) da {peer_address[0]}")
            peer_socket.sendall(b"[OK] Script salvato in /tmp/command.sh")

        except Exception as e:
            print(f"[ERRORE] Salvataggio file fallito: {e}")

    # ====================== LATO CLIENT ======================
    def connect_to_peer(self, ip: str, port: int) -> None:
        peer_address = (ip, port)
        with self.peers_lock:
            if peer_address in self.peers:
                print(f"[INFO] Già connesso a {ip}:{port}")
                return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(peer_address)
            with self.peers_lock:
                self.peers[peer_address] = sock
            print(f"[INFO] Connesso a {ip}:{port}")

            handler = threading.Thread(target=self._handle_peer, args=(sock, peer_address), daemon=True)
            handler.start()
        except Exception as e:
            print(f"[ERRORE] Connessione fallita: {e}")

    def send_script(self, target: str, local_file: str) -> None:
        if not os.path.isfile(local_file):
            print(f"[ERRORE] File non trovato: {local_file}")
            return

        with open(local_file, "rb") as f:
            file_data = f.read()

        header = f"UPLOAD:command.sh:{len(file_data)}\n".encode("utf-8")

        with self.peers_lock:
            peer_list = list(self.peers.items())

        if target.lower() == "all":
            print(f"[SEND_SCRIPT] Invio '{local_file}' a TUTTI i peer...")
            for addr, sock in peer_list:
                try:
                    sock.sendall(header + file_data)
                except OSError:
                    self._remove_peer(addr)

            time.sleep(1.5)
            print("[SEND_SCRIPT] Esecuzione automatica in corso...")
            self._send_to_all("EXEC:all:sh /tmp/command.sh")
            return

        try:
            idx = int(target) - 1
            if idx < 0 or idx >= len(peer_list):
                print(f"[ERRORE] Peer {target} non valido.")
                return
            addr, sock = peer_list[idx]
            print(f"[SEND_SCRIPT] Invio su peer {idx+1}...")
            sock.sendall(header + file_data)
            time.sleep(1.5)
            sock.sendall("EXEC:all:sh /tmp/command.sh".encode("utf-8"))
        except ValueError:
            print("Uso: send_script <numero|all> <file_locale>")

    def status(self, target: str) -> None:
        status_cmd = "echo '=== SYSTEM STATUS ===' && hostname && whoami && uname -a && uptime && free -h | head -n 2 && df -h / | tail -1"

        with self.peers_lock:
            peer_list = list(self.peers.items())

        if target.lower() == "all":
            print("[STATUS] Richiesta su TUTTI i peer...")
            self._send_to_all(f"EXEC:all:{status_cmd}")
            return

        try:
            idx = int(target) - 1
            if idx < 0 or idx >= len(peer_list):
                print(f"[ERRORE] Peer {target} non valido.")
                return
            addr, sock = peer_list[idx]
            print(f"[STATUS] Richiesta sul peer {idx+1}...")
            sock.sendall(f"EXEC:{addr[0]}:{addr[1]}:{status_cmd}".encode("utf-8"))
        except ValueError:
            print("Uso: status <numero|all>")

    def exec_on_peer(self, target: str, command: str) -> None:
        with self.peers_lock:
            peer_list = list(self.peers.items())

        if not peer_list:
            print("[INFO] Nessun peer connesso.")
            return

        if target.lower() == "all":
            print(f"[INFO] Esecuzione '{command}' su TUTTI i peer...")
            self._send_to_all(f"EXEC:all:{command}")
            return

        try:
            idx = int(target) - 1
            if idx < 0 or idx >= len(peer_list):
                print(f"[ERRORE] Peer {target} non valido.")
                return
            addr, sock = peer_list[idx]
            print(f"[INFO] Esecuzione sul peer {idx+1}")
            sock.sendall(f"EXEC:{addr[0]}:{addr[1]}:{command}".encode("utf-8"))
        except ValueError:
            print("Uso: exec <numero|all> <comando>")

    def _send_to_all(self, payload: str) -> None:
        encoded = payload.encode("utf-8")
        dead = []
        with self.peers_lock:
            for addr, sock in self.peers.items():
                try:
                    sock.sendall(encoded)
                except OSError:
                    dead.append(addr)
        for addr in dead:
            self._remove_peer(addr)

    def list_peers(self) -> None:
        with self.peers_lock:
            if not self.peers:
                print("[INFO] Nessun peer connesso.")
                return
            print(f"[INFO] Peer connessi ({len(self.peers)}):")
            for i, (ip, port) in enumerate(self.peers.keys(), 1):
                print(f"  {i}. {ip}:{port}")

    def shutdown(self) -> None:
        print("[INFO] Arresto del nodo in corso...")
        self.running = False
        with self.peers_lock:
            for sock in self.peers.values():
                try:
                    sock.close()
                except OSError:
                    pass
            self.peers.clear()

        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
        print("[INFO] Nodo terminato.")

    def _remove_peer(self, peer_address: tuple[str, int]) -> None:
        with self.peers_lock:
            sock = self.peers.pop(peer_address, None)
        if sock:
            try:
                sock.close()
            except OSError:
                pass
            print(f"[INFO] Peer {peer_address[0]}:{peer_address[1]} rimosso.")

    @staticmethod
    def _prompt() -> None:
        print("> ", end="", flush=True)


# ======================================================================
def cli_loop(node: P2PNode) -> None:
    help_text = (
        "=== ISTRUZIONI PER L'USO DEL NODO P2P ===\n\n"
        "Comandi disponibili:\n"
        "  connect <ip> <porta>\n"
        "  send <messaggio>\n"
        "  exec <numero|all> <comando>\n"
        "  send_script <numero|all> <file_locale>   ← upload + esecuzione automatica\n"
        "  status <numero|all>                      ← info sistema remoto\n"
        "  list\n"
        "  exit / quit\n"
        "  help\n\n"
        "=== ESEMPI DI UTILIZZO ===\n"
        "1. Connettersi:\n"
        "   connect 192.168.58.143 8082\n\n"
        "2. Inviare messaggio:\n"
        "   send Ciao a tutti!\n\n"
        "3. Eseguire comando:\n"
        "   exec all whoami\n"
        "   exec all ls -la\n\n"
        "4. Caricare ed eseguire script:\n"
        "   send_script all ./command.sh\n\n"
        "5. Info sistema:\n"
        "   status all"
    )
    print(help_text)

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue

        parts = line.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd == "connect":
            if len(parts) != 3:
                print("Uso: connect <ip> <porta>")
                continue
            try:
                node.connect_to_peer(parts[1], int(parts[2]))
            except ValueError:
                print("Porta non valida.")

        elif cmd == "send":
            if len(parts) < 2:
                print("Uso: send <messaggio>")
                continue
            node._send_to_all("CHAT:" + " ".join(parts[1:]))

        elif cmd == "exec":
            if len(parts) < 3:
                print("Uso: exec <numero|all> <comando>")
                continue
            node.exec_on_peer(parts[1], " ".join(parts[2:]))

        elif cmd == "send_script":
            if len(parts) < 3:
                print("Uso: send_script <numero|all> <file_locale>")
                continue
            node.send_script(parts[1], parts[2])

        elif cmd == "status":
            if len(parts) < 2:
                print("Uso: status <numero|all>")
                continue
            node.status(parts[1])

        elif cmd == "list":
            node.list_peers()

        elif cmd in ("exit", "quit"):
            break

        elif cmd == "help":
            print(help_text)
        else:
            print(f"Comando sconosciuto: {cmd}")

    node.shutdown()


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Uso: python3 {sys.argv[0]} <porta>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        if not 0 < port < 65536:
            raise ValueError
    except ValueError:
        print("Porta non valida (1-65535).")
        sys.exit(1)

    node = P2PNode("0.0.0.0", port)
    node.start()

    try:
        cli_loop(node)
    except Exception as e:
        print(f"[ERRORE FATALE] {e}")
        node.shutdown()


if __name__ == "__main__":
    main()