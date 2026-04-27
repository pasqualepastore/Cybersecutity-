#!/usr/bin/env python3
"""
Scambio di chiavi Diffie-Hellman (DH) tra Alice e Bob.
Richiede: pip install cryptography
"""
 
import hashlib
import sys
from pathlib import Path
 
try:
    from cryptography.hazmat.primitives.asymmetric.dh import generate_parameters
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, PrivateFormat, NoEncryption,
        load_pem_public_key, load_pem_private_key,
    )
except ImportError:
    print("[!] Libreria mancante. Esegui: pip install cryptography")
    sys.exit(1)
 
# ── Nomi dei file ──────────────────────────────────────────────────────────────
PARAM_FILE    = Path("parametersPG.pem")
ALICE_KEY     = Path("Alice_KeyPair.pem")
ALICE_PUB     = Path("Alice_Public.pem")
ALICE_SECRET  = Path("AliceSharedSecret.bin")
BOB_KEY       = Path("Bob_KeyPair.pem")
BOB_PUB       = Path("Bob_Public.pem")
BOB_SECRET    = Path("BobSharedSecret.bin")
 
ALL_FILES = [PARAM_FILE, ALICE_KEY, ALICE_PUB, ALICE_SECRET,
             BOB_KEY,   BOB_PUB,   BOB_SECRET]
 
 
def cleanup():
    """Rimuove i file generati in caso di errore."""
    for f in ALL_FILES:
        if f.exists():
            f.unlink()
 
 
def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
 
 
def main():
    try:
        # 1. Generazione parametri DH 2048-bit
        print("1. Generazione parametri DH 2048-bit (attendere...)")
        parameters = generate_parameters(generator=2, key_size=2048)
        PARAM_FILE.write_bytes(
            parameters.parameter_bytes(Encoding.PEM,
                                       format=__import__(
                                           "cryptography.hazmat.primitives.serialization",
                                           fromlist=["ParameterFormat"]
                                       ).ParameterFormat.PKCS3)
        )
 
        # 2. Alice: generazione chiavi
        print("2. Alice: Generazione chiavi...")
        alice_private = parameters.generate_private_key()
        alice_public  = alice_private.public_key()
 
        ALICE_KEY.write_bytes(
            alice_private.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        )
        ALICE_PUB.write_bytes(
            alice_public.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        )
 
        # 3. Bob: generazione chiavi
        print("3. Bob: Generazione chiavi...")
        bob_private = parameters.generate_private_key()
        bob_public  = bob_private.public_key()
 
        BOB_KEY.write_bytes(
            bob_private.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        )
        BOB_PUB.write_bytes(
            bob_public.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        )
 
        # 4. Derivazione segreti condivisi
        print("4. Derivazione segreti condivisi...")
        alice_secret = alice_private.exchange(bob_public)
        bob_secret   = bob_private.exchange(alice_public)
 
        ALICE_SECRET.write_bytes(alice_secret)
        BOB_SECRET.write_bytes(bob_secret)
 
        # 5. Verifica finale
        print("5. Verifica finale...")
        print("-" * 50)
        if alice_secret == bob_secret:
            print("SUCCESSO: I segreti corrispondono!")
            print(f"Impronta (Alice): {sha256_hex(ALICE_SECRET)}")
            print(f"Impronta (Bob):   {sha256_hex(BOB_SECRET)}")
        else:
            print("ERRORE: I segreti sono DIVERSI.")
            print(f"Impronta (Alice): {sha256_hex(ALICE_SECRET)}")
            print(f"Impronta (Bob):   {sha256_hex(BOB_SECRET)}")
        print("-" * 50)
 
    except Exception as e:
        print(f"\n[!] Errore: {e}")
        print("[!] Pulizia file temporanei...")
        cleanup()
        sys.exit(1)
 
 
if __name__ == "__main__":
    main()