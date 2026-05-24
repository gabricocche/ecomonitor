# 🌿 EcoMonitor

### 🧩 Descrizione del Progetto

Questo progetto consiste in un **sistema di monitoraggio ambientale** sviluppato in **Python** per la raccolta e l'elaborazione dei dati e in **Streamlit** per la dashboard di visualizzazione.

**Stato:** Funzionante. Il progetto è ancora in fase di sviluppo, perciò è da considerare inattendibile per un utilizzo costante.

L'applicazione consente di:

- 📡 **Raccogliere** misure ambientali (luminosità e rumore) direttamente da smartphone tramite **phyphox**
- 💾 **Salvare** i dati in un file **CSV** in modo automatico
- 📊 **Visualizzare** i dati in tempo reale tramite una **dashboard Streamlit**
- 🔍 **Filtrare** le misure per sensore, luogo e studente
- 🏆 **Confrontare** i dati tra aule, corridoi e momenti diversi della giornata

**Linguaggi & tecnologie:**  
I dati vengono raccolti via **Wi-Fi** dall'app phyphox e salvati su file CSV per garantire la **persistenza delle informazioni**. La dashboard è realizzata con **Streamlit** e **pandas**, mentre la comunicazione con phyphox avviene tramite le sue **API**.

---

## 👥 Autori

- [@Aldofredi Nicholas](https://github.com/aldofredinicholas)
- [@Gabriele Cocchetti](https://github.com/gabricocche)
- [@Stefano Losio](https://github.com/StefanoLosio)

---

## ▶️ Avvio rapido

1. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

2. Apri l'esperimento su phyphox, attiva l'**accesso remoto** e annota l'IP mostrato

3. Avvia `server.py` in un terminale:
   ```bash
   python server.py
   ```

4. Avvia `phyphox_reader.py` indicando i tuoi parametri:
   ```bash
   python phyphox_reader.py --ip "192.168.1.42" --studente "Il tuo nome" --luogo "aula_4A"
   ```
   Puoi vedere tutte le opzioni con `python phyphox_reader.py --help`.

5. Avvia la dashboard in un altro terminale:
   ```bash
   streamlit run dashboard.py
   ```

6. Apri il browser su `http://localhost:8501`

---

## 📁 Struttura del progetto

```
ecomonitor/
├── server.py           ← server socket per raccolta misure
├── client.py           ← client per inviare misure al server
├── phyphox_reader.py   ← legge i dati da phyphox
├── dashboard.py        ← dashboard Streamlit per visualizzazione
├── style.css           ← stile della dashboard
├── requirements.txt    ← dipendenze del progetto
└── misure.csv          ← dati raccolti (generato automaticamente)
```

---

## ⚖️ Licenza

Distribuito sotto licenza **[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/deed.it)**  
> È consentito condividere il progetto con attribuzione, ma **non è consentito modificarlo o usarlo a fini commerciali**.

---

## 📬 Contatti

Per qualsiasi domanda o segnalazione:  
- ✉️ mail@gabrielecocchetti.it
- ✉️ stefanolosio2008@gmail.com
- ✉️ aldofredi.nicholas@gmail.com

---

## ⚠️ Avvertenza

Questo progetto è stato sviluppato nell'ambito di una **UDA scolastica** — Sostenibilità ambientale, Classe 4EI ITIS Informatica.  
Tutti i contenuti sono da considerarsi **non definitivi** e **non destinati a un riutilizzo professionale**.
