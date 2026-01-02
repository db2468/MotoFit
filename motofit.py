import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="3D-Druck Ideen", page_icon="🧩", layout="centered")

DATA_FILE = "ideas.json"
ADMIN_PASS = "1243"


def load_ideas():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_ideas(ideas):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ideas, f, ensure_ascii=False, indent=2)


def add_idea(name: str, text: str):
    ideas = load_ideas()
    ideas.insert(0, {
        "name": name.strip(),
        "idea": text.strip(),
        "created_at": datetime.now().isoformat(timespec="seconds")
    })
    save_ideas(ideas)


def page_public():
    st.markdown("## 🧩 3D-Druck Ideenbox")
    st.write("Trag eine Idee ein. Ich sammle sie und was gut ist wird gedruckt.")

    with st.form("idea_form", clear_on_submit=True):
        idea = st.text_area(
            "✍️ Idee",
            placeholder="z.B. Halterung für..., Werkzeug-Organizer..., Moped-Teile...",
            height=140
        )
        name = st.text_input("👤 Dein Name", placeholder="Max, Lisa, ...")
        submitted = st.form_submit_button("✅ Absenden")

    if submitted:
        if not idea.strip():
            st.error("Leeres Ideen-Feld. Schreib eine Idee rein.")
            return

        # Name optional, aber nicht leer anzeigen
        safe_name = name.strip() if name.strip() else "Anonym"

        add_idea(safe_name, idea)
        st.success("Gespeichert.")


def page_admin():
    st.markdown("## 🔒 Admin – Ideen ansehen")

    if "admin_ok" not in st.session_state:
        st.session_state.admin_ok = False

    if not st.session_state.admin_ok:
        pw = st.text_input("Passwort", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASS:
                st.session_state.admin_ok = True
                st.success("OK.")
                st.rerun()
            else:
                st.error("Falsches Passwort.")
        st.stop()

    ideas = load_ideas()

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Aktualisieren"):
            st.rerun()
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.admin_ok = False
            st.rerun()

    st.markdown(f"### 📦 Gespeicherte Ideen: {len(ideas)}")

    if not ideas:
        st.info("Noch keine Ideen.")
        return

    for i, item in enumerate(ideas, start=1):
        created = item.get("created_at", "")
        idea_text = item.get("idea", "")
        name = item.get("name", "Anonym")

        with st.container(border=True):
            st.caption(f"#{i} • {created} • von: {name}")
            st.write(idea_text)


query = st.query_params
page = (query.get("page") or "").lower()

if page == "admin":
    page_admin()
else:
    page_public()

st.divider()
st.caption("Admin-Link: füge `?page=admin` an die URL an.")
