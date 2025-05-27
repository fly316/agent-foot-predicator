# === AGENT IA STREAMLIT POUR TRADING SPORTIF : INTERFACE EN LIGNE ===
# ⚙️ Interface Streamlit + Connexion API-Football + Alerte Telegram + Prévision Matchs à Venir + Analyse Mondiale

import requests
import telegram
import streamlit as st
import time
from datetime import datetime, timedelta
import random

# === 1. CLES & PARAMETRES ===
API_KEY = "4ce3808ad6b0fc8d86b0bb5a7a56713f"
TELEGRAM_TOKEN = "8150180352:AAHBVj4FtneHiXZ_NF1F-7j77LW1wU3jR0U"
CHAT_ID = 7147597381

bot = telegram.Bot(token=TELEGRAM_TOKEN)

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

def get_live_matches():
    url = f"{BASE_URL}/fixtures?live=all"
    response = requests.get(url, headers=headers)
    st.write(f"[DEBUG] Code réponse API : {response.status_code}")
    try:
        raw = response.json()
        st.write("[DEBUG] Contenu brut de l'API:", raw)
        return raw.get("response", [])
    except Exception as e:
        st.error(f"Erreur lors du décodage JSON de l'API : {e}")
        return []

def get_upcoming_matches():
    today = datetime.now().strftime('%Y-%m-%d')
    in_seven_days = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"{BASE_URL}/fixtures?from={today}&to={in_seven_days}"
    response = requests.get(url, headers=headers)
    return response.json().get("response", [])

def analyse_match(match):
    try:
        minute = match['fixture']['status']['elapsed']
        score_home = match['goals']['home']
        score_away = match['goals']['away']
        score_total = score_home + score_away

        xg_simulé = round(random.uniform(0.5, 2.5), 2)
        tirs_simulés = random.randint(5, 18)

        st.write(f"Analyse de : {match['teams']['home']['name']} vs {match['teams']['away']['name']} - {minute}′, score {score_home}-{score_away}, xG: {xg_simulé}, tirs: {tirs_simulés}")

        if 15 <= minute <= 45 and score_total == 0:
            if xg_simulé >= 0.7 and tirs_simulés >= 7:
                return {
                    "match": f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
                    "minute": minute,
                    "recommandation": "TEST - OVER 0.5 HT",
                    "confiance": "75%",
                    "justification": f"xG modéré, {tirs_simulés} tirs, score 0-0, minute {minute}"
                }
        if 55 <= minute <= 85 and score_total <= 1:
            if xg_simulé >= 1.1 and tirs_simulés >= 9:
                return {
                    "match": f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
                    "minute": minute,
                    "recommandation": "TEST - OVER 1.5 FT",
                    "confiance": "78%",
                    "justification": f"xG modéré, {tirs_simulés} tirs, score serré, pression intéressante"
                }
    except:
        return None

# === INTERFACE STREAMLIT ===
st.set_page_config(page_title="Agent IA Foot - Trading Sportif", page_icon="⚽")
st.title("⚽ Agent IA - Analyse mondiale en live + alertes Telegram")

if st.button("🔁 Scanner tous les matchs en direct dans le monde"):
    with st.spinner("Chargement et analyse des matchs en cours..."):
        matches = get_live_matches()

        if matches:
            st.subheader("📺 Matchs actuellement en cours")
            for match in matches:
                home = match['teams']['home']['name']
                away = match['teams']['away']['name']
                minute = match['fixture']['status']['elapsed']
                score_home = match['goals']['home']
                score_away = match['goals']['away']
                st.write(f"➡️ {home} {score_home} - {score_away} {away} ({minute}′)")
        else:
            st.info("Aucun match en direct en ce moment.")

        alertes = []
        for match in matches:
            resultat = analyse_match(match)
            if resultat:
                message = f"⚽ {resultat['match']}\n⏱ Minute : {resultat['minute']}\n💡 Recommandation : {resultat['recommandation']}\n🎯 Confiance : {resultat['confiance']}\n📌 {resultat['justification']}"
                st.success(message)
                bot.send_message(chat_id=CHAT_ID, text=message)
                alertes.append(message)
        if not alertes:
            st.info("Aucune opportunité détectée pour le moment.")

if st.button("📅 Voir les matchs à venir (7 jours)"):
    with st.spinner("Chargement des matchs à venir..."):
        matchs = get_upcoming_matches()
        count = 0
        for match in matchs:
            date = match['fixture']['date'][:10]
            equipes = f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}"
            st.info(f"📅 {date} - ⚽ {equipes} ({match['league']['name']})")
            count += 1
        if count == 0:
            st.warning("Aucun match détecté cette semaine.")

st.markdown("---")
st.caption("Agent IA connecté à l'API-Football & Telegram | by brodyyy")
