import streamlit as st
import pandas as pd
import os
import tempfile

st.set_page_config(page_title="EcoMonitor", page_icon="🌿", layout="wide")

with open("style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

CSV_FILE = "misure.csv"
COLONNE  = ["studente", "sensore", "valore", "luogo", "data_ora"]

UNITA_MISURA = {
    "rumore": "dB",
    "suono": "dB",
    "luce": "lux",
    "illuminamento": "lux",
    "temperatura": "°C",
    "umidita": "%",
    "umidità": "%",
    "pressione": "hPa",
    "accelerazione": "m/s²",
    "velocita": "m/s",
    "velocità": "m/s",
    "magnetico": "µT"
}

def get_unita(sensore: str) -> str:
    s = str(sensore).lower()
    for k, v in UNITA_MISURA.items():
        if k in s:
            return v
    return ""

@st.cache_data(ttl=3)
def carica_dati(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=COLONNE)
    df = pd.read_csv(path, parse_dates=["data_ora"])
    df["valore"] = pd.to_numeric(df["valore"], errors="coerce")
    df.dropna(subset=["valore"], inplace=True)
    return df


def importa_nel_db(file_path) -> tuple[int, int]:
    try:
        df_nuovo = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
        return 0, 0

    colonne_richieste = {"studente", "sensore", "valore", "luogo"}
    if not colonne_richieste.issubset(df_nuovo.columns):
        mancanti = colonne_richieste - set(df_nuovo.columns)
        st.error(f"Colonne mancanti nel file importato: {mancanti}")
        return 0, 0

    if "data_ora" not in df_nuovo.columns:
        df_nuovo["data_ora"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    df_nuovo = df_nuovo[COLONNE].copy()
    df_nuovo["valore"] = pd.to_numeric(df_nuovo["valore"], errors="coerce")
    df_nuovo.dropna(subset=["valore"], inplace=True)

    df_db = carica_dati(CSV_FILE)
    n_prima_db = len(df_db)
    df_merged = pd.concat([df_db, df_nuovo], ignore_index=True)
    df_merged["data_ora"] = df_merged["data_ora"].astype(str)
    df_merged.drop_duplicates(inplace=True)

    aggiunte  = len(df_merged) - n_prima_db
    duplicate = len(df_nuovo) - aggiunte

    df_merged.to_csv(CSV_FILE, index=False)
    st.cache_data.clear()
    return aggiunte, duplicate


def elabora_phyphox(df_phy: pd.DataFrame, colonna_valore: str, studente: str, sensore: str, luogo: str) -> tuple[int, int]:
    # usa la colonna scelta dall'utente invece di hardcodare iloc[:,1]
    time_col = df_phy.columns[0]

    df_clean = pd.DataFrame({
        "time":   pd.to_numeric(df_phy[time_col],      errors="coerce"),
        "valore": pd.to_numeric(df_phy[colonna_valore], errors="coerce"),
    })
    df_clean.dropna(inplace=True)

    # una misurazione per secondo intero
    df_clean["sec"] = df_clean["time"].astype(int)
    df_clean = df_clean.drop_duplicates(subset=["sec"])

    start_time = pd.Timestamp.now()
    df_clean["data_ora"] = df_clean["sec"].apply(
        lambda s: (start_time + pd.Timedelta(seconds=int(s))).strftime("%Y-%m-%d %H:%M:%S")
    )

    df_nuovo = pd.DataFrame({
        "studente": studente,
        "sensore":  sensore,
        "valore":   df_clean["valore"].values,
        "luogo":    luogo,
        "data_ora": df_clean["data_ora"].values,
    })

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        df_nuovo.to_csv(tmp, index=False)
        tmp_path = tmp.name

    try:
        return importa_nel_db(tmp_path)
    finally:
        os.remove(tmp_path)


# titolo 
st.title("EcoMonitor – UDA")
st.caption("Progetto di Aldofredi, Cocchetti e Losio")

df_raw = carica_dati(CSV_FILE)

# sidebar
with st.sidebar:
    st.header("Filtri")

    sensori_disponibili = sorted(df_raw["sensore"].unique().tolist()) if not df_raw.empty else []
    sensori_scelti = st.multiselect("Filtra per sensore",   options=sensori_disponibili, default=sensori_disponibili)

    luoghi_disponibili = sorted(df_raw["luogo"].unique().tolist()) if not df_raw.empty else []
    luoghi_scelti = st.multiselect("Filtra per luogo",      options=luoghi_disponibili, default=luoghi_disponibili)

    studenti_disponibili = sorted(df_raw["studente"].unique().tolist()) if not df_raw.empty else []
    studenti_scelti = st.multiselect("Filtra per studente", options=studenti_disponibili, default=studenti_disponibili)

    st.divider()
    if st.button("Aggiorna dati"):
        st.cache_data.clear()
        st.rerun()

    # import
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
            # leggi le colonne del file phyphox prima di mostrare il form
            try:
                file_caricato.seek(0)
                # tenta i separatori più comuni
                df_phy_preview = None
                for sep in [",", ";", "\t"]:
                    file_caricato.seek(0)
                    df_tmp = pd.read_csv(file_caricato, sep=sep, nrows=3)
                    if len(df_tmp.columns) >= 2:
                        df_phy_preview = df_tmp
                        break

                if df_phy_preview is None or len(df_phy_preview.columns) < 2:
                    st.error("Il file non ha il formato phyphox corretto (servono almeno 2 colonne).")
                else:
                    colonne_phy = list(df_phy_preview.columns)

                    st.markdown("**Dettagli misurazione**")
                    nuovo_studente = st.text_input("Studente")
                    nuovo_sensore  = st.text_input("Sensore (es. rumore, luce)")
                    nuovo_luogo    = st.text_input("Luogo")

                    # mostra le colonne disponibili con anteprima del valore
                    opzioni = {
                        f"{col}  (es. {df_phy_preview[col].iloc[0]})" : col
                        for col in colonne_phy[1:]   # salta la prima (è il tempo)
                    }
                    scelta_label = st.selectbox("Colonna del valore da importare", options=list(opzioni.keys()))
                    colonna_scelta = opzioni[scelta_label]

                    if st.button("Elabora e Importa"):
                        if not nuovo_studente or not nuovo_sensore or not nuovo_luogo:
                            st.error("Compila tutti i campi prima di importare.")
                        else:
                            try:
                                file_caricato.seek(0)
                                for sep in [",", ";", "\t"]:
                                    file_caricato.seek(0)
                                    df_phy = pd.read_csv(file_caricato, sep=sep)
                                    if len(df_phy.columns) >= 2:
                                        break

                                aggiunte, duplicate = elabora_phyphox(
                                    df_phy, colonna_scelta,
                                    nuovo_studente, nuovo_sensore, nuovo_luogo
                                )
                                if aggiunte > 0:
                                    st.success(f"✅ {aggiunte} misurazioni importate.")
                                else:
                                    st.info("Nessuna riga valida trovata.")
                                if duplicate > 0:
                                    st.warning(f"⚠️ {duplicate} righe duplicate ignorate.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Errore durante l'elaborazione: {e}")

            except Exception as e:
                st.error(f"Errore nella lettura del file: {e}")


# controllo dati
if df_raw.empty:
    st.warning("Nessun dato trovato. Importa un CSV o avvia phyphox_reader.py.")
    st.stop()

df = df_raw[
    df_raw["sensore"].isin(sensori_scelti)
    & df_raw["luogo"].isin(luoghi_scelti)
    & df_raw["studente"].isin(studenti_scelti)
].copy()

if df.empty:
    st.info("Nessuna misura corrisponde ai filtri selezionati.")
    st.stop()

# metriche
st.subheader("Riepilogo generale delle misurazioni")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Misure totali",      len(df))
col2.metric("Studenti attivi",    df["studente"].nunique())
col3.metric("Sensori utilizzati", df["sensore"].nunique())
col4.metric("Luoghi monitorati",  df["luogo"].nunique())

st.divider()

# statistiche
st.subheader("Statistiche per sensore")
stats_sensore = (
    df.groupby("sensore")["valore"]
    .agg(["count", "mean", "min", "max"])
    .rename(columns={"count": "N misure", "mean": "Media", "min": "Min", "max": "Max"})
    .round(3).reset_index().rename(columns={"sensore": "Sensore"})
)
stats_sensore["Unità"] = stats_sensore["Sensore"].apply(get_unita)
cols = list(stats_sensore.columns)
cols.insert(1, cols.pop(cols.index("Unità")))
stats_sensore = stats_sensore[cols]
st.dataframe(stats_sensore, use_container_width=True, hide_index=True)

st.divider()

# grafici
st.subheader("Grafici")
tab1, tab2, tab3, tab4 = st.tabs(["Per luogo", "Per studente", "Andamento temporale", "Classifica luoghi"])

with tab1:
    for sensore in df["sensore"].unique():
        df_s = df[df["sensore"] == sensore]
        unita = get_unita(sensore)
        etichetta = f"Media {sensore} ({unita})" if unita else f"Media {sensore}"
        
        media_luogo = (
            df_s.groupby("luogo")["valore"].mean().reset_index()
            .rename(columns={"luogo": "Luogo", "valore": etichetta})
            .sort_values(etichetta, ascending=False)
        )
        st.markdown(f"**Sensore: {sensore}**")
        st.bar_chart(media_luogo, x="Luogo", y=etichetta, color="#4caf72")

with tab2:
    misure_studente = (
        df.groupby("studente").size().reset_index(name="N misure")
        .sort_values("N misure", ascending=False)
    )
    st.bar_chart(misure_studente, x="studente", y="N misure", color="#4caf72")

with tab3:
    for sensore in df["sensore"].unique():
        df_s = df[df["sensore"] == sensore].copy()
        df_s = df_s[df_s["valore"] >= 0]
        if df_s.empty:
            st.info(f"Nessun dato valido per {sensore}.")
            continue
            
        unita = get_unita(sensore)
        col_valore = f"valore ({unita})" if unita else "valore"
        df_s.rename(columns={"valore": col_valore}, inplace=True)
            
        if df_s["data_ora"].nunique() <= 1:
            df_s = df_s.reset_index(drop=True)
            df_s["campione"] = df_s.index + 1
            st.markdown(f"**Andamento {sensore} (campioni sequenziali)**")
            st.line_chart(df_s, x="campione", y=col_valore, color="#4caf72")
        else:
            df_s = df_s.sort_values("data_ora")
            st.markdown(f"**Andamento {sensore} nel tempo**")
            st.line_chart(df_s, x="data_ora", y=col_valore, color="#4caf72")

with tab4:
    st.markdown("Luoghi ordinati per valore medio (dal più alto al più basso).")
    for sensore in df["sensore"].unique():
        df_s = df[df["sensore"] == sensore]
        unita = get_unita(sensore)
        col_media = f"Media ({unita})" if unita else "Media"
        
        classifica = (
            df_s.groupby("luogo")["valore"].mean().reset_index()
            .rename(columns={"luogo": "Luogo", "valore": col_media})
            .sort_values(col_media, ascending=False).reset_index(drop=True)
        )
        classifica.index += 1
        classifica[col_media] = classifica[col_media].round(3)
        st.markdown(f"**Classifica – {sensore}**")
        st.dataframe(classifica, use_container_width=True)

st.divider()

# tabella completa
st.subheader("Tabella completa delle misure")
df_display = df[COLONNE].copy().sort_values("data_ora", ascending=False).reset_index(drop=True)
df_display.index += 1
df_display.insert(2, "unità", df_display["sensore"].apply(get_unita))
st.dataframe(df_display, use_container_width=True)

csv_bytes = df_display.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Scarica dati filtrati (CSV)",
    data=csv_bytes,
    file_name="misure_filtrate.csv",
    mime="text/csv",
)

st.caption("EcoMonitor - UDA - Aldofredi, Cocchetti, Losio")
