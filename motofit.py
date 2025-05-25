import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Wetterdaten holen
@st.cache_data

def get_weather_data(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}&lang=de"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        wind_speed = data['wind']['speed'] * 3.6  # m/s in km/h
        regen = data['weather'][0]['main']
        luftfeuchtigkeit = data['main']['humidity']
        gefuehlte_temp = data['main']['feels_like']
        wetterbeschreibung = data['weather'][0]['description']
        warnung = data['weather'][0]['main'].lower() in ["thunderstorm", "extreme", "tornado"]
        return temp, wind_speed, regen, luftfeuchtigkeit, gefuehlte_temp, wetterbeschreibung, warnung
    else:
        st.error("Fehler beim Abrufen der Wetterdaten.")
        return None, None, None, None, None, None, False

# Anzeige eines Wetterblocks mit Warnung und Symbolen

def zeige_wetterblock(titel, ort, temp, feels_like, wind, hum, desc, warnung):
    st.markdown(f"### {titel} **{ort}**")
    st.info(f"🌡️ Temperatur: {temp:.1f}°C (gefühlt {feels_like:.1f}°C)  \n💨 Wind: {wind:.1f} km/h  \n💧 Luftfeuchtigkeit: {hum}%  \n☁️ Wetter: {desc}")
    if warnung:
        st.warning("⚠️ Wetterwarnung: Bitte besondere Vorsicht walten lassen!")

# Kleidungsempfehlung berechnen

def empfehlung(temp_c, wind_kmh, fahrtzeit_min, empfindlichkeit, typ, regen):
    if typ == "Moped/Roller (max 45 km/h)":
        windfaktor = 0.5
    elif typ == "Supermoto":
        windfaktor = 0.8
    elif typ == "Sportler":
        windfaktor = 1.3
    elif typ == "Tourer":
        windfaktor = 1.0
    else:
        windfaktor = 1.0

    windchill = temp_c - (wind_kmh * windfaktor / 10)
    gefuehlt = windchill - (0.1 * fahrtzeit_min)

    if empfindlichkeit == "Kälteempfindlich":
        gefuehlt -= 2
    elif empfindlichkeit == "Unempfindlich":
        gefuehlt += 2

    vorschlag = []

    if gefuehlt < 5:
        vorschlag = [
            "Thermounterwäsche (langarm, eng anliegend)",
            "Fleece oder dünne Softshell",
            "Textiljacke mit Thermofutter + Protektoren",
            "Motorradhose mit Thermofutter",
            "Balaclava, Nierengurt, Winterhandschuhe"
        ]
    elif gefuehlt < 10:
        vorschlag = [
            "Langarmshirt",
            "Dünner Pullover oder Softshell",
            "Textiljacke mit leichtem Futter",
            "Motorradhose mit Futter oder Leggings",
            "Halstuch, normale Handschuhe"
        ]
    elif gefuehlt < 15:
        vorschlag = [
            "T-Shirt",
            "Optionaler Midlayer",
            "Textiljacke (belüftet)",
            "Luftige Motorradhose",
            "Dünne Handschuhe, Sonnenvisier"
        ]
    else:
        vorschlag = [
            "T-Shirt oder Funktionsshirt",
            "Sommerjacke mit Protektoren",
            "Sommer-Motorradhose oder Kevlar-Jeans",
            "Leichte Handschuhe, getöntes Visier"
        ]

    if regen.lower() in ["rain", "drizzle", "thunderstorm"]:
        vorschlag.append("Regenkombi mitnehmen (Jacke & Hose wasserdicht)")
        vorschlag.append("Wasserdichte Handschuhe & Stiefel")

    return vorschlag

# Eingabemaske und Logik
st.markdown("""
    <h1 style='text-align: center; font-family: Helvetica, sans-serif; color: #ff4b4b;'>🏍️ <span style='font-weight: 700;'>MotoFit</span></h1>
    <h3 style='text-align: center; font-family: Helvetica, sans-serif; color: gray;'>Dein smarter Outfit-Check fürs Motorrad</h3>
    <hr>
""", unsafe_allow_html=True)

with st.form("Eingabeformular"):
    col1, col2 = st.columns(2)
    with col1:
        ort = st.text_input("📍 Startort", "Leipzig")
    with col2:
        ziel = st.text_input("🏁 Zielort", "")

    api_key = st.secrets["weather_api_key"] if "weather_api_key" in st.secrets else st.text_input("🔑 Wetter-API-Schlüssel")

    col3, col4 = st.columns(2)
    with col3:
        typ = st.selectbox("🏍️ Motorradtyp", ["Sportler", "Supermoto", "Moped/Roller (max 45 km/h)", "Tourer"])
    with col4:
        empf = st.radio("❄️ Kälteempfinden", ["Kälteempfindlich", "Normal", "Unempfindlich"])

    submitted = st.form_submit_button("🔍 Check starten")

if submitted and ort and api_key:
    temp, wind, regen, hum, feels_like, desc, warnung = get_weather_data(ort, api_key)
    if temp is not None:
        zeige_wetterblock("📍 Wetter am Startort:", ort, temp, feels_like, wind, hum, desc, warnung)

    verwendete_zeit = 45  # Standardwert
    vorschlag = None

    if ziel:
        ziel_temp, ziel_wind, ziel_regen, ziel_hum, ziel_feels_like, ziel_desc, ziel_warnung = get_weather_data(ziel, api_key)
        if ziel_temp is not None:
            zeige_wetterblock("🏁 Wetter am Zielort:", ziel, ziel_temp, ziel_feels_like, ziel_wind, ziel_hum, ziel_desc, ziel_warnung)

            geolocator = Nominatim(user_agent="motofit-routing")
            start = geolocator.geocode(ort)
            zielpunkt = geolocator.geocode(ziel)
            if not zielpunkt:
                st.warning(f"⚠️ Zielort '{ziel}' konnte nicht gefunden werden. Die Fahrtzeit basiert ggf. auf dem Standardwert.")
                st.warning("❌ Zielort ungültig – Kleidungsempfehlung kann nicht berechnet werden.")
            else:
                entfernung_km = geodesic((start.latitude, start.longitude), (zielpunkt.latitude, zielpunkt.longitude)).km
                geschwindigkeit = 45 if typ == "Moped/Roller (max 45 km/h)" else 70
                verwendete_zeit = round((entfernung_km / geschwindigkeit) * 60)
                vergleich_temp = ziel_temp
                vergleich_wind = ziel_wind
                vergleich_regen = ziel_regen
                vorschlag = empfehlung(vergleich_temp, vergleich_wind, verwendete_zeit, empf, typ, vergleich_regen)

    if not ziel:
        vergleich_temp = temp
        vergleich_wind = wind
        vergleich_regen = regen
        vorschlag = empfehlung(vergleich_temp, vergleich_wind, verwendete_zeit, empf, typ, vergleich_regen)

    if vorschlag:
        if ziel:
            stunden = verwendete_zeit // 60
            minuten = verwendete_zeit % 60
            if stunden > 0:
                st.markdown(f"### ⏱️ Geschätzte Fahrtzeit: {stunden} Stunde{'n' if stunden != 1 else ''} und {minuten} Minute{'n' if minuten != 1 else ''}")
            else:
                st.markdown(f"### ⏱️ Geschätzte Fahrtzeit: {minuten} Minute{'n' if minuten != 1 else ''}")

        st.markdown("### 👕 Kleidungsempfehlung")
        for teil in vorschlag:
            st.markdown(f"- {teil}")

# Footer-Banner
st.markdown("""
    <footer style='margin-top: 3rem; padding: 1rem; background: linear-gradient(to right, #222, #444); color: white; text-align: center; font-size: 1.1rem; border-radius: 0.5rem;'>
        🏍️ <strong>Ride Safe</strong>
    </footer>
""", unsafe_allow_html=True)
