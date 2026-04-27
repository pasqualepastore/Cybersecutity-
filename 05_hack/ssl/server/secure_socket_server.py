#!/usr/bin/env python3
import socket
import ssl

SERVER_CERT = "server.crt"
SERVER_KEY = "server.key"
CLIENT_CA = "client.crt"   # se i certificati sono self-signed, qui ci metti il cert del client o la CA che ha firmato il client
HOST = "0.0.0.0"
PORT = 8080


def main():
    # Context per autenticare il client (mTLS)
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
    context.load_verify_locations(cafile=CLIENT_CA)

    # Imposta versione minima TLS (se disponibile)
    try:
        context.minimum_version = ssl.TLSVersion.TLSv1_2
    except AttributeError:
        pass

    # Socket TCP plain
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(5)
        print(f"[server] in ascolto su {HOST}:{PORT}")

        while True:
            newsock, addr = sock.accept()
            print(f"[server] connessione TCP accettata da {addr}")
            # wrap TLS su singola connessione: handshake qui
            try:
                with context.wrap_socket(newsock, server_side=True) as ssock:
                    ssock.settimeout(10.0)
                    print("[server] handshake TLS OK - versione:", ssock.version())

                    # opzionale: informazioni certificato client
                    try:
                        cert = ssock.getpeercert()
                        print("[server] certificato client:", cert)
                    except Exception:
                        print("[server] nessun certificato client ottenuto o getpeercert non disponibile")

                    # ricezione e decodifica del messaggio (plaintext)
                    try:
                        data = ssock.recv(4096)
                        if not data:
                            print("[server] ricevuti 0 byte - connessione chiusa dal client")
                        else:
                            # decodifica in UTF-8 (sostituisce caratteri non validi)
                            text = data.decode("utf-8", errors="replace")
                            print("[server] Ricevuto (decriptato):", text)
                            # echo (opzionale)
                            ssock.sendall(text.upper().encode("utf-8"))
                    except socket.timeout:
                        print("[server] timeout sulla recv")
                    except Exception as e:
                        print("[server] errore recv/send:", e)
            except ssl.SSLError as e:
                print("[server] errore SSL durante handshake/wrap:", e)
            except Exception as e:
                print("[server] errore generico sulla connessione:", e)

if __name__ == "__main__":
    main()
