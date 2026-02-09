# MealBot (MVP) – piano alimentare mensile + lista spesa + ricette giornaliere

Questo progetto è un MVP di "chatbot" per:
1) generare un piano mensile (colazione/pranzo/cena) con porzioni scalate,
2) calcolare la lista della spesa mensile aggregata (grammi totali per ingrediente),
3) ogni giorno restituire la ricetta usando esclusivamente gli ingredienti pianificati e aggiornare l'inventario.

## Dataset nutrizionale
Usa `data/nutrition.csv`, un dataset compatto (8.463 alimenti, valori per 100g) che include macro e un set di micronutrienti.

## Lista spesa con "confezioni realistiche"
La lista spesa viene arrotondata a confezioni tipiche (es. 500 g avena, 1 kg riso, 6 uova).
Le regole sono in `data/packaging_rules.json` e puoi modificarle liberamente (aggiungi `food_key` che trovi in `data/recipes.json`).

## Web chat sopra gli endpoint
Dopo aver avviato il server, apri:
- `http://127.0.0.1:8000/chat`

È una chat "a comandi" (non richiede chiavi LLM):
- `pianifica 2026-03`
- `spesa 2026-03`
- `giorno 2026-03-05`
- `ricetta 2026-03-05 cena`

## Integrazioni
### Telegram
Installa le dipendenze opzionali:
```bash
pip install -r requirements-optional.txt
```
Poi:
```bash
export TELEGRAM_BOT_TOKEN="..."
export MEALBOT_API_BASE="http://127.0.0.1:8000"
python -m mealbot.integrations.telegram_bot
```

### WhatsApp (Twilio)
Esegui il webhook:
```bash
export MEALBOT_API_BASE="http://127.0.0.1:8000"
uvicorn mealbot.integrations.whatsapp_twilio:app --reload --port 9000
```
Configura Twilio per puntare la webhook URL pubblica (es. via ngrok) su `/twilio`.

## Avvio

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# genera data/recipes.json (catalogo ricette con nutrienti calcolati)
python -m scripts.build_recipes

# avvia API
uvicorn app.main:app --reload --port 8000
```

Poi:
- `POST /start_month` con body `{"month":"2026-03"}` (puoi anche passare `user_profile` per targets/prefs)
- `GET /day/2026-03/2026-03-01`
- `POST /cook` con body `{"date":"2026-03-01","meal":"lunch"}`

## Note importanti
- I calcoli nutrizionali dipendono dalla qualità del dataset e sono una stima.
- Per estendere la precisione sui micronutrienti: integra FoodData Central (USDA) o un database EU e sostituisci il planner euristico con un LP/MIP.
