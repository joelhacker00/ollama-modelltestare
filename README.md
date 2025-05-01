# Lokal Modelltestare för Ollama

Detta är en Streamlit-applikation för att testa och interagera med olika lokala språkmodeller (LLM) som körs via [Ollama](https://ollama.com/). Appen låter dig välja en installerad Ollama-modell och ställa frågor till den i ett chattgränssnitt. Den mäter och visar även svarstiden för varje fråga.

## Funktioner

*   Listar automatiskt lokalt installerade Ollama-modeller.
*   Chattgränssnitt för att interagera med den valda modellen.
*   Streaming av modellsvar för omedelbar feedback.
*   Mätning och visning av svarstid per genererat svar.
*   Visar ett systemmeddelande när en ny modell väljs.
*   (Valfritt) Möjlighet att sortera modellistan baserat på en `plan.md`-fil.

## Installation och Körning

### Förutsättningar

1.  **Python:** Se till att du har Python 3.8 eller senare installerat.
2.  **Ollama:** Du måste ha [Ollama installerat](https://ollama.com/download) och Ollama-servern måste vara igång i bakgrunden. Du behöver också ha laddat ner minst en modell via Ollama (t.ex. `ollama run qwen3:4b`).

### Steg

1.  **Klona Repositoriet (eller ladda ner filerna):**
    ```bash
    git clone <din-repo-url>
    cd ollama-modelltestare
    ```
    *(Eller ladda ner `app.py`, `requirements.txt` och `README.md` till en mapp)*

2.  **Installera Python-beroenden:**
    Navigera till mappen där filerna ligger och kör:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Kör Streamlit-appen:**
    ```bash
    streamlit run app.py
    ```
    Applikationen bör nu öppnas i din webbläsare.

## Valfri Konfiguration: `plan.md`

Om du vill att modellerna i sidofältet ska visas i en specifik ordning (t.ex. baserat på en testplan) istället för alfabetiskt, kan du skapa en fil som heter `plan.md` i samma mapp som `app.py`.

Filen ska innehålla en lista med modellnamn (inklusive tagg, t.ex. `qwen3:4b`) inom backticks på rader som börjar med `*   `:

**Exempel `plan.md`:**

```markdown
*   `qwen3:4b`
*   `gemma3:4b`
*   `deepseek-r1:8b`
*   ...andra modeller...
```

Appen kommer att försöka läsa denna fil och sortera de tillgängliga modellerna enligt denna ordning först, följt av övriga modeller i bokstavsordning. Om filen inte finns eller inte kan läsas, används enbart bokstavsordning. 