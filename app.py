import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import calendar
from email_sender import invia_email

# Config
DETERMINE_CSV = "determine_dashboard.csv"
CALENDARIO_CSV = "eventi_calendario.csv"
TODO_CSV = "todo_list.csv"
UTENTI_JSON = "utenti.json"
LOGO = "stemma.png"

def carica_csv(path, columns, date_cols=[]):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    else:
        df = pd.DataFrame(columns=columns)
    return df

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    with open(UTENTI_JSON, "r") as f:
        utenti = json.load(f)

    st.image(LOGO, width=120)
    st.title("🔐 Accesso Segretaria Digitale ")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Accedi"):
        if username in utenti and utenti[username]["password"] == password:
            st.session_state["login"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("Credenziali non valide.")
    st.stop()

st.set_page_config(page_title="Segretaria Digitale ", layout="wide")
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.image(LOGO, width=80)
with col_title:
    st.markdown(f"## 👩‍💼 Benvenuto {st.session_state['user'].capitalize()}! 👋")

menu = st.sidebar.radio("Menu", [
    "🏠 Dashboard", 
    "📅 Eventi", 
    "📁 Determinazioni", 
    "✅ To-do", 
    "📬 Invia promemoria"
])
if menu == "🏠 Dashboard":
    st.subheader("📊 Panoramica generale")
    today = datetime.today().date()
    settimana = today + timedelta(days=7)

    eventi = carica_csv(CALENDARIO_CSV, ["Titolo", "Data", "Ora", "Descrizione"], ["Data"])
    determine = carica_csv(DETERMINE_CSV, ["Numero", "Data", "Capitolo", "Importo", "Oggetto", "Scadenza"], ["Scadenza"])
    todo = carica_csv(TODO_CSV, ["Attività", "Scadenza", "Stato"], ["Scadenza"])

    eventi_today = eventi[eventi["Data"].dt.date == today]
    eventi_settimana = eventi[(eventi["Data"].dt.date > today) & (eventi["Data"].dt.date <= settimana)]
    determ_today = determine[determine["Scadenza"].dt.date == today]
    attive = todo[todo["Stato"] == "Da fare"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Eventi oggi", len(eventi_today))
    with col2:
        st.metric("📁 Determine in scadenza oggi", len(determ_today))
    with col3:
        st.metric("✅ Attività da fare", len(attive))

    st.markdown("### 🔔 Avvisi del giorno")
    if not eventi_today.empty:
        st.warning(f"Hai {len(eventi_today)} evento/i in programma oggi:")
        st.dataframe(eventi_today)
    if not determ_today.empty:
        st.warning(f"Hai {len(determ_today)} determina/e in scadenza oggi:")
        st.dataframe(determ_today)

    st.markdown("### 🗓️ Calendario settimanale (griglia)")
    griglia = {calendar.day_name[i]: [] for i in range(7)}
    for _, row in eventi_settimana.iterrows():
        giorno = calendar.day_name[row["Data"].weekday()]
        ora = row["Ora"] if "Ora" in row and pd.notnull(row["Ora"]) else "–"
        griglia[giorno].append(f"🕒 {ora} - {row['Titolo']}")

    col1, col2 = st.columns(2)
    giorni = list(griglia.keys())
    for i, giorno in enumerate(giorni):
        with (col1 if i < 4 else col2):
            st.markdown(f"**{giorno}**")
            if griglia[giorno]:
                for evento in griglia[giorno]:
                    st.markdown(f"- {evento}")
            else:
                st.markdown("_Nessun evento_")

    st.markdown("### 📝 Attività da fare")
    if not attive.empty:
        st.dataframe(attive.dropna(subset=["Scadenza"]).sort_values("Scadenza"))
    else:
        st.success("Nessuna attività attiva! Ottimo lavoro!")
elif menu == "📅 Eventi":
    st.subheader("📅 Calendario Eventi")
    eventi = carica_csv(CALENDARIO_CSV, ["Titolo", "Data", "Ora", "Descrizione"], ["Data"])

    st.markdown("### ➕ Aggiungi nuovo evento")
    with st.form("nuovo_evento"):
        titolo = st.text_input("Titolo")
        data_evento = st.date_input("Data evento")
        ora_evento = st.time_input("Ora evento")
        descrizione = st.text_area("Descrizione")
        invia = st.form_submit_button("Aggiungi evento")
        if invia:
            nuova = pd.DataFrame([{
                "Titolo": titolo,
                "Data": data_evento,
                "Ora": ora_evento.strftime('%H:%M'),
                "Descrizione": descrizione
            }])
            eventi = pd.concat([eventi, nuova], ignore_index=True)
            eventi.to_csv(CALENDARIO_CSV, index=False)
            st.success("✅ Evento aggiunto!")

    st.markdown("### ✏️ Modifica o elimina evento")
    if not eventi.empty:
        selez = st.selectbox("Seleziona evento", eventi["Titolo"].unique())
        evento_sel = eventi[eventi["Titolo"] == selez].iloc[0]

        data_valida = pd.to_datetime(evento_sel["Data"], errors="coerce")
        if pd.isna(data_valida):
            data_valida = datetime.today()

        ora_valida = pd.to_datetime(evento_sel["Ora"], errors="coerce")
        if pd.isna(ora_valida):
            ora_valida = datetime.now()

        with st.form("modifica_evento"):
            nuovo_data = st.date_input("Data", value=data_valida.date())
            nuova_ora = st.time_input("Ora", value=ora_valida.time())
            nuova_descr = st.text_area("Descrizione", value=evento_sel["Descrizione"])
            col1, col2 = st.columns(2)
            with col1:
                aggiorna = st.form_submit_button("Aggiorna")
            with col2:
                elimina = st.form_submit_button("Elimina")
            if aggiorna:
                eventi.loc[eventi["Titolo"] == selez, ["Data", "Ora", "Descrizione"]] = [
                    nuovo_data, nuova_ora.strftime('%H:%M'), nuova_descr
                ]
                eventi.to_csv(CALENDARIO_CSV, index=False)
                st.success("✅ Evento aggiornato!")
            if elimina:
                eventi = eventi[eventi["Titolo"] != selez]
                eventi.to_csv(CALENDARIO_CSV, index=False)
                st.success("🗑️ Evento eliminato!")

    st.markdown("### 📄 Elenco eventi")
    eventi["Data"] = pd.to_datetime(eventi["Data"], errors="coerce")
    st.dataframe(eventi.dropna(subset=["Data"]).sort_values("Data"))


elif menu == "📁 Determinazioni":
    st.subheader("📁 Gestione Determinazioni")
    df = carica_csv(DETERMINE_CSV, ["Numero", "Data", "Capitolo", "Importo", "Oggetto", "Scadenza"], ["Scadenza"])
    df["Scadenza"] = pd.to_datetime(df["Scadenza"], errors="coerce")

    st.markdown("### ➕ Aggiungi nuova determina")
    with st.form("nuova_determina"):
        numero = st.text_input("Numero")
        data = st.date_input("Data", value=datetime.today())
        capitolo = st.text_input("Capitolo")
        importo = st.number_input("Importo", step=100.0)
        oggetto = st.text_area("Oggetto")
        scadenza = st.date_input("Scadenza")
        salva = st.form_submit_button("Salva")
        if salva:
            nuova = pd.DataFrame([[numero, data, capitolo, importo, oggetto, scadenza]], columns=df.columns)
            df = pd.concat([df, nuova], ignore_index=True)
            df.to_csv(DETERMINE_CSV, index=False)
            st.success("✅ Determina salvata!")

    st.markdown("### ✏️ Modifica o elimina determina")
    if not df.empty:
        selezionata = st.selectbox("Seleziona numero determina", df["Numero"].unique())
        row = df[df["Numero"] == selezionata].iloc[0]

        data_valida = pd.to_datetime(row["Data"], errors="coerce")
        scad_valida = pd.to_datetime(row["Scadenza"], errors="coerce")

        if pd.isna(data_valida):
            data_valida = datetime.today()
        if pd.isna(scad_valida):
            scad_valida = datetime.today()

        with st.form("modifica_determina"):
            nuovo_data = st.date_input("Data", value=data_valida.date())
            nuovo_capitolo = st.text_input("Capitolo", value=row["Capitolo"])
            nuovo_importo = st.number_input("Importo", value=float(row["Importo"]), step=100.0)
            nuovo_oggetto = st.text_area("Oggetto", value=row["Oggetto"])
            nuova_scadenza = st.date_input("Scadenza", value=scad_valida.date())
            col1, col2 = st.columns(2)
            with col1:
                aggiorna = st.form_submit_button("Aggiorna")
            with col2:
                elimina = st.form_submit_button("Elimina")
            if aggiorna:
                df.loc[df["Numero"] == selezionata, ["Data", "Capitolo", "Importo", "Oggetto", "Scadenza"]] = [
                    nuovo_data, nuovo_capitolo, nuovo_importo, nuovo_oggetto, nuova_scadenza
                ]
                df.to_csv(DETERMINE_CSV, index=False)
                st.success(f"✅ Determina {selezionata} aggiornata con successo!")
            if elimina:
                df = df[df["Numero"] != selezionata]
                df.to_csv(DETERMINE_CSV, index=False)
                st.success(f"🗑️ Determina {selezionata} eliminata!")

    st.markdown("### 📄 Elenco completo delle determinazioni")
    st.dataframe(df.dropna(subset=["Scadenza"]).sort_values("Scadenza"))


elif menu == "✅ To-do":
    st.subheader("✅ Elenco Attività")
    todo = carica_csv(TODO_CSV, ["Attività", "Scadenza", "Stato"], ["Scadenza"])
    todo["Scadenza"] = pd.to_datetime(todo["Scadenza"], errors="coerce")

    st.markdown("### ➕ Aggiungi nuova attività")
    with st.form("nuova_attivita"):
        attivita = st.text_input("Attività")
        scadenza = st.date_input("Scadenza")
        stato = st.selectbox("Stato", ["Da fare", "Completato"])
        invia = st.form_submit_button("Salva attività")
        if invia:
            nuova = pd.DataFrame([[attivita, scadenza, stato]], columns=todo.columns)
            todo = pd.concat([todo, nuova], ignore_index=True)
            todo.to_csv(TODO_CSV, index=False)
            st.success("✅ Attività aggiunta!")

    st.markdown("### ✏️ Modifica o elimina attività")
    if not todo.empty:
        selez = st.selectbox("Seleziona attività", todo["Attività"].unique())
        att_sel = todo[todo["Attività"] == selez].iloc[0]

        scad_valida = pd.to_datetime(att_sel["Scadenza"], errors="coerce")
        if pd.isna(scad_valida):
            scad_valida = datetime.today()

        with st.form("modifica_attivita"):
            nuova_scad = st.date_input("Scadenza", value=scad_valida.date())
            nuovo_stato = st.selectbox("Stato", ["Da fare", "Completato"], index=0 if att_sel["Stato"] == "Da fare" else 1)
            col1, col2 = st.columns(2)
            with col1:
                aggiorna = st.form_submit_button("Aggiorna")
            with col2:
                elimina = st.form_submit_button("Elimina")
            if aggiorna:
                todo.loc[todo["Attività"] == selez, ["Scadenza", "Stato"]] = [nuova_scad, nuovo_stato]
                todo.to_csv(TODO_CSV, index=False)
                st.success("✅ Attività aggiornata!")
            if elimina:
                todo = todo[todo["Attività"] != selez]
                todo.to_csv(TODO_CSV, index=False)
                st.success("🗑️ Attività eliminata!")

    st.markdown("### 📄 Elenco Attività")
    st.dataframe(todo.dropna(subset=["Scadenza"]).sort_values("Scadenza"))

elif menu == "📬 Invia promemoria":
    st.subheader("📬 Invio automatico email")
    today = datetime.today().date()

    eventi = carica_csv(CALENDARIO_CSV, ["Titolo", "Data", "Descrizione"], ["Data"])
    determine = carica_csv(DETERMINE_CSV, ["Numero", "Data", "Capitolo", "Importo", "Oggetto", "Scadenza"], ["Scadenza"])

    eventi_alert = eventi[eventi["Data"].dt.date == today + timedelta(days=2)]
    if not eventi_alert.empty:
        corpo = "📅 Eventi in programma tra 2 giorni:\n\n"
        for _, row in eventi_alert.iterrows():
            corpo += f"- {row['Titolo']} ({row['Data'].date()}): {row['Descrizione']}\n"
        invia_email("Promemoria Eventi", corpo)
        st.success("📧 Email eventi inviata")

    determ_alert = determine[determine["Scadenza"].dt.date == today + timedelta(days=30)]
    if not determ_alert.empty:
        corpo = "📁 Determine in scadenza tra 30 giorni:\n\n"
        for _, row in determ_alert.iterrows():
            corpo += f"- {row['Oggetto']} (Scadenza: {row['Scadenza'].date()})\n"
        invia_email("Promemoria Determine", corpo)
        st.success("📧 Email determine inviata")

    if eventi_alert.empty and determ_alert.empty:
        st.info("📭 Nessun promemoria da inviare oggi.")
