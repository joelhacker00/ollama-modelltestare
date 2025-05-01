import streamlit as st
import subprocess
import json
import sys
import time # Importera time-modulen

# LangChain Import
from langchain_community.llms import Ollama

# Försök sätta stdout encoding till UTF-8, viktigt för subprocess output (för 'ollama list')
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    print("Kunde inte omkonfigurera stdout/stderr encoding.", file=sys.stderr)

# --- Sidofältsfunktioner ---
@st.cache_data(ttl=300)
def get_ollama_models():
    """Hämtar listan över lokalt tillgängliga Ollama-modeller."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True, encoding='utf-8')
        lines = result.stdout.strip().split('\n')
        models = []
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])
        if not models:
            st.warning("Inga Ollama-modeller hittades.")
            return []
        return sorted(models)
    except FileNotFoundError:
        st.error("Kommandot 'ollama' hittades inte. Kontrollera att Ollama är installerat.")
        return []
    except Exception as e:
        st.error(f"Fel vid hämtning av modeller: {e}")
        return []

# Funktion för att generera svar med streaming via LangChain
def generate_response_stream(model_name, prompt):
    """Genererar ett svar från Ollama-modellen med streaming via LangChain.
       Returnerar en generator.
    """
    try:
        llm = Ollama(model=model_name)
        return llm.stream(prompt)
    except Exception as e:
        st.error(f"Fel vid kommunikation med Ollama: {e}")
        if "connection refused" in str(e).lower():
            st.error("Kontrollera att Ollama-servern körs.")
        # Returnera en tom generator vid fel
        def empty_gen():
            if False: yield
        return empty_gen()

# --- Streamlit App Huvudlogik ---
st.set_page_config(page_title="Lokal Modelltestare", layout="centered")
st.title("🤖 Lokal Modelltestare (Ollama)")

# Initiera chatthistorik och tidigare modell i session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "previous_model" not in st.session_state:
    st.session_state.previous_model = None # Håller reda på senast valda modell

# --- Sidofält för Modellval ---
with st.sidebar:
    st.header("Modellval")
    available_models = get_ollama_models()
    
    # Variabel för att hålla det faktiskt valda värdet från selectboxen
    current_selection = None 

    if not available_models:
        st.error("Kunde inte ladda modeller.")
        # selected_model = None # Behövs inte här längre, hanteras av session state
    else:
        # Försök sortera enligt plan.md om den finns, annars bara tillgängliga
        try:
            # Läser plan.md för att få önskad ordning (bäst att läsa filen här)
            with open("plan.md", "r", encoding="utf-8") as f:
                plan_content = f.read()
            
            planned_models_raw = [line.split('`')[1] for line in plan_content.split('\n') if line.strip().startswith('*   `')]
            # Ta bort eventuell kvantiseringsinfo etc. för matchning mot 'ollama list'
            # Exempel: `qwen2:7b-instruct-q4_K_M` blir `qwen2:7b`
            planned_models = []
            for m_raw in planned_models_raw:
                 parts = m_raw.split(':')
                 if len(parts) == 2:
                     tag_base = parts[1].split('-')[0] # Ta bara bas-taggen
                     planned_models.append(f"{parts[0]}:{tag_base}")
                 else:
                      planned_models.append(m_raw) # Om ingen tagg, behåll som den är

        except FileNotFoundError:
            st.warning("plan.md hittades inte, visar modeller i bokstavsordning.")
            planned_models = []
        except Exception as e:
            st.warning(f"Kunde inte läsa modellordning från plan.md: {e}")
            planned_models = []

        # Matcha mot faktiskt tillgängliga modeller
        ordered_models = [m for m in planned_models if m in available_models]
        other_models = sorted([m for m in available_models if m not in planned_models])
        display_models = ordered_models + other_models

        if not display_models:
            st.warning("Inga Ollama-modeller verkar vara installerade.")
            # selected_model = None
        else:
            current_selection_index = 0
            # Hämta nuvarande val från session state om det finns och matchar
            initial_model = st.session_state.get('selected_model', None)
            if initial_model and initial_model in display_models:
                 try:
                     current_selection_index = display_models.index(initial_model)
                 except ValueError:
                     current_selection_index = 0 
            else:
                 # Om inget sparat val eller om det inte finns längre, välj första
                 initial_model = display_models[0]
                 st.session_state.selected_model = initial_model # Sätt initialt val

            # Låt selectboxen uppdatera session state direkt via on_change eller läs dess värde
            # Här sparar vi värdet till en lokal variabel först
            current_selection = st.selectbox(
                "Välj modell:",
                options=display_models,
                index=current_selection_index,
                key='model_selector', # Använd en separat nyckel för widgeten
                help="Listan visar modeller hämtade via 'ollama list'."
            )
            # Uppdatera session state EFTER att widgeten renderats
            st.session_state.selected_model = current_selection

    st.markdown("--- ")
    st.info("Chatta med den valda lokala modellen nedan.")

# --- Systemmeddelande vid modellbyte (körs efter sidebar) ---
selected_model_from_state = st.session_state.get('selected_model', None)

# Kontrollera om modellen har ändrats sedan förra körningen
if selected_model_from_state is not None and \
   st.session_state.previous_model is not None and \
   selected_model_from_state != st.session_state.previous_model:
    
    system_message = {"role": "system", "content": f"Modell ändrad till `{selected_model_from_state}`"}
    st.session_state.messages.append(system_message)

# Uppdatera alltid previous_model till det nuvarande valda värdet för nästa jämförelse
if selected_model_from_state is not None:
    st.session_state.previous_model = selected_model_from_state

# --- Chattgränssnitt --- 

# Visa tidigare meddelanden (inklusive systemmeddelanden)
for message in st.session_state.messages:
    # Sätt ikon baserat på roll
    role_icon = None
    if message["role"] == "system":
        role_icon = "⚙️" # System-ikon
    elif message["role"] == "user":
        role_icon = "user" # Standard användar-ikon
    else: # assistant
        role_icon = "assistant" # Standard assistent-ikon

    with st.chat_message(message["role"] if message["role"] != "system" else "assistant", avatar=role_icon):
        if message["role"] == "system":
            st.markdown(f"*{message['content']}*" ) # Visa systemmeddelande kursivt
        else:
            st.markdown(message["content"])

# Ta emot ny input från användaren
if prompt := st.chat_input("Ställ din fråga här...", key="chat_input"):
    # Lägg till användarens meddelande i historiken och visa det
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Kontrollera om en modell är vald från session state
    active_model = st.session_state.get('selected_model', None)
    if active_model:
        # Visa assistentens svar med streaming
        with st.chat_message("assistant"):
            with st.spinner(f"Tänker ({active_model})..."):
                try:
                    start_time = time.monotonic() # Registrera starttid
                    response_stream = generate_response_stream(active_model, prompt)
                    
                    # st.write_stream hanterar visningen och returnerar hela svaret
                    full_response = st.write_stream(response_stream)
                    
                    end_time = time.monotonic() # Registrera sluttid
                    duration = end_time - start_time # Beräkna tid
                    
                    # Lägg till det fullständiga svaret OCH tiden i historiken
                    if full_response:
                        # Formatera innehållet med tid
                        content_with_time = f"{full_response}\n\n---\n*Svarstid: {duration:.2f} sekunder*"
                        st.session_state.messages.append({"role": "assistant", "content": content_with_time})
                    # Inget behov av else här längre, generate_response_stream hanterar fel

                except Exception as e:
                    st.error(f"Ett oväntat fel inträffade under streaming: {e}")
    else:
        # Påminn om att välja modell om man försöker chatta utan val
        with st.chat_message("assistant"):
            st.warning("Vänligen välj en modell i sidofältet först.") 