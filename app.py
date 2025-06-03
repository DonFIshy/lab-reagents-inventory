import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Reagents Inventory", layout="wide")

# פונקציה לפירוש תאריכים בפורמטים שונים
def parse_flexible_date(series):
    return pd.to_datetime(series, errors='coerce', dayfirst=True)

# תרגומים
translations = {
    "he": {
        "title": "📦 ניהול מלאי ריאגנטים במעבדה",
        "add_reagent": "➕ הוסף ריאגנט",
        "name": "שם הריאגנט",
        "supplier": "ספק",
        "catalog_number": "מספר קטלוגי",
        "cas_number": "מספר CAS",
        "internal_id": "מספר פנימי במעבדה",
        "batch_number": "מספר אצווה",
        "received_date": "תאריך קבלה",
        "expiry_date": "תוקף",
        "expiry_note": "הערת תוקף",
        "quantity": "כמות במלאי",
        "open_date": "תאריך פתיחה",
        "location": "מיקום פיזי",
        "username": "שם משתמש",
        "alerts": "⚠️ חומרים שתוקפם קרוב",
        "expiring_soon": "ריאגנטים שתוקפם תוך 60 יום:",
        "no_expiry_alerts": "אין חומרים שתוקפם קרוב.",
        "history_log": "🕒 היסטוריית הוצאות",
        "delete": "🗑️ מחק",
        "use_bottle": "📤 הוצא בקבוק",
        "confirm_msg": "האם למחוק את",
        "confirm_delete": "✅ מחק",
        "cancel": "❌ ביטול",
        "deleted": "הריאגנט נמחק.",
        "cancelled": "המחיקה בוטלה.",
        "file_loaded": "📁 הקובץ נטען בהצלחה.",
        "file_error": "❌ הקובץ לא כולל את כל העמודות.",
        "file_exception": "שגיאה בטעינת הקובץ:"
    },
    "en": {
        "title": "📦 Lab Reagents Inventory Management",
        "add_reagent": "➕ Add Reagent",
        "name": "Reagent Name",
        "supplier": "Supplier",
        "catalog_number": "Catalog Number",
        "cas_number": "CAS Number",
        "internal_id": "Internal Lab ID",
        "batch_number": "Batch Number",
        "received_date": "Date Received",
        "expiry_date": "Expiry Date",
        "expiry_note": "Expiry Note",
        "quantity": "Stock Quantity",
        "open_date": "Opening Date",
        "location": "Physical Location",
        "username": "Username",
        "alerts": "⚠️ Expiring Soon",
        "expiring_soon": "Reagents expiring within 60 days:",
        "no_expiry_alerts": "No expiring reagents.",
        "history_log": "🕒 Usage Log",
        "delete": "🗑️ Delete",
        "use_bottle": "📤 Use Bottle",
        "confirm_msg": "Are you sure you want to delete",
        "confirm_delete": "✅ Delete",
        "cancel": "❌ Cancel",
        "deleted": "Reagent deleted.",
        "cancelled": "Deletion cancelled.",
        "file_loaded": "📁 File loaded.",
        "file_error": "❌ Missing required columns.",
        "file_exception": "File error:"
    }
}

# שפה
language = st.sidebar.selectbox("Language / שפה", ["English", "עברית"])
lang = "he" if language == "עברית" else "en"
t = translations[lang]

# יוזר
if st. sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.experimental_rerun()
username = st.sidebar.text_input(t["username"], value="")

# עמודות נדרשות
columns = [
    t["name"], t["supplier"], t["catalog_number"], t["cas_number"],
    t["internal_id"], t["batch_number"], t["received_date"],
    t["expiry_date"], t["expiry_note"], t["quantity"],
    t["open_date"], t["location"]
]

# יוזר סשן
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=columns)

if "log" not in st.session_state:
    st.session_state.log = pd.DataFrame(columns=["Date", t["name"], t["batch_number"], t["username"]])

if "delete_index" not in st.session_state:
    st.session_state.delete_index = None

# העלאת קובץ
file = st.sidebar.file_uploader("📤 Excel", type=["xlsx"])
if file:
    try:
        uploaded = pd.read_excel(file)
        if all(c in uploaded.columns for c in columns):
            for col in ["Date Received", "Expiry Date", "Opening Date"]:
                uploaded[col] = parse_flexible_date(uploaded[col])
            uploaded[t["quantity"]] = pd.to_numeric(uploaded[t["quantity"]], errors='coerce').fillna(1).astype(int)
            st.session_state.df = uploaded
            st.success(t["file_loaded"])
        else:
            st.error(t["file_error"])
    except Exception as e:
        st.error(f"{t['file_exception']} {e}")

# טופס הוספה
st.title(t["title"])
with st.form("add"):
    c1, c2 = st.columns(2)
    name = c1.text_input(t["name"])
    supplier = c2.text_input(t["supplier"])
    c3, c4 = st.columns(2)
    catalog = c3.text_input(t["catalog_number"])
    cas = c4.text_input(t["cas_number"])
    c5, c6 = st.columns(2)
    internal = c5.text_input(t["internal_id"])
    batch = c6.text_input(t["batch_number"])
    c7, c8 = st.columns(2)
    received = c7.date_input(t["received_date"])
    expiry = c8.date_input(t["expiry_date"])
    note = st.text_input(t["expiry_note"])
    c9, c10 = st.columns(2)
    qty = c9.number_input(t["quantity"], min_value=0, format="%d")
    opened = c10.date_input(t["open_date"])
    location = st.text_input(t["location"])
    if st.form_submit_button(t["add_reagent"]):
        new = pd.DataFrame([[name, supplier, catalog, cas, internal, batch,
                             received, expiry, note, qty, opened, location]],
                           columns=columns)
        st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True)

# התראות
st.subheader(t["alerts"])
today = datetime.today().date()
df_alert = st.session_state.df.copy()
if t["expiry_date"] in df_alert.columns:
    try:
        df_alert[t["expiry_date"]] = parse_flexible_date(df_alert[t["expiry_date"]]).dt.date
        df_alert = df_alert[df_alert[t["expiry_date"]].notna() &
                            (df_alert[t["expiry_date"]] <= today + timedelta(days=60))]
        if not df_alert.empty:
            st.warning(t["expiring_soon"])
            st.dataframe(df_alert, use_container_width=True)
        else:
            st.success(t["no_expiry_alerts"])
    except Exception as e:
        st.error(f"⚠️ {e}")

# תצוגת מלאי
st.subheader(t["title"])
for i, row in st.session_state.df.iterrows():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(
            f"**{row[t['name']]}** | {t['batch_number']}: {row[t['batch_number']]} | "
            f"{t['expiry_date']}: {row[t['expiry_date']]} | {t['expiry_note']}: {row[t['expiry_note']]} | "
            f"{t['quantity']}: {row[t['quantity']]} | {t['location']}: {row[t['location']]}"
        )
    with col2:
        if st.button(t["delete"], key=f"del_{i}"):
            st.session_state.delete_index = i
        if row[t["quantity"]] > 0:
            if st.button(t["use_bottle"], key=f"use_{i}"):
                st.session_state.df.at[i, t["quantity"]] -= 1
                log_row = pd.DataFrame([[datetime.now(), row[t["name"]], row[t["batch_number"]], username]],
                                       columns=["Date", t["name"], t["batch_number"], t["username"]])
                st.session_state.log = pd.concat([st.session_state.log, log_row], ignore_index=True)
                st.rerun()
        else:
            st.info("❗ 0")

if st.session_state.delete_index is not None:
    i = st.session_state.delete_index
    st.error(f"{t['confirm_msg']} {st.session_state.df.loc[i, t['name']]}?")
    b1, b2 = st.columns(2)
    if b1.button(t["confirm_delete"]):
        st.session_state.df = st.session_state.df.drop(index=i).reset_index(drop=True)
        st.session_state.delete_index = None
        st.success(t["deleted"])
        st.rerun()
    if b2.button(t["cancel"]):
        st.session_state.delete_index = None
        st.info(t["cancelled"])

# הורדה ל-CSV
csv = st.session_state.df.to_csv(index=False, encoding='utf-8-sig')
st.download_button("📥 Download CSV", csv, file_name="inventory.csv", mime="text/csv")

# לוג שימוש
st.subheader(t["history_log"])
st.dataframe(st.session_state.log, use_container_width=True)
