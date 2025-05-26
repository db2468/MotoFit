import streamlit as st
import requests
import openrouteservice
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Wetterdaten abrufen
@st.cache_data
def get_weather_data(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}&lang=de"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        wind_speed = data['wind']['speed'] * 3.6
        regen = data['weather'][0]['main']
        hum = data['main']['humidity']
        feels_like = data['main']['feels_like']
        desc = data['weather'][0]['description']
        warnung = regen.lower() in ["thunderstorm", "extreme", "tornado"]
        return temp, wind_speed, regen, hum, feels_like, desc, warnung
    else:
        st.error("❌ Fehler beim Abrufen der Wetterdaten.")
        return None, None, None, None, None, None, False

# ORS: echte Fahrtzeit holen
@st.cache_data
def get_ors_duration(start_coords, ziel_coords, api_key):
    client = openrouteservice.Client(key=api_key)
    try:
        route = client.directions(
            coordinates=[start_coords, ziel_coords],
            profile='driving-car',
            format='geojson'
        )
        duration_sec = route['features'][0]['properties']['summary']['duration']
        return round(duration_sec / 60)
    except Exception as e:
        st.warning(f"ORS Fehler: {e}")
        return None

# Geocoding
@st.cache_data
def cached_geocode(location):
    geolocator = Nominatim(user_agent="motofit-routing")
    return geolocator.geocode(location)

# Wetteranzeige
def zeige_wetterblock(titel, ort, temp, feels_like, wind, hum, desc, warnung):
    st.markdown(f"### {titel} **{ort}**")
    st.info(f"🌡️ Temperatur: {temp:.1f}°C (gefühlt {feels_like:.1f}°C)  \n💨 Wind: {wind:.1f} km/h  \n💧 Luftfeuchtigkeit: {hum}%  \n☁️ Wetter: {desc}")
    if warnung:
        st.warning("⚠️ Wetterwarnung: Bitte besondere Vorsicht walten lassen!")

# Kleidungsempfehlung
def empfehlung(temp_c, wind_kmh, fahrtzeit_min, empfindlichkeit, typ, regen):
    windfaktor_map = {
        "Moped/Roller (max 45 km/h)": 0.5,
        "Supermoto": 0.8,
        "Sportler": 1.3,
        "Tourer": 1.0
    }
    windfaktor = windfaktor_map.get(typ, 1.0)
    windchill = temp_c - (wind_kmh * windfaktor / 10)
    gefuehlt = windchill - (0.1 * fahrtzeit_min)

    if empfindlichkeit == "Kälteempfindlich":
        gefuehlt -= 2
    elif empfindlichkeit == "Unempfindlich":
        gefuehlt += 2

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

    if any(r in regen.lower() for r in ["rain", "drizzle", "thunderstorm"]):
        vorschlag += [
            "Regenkombi mitnehmen (Jacke & Hose wasserdicht)",
            "Wasserdichte Handschuhe & Stiefel"
        ]
    return vorschlag

# UI
st.markdown("""
    <h1 style='text-align: center; font-family: Helvetica, sans-serif; color: #ff4b4b;'>🏍️ <span style='font-weight: 700;'>MotoFit</span></h1>
    <h3 style='text-align: center; font-family: Helvetica, sans-serif; color: gray;'>Dein smarter Outfit-Check fürs Motorrad</h3>
    <hr>
""", unsafe_allow_html=True)

# Eingabeformular
with st.form("Eingabeformular"):
    col1, col2 = st.columns(2)
    ort = col1.text_input("📍 Startort", "Leipzig")
    ziel = col2.text_input("🏁 Zielort", "")

    weather_api_key = st.secrets["weather_api_key"] if "weather_api_key" in st.secrets else st.text_input("🔑 Wetter-API-Schlüssel")
    ors_api_key = st.secrets["ors_api_key"] if "ors_api_key" in st.secrets else st.text_input("🧭 ORS API-Key")

    col3, col4 = st.columns(2)
    typ = col3.selectbox("🏍️ Motorradtyp", ["Sportler", "Supermoto", "Moped/Roller (max 45 km/h)", "Tourer"])
    empf = col4.radio("❄️ Kälteempfinden", ["Kälteempfindlich", "Normal", "Unempfindlich"])

    submitted = st.form_submit_button("🔍 Check starten")

# Hauptlogik
if submitted and ort and weather_api_key and ors_api_key:
    temp, wind, regen, hum, feels_like, desc, warnung = get_weather_data(ort, weather_api_key)
    if temp is not None:
        zeige_wetterblock("📍 Wetter am Startort:", ort, temp, feels_like, wind, hum, desc, warnung)

        verwendete_zeit = 45  # fallback
        vorschlag = None
        start = cached_geocode(ort)

        if not start:
            st.error(f"❌ Startort '{ort}' konnte nicht gefunden werden.")
        else:
            if ziel:
                zielpunkt = cached_geocode(ziel)
                if not zielpunkt:
                    st.warning(f"⚠️ Zielort '{ziel}' konnte nicht gefunden werden. Verwende Standardzeit.")
                else:
                    ziel_temp, ziel_wind, ziel_regen, ziel_hum, ziel_feels_like, ziel_desc, ziel_warnung = get_weather_data(ziel, weather_api_key)
                    if ziel_temp is not None:
                        zeige_wetterblock("🏁 Wetter am Zielort:", ziel, ziel_temp, ziel_feels_like, ziel_wind, ziel_hum, ziel_desc, ziel_warnung)

                        start_coords = (start.longitude, start.latitude)
                        ziel_coords = (zielpunkt.longitude, zielpunkt.latitude)
                        verwendete_zeit = get_ors_duration(start_coords, ziel_coords, ors_api_key)

                        if verwendete_zeit is None:
                            entfernung_km = geodesic((start.latitude, start.longitude), (zielpunkt.latitude, zielpunkt.longitude)).km
                            geschwindigkeit = 45 if typ == "Moped/Roller (max 45 km/h)" else 70
                            verwendete_zeit = round((entfernung_km * 1.4 / geschwindigkeit) * 60)
                        else:
                            typ_faktoren = {
                                "Moped/Roller (max 45 km/h)": 1.5,
                                "Supermoto": 1.2,
                                "Sportler": 1.0,
                                "Tourer": 1.0
                            }
                            verwendete_zeit = round(verwendete_zeit * typ_faktoren.get(typ, 1.0))

                        vorschlag = empfehlung(ziel_temp, ziel_wind, verwendete_zeit, empf, typ, ziel_regen)

            if not ziel or not vorschlag:
                vorschlag = empfehlung(temp, wind, verwendete_zeit, empf, typ, regen)

            if vorschlag:
                st.markdown(f"### ⏱️ Geschätzte Fahrtzeit: {verwendete_zeit} Minuten")
                st.markdown("### 👕 Kleidungsempfehlung")
                for teil in vorschlag:
                    st.markdown(f"- {teil}")

# Footer
st.markdown("""
    <footer style='margin-top: 3rem; padding: 1rem; background: linear-gradient(to right, #222, #444); color: white; text-align: center; font-size: 1.1rem; border-radius: 0.5rem;'>
        🏍️ <strong>Ride Safe</strong>
    </footer>
""", unsafe_allow_html=True)
