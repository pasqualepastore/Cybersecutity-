from scapy.all import IP, ICMP, TCP, sr1, sr, conf
import sys
from datetime import datetime

# Disabilita l'output verboso di Scapy
conf.verb = 0

def print_banner():
    """
    Stampa il banner iniziale del programma
    """
    print("\n" + "="*60)
    print("     SYN SCANNER - AUTO DISCOVERY (1-65535)")
    print("="*60)

def icmp_probe(ip):
    """
    Verifica se un host è raggiungibile tramite un ping ICMP.
    
    Args:
        ip (str): L'indirizzo IP dell'host da verificare
    
    Returns:
        bool: True se l'host risponde, False altrimenti
    """
    print(f"\n[*] ICMP probe su {ip}...")
    
    # Crea e invia un pacchetto ICMP Echo Request
    """
    Questa espressione costruisce un pacchetto composto (stacked packet) con un layer IP in testa e, 
    come suo payload, un layer ICMP. In Scapy l'operatore / serve ad impilare (stacking) layer uno sopra 
    l'altro: il layer a sinistra è l'header di più alto livello (qui IP), quello a destra è il payload 
    (qui ICMP). Il risultato è un singolo oggetto Packet che contiene entrambi i layer.

    Cosa fa IP(dst=ip)
    IP() è il costruttore del layer IP (classe scapy.layers.inet.IP).
    dst=ip imposta il campo dst (destination IP) sull'indirizzo passato nella variabile ip.
    Se non specifichi altri campi, Scapy inizializza i campi con valori di default o con None per quelli 
    che verranno calcolati automaticamente (es. checksum).
    Campi utili che puoi impostare: src, dst, ttl, id, tos, flags, chksum (di solito lasci None e Scapy 
    calcola automaticamente su invio).

    Esempio: IP(src="10.0.0.5", dst="8.8.8.8", ttl=64).

    Cosa fa ICMP()

    ICMP() costruisce il layer ICMP (classe scapy.layers.inet.ICMP).
    Se invii ICMP() senza parametri ottieni per default un messaggio ICMP Echo Request 
    (tipicamente type=8, code=0) — cioè un "ping".

    Puoi specificare campi come type, code, id, seq ecc.
    Esempio: ICMP(type=8, code=0, id=0x1234, seq=1) (Echo Request con id/seq).

    Quando il pacchetto viene inviato, Scapy calcola automaticamente il checksum ICMP se il campo chksum 
    è None.
    """
    icmp_packet = IP(dst=ip)/ICMP()
    # invia e attende una risposta (ICMP o altro)
    resp_packet = sr1(icmp_packet, timeout=2, verbose=0)
    
    if resp_packet is not None:
        print(f"[+] Host {ip} raggiungibile\n")
        return True
    else:
        print(f"[-] Host {ip} non risponde al ping ICMP")
        print(f"[*] Continuo comunque la scansione...\n")
        return False

def syn_scan(ip, port):
    """
    Esegue una scansione SYN su una singola porta.
    
    Args:
        ip (str): L'indirizzo IP target
        port (int): La porta da scansionare
    
    Returns:
        str: "open", "closed" o "filtered"
    """
    # Crea un pacchetto TCP SYN
    """
    Cosa succede, passo-passo

    IP(dst=ip)

    Costruisce il layer IP (istanza di scapy.layers.inet.IP).

    dst=ip imposta il campo destination IP sull'indirizzo contenuto nella variabile ip.

    Altri campi utili che puoi impostare: src (indirizzo sorgente), ttl, id, tos. Se non li imposti, 
    Scapy userà valori di default o li calcolerà al momento dell'invio (es. checksum).

    TCP(dport=port, flags='S')

    Costruisce il layer TCP (istanza di scapy.layers.inet.TCP).

    dport=port imposta la destination port (porta di destinazione). Deve essere un intero (es. 80).

    flags='S' imposta i flag TCP; qui 'S' significa SYN. Scapy accetta le flag sia come stringa 
    (es. 'S', 'SA', 'R', ecc.) sia come valore numerico (es. flags=0x02 per SYN).

    Altri campi TCP importanti che puoi impostare: sport (porta sorgente), seq (sequence number), 
    ack (acknowledgement), window, options (es. MSS, Timestamps). Se sport non è specificato, 
    puoi scegliere uno tu o lasciare che il kernel/Scapy gestisca (meglio impostarlo per scansioni).

    L'operatore / tra IP(...) e TCP(...)

    In Scapy l'operatore / impila layer: il layer a sinistra (IP) diventa l'header esterno, 
    quello a destra (TCP) il payload. Il risultato è un unico oggetto Packet che contiene entrambi i layer: 
    un pacchetto IP/TCP pronto per l'invio.

    Cosa rappresenta il pacchetto risultante

    syn_packet è un pacchetto con:

    Header IP verso ip

    Header TCP con destinazione port e il flag SYN impostato

    È il tipico pacchetto che si invia per iniziare una handshake TCP (SYN). Se il server ha la porta aperta, 
    normalmente risponderà con SYN+ACK (flags S+A, valore numerico 0x12). Se la porta è chiusa, 
    spesso risponde con RST (reset, tipicamente 0x14 se include ACK).
    """
    syn_packet = IP(dst=ip)/TCP(dport=port, flags='S')
    
    # Invia il pacchetto e attendi risposta (timeout 1 secondo)
    resp_packet = sr1(syn_packet, timeout=1, verbose=0)
    
    # Analizza la risposta
    if resp_packet is None:
        # Nessuna risposta = porta filtrata
        return "filtered"
    
    elif resp_packet.haslayer(TCP):
        # Estrai i flag TCP dalla risposta
        tcp_flags = resp_packet[TCP].flags
        
        # Flag 0x12 = SYN-ACK (porta aperta)
        if tcp_flags == 0x12:
            # Invia RST per chiudere la connessione
            """
            Cosa costruisce 

            IP(dst=ip) crea il layer IP e imposta il campo dst (destinazione) sull'indirizzo ip.

            TCP(dport=port, flags='R') crea il layer TCP con:

            dport=port → porta di destinazione

            flags='R' → imposta il flag RST (Reset)

            L'operatore / impila i layer: il pacchetto risultante è un pacchetto IP/TCP con il flag RST impostato, 
            pronto per essere inviato.

            Cosa significa il flag RST (Reset)

            Un pacchetto TCP con il flag RST serve a terminare bruscamente una connessione TCP o a indicare che non 
            esiste una connessione corrispondente alla coppia 4-tuple (src, sport, dst, dport).

            È usato per far sì che il peer chiuda/ignorii la connessione senza il normale 3-way handshake di chiusura.

            In una SYN-scan, dopo aver ricevuto un SYN+ACK dal target, lo scanner invia un RST per non completare 
            la TCP handshake (modalità “half-open”). Questo evita di aprire una connessione completa e lascia 
            meno tracce applicative.

            Campi importanti che mancano nella forma minima

            La riga minimale non imposta sport, seq o ack. Alcuni stack TCP (o il target) possono ignorare 
            un RST se i numeri di sequenza non sono coerenti con la connessione attesa. Per essere affidabili 
            conviene:

            impostare sport uguale alla porta sorgente che hai usato per il SYN (altrimenti il target non 
            riconosce a quale connessione il RST si riferisce);

            impostare il numero di sequenza (seq) correttamente (o usare ack con flags='AR') in funzione 
            del pacchetto ricevuto.
            """
            rst_packet = IP(dst=ip)/TCP(dport=port, flags='R', seq=int(resp_packet[TCP].ack))
            sr1(rst_packet, timeout=1, verbose=0)
            return "open"
        
        # Flag 0x14 = RST-ACK (porta chiusa)
        elif tcp_flags & 0x04:  # Controlla se RST è impostato
            return "closed"
    
    # Altri casi = porta filtrata
    return "filtered"

def quick_scan(ip, start_port=1, end_port=1024, batch_size=100):
    """
    Scansiona rapidamente un range di porte per trovare quelle aperte.
    Usa batch per velocizzare (invia più pacchetti insieme).
    
    Args:
        ip (str): IP target
        start_port (int): Prima porta del range
        end_port (int): Ultima porta del range
        batch_size (int): Numero di porte da scansionare per batch
    
    Returns:
        list: Lista delle porte aperte
    """
    open_ports = []
    total_ports = end_port - start_port + 1
    scanned = 0
    
    print(f"[*] Scansione veloce porte {start_port}-{end_port}...")
    print(f"[*] Totale porte: {total_ports}")
    print(f"[*] Questo potrebbe richiedere alcuni minuti...\n")
    
    # Scansiona a batch per velocizzare
    for batch_start in range(start_port, end_port + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_port)
        
        # Crea pacchetti SYN per tutte le porte del batch
        packets = [
            IP(dst=ip)/TCP(dport=port, flags='S') 
            for port in range(batch_start, batch_end + 1)
        ]
        
        # Invia tutti i pacchetti e ricevi risposte
        # inter=0.001 = 1ms tra un pacchetto e l'altro (evita sovraccarico)
        answered, unanswered = sr(packets, timeout=2, verbose=0, inter=0.001)
        
        # Analizza le risposte
        """
        Spiegazione dettagliata

        for sent, received in answered:
        answered è il risultato della chiamata sr() o sr1() di Scapy quando si inviano più pacchetti. 
        È una lista di coppie (sent_packet, received_packet) dove:

        sent è l'oggetto Packet che abbiamo inviato (es. IP()/TCP(...) con dport impostato alla porta target).

        received è il pacchetto ricevuto in risposta dal target per quel sent.

        Questo ciclo itera su tutte le risposte abbinate ai pacchetti inviati.

        if received.haslayer(TCP):
        Controlla se il pacchetto di risposta contiene un layer TCP. Se ad esempio è arrivato un messaggio 
        ICMP (es. "destination unreachable"), haslayer(TCP) restituirebbe False. Quindi questo blocco 
        gestisce solo risposte TCP.

        if received[TCP].flags == 0x12: # SYN-ACK
        Qui si verifica che i flag del layer TCP della risposta siano esattamente 0x12, 
        cioè SYN (0x02) + ACK (0x10) — la tipica risposta di una porta aperta a un SYN.
        Nota pratica: Scapy presenta flags talvolta come stringa (es. 'SA') o come oggetto 
        che si può convertire in intero; per sicurezza è preferibile usare int(received[TCP].flags) == 0x12. 
        La comparazione diretta == 0x12 può funzionare ma in alcune versioni/contesti conviene il cast a int.

        port = received[TCP].sport
        Qui si prende received[TCP].sport — cioè la porta sorgente del pacchetto ricevuto (sul target).
        Quando il target risponde da sport = target_port, quella corrisponde alla porta del servizio remoto 
        (la porta che abbiamo scansionato). Quindi received[TCP].sport è effettivamente il numero di porta 
        remoto che ha risposto.
        Alternativa più esplicita/robusta: usare sent[TCP].dport, cioè la porta destinazione che avevamo 
        inviato nel pacchetto sent. Entrambe sono equivalenti perché la 4-tuple è invertita nella risposta, 
        ma sent[TCP].dport rimane più leggibile e meno soggetto a confusione.

        open_ports.append(port) e print(...)
        Si registra la porta come aperta e si stampa un messaggio.

        Costruzione del RST:

        rst = IP(dst=ip)/TCP(dport=port, flags='R')


        Crea un pacchetto IP/TCP con destinazione ip, porta di destinazione dport=port e flag R (Reset).

        Problema: così com'è non si imposta sport (porta sorgente), né seq/ack. 
        Alcuni target richiedono che il RST arrivi dalla stessa sport e con numeri di sequenza coerenti per accettarlo; altrimenti il RST può essere ignorato. Inoltre, non impostando sport si rischia che la risposta (se presente) provenga da una porta sorgente diversa o che il kernel locale generi interferenze.

        sr1(rst, timeout=1, verbose=0)

        sr1() invia il pacchetto e attende una singola risposta. 
        In questo caso un RST tipicamente non genera risposta: è un pacchetto di chiusura. 
        Quindi sr1 spesso ritornerà None e lo timeout scadrà.

        verbose=0 sopprime l'output verboso di Scapy.

        Usare sr1 per inviare un RST è inefficiente: conviene usare send() (che invia "fire-and-forget" 
        senza aspettare risposte), o sendp() se si vuole lavorare a livello di link. 
        sr1 può rallentare e non aggiunge valore qui.
        """
        for sent, received in answered:
            if received.haslayer(TCP):
                # Se riceve SYN-ACK, la porta è aperta
                if received[TCP].flags == 0x12:  # SYN-ACK
                    port = received[TCP].sport
                    open_ports.append(port)
                    print(f"[+] Porta {port:5d} APERTA")
                    
                    # Invia RST per chiudere la connessione
                    rst = IP(dst=ip)/TCP(dport=port, flags='R')
                    sr1(rst, timeout=1, verbose=0)
        
        # Aggiorna progresso
        scanned += (batch_end - batch_start + 1)
        percentage = (scanned / total_ports) * 100
        print(f"[*] Progresso: {scanned}/{total_ports} ({percentage:.1f}%)", end='\r')
    
    print("\n")  # Nuova riga dopo il progresso
    return sorted(open_ports)

def full_scan(ip, ports):
    """
    Esegue una scansione dettagliata sulle porte specificate.
    
    Args:
        ip (str): IP target
        ports (list): Lista di porte da scansionare in dettaglio
    """
    print("\n" + "="*60)
    print("     SCANSIONE DETTAGLIATA PORTE APERTE")
    print("="*60 + "\n")
    
    results = {"open": [], "closed": [], "filtered": []}
    
    for port in ports:
        print(f"[*] Analisi dettagliata porta {port}...", end='')
        status = syn_scan(ip, port)
        results[status].append(port)
        
        # Codifica colori ANSI
        if status == "open":
            print(f" [\033[92mAPERTA\033[0m]")
        elif status == "closed":
            print(f" [\033[91mCHIUSA\033[0m]")
        else:
            print(f" [\033[93mFILTRATA\033[0m]")
    
    return results

def print_summary(results, start_time):
    """
    Stampa il riepilogo finale della scansione.
    
    Args:
        results (dict): Dizionario con i risultati della scansione
        start_time (datetime): Timestamp di inizio scansione
    """
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("     RIEPILOGO SCANSIONE")
    print("="*60 + "\n")
    
    # Porte aperte
    if results["open"]:
        print(f"[+] Porte APERTE ({len(results['open'])}):")
        for port in results["open"]:
            print(f"    - Porta {port}")
    else:
        print("[-] Nessuna porta aperta trovata")
    
    print()
    
    # Porte chiuse
    if results["closed"]:
        print(f"[-] Porte CHIUSE ({len(results['closed'])}):")
        for port in results["closed"]:
            print(f"    - Porta {port}")
    
    print()
    
    # Porte filtrate
    if results["filtered"]:
        print(f"[?] Porte FILTRATE ({len(results['filtered'])}):")
        for port in results["filtered"]:
            print(f"    - Porta {port}")
    
    print("\n" + "="*60)
    print(f"[*] Tempo totale: {duration:.2f} secondi")
    print("="*60 + "\n")

def main():
    """
    Funzione principale del programma
    """
    # Controlla argomenti
    if len(sys.argv) < 2:
        print("\n[!] Uso corretto:")
        print("    sudo python3 syn_scanner_auto.py <IP> [opzioni]\n")
        print("Opzioni:")
        print("    --quick       Scansiona solo porte 1-1024 (veloce)")
        print("    --common      Scansiona solo le 100 porte più comuni")
        print("    --full        Scansiona tutte le 65535 porte (lento)\n")
        print("Esempi:")
        print("    sudo python3 syn_scanner_auto.py 192.168.1.1 --quick")
        print("    sudo python3 syn_scanner_auto.py 192.168.1.1 --full")
        print("    sudo python3 syn_scanner_auto.py 192.168.1.1  (default: --quick)\n")
        sys.exit(1)
    
    # Estrai IP e opzioni
    ip = sys.argv[1]
    
    # Determina range di porte
    if "--full" in sys.argv:
        start_port = 1
        end_port = 65535
        scan_type = "COMPLETA (1-65535)"
    elif "--common" in sys.argv:
        # Lista delle 100 porte più comuni
        common_ports = [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 
            995, 1723, 3306, 3389, 5900, 8080, 20, 69, 161, 162, 389, 636, 
            1433, 1521, 2049, 3268, 5432, 5800, 8443, 1080, 1194, 8888, 27017,
            137, 138, 500, 1701, 4500, 465, 587, 514, 515, 631, 873, 2181,
            2375, 2376, 3000, 5000, 5001, 5432, 5984, 6379, 7001, 8000, 8008,
            8081, 8443, 8888, 9000, 9090, 9200, 9300, 10000, 27017, 28017,
            50000, 50070, 123, 161, 162, 179, 389, 443, 636, 989, 990, 1433,
            1434, 1521, 1830, 2082, 2083, 2086, 2087, 2095, 2096, 3128, 8009,
            9999, 19132, 19133, 25565, 25575
        ][:100]  # Prendi solo le prime 100
        print(f"[*] Modalità: scansione porte comuni")
        start_time = datetime.now()
        print_banner()
        print(f"Target: {ip}")
        print(f"Tipo scansione: PORTE COMUNI (top 100)\n")
        
        # Ping check
        icmp_probe(ip)
        
        # Scansiona solo le porte comuni
        open_ports = []
        for port in common_ports:
            status = syn_scan(ip, port)
            if status == "open":
                open_ports.append(port)
                print(f"[+] Porta {port:5d} APERTA")
        
        if open_ports:
            results = full_scan(ip, open_ports)
            print_summary(results, start_time)
        else:
            print("[-] Nessuna porta comune aperta trovata")
        
        return
    else:  # Default: --quick
        start_port = 1
        end_port = 1024
        scan_type = "VELOCE (1-1024)"
    
    # Stampa informazioni iniziali
    start_time = datetime.now()
    print_banner()
    print(f"Target: {ip}")
    print(f"Tipo scansione: {scan_type}")
    print(f"Ora inizio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Verifica che l'host sia raggiungibile
    icmp_probe(ip)
    
    # Step 2: Quick scan per trovare porte aperte
    open_ports = quick_scan(ip, start_port, end_port)
    
    # Step 3: Se trova porte aperte, fai scan dettagliato
    if open_ports:
        print(f"\n[+] Trovate {len(open_ports)} porte aperte")
        print(f"[*] Avvio scansione dettagliata...\n")
        
        results = full_scan(ip, open_ports)
        print_summary(results, start_time)
    else:
        print(f"[-] Nessuna porta aperta trovata nel range {start_port}-{end_port}")
        print(f"[*] Tempo totale: {(datetime.now() - start_time).total_seconds():.2f} secondi\n")

# Entry point del programma
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Scansione interrotta dall'utente")
        sys.exit(0)
    except PermissionError:
        print("\n[!] Errore: privilegi insufficienti")
        print("[!] Esegui il programma con privilegi di root/amministratore")
        print("[!] Linux/Mac: sudo python3 syn_scanner_auto.py <IP>")
        print("[!] Windows: esegui come Amministratore\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Errore imprevisto: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)