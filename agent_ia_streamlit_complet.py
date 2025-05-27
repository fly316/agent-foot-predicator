# === AGENT IA STREAMLIT POUR TRADING SPORTIF : INTERFACE EN LIGNE ===
# ⚙️ Interface Streamlit + Connexion API-Football + Alerte Telegram + Analyse Forme + Analyse Joueurs + Analyse Mondiale

import requests
import telegram
import streamlit as st
import time
import csv
from datetime import datetime, timedelta

# === 1. CLES & PARAMETRES ===
API_KEY = "4ce3808ad6b0fc8d86b0bb5a7a56713f"
TELEGRAM_TOKEN = "8150180352:AAHBVj4FtneHiXZ_NF1F-7j77LW1wU3jR0U"
CHAT_ID = 7147597381

bot = telegram.Bot(token=TELEGRAM_TOKEN)

headers = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"
FICHIER_LOG = "historique_alertes.csv"
mode_test = st.sidebar.checkbox("🧪 Mode test (seuils allégés)", value=False)

try:
    with open(FICHIER_LOG, "x", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["datetime", "match", "minute", "recommandation", "confiance", "justification", "resultat"])
except FileExistsError:
    pass

def log_alerte(resultat):
    with open(FICHIER_LOG, "a", newline="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            resultat['match'],
            resultat['minute'],
            resultat['recommandation'],
            resultat['confiance'],
            resultat['justification'],
            "🟨 en attente"
        ])

def get_live_matches():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/fixtures?date={today}"
    response = requests.get(url, headers=headers)
    st.write(f"[DEBUG] Code réponse API : {response.status_code}")
    try:
        raw = response.json()
        return raw.get("response", [])
    except Exception as e:
        st.error(f"Erreur JSON : {e}")
        return []

def get_match_stats(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            stats = response.json().get("response", [])
            if len(stats) >= 2:
                t1 = {i['type']: i['value'] for i in stats[0]['statistics']}
                t2 = {i['type']: i['value'] for i in stats[1]['statistics']}
                return t1, t2
        except:
            return None, None
    return None, None

def get_buteurs_recent(fixture_ids):
    buteurs = []
    for fid in fixture_ids:
        url = f"{BASE_URL}/fixtures/events?fixture={fid}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get("response", [])
            for event in data:
                if event['type'] == "Goal" and event['detail'] != "Own Goal":
                    buteurs.append(event['player']['name'])
    return list(set(buteurs))[:5]

def get_forme_equipe(team_id):
    url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            matchs = response.json().get("response", [])
            total_buts = 0
            fixture_ids = []
            for m in matchs:
                total_buts += m['goals']['for'] + m['goals']['against']
                fixture_ids.append(m['fixture']['id'])
            moyenne_buts = total_buts / len(matchs) if matchs else 0
            buteurs = get_buteurs_recent(fixture_ids)
            return round(moyenne_buts, 2), buteurs
        except:
            return 0, []
    return 0, []

def get_effectif_match(fixture_id):
    url = f"{BASE_URL}/fixtures/lineups?fixture={fixture_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            return response.json().get("response", [])
        except:
            return []
    return []

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

        team_home_id = match['teams']['home']['id']
        team_away_id = match['teams']['away']['id']

        forme_home, buteurs_home = get_forme_equipe(team_home_id)
        forme_away, buteurs_away = get_forme_equipe(team_away_id)
        forme_moyenne = (forme_home + forme_away) / 2

        effectifs = get_effectif_match(fixture_id)
        joueurs_home = []
        joueurs_away = []
        if len(effectifs) >= 2:
            joueurs_home = [p['player']['name'] for p in effectifs[0]['startXI']]
            joueurs_away = [p['player']['name'] for p in effectifs[1]['startXI']]

        tirs_total = (stats_home.get("Total Shots on Goal", 0) or 0) + (stats_away.get("Total Shots on Goal", 0) or 0)
        corners_total = (stats_home.get("Corner Kicks", 0) or 0) + (stats_away.get("Corner Kicks", 0) or 0)
        attaques_dang = (stats_home.get("Attacks", 0) or 0) + (stats_away.get("Attacks", 0) or 0)
        xg_home = stats_home.get("Expected Goals", 0.0) or 0.0
        xg_away = stats_away.get("Expected Goals", 0.0) or 0.0
        xg_total = round(xg_home + xg_away, 2)

        pression = tirs_total * 1.5 + corners_total + attaques_dang * 0.3 + xg_total * 10 + forme_moyenne * 5

        st.write(f"📊 {match['teams']['home']['name']} vs {match['teams']['away']['name']} | Minute {minute} | Pression : {pression:.1f} | Forme: {forme_moyenne}")

        seuil_ht = 40 if mode_test else 55
        seuil_ft = 60 if mode_test else 75

        if 15 <= minute <= 45 and score_total == 0 and pression > seuil_ht:
            return {
                "match": f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
                "minute": minute,
                "recommandation": "OVER 0.5 HT (complet)",
                "confiance": "88%",
                "justification": f"Pression {pression:.1f}, forme {forme_moyenne:.2f}, xG {xg_total}, tirs {tirs_total}, corners {corners_total}, attaques {attaques_dang}\n📋 Effectif Home: {', '.join(joueurs_home)}\n📋 Effectif Away: {', '.join(joueurs_away)}\n🔥 Buteurs récents Home: {', '.join(buteurs_home)}\n🔥 Buteurs récents Away: {', '.join(buteurs_away)}"
            }

        if 55 <= minute <= 85 and score_total <= 1 and pression > seuil_ft:
            return {
                "match": f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
                "minute": minute,
                "recommandation": "OVER 1.5 FT (complet)",
                "confiance": "91%",
                "justification": f"Pression {pression:.1f}, forme {forme_moyenne:.2f}, xG {xg_total}, tirs {tirs_total}, corners {corners_total}, attaques {attaques_dang}\n📋 Effectif Home: {', '.join(joueurs_home)}\n📋 Effectif Away: {', '.join(joueurs_away)}\n🔥 Buteurs récents Home: {', '.join(buteurs_home)}\n🔥 Buteurs récents Away: {', '.join(buteurs_away)}"
            }
    except:
        return None
