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
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

def get_live_matches():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/fixtures?date={today}"
    response = requests.get(url, headers=headers)
    st.write(f"[DEBUG] Code réponse API : {response.status_code}")
    try:
        raw = response.json()
        st.write("[DEBUG] Contenu brut de l'API:", raw)
        return raw.get("response", [])
    except Exception as e:
        st.error(f"Erreur lors du décodage JSON de l'API : {e}")
        return []

def get_match_stats(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            stats = response.json().get("response", [])
            if len(stats) >= 2:
                team1_stats = {item['type']: item['value'] for item in stats[0]['statistics']}
                team2_stats = {item['type']: item['value'] for item in stats[1]['statistics']}
                return team1_stats, team2_stats
        except:
            return None, None
    return None, None

def analyse_match(match):
    try:
        minute = match['fixture']['status']['elapsed']
        score_home = match['goals']['home']
        score_away = match['goals']['away']
        score_total = score_home + score_away
        fixture_id = match['fixture']['id']

        stats_home, stats_away = get_match_stats(fixture_id)
        if not stats_home or not stats_away:
            return None

        tirs_total = (stats_home.get("Total Shots on Goal", 0) or 0) + (stats_away.get("Total Shots on Goal", 0) or 0)
        corners_total = (stats_home.get("Corner Kicks", 0) or 0) + (stats_away.get("Corner Kicks", 0) or 0)
        attaques_dang = (stats_home.get("Attacks", 0) or 0) + (stats_away.get("Attacks", 0) or 0)
        xg_home = stats_home.get("Expected Goals", 0.0) or 0.0
        xg_away = stats_away.get("Expected Goals", 0.0) or 0.0
        xg_total = round(xg_home + xg_away, 2)

        st.write(f"Analyse réelle : {match['teams']['home']['name']} vs {match['teams']['away']['name']} - {minute}′, Score: {score_home}-{score_away}, Tirs: {tirs_total}, Corners: {corners_total}, Attaques: {attaques_dang}, xG: {xg_total}")

        if 15 <= minute <= 45 and score_total == 0:
            if tirs_total >= 8 or corners_total >= 6 or attaques_dang >= 40 or xg_total >= 1.2:
                return {
                    "match": f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
                    "minute": minute,
                    "recommandation": "OVER 0.5 HT (stats réelles)",
                    "confiance": "86%",
                    "justification": f"Pression : {tirs_total} tirs, {corners_total} corners, {attaques_dang} attaques, xG={xg_total}"
                }
        if 55 <= minute <= 85 and score_total <= 1:
            if tirs_total >= 13 or corners_total >= 9 or attaques_dang >= 70 or xg_total >= 2.1:
                return {
                    "match": f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
                    "minute": minute,
                    "recommandation": "OVER 1.5 FT (stats réelles)",
                    "confiance": "90%",
                    "justification": f"Intensité : {tirs_total} tirs, {corners_total} corners, {attaques_dang} attaques, xG={xg_total}"
                }
    except:
        return None

# === INTERFACE STREAMLIT ===
st.set_page_config(page_title="Agent IA Foot - Trading Sportif", page_icon="⚽")
st.title("⚽ Agent IA - Analyse mondiale en live + alertes Telegram")

if st.button("🔁 Scanner tous les matchs en direct dans le monde"):
    with st.spinner("Chargement et analyse des matchs du jour..."):
        matches = get_live_matches()

        if matches:
            st.subheader("📺 Matchs programmés aujourd'hui")
            for match in matches:
                home = match['teams']['home']['name']
                away = match['teams']['away']['name']
                status = match['fixture']['status']['short']
                minute = match['fixture']['status'].get('elapsed', '-')
                score_home = match['goals']['home']
                score_away = match['goals']['away']
                st.write(f"➡️ {home} {score_home} - {score_away} {away} ({status}, {minute}′)")
        else:
            st.info("Aucun match trouvé aujourd'hui.")

        alertes = []
        for match in matches:
            if match['fixture']['status']['short'] in ["1H", "2H"]:
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
