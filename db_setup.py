# app.py
import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime, timedelta

# התחברות למסד הנתונים
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

# פונקציית התחברות

def login_user(username, password):
    c.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result and bcrypt.checkpw(password.encode(), result[0].encode()):
        return True, result[1]
    return False, None

# פונקציית טעינת תרגומים
translations = {
    "en": {
        "Reagent Name": "Reagent Name",
        "Supplier": "Supplier",
        "Catalog Number": "Catalog Number",
        "CAS Number": "CAS Number",
        "Internal Lab ID": "Internal Lab ID",
        "Batch Number": "Batch Number",
        "Date Received": "Date Received",
        "Expiry Date": "Expiry Date",
        "Expiry Note": "Expiry Note",
        "Stock Quantity": "Stock Quantity",
        "Opening Date": "Opening Date",
        "Physical Location": "Physical Location"
    },
    "he": {
        "Reagent Name": "שם הריאגנט",
        "Supplier": "ספק",
        "Catalog Number": "מספר קטלוגי",
        "CAS Number": "מספר CAS",
        "Internal Lab ID": "מספר פנימי במעבדה",
        "Batch Number": "מספר אצווה",
        "Date Received": "תאריך קבלה",
        "Expiry Date": "תוקף",
        "Expiry Note": "הערת תוקף",
        "Stock Quantity": "כמות במלאי",
        "Opening Date": "תאריך פתיחה",
        "Physical Location": "מיקום פיזי"
    }
}

# פונקציית תרגום עמודות

def translate_columns(df, lang):
    mapping = translations[lang]
    return df.rename(columns=mapping)

# התחברות
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 Login")
    user = st.text_input("Username")

    show_password = st.checkbox("Show Password")
    pwd = st.text_input("Password", type="default" if show_password else "password")

    if st.button("Login"):
        valid, role = login_user(user, pwd)
        if valid:
            st.session_state.logged_in = True
            st.session_state.username = user
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.stop()

# אחרי התחברות
st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

language = st.sidebar.selectbox("Language / שפה", ["en", "he"])

st.title("📦 Lab Reagents Inventory")

# העלאת קובץ
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df = translate_columns(df, language)
        df["Expiry Date"] = pd.to_datetime(df["Expiry Date"], errors="coerce", dayfirst=True)
        df["Date Received"] = pd.to_datetime(df["Date Received"], errors="coerce", dayfirst=True)
        df["Opening Date"] = pd.to_datetime(df["Opening Date"], errors="coerce", dayfirst=True)

        # עיצוב טבלת ריאגנטים
        def highlight_expiry(val):
            if isinstance(val, pd.Timestamp):
                days_left = (val - datetime.today()).days
                if days_left < 0:
                    return "background-color: red; color: white"
                elif days_left <= 60:
                    return "background-color: orange"
            return ""

        styled_df = df.style.applymap(highlight_expiry, subset=["Expiry Date"])
        st.subheader("🧪 Full Reagent Table")
        st.dataframe(styled_df, use_container_width=True)

        # הצגת חומרים שתוקפם מתקרב
        st.subheader("⚠️ Expiring Within 60 Days")
        expiring = df[df["Expiry Date"] <= (datetime.today() + timedelta(days=60))]
        if not expiring.empty:
            st.dataframe(expiring.style.applymap(highlight_expiry, subset=["Expiry Date"]), use_container_width=True)
        else:
            st.info("No reagents expiring soon.")

        # כפתור מחיקה - רק לאדמין
        if st.session_state.role == "admin":
            if st.button("🗑️ Delete All Data"):
                st.warning("This would delete data from memory. Implement DB deletion here if needed.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please upload a valid Excel file.")
