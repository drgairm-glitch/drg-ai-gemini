import streamlit as st
import google.generativeai as genai

# 1. Základné nastavenie stránky
st.set_page_config(page_title="DRG Asistent", page_icon="🩺", layout="wide")
st.title("🩺 DRG Inteligentný Asistent")
st.subheader("Multiformátový pomocník (PDF, CSV, TXT)")
st.markdown("---")

# 2. Bočný panel pre nastavenia
with st.sidebar:
    st.header("Konfigurácia")
    # API Kľúč z Google AI Studio
    api_key = st.text_input("Vlož Gemini API kľúč:", type="password")
    
    st.markdown("---")
    # Nahrávanie rôznych formátov
    uploaded_files = st.file_uploader(
        "Nahraj DRG podklady", 
        type=["pdf", "csv", "txt"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.info(f"Nahratých súborov: {len(uploaded_files)}")

# 3. Hlavná logika aplikácie
if api_key:
    # Inicializácia Gemini
    genai.configure(api_key=api_key)
    
    # Tvrdý prompt pre DRG experta
    system_prompt = """
    Si špičkový expert na slovenský DRG systém (diagnosticky príbuzné skupiny). 
    Tvojou úlohou je radiť lekárom a kodérom pri kódovaní hospitalizácií.
    VŽDY sa opieraj výhradne o priložené dokumenty (PDF metodiky, CSV číselníky alebo TXT poznámky). 
    Ak informácia v dokumentoch nie je, slušne povedz, že to nevieš. 
    Uvádzaj presné kódy MKN-10 a kódov výkonov.
    Odpovedaj v slovenčine a buď maximálne stručný a presný.
    """
    
    # Použijeme Gemini 1.5 Pro pre "NotebookLM" kvalitu
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_prompt
    )

    # Ak sú nahraté súbory, spracujeme ich
    if uploaded_files:
        # Chatovacie rozhranie
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Zobrazenie histórie chatu
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Vstup od používateľa
        if prompt := st.chat_input("Napr.: Aký kód priradiť k diagnóze..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.spinner("Prezerám manuály a číselníky..."):
                try:
                    # Príprava "balíka" dát pre Gemini
                    content_to_send = []
                    
                    # Spracovanie každého súboru podľa jeho typu
                    for f in uploaded_files:
                        if f.type == "application/pdf":
                            content_to_send.append({
                                "mime_type": "application/pdf",
                                "data": f.getvalue()
                            })
                        elif f.type == "text/plain":
                            # TXT súbory pridáme ako text s popisom
                            content_to_send.append(f"\nObsah poznámkového súboru {f.name}:\n{f.getvalue().decode('utf-8')}")
                        elif f.type == "text/csv" or f.name.endswith(".csv"):
                            # CSV súbory pridáme ako štruktúrovaný text
                            content_to_send.append(f"\nObsah číselníka CSV {f.name}:\n{f.getvalue().decode('utf-8')}")
                    
                    # Na koniec pridáme samotnú otázku
                    content_to_send.append(prompt)
                    
                    # Generovanie odpovede
                    response = model.generate_content(content_to_send)
                    
                    with st.chat_message("assistant"):
                        st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                except Exception as e:
                    st.error(f"Vyskytla sa chyba pri spracovaní: {str(e)}")
    else:
        st.info("👈 Do bočného panela nahraj PDF manuály, CSV číselníky alebo TXT poznámky.")

else:
    st.warning("👈 Najprv vlož svoj API kľúč v bočnom paneli.")
