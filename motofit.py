import streamlit as st
import math
import requests

# Wetterdaten holen
@st.cache_data

def get_weather_data(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}&lang=de"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        wind_speed = data['wind']['speed'] * 3.6  # m/s in km/h
        return temp, wind_speed
    else:
        st.error("Fehler beim Abrufen der Wetterdaten.")
        return None, None

# Hilfsfunktion zur Kleidungsempfehlung
def empfehlung(temp_c, wind_kmh, fahrtzeit_min, empfindlichkeit):
    windchill = temp_c - (wind_kmh / 10)  # grober Windchill-Effekt
    gefuehlt = windchill - (0.1 * fahrtzeit_min)

    if empfindlichkeit == "Kälteempfindlich":
        gefuehlt -= 2
    elif empfindlichkeit == "Unempfindlich":
        gefuehlt += 2

    kleidung = []

    if gefuehlt < 5:
        kleidung = [
            "Baselayer: Thermounterwäsche (langarm, eng anliegend)",
            "Midlayer: Fleece oder dünne Softshell",
            "Oberbekleidung: Textiljacke mit Thermofutter + Protektoren",
            "Unterkörper: Motorradhose mit Thermofutter",
            "Zubehör: Balaclava, Nierengurt, Winterhandschuhe",
            "Hinweis: Klarvisier empfohlen – kein direktes Sonnenlicht"
        ]
    elif gefuehlt < 10:
        kleidung = [
            "Baselayer: Langarmshirt",
            "Midlayer: Dünner Pullover oder Softshell",
            "Oberbekleidung: Textiljacke mit leichtem Futter",
            "Unterkörper: Motorradhose mit Futter oder Leggings drunter",
            "Zubehör: Halstuch, normale Handschuhe"
        ]
    elif gefuehlt < 15:
        kleidung = [
            "Baselayer: T-Shirt",
            "Midlayer: Optional",
            "Oberbekleidung: Textiljacke (belüftet)",
            "Unterkörper: Luftige Motorradhose",
            "Zubehör: Dünne Handschuhe, Sonnenvisier"
        ]
    else:
        kleidung = [
            "Baselayer: T-Shirt oder Funktionsshirt",
            "Oberbekleidung: Sommerjacke mit Protektoren",
            "Unterkörper: Sommer-Motorradhose oder Jeans mit Kevlar",
            "Zubehör: Leichte Handschuhe, getöntes Visier"
        ]

    return kleidung

# Streamlit UI
st.title("🏍️ MotoFit – Kleidungsempfehlung für Biker")

st.markdown("Gib deinen Ort an und erhalte wetterbasierte Empfehlungen für dein Motorrad-Outfit.")

ort = st.text_input("Standort", "Leipzig")
api_key = st.secrets["weather_api_key"] if "weather_api_key" in st.secrets else st.text_input("OpenWeatherMap API-Schlüssel")

if ort and api_key:
    temp, wind = get_weather_data(ort, api_key)
    if temp is not None and wind is not None:
        st.success(f"Wetter in {ort}: {temp:.1f}°C, Wind: {wind:.1f} km/h")

        zeit = st.slider("Geplante Fahrtzeit (Minuten)", 5, 180, 45)
        typ = st.selectbox("Motorradtyp", ["Naked Bike", "Tourer", "Cruiser", "Sportler"])
        empf = st.radio("Kälteempfinden", ["Kälteempfindlich", "Normal", "Unempfindlich"])

        if st.button("Kleidung anzeigen"):
            vorschlag = empfehlung(temp, wind, zeit, empf)
            st.subheader("Empfohlene Kleidung")
            for teil in vorschlag:
                st.write("- " + teil)

            st.info("Fühlst du dich mit dem Vorschlag wohl? Gib Feedback unten!")
            feedback = st.radio("Feedback", ["Passt", "Zu kalt", "Zu warm"])
else:
    st.warning("Bitte gib einen Ort und einen gültigen OpenWeatherMap API-Schlüssel ein.")
