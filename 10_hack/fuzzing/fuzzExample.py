import sys
import afl
import os

# -----------------------------------------
# Collocate qui la funzione di test
# -----------------------------------------
def testFunction(a, b, c):
    """
    Esempio di funzione di test.
    Sostituisci questa logica con quella che desideri analizzare.
    """
    if a + b == c:
        if a > 100:
            # Esempio di percorso che AFL cercherà di trovare
            print("Percorso specifico trovato!")
    return

def main():
    try:
        # Legge l'input da stdin (fornito da AFL)
        in_str = sys.stdin.read()

        # Gestione base dell'input per evitare crash banali
        parts = in_str.strip().split()
        if len(parts) == 3:
            a = int(parts[0])
            b = int(parts[1])
            c = int(parts[2])

            testFunction(a, b, c)

    except (ValueError, IndexError):
        # Ignora input formattati male durante il fuzzing
        pass

if __name__ == "__main__":
    # Inizializza lo strumento di analisi di AFL
    afl.init()
    main()

    # os._exit(0) è preferibile a sys.exit() per AFL
    # perché interrompe immediatamente il processo
    os._exit(0)
