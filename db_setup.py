# app.py
import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime, timedelta

# התחברות למסד הנתונים

create_admin_if_missing()

conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT,
    role TEXT
)
""")
conn.commit()

# פונקציית התחברות

def login_user(username, password):
    c.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result and bcrypt.checkpw(password.encode(), result[0].encode()):
        return True, result[1]
    return False, None

# פונקציית הרשמה

def register_user(username, password, role):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

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

# התחברות או הרשמה
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 Login or Register")
    mode = st.radio("Choose Mode", ["Login", "Register"])

    user = st.text_input("Username")
    show_password = st.checkbox("Show Password")
    pwd = st.text_input("Password", type="default" if show_password else "password")

    if mode == "Login":
        if st.button("Login"):
            valid, role = login_user(user, pwd)
            if valid:
                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid username or password.")
    else:
        role = st.selectbox("Role", ["user", "admin"])
        if st.button("Register"):
            success = register_user(user, pwd, role)
            if success:
                st.success("User registered successfully. You can now log in.")
            else:
                st.error("Username already exists.")

    st.stop()

# אחרי התחברות
st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# כפתור איפוס session
if st.sidebar.button("🧼 Clear Session"):
    st.session_state.clear()
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

        # סינון לפי חיפוש
        st.sidebar.markdown("### 🔍 Search Filters")
        reagent_search = st.sidebar.text_input("Reagent Name")
        catalog_search = st.sidebar.text_input("Catalog Number")
        cas_search = st.sidebar.text_input("CAS Number")
        labid_search = st.sidebar.text_input("Internal Lab ID")

        filtered_df = df.copy()
        if reagent_search:
            filtered_df = filtered_df[filtered_df["Reagent Name"].astype(str).str.contains(reagent_search, case=False)]
        if catalog_search:
            filtered_df = filtered_df[filtered_df["Catalog Number"].astype(str).str.contains(catalog_search, case=False)]
        if cas_search:
            filtered_df = filtered_df[filtered_df["CAS Number"].astype(str).str.contains(cas_search, case=False)]
        if labid_search:
            filtered_df = filtered_df[filtered_df["Internal Lab ID"].astype(str).str.contains(labid_search, case=False)]

        # עיצוב טבלת ריאגנטים
        def highlight_expiry(val):
            if isinstance(val, pd.Timestamp):
                days_left = (val - datetime.today()).days
                if days_left < 0:
                    return "background-color: red; color: white"
                elif days_left <= 60:
                    return "background-color: orange"
            return ""

        styled_df = filtered_df.style.applymap(highlight_expiry, subset=["Expiry Date"])
        st.subheader("🧪 Filtered Reagent Table")
        st.dataframe(styled_df, use_container_width=True)

        # הצגת חומרים שתוקפם מתקרב
        st.subheader("⚠️ Expiring Within 60 Days")
        expiring = filtered_df[filtered_df["Expiry Date"] <= (datetime.today() + timedelta(days=60))]
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
