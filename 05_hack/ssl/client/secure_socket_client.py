#!/usr/bin/env python3
import argparse
import socket
import ssl
import sys

DEFAULT_HOST = "192.168.58.138"
DEFAULT_PORT = 8080
CLIENT_CERT = "client.crt"
CLIENT_KEY = "client.key"
SERVER_CA = "server.crt"   # CA o cert del server se self-signed

def build_context(cafile: str, certfile: str, keyfile: str, check_hostname: bool) -> ssl.SSLContext:
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cafile)
    ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
    ctx.verify_mode = ssl.CERT_REQUIRED
    # se usi un IP e il certificato non ha il SAN con quell'IP, lascia False
    ctx.check_hostname = check_hostname
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    except AttributeError:
        pass
    return ctx

def main():
    ap = argparse.ArgumentParser(description="mTLS TLS client")
    ap.add_argument("--host", default=DEFAULT_HOST, help="Hostname/IP del server (default: %(default)s)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta del server (default: %(default)s)")
    ap.add_argument("--cafile", default=SERVER_CA, help="CA file per verificare il server (default: %(default)s)")
    ap.add_argument("--cert", default=CLIENT_CERT, help="Certificato client (default: %(default)s)")
    ap.add_argument("--key", default=CLIENT_KEY, help="Chiave privata client (default: %(default)s)")
    ap.add_argument("--check-hostname", action="store_true",
                    help="Abilita il controllo hostname sul certificato server (richiede SAN coerente)")
    ap.add_argument("--connect-timeout", type=float, default=5.0, help="Timeout connessione in secondi (default: %(default)s)")
    ap.add_argument("--io-timeout", type=float, default=10.0, help="Timeout I/O TLS in secondi (default: %(default)s)")
    args = ap.parse_args()

    try:
        context = build_context(args.cafile, args.cert, args.key, args.check_hostname)

        with socket.create_connection((args.host, args.port), timeout=args.connect_timeout) as raw:
            # usa server_hostname per SNI anche se check_hostname è False
            with context.wrap_socket(raw, server_side=False, server_hostname=args.host) as ssock:
                ssock.settimeout(args.io_timeout)
                print("[client] TLS ok - versione:", ssock.version())

                # loop invio/ricezione: invia righe finché l'utente preme solo Invio
                print("Digita un messaggio e premi Invio (vuoto per uscire).")
                while True:
                    try:
                        message = input("Please enter your message: ").rstrip("\n")
                    except (EOFError, KeyboardInterrupt):
                        print("\n[client] uscita richiesta.")
                        break

                    if not message:
                        print("[client] nessun messaggio: chiudo la sessione.")
                        break

                    # invia (aggiungo newline: utile se il server delimita a riga)
                    ssock.sendall((message + "\n").encode("utf-8"))

                    # prova a ricevere una risposta (può essere eco o protocollo app)
                    try:
                        data = ssock.recv(4096)
                        if not data:
                            print("[client] server ha chiuso la connessione.")
                            break
                        print("[client] Risposta (decriptata):", data.decode("utf-8", errors="replace").rstrip("\n"))
                    except socket.timeout:
                        print("[client] timeout ricezione: nessuna risposta entro", args.io_timeout, "s")

                # opzionale: chiudi graziosamente metà scrittura
                try:
                    ssock.shutdown(socket.SHUT_WR)
                except OSError:
                    pass

    except ssl.SSLError as e:
        print("[client] Errore SSL:", e)
        sys.exit(1)
    except socket.timeout:
        print("[client] Timeout connessione.")
        sys.exit(1)
    except ConnectionRefusedError:
        print("[client] Connessione rifiutata.")
        sys.exit(1)
    except Exception as e:
        print("[client] Errore generico:", type(e).__name__, e)
        sys.exit(1)

if __name__ == "__main__":
    main()