import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Reagents Inventory", layout="wide")

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
        "quantity": "כמות במלאי (בקבוקים)",
        "open_date": "תאריך פתיחה",
        "location": "מיקום פיזי",
        "username": "שם המשתמש",
        "added": "✔️ הריאגנט נוסף!",
        "reagents_list": "📋 רשימת ריאגנטים",
        "delete": "🗑️ מחק",
        "confirm_msg": "האם אתה בטוח שברצונך למחוק את הריאגנט:",
        "confirm_delete": "✅ כן, מחק",
        "cancel": "❌ ביטול",
        "deleted": "הריאגנט נמחק בהצלחה.",
        "cancelled": "המחיקה בוטלה.",
        "alerts": "⚠️ התראות: תוקפים קרובים",
        "expiring_soon": "חומרים שתוקפם תוך חודשיים:",
        "no_expiry_alerts": "אין תוקפים קרובים.",
        "download": "⬇️ הורד CSV",
        "download_btn": "📥 הורד CSV",
        "upload_excel": "📤 העלה קובץ Excel (xlsx)",
        "history_log": "🕒 היסטוריית הוצאות",
        "use_bottle": "📤 הוצא בקבוק",
        "no_stock": "❗ אין בקבוקים במלאי",
        "bottle_used": "בקבוק הוצא ({}) - נותרו {}",
        "file_loaded": "📁 הקובץ נטען בהצלחה.",
        "file_error": "❌ הקובץ לא כולל את כל העמודות הנדרשות.",
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
        "quantity": "Stock Quantity (Bottles)",
        "open_date": "Opening Date",
        "location": "Physical Location",
        "username": "Username",
        "added": "✔️ Reagent added!",
        "reagents_list": "📋 Reagent List",
        "delete": "🗑️ Delete",
        "confirm_msg": "Are you sure you want to delete this reagent:",
        "confirm_delete": "✅ Yes, delete",
        "cancel": "❌ Cancel",
        "deleted": "Reagent deleted successfully.",
        "cancelled": "Deletion cancelled.",
        "alerts": "⚠️ Alerts: Expiring Soon",
        "expiring_soon": "Reagents expiring within 60 days:",
        "no_expiry_alerts": "No expiring reagents.",
        "download": "⬇️ Download CSV",
        "download_btn": "📥 Download CSV",
        "upload_excel": "📤 Upload Excel file (xlsx)",
        "history_log": "🕒 Usage History Log",
        "use_bottle": "📤 Use Bottle",
        "no_stock": "❗ No bottles in stock",
        "bottle_used": "Bottle used ({}) - {} left",
        "file_loaded": "📁 File loaded successfully.",
        "file_error": "❌ File missing required columns.",
        "file_exception": "File load error:"
    }
}

language = st.sidebar.selectbox("Language / שפה", ["עברית", "English"])
lang_code = "he" if language == "עברית" else "en"
t = translations[lang_code]

username = st.sidebar.text_input(t["username"], value="")

@st.cache_data
def init_data():
    return pd.DataFrame(columns=[
        t["name"], t["supplier"], t["catalog_number"], t["cas_number"], t["internal_id"],
        t["batch_number"], t["received_date"], t["expiry_date"], t["quantity"], t["open_date"], t["location"]
    ])

@st.cache_data
def init_log():
    return pd.DataFrame(columns=["Date", t["name"], t["batch_number"], t["username"]])

if "df" not in st.session_state:
    st.session_state.df = init_data()

if "log" not in st.session_state:
    st.session_state.log = init_log()

if "delete_index" not in st.session_state:
    st.session_state.delete_index = None

uploaded_file = st.sidebar.file_uploader(t["upload_excel"], type=["xlsx"])
if uploaded_file:
    try:
        uploaded_df = pd.read_excel(uploaded_file)
        expected_columns = [
            t["name"], t["supplier"], t["catalog_number"], t["cas_number"], t["internal_id"],
            t["batch_number"], t["received_date"], t["expiry_date"], t["quantity"], t["open_date"], t["location"]
        ]
        if all(col in uploaded_df.columns for col in expected_columns):
            st.session_state.df = uploaded_df
            st.success(t["file_loaded"])
        else:
            st.error(t["file_error"])
    except Exception as e:
        st.error(f"{t['file_exception']} {e}")

st.title(t["title"])

with st.form("form_add"):
    cols = st.columns(2)
    name = cols[0].text_input(t["name"])
    supplier = cols[1].text_input(t["supplier"])

    cols = st.columns(2)
    catalog_number = cols[0].text_input(t["catalog_number"])
    cas_number = cols[1].text_input(t["cas_number"])

    cols = st.columns(2)
    internal_id = cols[0].text_input(t["internal_id"])
    batch_number = cols[1].text_input(t["batch_number"])

    cols = st.columns(2)
    received_date = cols[0].date_input(t["received_date"], value=datetime.today())
    expiry_date = cols[1].date_input(t["expiry_date"])

    cols = st.columns(2)
    quantity = cols[0].number_input(t["quantity"], min_value=0, format="%d")
    open_date = cols[1].date_input(t["open_date"], value=datetime.today())

    location = st.text_input(t["location"])

    submitted = st.form_submit_button(t["add_reagent"])
    if submitted:
        new_row = pd.DataFrame([[
            name, supplier, catalog_number, cas_number, internal_id,
            batch_number, received_date, expiry_date, quantity, open_date, location
        ]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.success(t["added"])

st.subheader(t["reagents_list"])
for i, row in st.session_state.df.iterrows():
    cols = st.columns([5, 1])
    with cols[0]:
       st.markdown(f"**{row[t['name']]}** | {t['batch_number']}: {row[t['batch_number']]} | {t['expiry_date']}: {row[t['expiry_date']]} | {t['quantity']}: {row[t['quantity']]} | {t['location']}: {row[t['location']]}")


    with cols[1]:
        if st.button(t["delete"], key=f"delete_{i}"):
            st.session_state.delete_index = i
        if row[t["quantity"]] > 0:
            if st.button(t["use_bottle"], key=f"use_{i}"):
                st.session_state.df.at[i, t["quantity"]] -= 1
                new_log = pd.DataFrame([[datetime.now(), row[t["name"]], row[t["batch_number"]], username]],
                                       columns=st.session_state.log.columns)
                st.session_state.log = pd.concat([st.session_state.log, new_log], ignore_index=True)
                st.success(t["bottle_used"].format(row[t["name"]], st.session_state.df.at[i, t["quantity"]]))
                st.rerun()
        else:
            st.info(t["no_stock"])

if st.session_state.delete_index is not None:
    index = st.session_state.delete_index
    st.error(f"{t['confirm_msg']} **{st.session_state.df.loc[index, t['name']]}**?")
    col_confirm = st.columns(2)
    if col_confirm[0].button(t["confirm_delete"], key="confirm_delete"):
        st.session_state.df = st.session_state.df.drop(index=index).reset_index(drop=True)
        st.session_state.delete_index = None
        st.success(t["deleted"])
        st.rerun()
    if col_confirm[1].button(t["cancel"], key="cancel_delete"):
        st.session_state.delete_index = None
        st.info(t["cancelled"])

st.subheader(t["alerts"])
today = datetime.today().date()
df_alert = st.session_state.df.copy()
df_alert[t["expiry_date"]] = pd.to_datetime(df_alert[t["expiry_date"]], errors='coerce').dt.date
df_alert = df_alert[df_alert[t["expiry_date"]].notna() & (df_alert[t["expiry_date"]] <= today + timedelta(days=60))]

if not df_alert.empty:
    st.warning(t["expiring_soon"])
    st.dataframe(df_alert, use_container_width=True)
else:
    st.success(t["no_expiry_alerts"])

st.subheader(t["download"])
buffer = io.StringIO()
st.session_state.df.to_csv(buffer, index=False, encoding='utf-8-sig')
st.download_button(t["download_btn"], buffer.getvalue(), file_name="reagents_inventory.csv", mime="text/csv")

st.subheader(t["history_log"])
st.dataframe(st.session_state.log, use_container_width=True)
