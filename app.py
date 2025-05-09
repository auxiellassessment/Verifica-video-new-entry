import streamlit as st  
import pandas as pd
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime

st.set_page_config(page_title="Quiz auxiell", layout="centered")

# Logo fisso
st.markdown("""
    <style>
    .fixed-logo-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: white;
        text-align: center;
        padding-top: 65px;
        padding-bottom: 0px;
        z-index: 1000;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
    }
    .fixed-logo-container img {
        max-height: 80px;
    }
    .fixed-logo-divider {
        border: none;
        height: 1px;
        background-color: #ccc;
        margin: 0;
        padding: 0;
    }
    .spacer { height: 140px; }
    </style>
    <div class="fixed-logo-container">
        <img src="https://raw.githubusercontent.com/auxiellMF/prova/0e7fd16a41139ea306af35cc0f6dccb852403b86/auxiell_logobase.png" alt="Logo Auxiell">
        <hr class="fixed-logo-divider">
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Verifica conoscenze Video New Entry</h1>", unsafe_allow_html=True)

# Stato iniziale
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "proseguito" not in st.session_state:
    st.session_state["proseguito"] = False
if "email_sent" not in st.session_state:
    st.session_state["email_sent"] = False

# Caricamento Excel
file_path = "questionario conoscenze New Entry.xlsx"
try:
    df = pd.read_excel(file_path)
    st.success("Domande pronte!")
except FileNotFoundError:
    st.error(f"File non trovato: {file_path}")
    st.stop()

# Verifica colonne necessarie
required_cols = ["principio", "Domanda", "Corretta", "opzione 1"]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    st.error(f"Mancano le colonne obbligatorie: {', '.join(missing)}")
    st.stop()

# Colonne opzione
option_cols = [c for c in df.columns if c.lower().strip().startswith("opzione")]
if not option_cols:
    st.error("Nessuna colonna di opzione trovata.")
    st.stop()

# Usa direttamente tutto il dataframe
if "domande_selezionate" not in st.session_state:
    st.session_state["domande_selezionate"] = df.reset_index(drop=True)

domande = st.session_state["domande_selezionate"]

# Input utente
utente = st.text_input("Inserisci il tuo nome")
email_utente = st.text_input("Inserisci la tua email aziendale")

# Validazione email
errore_email = None
domini_validi = ["@auxiell.com", "@euxilia.com", "@xva-services.com"]

if email_utente and not any(email_utente.endswith(dominio) for dominio in domini_validi):
    errore_email = "La tua email deve terminare con @auxiell.com, @euxilia.com o @xva-services.com"

if errore_email:
    st.warning(errore_email)

# Pulsante Prosegui
if utente and email_utente and not errore_email and not st.session_state["proseguito"]:
    st.markdown("<div style='text-align: center; margin-top:20px;'><br>", unsafe_allow_html=True)
    if st.button("Prosegui"):
        st.session_state["proseguito"] = True
    st.markdown("</div>", unsafe_allow_html=True)

# Step 4: Quiz
if st.session_state["proseguito"]:
    risposte = []
    st.write("### Rispondi alle seguenti domande:")

    for idx, row in domande.iterrows():
        st.markdown(f"**{row['Domanda']}**")
        if pd.isna(row["opzione 1"]):
            ans = st.text_input(
                f"Risposta libera:",
                key=f"open_{idx}",
                disabled=st.session_state["submitted"] or st.session_state["email_sent"]
            )
            risposte.append({
                "Tipo": "aperta",
                "Utente": utente,
                "Domanda": row["Domanda"],
                "Risposta": ans,
                "Corretta": None,
                "Esatta": None
            })
        else:
            opts = [str(row[c]) for c in option_cols if pd.notna(row[c])]
            sel = st.radio(
                f"Argomento: {row['principio']}",
                opts,
                key=idx,
                index=None,
                disabled=st.session_state["submitted"] or st.session_state["email_sent"]
            )
            corrette = [c.strip() for c in str(row["Corretta"]).split(";")]
            is_corr = sel in corrette
            risposte.append({
                "Tipo": "chiusa",
                "Utente": utente,
                "Domanda": row["Domanda"],
                "Argomento": row["principio"],
                "Risposta": sel,
                "Corretta": row["Corretta"],
                "Esatta": is_corr
            })

    # Pulsante invio con blocco immediato
    if not (st.session_state["submitted"] or st.session_state["email_sent"]):
        submit_clicked = st.button("Invia Risposte")
        
        if submit_clicked:
            st.session_state["submitted"] = True
            st.rerun()
    else:
        submit_clicked = False

    # Gestisce l'invio delle risposte solo una volta
    if st.session_state["submitted"] and not st.session_state["email_sent"]:
        st.success("Risposte inviate.")
        
        df_r = pd.DataFrame(risposte)
        chiuse = df_r[df_r["Tipo"] == "chiusa"]
        n_tot = len(chiuse)
        n_cor = int(chiuse["Esatta"].sum()) if n_tot else 0
        perc = int(n_cor / n_tot * 100) if n_tot else 0
        st.success(f"Punteggio finale: {n_cor} su {n_tot} ({perc}%)")
        
        # Creazione file Excel con due tabelle
        data_test = datetime.now().strftime("%d/%m/%Y")
        
        # Estrai dominio email per determinare l'azienda
        domain = email_utente.split('@')[1]
        if domain == "auxiell.com":
            azienda = "auxiell"
        elif domain == "euxilia.com":
            azienda = "euxilia"
        elif domain == "xva-services.com":
            azienda = "xva"
        else:
            azienda = "altra"
        
        info = pd.DataFrame([{
            "Nome": utente,
            "Data": data_test,
            "Punteggio": f"{perc}%",
            "Email": email_utente,
            "Azienda": azienda
        }])
        
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            info.to_excel(writer, index=False, sheet_name="Risposte", startrow=0)
            pd.DataFrame([], columns=[""]).to_excel(writer, index=False, sheet_name="Risposte", startrow=2)
            df_r["Email"] = email_utente
            df_r["Punteggio"] = f"{perc}%"
            df_r["Azienda"] = azienda
            df_r.to_excel(writer, index=False, sheet_name="Risposte", startrow=3)
        buf.seek(0)
        
        # Email
        msg = MIMEMultipart()
        msg["From"] = "infusionauxiell@gmail.com"
        msg["To"] = email_utente  # Invia all'email dell'utente
        msg["Subject"] = f"Risultati Quiz - {utente}"
        body = f"""Ciao {utente},

Grazie per aver completato il quiz di verifica conoscenze Video New Entry.
I tuoi risultati sono allegati a questa email.

Punteggio finale: {n_cor} su {n_tot} ({perc}%)

Cordiali saluti,
Team auxiell"""

        msg.attach(MIMEText(body, "plain"))
        attachment = MIMEApplication(buf.getvalue(), Name=f"risultati_{utente}.xlsx")
        attachment["Content-Disposition"] = f'attachment; filename="risultati_{utente}.xlsx"'
        msg.attach(attachment)
        
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login("infusionauxiell@gmail.com", "ubrwqtcnbyjiqach")
                server.send_message(msg)
            st.session_state["email_sent"] = True
            st.success(f"Email inviata a {email_utente}")
            
            # Aggiungiamo un messaggio di chiusura e ringraziamento
            st.balloons()  # Effetto celebrativo
            st.markdown(f"""
            ### Quiz completato!
            Grazie per aver completato il quiz. I risultati sono stati inviati alla tua email ({email_utente}).
            Puoi chiudere questa finestra.
            """)
            
            # Disabilitiamo l'intera interfaccia utente
            st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"] > div:not(:nth-child(-n+3)) {
                opacity: 0.7;
                pointer-events: none;
            }
            </style>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Errore durante l'invio email: {e}")
