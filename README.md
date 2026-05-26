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

## ▶️ Avvio rapido (con phyphox)

1. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

2. Apri l'esperimento su phyphox, attiva l'**accesso remoto** e annota l'IP mostrato

3. Avvia `phyphox_reader.py` in un terminale:
   ```bash
   python phyphox_reader.py --ip "192.168.1.42" --studente "Il tuo nome" --luogo "aula_4A"
   ```

4. Avvia la dashboard in un altro terminale:
   ```bash
   streamlit run dashboard.py
   ```

5. Apri il browser su `http://localhost:8501`

---

## ▶️ Avvio alternativo (con server TCP + client CLI)

Se preferisci inserire i dati manualmente da riga di comando:

1. Avvia il server:
   ```bash
   python server.py
   ```

2. Avvia il client in un altro terminale:
   ```bash
   python client.py
   ```

---

## 📁 Struttura del progetto

```
ecomonitor/
├── phyphox_reader.py   ← legge i dati da phyphox via Wi-Fi
├── dashboard.py        ← dashboard Streamlit
├── style.css           ← stile della dashboard
├── server.py           ← server TCP (per uso via client CLI)
├── client.py           ← client CLI
├── requirements.txt
└── misure.csv          ← database misure (generato automaticamente)
```

---

## ⚖️ Licenza

Distribuito sotto licenza **[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/deed.it)**  
> È consentito condividere il progetto con attribuzione, ma **non è consentito modificarlo o usarlo a fini commerciali**.

---

## 📬 Contatti

Per qualsiasi domanda o segnalazione:
- ✉️ aldofredi.nicholas@gmail.com
- ✉️ mail@gabrielecocchetti.it
- ✉️ stefanolosio2008@gmail.com

---

## ⚠️ Avvertenza

Questo progetto è stato sviluppato nell'ambito dell' **UDA scolastica** di TPI — Sostenibilità ambientale, Classe 4EI.  
Tutti i contenuti sono da considerarsi **non definitivi** e **non destinati a un riutilizzo professionale**.
