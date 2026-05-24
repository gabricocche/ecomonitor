import socket
import threading
import csv
from datetime import datetime
import os

HOST = "0.0.0.0"
PORT = 5050
CSV_FILE = "misure.csv"
CSV_HEADER = ["studente", "sensore", "valore", "luogo", "data_ora"]
coda = []
coda_lock = threading.Lock()
csv_lock = threading.Lock()

# Crea il file CSV con intestazione
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADER)
        print(f"SERVER - File '{CSV_FILE}' creato.")

# Salva una misura nel file CSV (thread-safe)
def salva_csv(dati):
    with csv_lock:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            if os.path.getsize(CSV_FILE) > 0:
                with open(CSV_FILE, "rb") as rf:
                    rf.seek(-1, os.SEEK_END)
                    if rf.read(1) != b'\n':
                        f.write('\n')
            csv.DictWriter(f, fieldnames=CSV_HEADER).writerow(dati)

# Worker che elabora la coda di misure in background
def worker():
    while True:
        with coda_lock:
            item = coda.pop(0) if coda else None
        if item:
            salva_csv(item)
        else:
            threading.Event().wait(0.2)

# Gestisce i comandi ricevuti dai client
def gestisci_client(conn, addr):
    print(f"SERVER - Nuova connessione da {addr}")
    studente = None
    try:
        conn.sendall(b"Nome: ")
        studente = conn.recv(1024).decode().strip()
        if not studente:
            return
        conn.sendall(f"Ciao {studente}!\n".encode())
        print(f"SERVER - Studente: {studente} ({addr})")

        while True:
            try:
                raw = conn.recv(4096).decode().strip()
            except (ConnectionResetError, OSError):
                break

            if not raw:
                break

            parti = raw.upper().split()
            if not parti:
                continue
            cmd = parti[0]

            if cmd == "INVIA":
                parti = raw.split(maxsplit=3)
                if len(parti) < 4:
                    conn.sendall(b"Formato: INVIA <sensore> <valore> <luogo>\n")
                    continue
                _, sensore, valore, luogo = parti
                try:
                    valore = float(valore)
                except ValueError:
                    conn.sendall(b"Valore non numerico.\n")
                    continue

                record = {
                    "studente": studente,
                    "sensore": sensore.lower(),
                    "valore": valore,
                    "luogo": luogo.lower(),
                    "data_ora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with coda_lock:
                    coda.append(record)
                    coda_len = len(coda)
                print(f"SERVER - Misura in coda: {record}")
                conn.sendall(f"In coda: {coda_len}\n".encode())

            elif cmd == "CODA":
                with coda_lock:
                    coda_len = len(coda)
                conn.sendall(f"Coda: {coda_len}\n".encode())

            elif cmd == "ESCI":
                conn.sendall(b"Arrivederci!\n")
                break

            else:
                conn.sendall(b"Comando sconosciuto.\n")

    except (ConnectionResetError, OSError):
        pass
    finally:
        conn.close()
        print(f"SERVER - Connessione chiusa: {addr} ({studente})")

# Avvia il server
def main():
    init_csv()
    threading.Thread(target=worker, daemon=True).start()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen()
        print(f"SERVER - ascolto su {HOST}:{PORT}")
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=gestisci_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
