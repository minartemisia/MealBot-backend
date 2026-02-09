from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Dict, Any
from datetime import date

from .models import StartMonthRequest, StartMonthResponse, CookMealRequest, CookMealResponse, ChatMessageRequest, ChatMessageResponse
from .nutrition import NutritionDB
from .planner import build_month_plan, RecipeBook
from .inventory import aggregate_grocery_list, grocery_list_items, apply_meal_to_inventory
from .llm_recipes import render_recipe_basic

app = FastAPI(title="MealPlanner Chatbot Backend", version="0.1.0")

# CORS
#
# In development you might run the frontend on localhost (Vite 5173).
# In hosted previews (e.g., Lovable) the Origin can be a random https domain.
#
# Since this project does not rely on cookies/credentials, we can safely allow
# any Origin for the API to avoid "Load failed" / CORS-blocked fetches.
# (If you later add auth cookies, replace this with a strict allowlist.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = NutritionDB()
book = RecipeBook()

# Simple in-memory session store (replace with DB for production)
SESSIONS: Dict[str, Dict[str, Any]] = {}


def _session_key(month: str) -> str:
    return month


@app.post("/start_month", response_model=StartMonthResponse)
def start_month(req: StartMonthRequest):
    user_profile = req.user_profile.model_dump()
    month_plan = build_month_plan(req.month, user_profile)
    totals = aggregate_grocery_list(month_plan, book)
    items = grocery_list_items(totals, db)
    inventory = totals.copy()

    key = _session_key(req.month)
    SESSIONS[key] = {
        "user_profile": user_profile,
        "month_plan": month_plan,
        "inventory": inventory,
    }

    return {
        "month_plan": month_plan,
        "grocery_list": {"items": items},
        "inventory": inventory,
    }


@app.get("/day/{month}/{date}")
def get_day(month: str, date: str):
    key = _session_key(month)
    if key not in SESSIONS:
        raise HTTPException(status_code=404, detail="Month not initialized. Call /start_month first")
    plan = SESSIONS[key]["month_plan"]
    for d in plan["days"]:
        if d["date"] == date:
            return d
    raise HTTPException(status_code=404, detail="Date not found in month plan")


@app.post("/cook", response_model=CookMealResponse)
def cook(req: CookMealRequest):
    # req.date is YYYY-MM-DD; infer month
    month = req.date[:7]
    key = _session_key(month)
    if key not in SESSIONS:
        raise HTTPException(status_code=404, detail="Month not initialized. Call /start_month first")

    sess = SESSIONS[key]
    day = next((d for d in sess["month_plan"]["days"] if d["date"] == req.date), None)
    if not day:
        raise HTTPException(status_code=404, detail="Date not found")

    meal_item = day[req.meal]
    recipe = book.by_id[meal_item["recipe_id"]]
    servings = float(meal_item["servings"])

    # Build ingredient list with human names, and scale grams
    ingredients = []
    for ing in recipe.ingredients:
        fk = str(ing["food_key"])
        grams = round(float(ing["grams"]) * servings, 1)
        name = db.get_food_row(fk)["food"]
        ingredients.append({"food_key": fk, "name": name, "grams": grams})

    text = render_recipe_basic(recipe.title, ingredients, max_minutes=sess["user_profile"]["preferences"]["max_prep_minutes"])

    inv_after = apply_meal_to_inventory(recipe, servings, sess["inventory"])
    sess["inventory"] = inv_after

    return {
        "recipe_id": recipe.recipe_id,
        "servings": servings,
        "ingredients": ingredients,
        "recipe_text": text,
        "inventory_after": inv_after,
    }


CHAT_HTML = """<!doctype html>
<html lang=\"it\">
  <head>
    <meta charset=\"utf-8\"/>
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
    <title>Mealbot Web Chat</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 0; padding: 0; }
      header { padding: 12px 16px; border-bottom: 1px solid #ddd; }
      main { padding: 16px; max-width: 900px; margin: 0 auto; }
      #log { white-space: pre-wrap; border: 1px solid #ddd; padding: 12px; border-radius: 8px; min-height: 280px; }
      #row { display: flex; gap: 8px; margin-top: 10px; }
      input { flex: 1; padding: 10px; border-radius: 8px; border: 1px solid #ccc; }
      button { padding: 10px 14px; border-radius: 8px; border: 1px solid #ccc; background: #f7f7f7; cursor: pointer; }
      .hint { color: #555; font-size: 13px; margin-top: 10px; }
    </style>
  </head>
  <body>
    <header><strong>Mealbot</strong> – chat (comandi rapidi)</header>
    <main>
      <div id=\"log\"></div>
      <div id=\"row\">
        <input id=\"msg\" placeholder=\"Scrivi un comando (es: pianifica 2026-03)\" />
        <button id=\"send\">Invia</button>
      </div>
      <div class=\"hint\">
        Comandi: <code>pianifica YYYY-MM</code>, <code>spesa YYYY-MM</code>, <code>giorno YYYY-MM-DD</code>, <code>ricetta YYYY-MM-DD colazione|pranzo|cena</code>.
      </div>
    </main>
    <script>
      const log = document.getElementById('log');
      const msg = document.getElementById('msg');
      const send = document.getElementById('send');
      function add(who, text){
        log.textContent += `${who}: ${text}\n\n`;
        log.scrollTop = log.scrollHeight;
      }
      async function doSend(){
        const t = msg.value.trim();
        if(!t) return;
        add('Tu', t);
        msg.value = '';
        const r = await fetch('/chat/message', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({session_id: 'web', message: t})});
        const j = await r.json();
        add('Mealbot', j.reply);
      }
      send.onclick = doSend;
      msg.addEventListener('keydown', (e)=>{ if(e.key==='Enter') doSend(); });
      add('Mealbot', 'Ciao. Scrivi "pianifica 2026-03" per generare mese+spesa.');
    </script>
  </body>
</html>"""


@app.get("/chat", response_class=HTMLResponse)
def chat_ui():
    return CHAT_HTML


def _format_grocery(month: str) -> str:
    key = _session_key(month)
    if key not in SESSIONS:
        return "Mese non inizializzato. Usa: pianifica YYYY-MM"
    sess = SESSIONS[key]
    totals = sess["inventory"]  # remaining; but spesa is based on initial totals
    # re-build from plan to show purchase quantities
    plan = sess["month_plan"]
    totals_initial = aggregate_grocery_list(plan, book)
    items = grocery_list_items(totals_initial, db)
    lines = [f"Spesa per {month} (quantità arrotondate):"]
    for it in items:
        lines.append(f"- {it['name']}: {it['rounded_purchase_qty']} (uso stimato {it['total_grams']} g)")
    return "\n".join(lines)


@app.post("/chat/message", response_model=ChatMessageResponse)
def chat_message(req: ChatMessageRequest):
    # New frontend sends `message`; legacy embedded chat sends `text`.
    text_raw = (req.message or req.text or "").strip()
    text = text_raw
    if not text:
        return {"reply": "Scrivi un comando. Es: pianifica 2026-03"}

    parts = text.split()
    cmd = parts[0].lower()

    if cmd in {"pianifica", "start"}:
        month = parts[1] if len(parts) > 1 else date.today().strftime("%Y-%m")
        # use defaults if not provided
        start_req = StartMonthRequest(month=month)
        resp = start_month(start_req)
        return {
            "reply": f"OK. Ho generato il piano per {month} e la spesa.\nPuoi: \n- vedere la spesa\n- aprire un giorno\n- generare una ricetta.",
            "actions": [
                {"type": "SHOW_GROCERY_LIST", "payload": {"month": month}},
                {"type": "SHOW_DAY", "payload": {"date": f"{month}-01"}},
            ],
            "data": {"month": month},
        }

    if cmd in {"spesa", "grocery"}:
        month = parts[1] if len(parts) > 1 else date.today().strftime("%Y-%m")
        return {
            "reply": _format_grocery(month),
            "actions": [{"type": "SHOW_GROCERY_LIST", "payload": {"month": month}}],
            "data": {"month": month},
        }

    if cmd in {"giorno", "day"}:
        d = parts[1] if len(parts) > 1 else date.today().isoformat()
        month = d[:7]
        try:
            day = get_day(month, d)
        except HTTPException as e:
            return {"reply": str(e.detail)}
        b = day["breakfast"]; l = day["lunch"]; di = day["dinner"]
        return {
            "reply": f"{d}\n- colazione: {b['recipe_id']} (serv {b['servings']})\n- pranzo: {l['recipe_id']} (serv {l['servings']})\n- cena: {di['recipe_id']} (serv {di['servings']})",
            "actions": [{"type": "SHOW_DAY", "payload": {"date": d}}],
        }

    if cmd in {"ricetta", "cook"}:
        if len(parts) < 3:
            return {"reply": "Formato: ricetta YYYY-MM-DD (colazione|pranzo|cena)"}
        d = parts[1]
        meal_raw = parts[2].lower()
        meal_map = {
            "colazione": "breakfast",
            "pranzo": "lunch",
            "cena": "dinner",
            "breakfast": "breakfast",
            "lunch": "lunch",
            "dinner": "dinner",
        }
        if meal_raw not in meal_map:
            return {"reply": "Pasto non valido: usa colazione/pranzo/cena"}
        meal = meal_map[meal_raw]
        try:
            resp = cook(CookMealRequest(date=d, meal=meal))
        except HTTPException as e:
            return {"reply": str(e.detail)}
        return {
            "reply": resp["recipe_text"],
            "data": {"recipe_id": resp["recipe_id"], "date": d, "meal": meal},
        }

    return {"reply": "Comando non riconosciuto. Usa: pianifica, spesa, giorno, ricetta."}


### NOTE: a second/older chat UI was removed to avoid duplicate routes.
