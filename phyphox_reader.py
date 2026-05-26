"""
per l'avvio fare il seguente comando: python phyphox_reader.py --ip 192.168.1.x --studente Nome --luogo posto
"""

import requests
import csv
import io
import zipfile
import argparse
from datetime import datetime, timedelta

CSV_FILE = "misure.csv"
COLONNE  = ["studente", "sensore", "valore", "luogo", "data_ora"]


def trova_porta(ip: str) -> str | None:
    for porta in [8080, 80]:
        try:
            r = requests.get(f"http://{ip}:{porta}/", timeout=3)
            if r.ok:
                return str(porta)
        except Exception:
            continue
    return None


def parse_csv_testo(testo: str) -> list[dict]:
    testo = testo.replace("\r\n", "\n").replace("\r", "\n")
    righe = testo.splitlines()
    idx = 0
    delimiter = ","
    for i, riga in enumerate(righe):
        if not riga.strip():
            continue
        for d in [",", "\t", ";"]:
            if len(riga.split(d)) >= 2:
                idx = i
                delimiter = d
                break
        if idx == i:
            break
    return list(csv.DictReader(io.StringIO("\n".join(righe[idx:])), delimiter=delimiter))


def scarica_csv_phyphox(ip: str, porta: str) -> list[dict]:
    r = requests.get(f"http://{ip}:{porta}/export?format=2", timeout=10)
    r.raise_for_status()
    raw = r.content

    if raw[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(raw))
        csv_files = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_files:
            raise ValueError("ZIP senza file CSV dentro.")
        migliore = []
        for nome in csv_files:
            testo = zf.read(nome).decode("utf-8", errors="replace")
            righe = parse_csv_testo(testo)
            if len(righe) > len(migliore):
                migliore = righe
        return migliore

    return parse_csv_testo(raw.decode("utf-8", errors="replace"))


def salva_nel_db(righe: list[dict], studente: str, sensore: str, luogo: str, colonna: str, start_time: datetime) -> int:
    # start_time passato come parametro
    if not righe:
        return 0
    if colonna not in righe[0]:
        raise ValueError(f"Colonna '{colonna}' non trovata nei dati.")

    esistenti = set()
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                esistenti.add(tuple(row))
    except FileNotFoundError:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLONNE)

    aggiunte = 0
    time_col = list(righe[0].keys())[0]
    ultimo_secondo = -1

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for riga in righe:
            try:
                time_s = float(str(riga.get(time_col, "")).replace(",", "."))
                int_sec = int(time_s)
            except (ValueError, TypeError):
                continue

            if int_sec <= ultimo_secondo:
                continue
            ultimo_secondo = int_sec

            try:
                valore = float(str(riga.get(colonna, "")).replace(",", "."))
            except (ValueError, TypeError):
                continue

            # usa start_time del singolo import, non dell'avvio script
            data_ora = (start_time + timedelta(seconds=int_sec)).strftime("%Y-%m-%d %H:%M:%S")

            nuova = (studente, sensore, str(round(valore, 4)), luogo, data_ora)
            if nuova not in esistenti:
                writer.writerow(nuova)
                esistenti.add(nuova)
                aggiunte += 1

    return aggiunte


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",       required=True)
    parser.add_argument("--studente", required=True)
    parser.add_argument("--luogo",    required=True)
    parser.add_argument("--porta",    default=None)
    args = parser.parse_args()

    print(f"\nEcoMonitor – connessione a phyphox su {args.ip} ...")

    porta = args.porta
    if porta is None:
        print("  Ricerca porta...", end=" ", flush=True)
        porta = trova_porta(args.ip)
        if porta:
            print(f"trovata porta {porta}")
        else:
            print("\n\n[ERRORE] Impossibile connettersi a phyphox.")
            print("  Controlla che:")
            print("  1. Il telefono sia sulla stessa rete Wi-Fi del PC")
            print(f"  2. L'IP sia corretto (ora: {args.ip})")
            print("  3. In phyphox: ⋮ → 'Allow Remote Access' sia attivo")
            print("  4. L'esperimento sia aperto (non solo l'app)")
            return

    # scarica anteprima per scegliere la colonna
    print(f"  Scarico anteprima...", end=" ", flush=True)
    try:
        righe_test = scarica_csv_phyphox(args.ip, porta)
    except Exception as e:
        print(f"\n[ERRORE] {e}")
        return

    if not righe_test:
        print("\n[ERRORE] Nessun dato. Avvia la misurazione su phyphox prima di importare.")
        return

    colonne = list(righe_test[0].keys())
    print(f"OK — {len(righe_test)} righe trovate\n")

    print("Colonne disponibili:")
    for i, col in enumerate(colonne, 1):
        print(f"  {i}. {col!r}  →  es. {righe_test[0].get(col, '')!r}")

    while True:
        scelta = input("\nQuale colonna contiene il valore da salvare? (numero): ").strip()
        if scelta.isdigit() and 1 <= int(scelta) <= len(colonne):
            colonna_scelta = colonne[int(scelta) - 1]
            break
        print("  Numero non valido.")

    print(f"  Colonna scelta: '{colonna_scelta}'\n")
    sensore = input("Come si chiama questo sensore nel CSV? (es. luce, rumore): ").strip().lower() or "sconosciuto"
    print(f"\nOK — salverò '{sensore}' da '{colonna_scelta}'")
    print("Premi INVIO ogni volta che vuoi importare i dati attuali. Ctrl+C per uscire.\n")

    while True:
        try:
            input("[ INVIO per importare ] ")
        except KeyboardInterrupt:
            print("\nUscita.")
            break

        print("  Download...", end=" ", flush=True)
        try:
            start_time = datetime.now()   # timestamp fresco ad ogni import
            righe = scarica_csv_phyphox(args.ip, porta)
            n = salva_nel_db(righe, args.studente, sensore, args.luogo, colonna_scelta, start_time)
            print(f"OK — {n} nuove righe salvate in {CSV_FILE}.")
        except Exception as e:
            print(f"\n  [ERRORE] {e}")

        altro = input("  Cambiare sensore? (s/n): ").strip().lower()
        if altro == "s":
            sensore = input("  Nuovo nome sensore: ").strip().lower() or sensore
        print()


if __name__ == "__main__":
    main()
