import nest_asyncio
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

nest_asyncio.apply()

TOKEN = "7521489143:AAHriLmdhy_HOLg0aG9-c_CkbdVKqpqCshg"
URL = "https://10elotto5minuti.com/estrazioni-di-oggi"

strategies = {
    (25, 26): [4, 16, 21],
    (55, 56): [4, 16, 21],
    (58, 59): [4, 16, 21],
    (82, 83): [4, 16, 21],
    (32, 35): [4, 16, 21],
    (20, 21, 25): [4, 16, 21],
    (51, 55, 56): [4, 16, 21]
}

active_schedules = {}
last_checked_draw = None

def get_ultima_estrazione():
    try:
        response = requests.get(URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find_all("table")[0]
        intestazione = table.find("tr").text.strip()
        estr_num = int(intestazione.split("n.")[1].split("ore")[0].strip())
        numeri = []
        for td in table.find_all("td"):
            val = td.text.strip()
            if val.isdigit():
                numeri.append(int(val))
            if len(numeri) == 20:
                break
        return estr_num, numeri
    except Exception as e:
        print("Errore parsing:", e)
        return None, []

async def analizza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_checked_draw
    estr_num, numeri = get_ultima_estrazione()
    if not numeri or estr_num is None:
        await update.message.reply_text("❌ Estrazione non trovata.")
        return
    if estr_num == last_checked_draw:
        await update.message.reply_text("⏳ Nessuna nuova estrazione.")
        return

    messaggi = [f"🟢 Estrazione n.{estr_num}", f"🎱 Numeri estratti: {numeri}"]
    nuovi_numeri = set()

    for k, v in strategies.items():
        if all(x in numeri for x in k):
            nuovi_numeri.update(v)
            active_schedules[estr_num] = {
                "numeri": v,
                "colpi": 0,
                "attivato_da": estr_num,
                "combo": k
            }
            messaggi.append(f"📌 Attivata strategia {k} → {v}")

    if nuovi_numeri:
        messaggi.append(f"🎯 Numeri da giocare: {sorted(nuovi_numeri)}")
    else:
        messaggi.append("⚠ Nessuna strategia attivata.")

    last_checked_draw = estr_num
    await update.message.reply_text("\n".join(messaggi))

async def verifica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estr_num, numeri = get_ultima_estrazione()
    if not numeri or estr_num is None:
        await update.message.reply_text("❌ Errore recupero estrazione.")
        return

    messaggi = [f"🔍 Verifica estrazione n.{estr_num}", f"🎱 Numeri: {numeri}"]

    for sched, dati in list(active_schedules.items()):
        dati["colpi"] += 1
        hits = [n for n in dati["numeri"] if n in numeri]

        if hits:
            messaggi.append(f"🏆 Vincita per combo {dati['combo']}: usciti {hits}")

        if dati["colpi"] >= 5:
            del active_schedules[sched]
            messaggi.append(f"⏳ Strategia {dati['combo']} terminata dopo 5 colpi.")

    if len(messaggi) == 2:
        messaggi.append("❌ Nessuna vincita trovata.")

    await update.message.reply_text("\n".join(messaggi))

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_schedules.clear()
    await update.message.reply_text("🔁 Reset: tutte le strategie azzerate.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("analizza", analizza))
app.add_handler(CommandHandler("verifica", verifica))
app.add_handler(CommandHandler("reset", reset))

print("🤖 Bot attivo su Render.")

async def avvia():
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

if __name__ == "__main__":
    asyncio.run(avvia())
