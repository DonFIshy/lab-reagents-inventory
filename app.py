# app.py
import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime, timedelta

# התחברות למסד הנתונים
conn = sqlite3.connect("reagents.db", check_same_thread=False)
c = conn.cursor()

# יצירת טבלת משתמשים
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT,
    role TEXT
)
""")

# יצירת טבלת ריאגנטים
c.execute("""
CREATE TABLE IF NOT EXISTS reagents (
    name TEXT,
    supplier TEXT,
    catalog_number TEXT,
    cas_number TEXT,
    internal_id TEXT,
    batch_number TEXT,
    date_received TEXT,
    expiry_date TEXT,
    expiry_note TEXT,
    stock_quantity INTEGER,
    opening_date TEXT,
    location TEXT
)
""")

conn.commit()

# יצירת משתמש admin זמני אם לא קיים
def create_admin_if_missing():
    c.execute("SELECT username FROM users WHERE username = 'admin'")
    if not c.fetchone():
        password = '1234'
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                  ('admin', hashed, 'admin'))
        conn.commit()
        print("✅ Admin user created with username: admin and password: 1234")

create_admin_if_missing()

# פונקציות התחברות והרשמה

def login_user(username, password):
    c.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result and bcrypt.checkpw(password.encode(), result[0].encode()):
        return True, result[1]
    return False, None

def register_user(username, password, role):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# תרגומים
translations = {
    "en": {
        "name": "Reagent Name",
        "supplier": "Supplier",
        "catalog_number": "Catalog Number",
        "cas_number": "CAS Number",
        "internal_id": "Internal Lab ID",
        "batch_number": "Batch Number",
        "date_received": "Date Received",
        "expiry_date": "Expiry Date",
        "expiry_note": "Expiry Note",
        "stock_quantity": "Stock Quantity",
        "opening_date": "Opening Date",
        "location": "Physical Location"
    },
    "he": {
        "name": "שם הריאגנט",
        "supplier": "ספק",
        "catalog_number": "מספר קטלוגי",
        "cas_number": "מספר CAS",
        "internal_id": "מספר פנימי במעבדה",
        "batch_number": "מספר אצווה",
        "date_received": "תאריך קבלה",
        "expiry_date": "תוקף",
        "expiry_note": "הערת תוקף",
        "stock_quantity": "כמות במלאי",
        "opening_date": "תאריך פתיחה",
        "location": "מיקום פיזי"
    }
}

def translate_columns(lang):
    return translations[lang]

# התחברות
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

# ממשק ראשי לאחר התחברות
st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()
if st.sidebar.button("🧼 Clear Session"):
    st.session_state.clear()
    st.rerun()

language = st.sidebar.selectbox("Language / שפה", ["en", "he"])
labels = translate_columns(language)
st.title("📦 Lab Reagents Inventory")

# טופס להוספת ריאגנט למסד נתונים
with st.expander("➕ Add New Reagent"):
    with st.form("add_form"):
        new_data = {}
        for key in labels:
            if key in ["stock_quantity"]:
                new_data[key] = st.number_input(labels[key], min_value=0, step=1)
            else:
                new_data[key] = st.text_input(labels[key])
        submitted = st.form_submit_button("Add Reagent")
        if submitted:
            c.execute(f"""
                INSERT INTO reagents ({', '.join(new_data.keys())})
                VALUES ({', '.join(['?']*len(new_data))})
            """, list(new_data.values()))
            conn.commit()
            st.success("Reagent added successfully.")
            st.rerun()

# הצגת טבלה עם אפשרות חיפוש
st.sidebar.markdown("### 🔍 Search Filters")
reagent_search = st.sidebar.text_input("Reagent Name")
catalog_search = st.sidebar.text_input("Catalog Number")
cas_search = st.sidebar.text_input("CAS Number")
labid_search = st.sidebar.text_input("Internal Lab ID")

query = "SELECT * FROM reagents"
df = pd.read_sql_query(query, conn)

if not df.empty:
    df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce")
    df["date_received"] = pd.to_datetime(df["date_received"], errors="coerce")
    df["opening_date"] = pd.to_datetime(df["opening_date"], errors="coerce")

    if reagent_search:
        df = df[df["name"].str.contains(reagent_search, case=False, na=False)]
    if catalog_search:
        df = df[df["catalog_number"].str.contains(catalog_search, case=False, na=False)]
    if cas_search:
        df = df[df["cas_number"].str.contains(cas_search, case=False, na=False)]
    if labid_search:
        df = df[df["internal_id"].str.contains(labid_search, case=False, na=False)]

    def highlight_expiry(val):
        if isinstance(val, pd.Timestamp):
            days_left = (val - datetime.today()).days
            if days_left < 0:
                return "background-color: red; color: white"
            elif days_left <= 60:
                return "background-color: orange"
        return ""

    st.subheader("🧪 Reagents Table")
    st.dataframe(df.style.applymap(highlight_expiry, subset=["expiry_date"]), use_container_width=True)

    st.subheader("⚠️ Expiring Within 60 Days")
    expiring = df[df["expiry_date"] <= (datetime.today() + timedelta(days=60))]
    if not expiring.empty:
        st.dataframe(expiring.style.applymap(highlight_expiry, subset=["expiry_date"]), use_container_width=True)
    else:
        st.info("No reagents expiring soon.")

# כפתור מחיקה - רק לאדמין
if st.session_state.role == "admin":
    if st.button("🗑️ Delete All Reagents"):
        c.execute("DELETE FROM reagents")
        conn.commit()
        st.success("All reagent data deleted.")
