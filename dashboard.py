import streamlit as st
import pandas as pd
import os
import tempfile

st.set_page_config(page_title="EcoMonitor", page_icon="🌿", layout="wide")

# Carica i CSS custom
with open("style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

CSV_FILE = "misure.csv"
COLONNE = ["studente", "sensore", "valore", "luogo", "data_ora"]

# Carica il CSV con cache di 3 secondi
@st.cache_data(ttl=3)
def carica_dati(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=COLONNE)
    df = pd.read_csv(path, parse_dates=["data_ora"])
    df["valore"] = pd.to_numeric(df["valore"], errors="coerce")
    df.dropna(subset=["valore"], inplace=True)
    return df

# Importa dati da file CSV caricato
def importa_nel_db(file_path) -> tuple[int, int]:
    try:
        df_nuovo = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
        return 0, 0

    # Verifica colonne obbligatorie
    colonne_richieste = {"studente", "sensore", "valore", "luogo"}
    if not colonne_richieste.issubset(df_nuovo.columns):
        mancanti = colonne_richieste - set(df_nuovo.columns)
        st.error(f"Colonne mancanti nel file importato: {mancanti}")
        return 0, 0

    # Aggiunge data_ora se mancante
    if "data_ora" not in df_nuovo.columns:
        df_nuovo["data_ora"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    df_nuovo = df_nuovo[COLONNE].copy()
    df_nuovo["valore"] = pd.to_numeric(df_nuovo["valore"], errors="coerce")
    df_nuovo.dropna(subset=["valore"], inplace=True)

    # Unisce con i dati esistenti e rimuove duplicati
    df_db = carica_dati(CSV_FILE)
    n_prima_db = len(df_db)
    df_merged = pd.concat([df_db, df_nuovo], ignore_index=True)
    df_merged["data_ora"] = df_merged["data_ora"].astype(str)
    df_merged.drop_duplicates(inplace=True)

    aggiunte = len(df_merged) - n_prima_db
    duplicate = len(df_nuovo) - aggiunte

    df_merged.to_csv(CSV_FILE, index=False)
    st.cache_data.clear()
    return aggiunte, duplicate

# Elabora e importa dati da phyphox grezzo
def elabora_phyphox(df_phy, nuovo_studente, nuovo_sensore, nuovo_luogo) -> tuple[int, int]:
    # Prende prima colonna (tempo) e seconda colonna (valore)
    tempi = df_phy.iloc[:, 0].copy()
    valori = df_phy.iloc[:, 1].copy()

    df_clean = pd.DataFrame({"time": tempi, "valore": valori})
    df_clean["time"] = pd.to_numeric(df_clean["time"], errors="coerce")
    df_clean["valore"] = pd.to_numeric(df_clean["valore"], errors="coerce")
    df_clean.dropna(inplace=True)

    # Una misurazione per secondo intero
    df_clean["sec"] = df_clean["time"].astype(int)
    df_clean = df_clean.drop_duplicates(subset=["sec"])

    # Calcola orari incrementali
    start_time = pd.Timestamp.now()
    df_clean["data_ora"] = df_clean["sec"].apply(
        lambda s: (start_time + pd.Timedelta(seconds=int(s))).strftime("%Y-%m-%d %H:%M:%S")
    )

    # Crea dataframe nel formato del DB
    df_nuovo = pd.DataFrame({
        "studente": nuovo_studente,
        "sensore": nuovo_sensore,
        "valore": df_clean["valore"].values,
        "luogo": nuovo_luogo,
        "data_ora": df_clean["data_ora"].values
    })

    # Salva in file temporaneo
    with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False, encoding='utf-8') as tmp:
        df_nuovo.to_csv(tmp, index=False)
        tmp_path = tmp.name

    try:
        aggiunte, duplicate = importa_nel_db(tmp_path)
        return aggiunte, duplicate
    finally:
        os.remove(tmp_path)

st.title("EcoMonitor – UDA")
st.caption("Progetto di Aldofredi, Cocchetti e Losio")

df_raw = carica_dati(CSV_FILE)

# Sidebar con filtri
with st.sidebar:
    st.header("Filtri")

    sensori_disponibili = sorted(df_raw["sensore"].unique().tolist()) if not df_raw.empty else []
    sensori_scelti = st.multiselect("Filtra per sensore", options=sensori_disponibili, default=sensori_disponibili)

    luoghi_disponibili = sorted(df_raw["luogo"].unique().tolist()) if not df_raw.empty else []
    luoghi_scelti = st.multiselect("Filtra per luogo", options=luoghi_disponibili, default=luoghi_disponibili)

    studenti_disponibili = sorted(df_raw["studente"].unique().tolist()) if not df_raw.empty else []
    studenti_scelti = st.multiselect("Filtra per studente", options=studenti_disponibili, default=studenti_disponibili)

    st.divider()
    if st.button("Aggiorna dati"):
        st.cache_data.clear()
        st.rerun()

    # Import dei dati
    st.divider()
    st.subheader("Importa Dati")
    tipo_import = st.radio("Tipo di file", ["CSV Phyphox (Grezzo)", "Backup Database (Completo)"])
    file_caricato = st.file_uploader("Carica un file CSV", type="csv", label_visibility="collapsed")

    if file_caricato is not None:
        if tipo_import == "Backup Database (Completo)":
            if st.button("Importa nel database"):
                aggiunte, duplicate = importa_nel_db(file_caricato)
                if aggiunte > 0:
                    st.success(f"✅ {aggiunte} righe aggiunte al database.")
                else:
                    st.info("Nessuna riga nuova da aggiungere.")
                if duplicate > 0:
                    st.warning(f"⚠️ {duplicate} righe duplicate ignorate.")
                st.rerun()
        else:
            st.markdown("📝 **Dettagli misurazione**")
            nuovo_studente = st.text_input("Studente")
            nuovo_sensore = st.text_input("Sensore (es. rumore, luce)")
            nuovo_luogo = st.text_input("Luogo")

            if st.button("Elabora e Importa"):
                if not nuovo_studente or not nuovo_sensore or not nuovo_luogo:
                    st.error("Compila tutti i campi prima di importare.")
                else:
                    try:
                        # Leggi il file di phyphox con rilevamento separatore
                        file_caricato.seek(0)
                        try:
                            df_phy = pd.read_csv(file_caricato, sep=',')
                            if len(df_phy.columns) < 2:
                                file_caricato.seek(0)
                                df_phy = pd.read_csv(file_caricato, sep=';')
                            if len(df_phy.columns) < 2:
                                file_caricato.seek(0)
                                df_phy = pd.read_csv(file_caricato, sep='\t')
                        except Exception as e:
                            st.error(f"Impossibile leggere il file CSV: {e}")
                            st.stop()

                        if len(df_phy.columns) < 2:
                            st.error("Il file non sembra avere il formato Phyphox corretto (richieste almeno 2 colonne).")
                        else:
                            aggiunte, duplicate = elabora_phyphox(df_phy, nuovo_studente, nuovo_sensore, nuovo_luogo)
                            if aggiunte > 0:
                                st.success(f"✅ {aggiunte} misurazioni importate da Phyphox.")
                            else:
                                st.info("Nessuna riga valida trovata o importata.")
                            if duplicate > 0:
                                st.warning(f"⚠️ {duplicate} righe duplicate ignorate.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Errore durante l'elaborazione: {e}")

# Controlla se ci sono dati
if df_raw.empty:
    st.warning("Nessun dato trovato. Importa un CSV o avvia phyphox_reader.py.")
    st.stop()

# Applica filtri
df = df_raw[
    df_raw["sensore"].isin(sensori_scelti)
    & df_raw["luogo"].isin(luoghi_scelti)
    & df_raw["studente"].isin(studenti_scelti)
].copy()

if df.empty:
    st.info("Nessuna misura corrisponde ai filtri selezionati.")
    st.stop()

# Metriche principali
st.subheader("Riepilogo generale delle misurazioni")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Misure totali", len(df))
col2.metric("Studenti attivi", df["studente"].nunique())
col3.metric("Sensori utilizzati", df["sensore"].nunique())
col4.metric("Luoghi monitorati", df["luogo"].nunique())

st.divider()

# Statistiche per sensore
st.subheader("Statistiche per sensore")
stats_sensore = (
    df.groupby("sensore")["valore"]
    .agg(["count", "mean", "min", "max"])
    .rename(columns={"count": "N misure", "mean": "Media", "min": "Min", "max": "Max"})
    .round(3)
    .reset_index()
    .rename(columns={"sensore": "Sensore"})
)
st.dataframe(stats_sensore, use_container_width=True, hide_index=True)

st.divider()

# Grafici
st.subheader("Grafici")
tab1, tab2, tab3, tab4 = st.tabs(["Per luogo", "Per studente", "Andamento temporale", "Classifica luoghi"])

# Media dei sensori per luogo
with tab1:
    for sensore in df["sensore"].unique():
        df_s = df[df["sensore"] == sensore]
        media_luogo = (
            df_s.groupby("luogo")["valore"]
            .mean()
            .reset_index()
            .rename(columns={"luogo": "Luogo", "valore": f"Media {sensore}"})
            .sort_values(f"Media {sensore}", ascending=False)
        )
        st.markdown(f"**Sensore: {sensore}**")
        st.bar_chart(media_luogo, x="Luogo", y=f"Media {sensore}", color="#4caf72")

# Numero di misure per studente
with tab2:
    misure_studente = (
        df.groupby("studente")
        .size()
        .reset_index(name="N misure")
        .sort_values("N misure", ascending=False)
    )
    st.bar_chart(misure_studente, x="studente", y="N misure", color="#4caf72")

# Andamento nel tempo per sensore
with tab3:
    for sensore in df["sensore"].unique():
        df_s = df[df["sensore"] == sensore].copy()
        df_s = df_s[df_s["valore"] >= 0]

        if df_s.empty:
            st.info(f"Nessun dato valido per {sensore}.")
            continue

        if df_s["data_ora"].nunique() <= 1:
            df_s = df_s.reset_index(drop=True)
            df_s["campione"] = df_s.index + 1
            st.markdown(f"**Andamento {sensore} (campioni sequenziali)**")
            st.line_chart(df_s, x="campione", y="valore", color="#4caf72")
        else:
            df_s = df_s.sort_values("data_ora")
            st.markdown(f"**Andamento {sensore} nel tempo**")
            st.line_chart(df_s, x="data_ora", y="valore", color="#4caf72")

# Classifica dei luoghi per valore medio
with tab4:
    st.markdown("Luoghi ordinati per valore medio (dal più alto al più basso).")
    for sensore in df["sensore"].unique():
        df_s = df[df["sensore"] == sensore]
        classifica = (
            df_s.groupby("luogo")["valore"]
            .mean()
            .reset_index()
            .rename(columns={"luogo": "Luogo", "valore": "Media"})
            .sort_values("Media", ascending=False)
            .reset_index(drop=True)
        )
        classifica.index += 1
        classifica["Media"] = classifica["Media"].round(3)
        st.markdown(f"**Classifica – {sensore}**")
        st.dataframe(classifica, use_container_width=True)

st.divider()

# Tabella completa
st.subheader("Tabella completa delle misure")
df_display = df[COLONNE].copy().sort_values("data_ora", ascending=False).reset_index(drop=True)
df_display.index += 1
st.dataframe(df_display, use_container_width=True)

# Download CSV
csv_bytes = df_display.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Scarica dati filtrati (CSV)",
    data=csv_bytes,
    file_name="misure_filtrate.csv",
    mime="text/csv",
)

st.caption("EcoMonitor - UDA - Aldofredi, Cocchetti, Losio")
