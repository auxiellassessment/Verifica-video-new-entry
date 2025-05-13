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
    
    /* Nuovi stili per migliorare la formattazione delle domande e risposte */
    .question-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #1f77b4;
    }
    
    .question-text {
        font-weight: bold;
        margin-bottom: 8px;
        color: #2c3e50;
    }
    
    /* Per ridurre lo spazio tra domanda e opzioni di risposta */
    .stRadio > div {
        margin-top: -15px;
    }
    
    /* Per input di testo aperto */
    .stTextInput > div:first-child {
        margin-top: -10px;
    }
    
    /* Sfondo alternato per le domande */
    .question-container:nth-child(even) {
        background-color: #e9f0f8;
    }
    
    /* Stilizzazione dei radio button */
    .stRadio label {
        padding: 8px;
        border-radius: 5px;
    }
    
    .stRadio label:hover {
        background-color: #e6e6e6;
    }
    </style>
    <div class="fixed-logo-container">
        <img src="https://raw.githubusercontent.com/auxiellMF/prova/0e7fd16a41139ea306af35cc0f6dccb852403b86/auxiell_logobase.png" alt="Logo Auxiell">
        <hr class="fixed-logo-divider">
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Test Video New Entry</h1>", unsafe_allow_html=True)

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

# Input utente con stile migliorato
st.markdown("""
    <style>
    .user-inputs {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="user-inputs">', unsafe_allow_html=True)
utente = st.text_input("Inserisci il tuo nome")
email_utente = st.text_input("Inserisci la tua email aziendale")
st.markdown('</div>', unsafe_allow_html=True)

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
        # Utilizziamo un contenitore personalizzato per ogni domanda
        st.markdown(f'<div class="question-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="question-text">{row["Domanda"]}</div>', unsafe_allow_html=True)
        
        if pd.isna(row["opzione 1"]):
            ans = st.text_input(
                f"",  # Etichetta vuota per rimuovere spazio aggiuntivo
                key=f"open_{idx}",
                placeholder="Inserisci la tua risposta qui",
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
                f"",  # Etichetta vuota per rimuovere spazio aggiuntivo
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
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Pulsante invio con stile migliorato
    if not (st.session_state["submitted"] or st.session_state["email_sent"]):
        st.markdown("""
            <style>
            div.stButton > button:first-child {
                background-color: #1f77b4;
                color: white;
                font-weight: bold;
                padding: 0.5em 2em;
                border-radius: 8px;
                border: none;
                margin-top: 20px;
                margin-bottom: 20px;
                width: 100%;
            }
            div.stButton > button:hover {
                background-color: #135a8c;
            }
            </style>
        """, unsafe_allow_html=True)
        
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
        
        # Risultato finale con stile migliorato
        st.markdown(f"""
            <div style="background-color: #e6f7ff; padding: 20px; border-radius: 10px; 
                        border-left: 5px solid #1f77b4; margin: 20px 0;">
                <h3 style="margin-top: 0;">Punteggio finale</h3>
                <div style="font-size: 22px; font-weight: bold; color: #1f77b4;">
                    {n_cor} su {n_tot} ({perc}%)
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Creazione file Excel con due tabelle
        data_test = datetime.now().strftime("%d/%m/%Y")
        
        info = pd.DataFrame([{
            "Nome": utente,
            "Data": data_test,
            "Punteggio": f"{perc}%",
            "Email": email_utente
        }])
        
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            info.to_excel(writer, index=False, sheet_name="Risposte", startrow=0)
            pd.DataFrame([], columns=[""]).to_excel(writer, index=False, sheet_name="Risposte", startrow=2)
            df_r["Email"] = email_utente
            df_r["Punteggio"] = f"{perc}%"
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
            
            # Messaggio di successo con stile migliorato
            st.markdown(f"""
                <div style="background-color: #dff0d8; padding: 20px; border-radius: 10px; 
                            border-left: 5px solid #3c763d; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #3c763d;">Email inviata con successo!</h3>
                    <p>I risultati sono stati inviati all'indirizzo: {email_utente}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Aggiungiamo un messaggio di chiusura e ringraziamento
            st.balloons()  # Effetto celebrativo
            st.markdown(f"""
            <div style="text-align: center; margin: 40px 0; padding: 30px; background-color: #f8f9fa; border-radius: 10px;">
                <h2>Quiz completato!</h2>
                <p style="font-size: 18px;">Grazie per aver completato il quiz.</p>
                <p>I risultati sono stati inviati alla tua email ({email_utente}).</p>
                <p style="margin-top: 20px; font-style: italic;">Puoi chiudere questa finestra.</p>
            </div>
            """, unsafe_allow_html=True)
            
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
