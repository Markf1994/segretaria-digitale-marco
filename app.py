
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from google_sheets import carica_df, salva_df
from email_sender import invia_email
import os

LOGO = "stemma.png"

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    with open("utenti.json", "r") as f:
        utenti = json.load(f)

    if os.path.exists(LOGO):
        try:
            st.image(LOGO, width=120)
        except:
            st.warning("⚠️ Immagine non valida.")
    else:
        st.warning("⚠️ Immagine non trovata.")

    st.title("🔐 Accesso Segretaria Digitale")
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

st.set_page_config(page_title="Segretaria Digitale", layout="wide")

col_logo, col_title = st.columns([1, 10])
with col_logo:
    if os.path.exists(LOGO):
        st.image(LOGO, width=80)
with col_title:
    st.markdown(f"## 👩‍💼 Benvenuto {st.session_state['user'].capitalize()}!")

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

    eventi = carica_df("eventi_calendario")
    eventi["Data"] = pd.to_datetime(eventi["Data"], errors="coerce")
    determine = carica_df("determine_dashboard")
    determine["Scadenza"] = pd.to_datetime(determine["Scadenza"], errors="coerce")
    todo = carica_df("todo_list")
    todo["Scadenza"] = pd.to_datetime(todo["Scadenza"], errors="coerce")

    eventi_today = eventi[eventi["Data"].dt.date == today]
    determ_today = determine[determine["Scadenza"].dt.date == today]
    attive = todo[todo["Stato"] == "Da fare"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Eventi oggi", len(eventi_today))
    with col2:
        st.metric("📁 Determine oggi", len(determ_today))
    with col3:
        st.metric("✅ To-do attivi", len(attive))

    if not eventi_today.empty:
        st.warning("Eventi di oggi:")
        st.dataframe(eventi_today)

    if not determ_today.empty:
        st.warning("Determine in scadenza oggi:")
        st.dataframe(determ_today)

    if not attive.empty:
        st.markdown("### 📝 Attività da fare")
        st.dataframe(attive.sort_values("Scadenza"))

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
