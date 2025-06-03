# app.py
import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime, timedelta
from io import BytesIO

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

# ניהול משתמשים (רק לאדמין)
if st.session_state.role == "admin":
    with st.expander("👥 Manage Users"):
        st.subheader("Registered Users")
        users_df = pd.read_sql_query("SELECT username, role FROM users", conn)
        selected_user = st.selectbox("Select User", users_df["username"])
        selected_role = users_df[users_df["username"] == selected_user]["role"].values[0]
        st.write(f"Current role: {selected_role}")

        # שינוי סיסמה
        st.write("Change Password")
        new_pwd = st.text_input("New Password", key="pwd1")
        if st.button("Update Password"):
            new_hash = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode()
            c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, selected_user))
            conn.commit()
            st.success("Password updated")

        # שינוי תפקיד
        new_role = st.selectbox("Change Role", ["user", "admin"], index=["user", "admin"].index(selected_role))
        if st.button("Update Role"):
            c.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, selected_user))
            conn.commit()
            st.success("Role updated")

        # מחיקת יוזר
        if st.button("Delete User"):
            if selected_user != "admin":
                c.execute("DELETE FROM users WHERE username = ?", (selected_user,))
                conn.commit()
                st.success("User deleted")
            else:
                st.warning("Cannot delete the admin user")

        users_df = pd.read_sql_query("SELECT username, role FROM users", conn)
        st.dataframe(users_df)

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
    mode = st.radio("Choose Mode", ["Login"] if st.session_state.role != "admin" else ["Login", "Register"])
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

# 📥 ייבוא מבוקר מקובץ Excel (Admin בלבד)
if st.session_state.role == "admin":
    with st.expander("📥 Import from Excel"):
        excel_file = st.file_uploader("Upload Excel File", type=["xlsx"])
        if excel_file:
            # טען לקובץ pandas
            df_excel = pd.read_excel(excel_file)

            # נקה עמודות - הסר רווחים, הפוך לאותיות קטנות, והחלף רווחים בקווים תחתיים
            df_excel.columns = df_excel.columns.str.strip().str.lower().str.replace(" ", "_")

            # העמודות שאנחנו מצפים להן במסד הנתונים
            expected_cols = [
                "name", "supplier", "catalog_number", "cas_number", "internal_id",
                "batch_number", "date_received", "expiry_date", "expiry_note",
                "stock_quantity", "opening_date", "location"
            ]

            # סינון לפי העמודות הקיימות במסד הנתונים
            df_filtered = df_excel[[col for col in df_excel.columns if col in expected_cols]]

            # הצגה מקדימה
            st.subheader("Preview of Uploaded Data")
            st.dataframe(df_filtered)

            # לחצן לאישור הוספה למסד
            if st.button("✅ Confirm Import"):
                try:
                    df_filtered.to_sql("reagents", conn, if_exists="append", index=False)
                    st.success("Data successfully imported into database.")
                except Exception as e:
                    st.error(f"Import failed: {e}")

            st.success("Excel data imported to database.")

# ייצוא לאקסל
if st.button("📤 Export Full Inventory to Excel"):
    df_full = pd.read_sql_query("SELECT * FROM reagents", conn)
    buffer = BytesIO()
    df_full.to_excel(buffer, index=False)
    st.download_button("Download Full Inventory", buffer.getvalue(), file_name="full_inventory.xlsx")

if st.button("📤 Export Expiring Reagents to Excel"):
    df_all = pd.read_sql_query("SELECT * FROM reagents", conn)
    df_all["expiry_date"] = pd.to_datetime(df_all["expiry_date"], errors="coerce")
    exp = df_all[df_all["expiry_date"] <= (datetime.today() + timedelta(days=60))]
    buffer2 = BytesIO()
    exp.to_excel(buffer2, index=False)
    st.download_button("Download Expiring Reagents", buffer2.getvalue(), file_name="expiring_reagents.xlsx")
