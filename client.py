import socket
import sys
import os
import csv

HOST = "127.0.0.1"
PORT = 5050

# Riceve dati dal socket
def ricevi(sock):
    try:
        data = sock.recv(4096)
        if not data:
            return "[Connessione chiusa dal server]"
        return data.decode(errors="ignore")
    except (ConnectionResetError, OSError, BrokenPipeError) as e:
        return f"[Errore ricezione: {e}]"

# Verifica se una stringa è convertibile a float
def is_float(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

def main():
    print("╔══════════════════════════════════════╗")
    print("║       EcoMonitor – Avvio client      ║")
    print("╚══════════════════════════════════════╝")
    print(f"Connessione a {HOST}:{PORT} …")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
    except (ConnectionRefusedError, TimeoutError, OSError):
        print("\nImpossibile connettersi al server.")
        print("Il server è in esecuzione? Ricontrolla.")
        sys.exit(1)

    print("Connesso al server.\n")
    print(ricevi(sock))
    nome = input("Nome studente: ").strip()

    if not nome:
        print("Nome obbligatorio.")
        sock.close()
        return

    sock.sendall(nome.encode())
    print(ricevi(sock))

    print("\n--- Caricamento dati da CSV Phyphox ---")
    csv_path = input("Percorso del file CSV: ").strip().strip('"\'')

    # Valida il percorso
    if not csv_path:
        print("Errore: Percorso vuoto.")
        sock.close()
        return

    if not os.path.isfile(csv_path):
        print("Errore: Il file specificato non esiste o non è un file.")
        sock.close()
        return

    sensore = input("Sensore (es. luce, rumore, temperatura): ").strip()
    luogo = input("Luogo della misurazione: ").strip()

    print("\nLettura e invio in corso...")
    inviati = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Deduce il separatore dalla prima riga
            prima_riga = f.readline()
            sep = ';' if ';' in prima_riga else ','
            f.seek(0)

            reader = csv.reader(f, delimiter=sep)
            next(reader, None)  # Salta intestazione

            for row in reader:
                if len(row) >= 2:
                    valore = row[1].strip().replace(',', '.')
                    if is_float(valore):
                        msg = f"INVIA {sensore} {valore} {luogo}"
                        sock.sendall(msg.encode())
                        ricevi(sock)
                        inviati += 1
                        if inviati % 50 == 0:
                            print(".", end="", flush=True)

        print(f"\n\nOperazione completata! Inviati {inviati} valori dal file CSV.")

    except Exception as e:
        print(f"\nErrore durante l'elaborazione del CSV: {e}")

    sock.sendall(b"ESCI")
    print(ricevi(sock))
    sock.close()
    print("Connessione chiusa.")

if __name__ == "__main__":
    main()
