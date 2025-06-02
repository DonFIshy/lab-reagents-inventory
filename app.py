import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Reagents Inventory", layout="wide")

# תרגום טקסטים
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
        "quantity": "כמות במלאי",
        "open_date": "תאריך פתיחה",
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
        "download_btn": "📥 הורד CSV"
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
        "quantity": "Stock Quantity",
        "open_date": "Opening Date",
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
        "download_btn": "📥 Download CSV"
    }
}

# בחירת שפה
language = st.sidebar.selectbox("Language / שפה", ["עברית", "English"])
lang_code = "he" if language == "עברית" else "en"
t = translations[lang_code]

# התחלה
@st.cache_data
def init_data():
    return pd.DataFrame(columns=[
        t["name"], t["supplier"], t["catalog_number"], t["cas_number"],
        t["internal_id"], t["batch_number"], t["received_date"],
        t["expiry_date"], t["quantity"], t["open_date"]
    ])

if "df" not in st.session_state:
    st.session_state.df = init_data()

uploaded_file = st.sidebar.file_uploader("📤 העלה קובץ Excel (xlsx)", type=["xlsx"])
if uploaded_file:
    try:
        uploaded_df = pd.read_excel(uploaded_file)
        expected_columns = [
            t["name"], t["supplier"], t["catalog_number"], t["cas_number"],
            t["internal_id"], t["batch_number"], t["received_date"],
            t["expiry_date"], t["quantity"], t["open_date"]
        ]
        if all(col in uploaded_df.columns for col in expected_columns):
            st.session_state.df = uploaded_df
            st.success("📁 הקובץ נטען בהצלחה.")
        else:
            st.error("❌ הקובץ לא כולל את כל העמודות הנדרשות.")
    except Exception as e:
        st.error(f"שגיאה בטעינת הקובץ: {e}")


if "delete_index" not in st.session_state:
    st.session_state.delete_index = None

st.title(t["title"])

# טופס הוספה
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
    quantity = cols[0].number_input(t["quantity"], min_value=0.0, format="%.2f")
    open_date = cols[1].date_input(t["open_date"], value=datetime.today())

    submitted = st.form_submit_button(t["add_reagent"])
    if submitted:
        new_row = pd.DataFrame([[
            name, supplier, catalog_number, cas_number, internal_id,
            batch_number, received_date, expiry_date, quantity, open_date
        ]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.success(t["added"])

# הצגת טבלה עם כפתורי מחיקה
st.subheader(t["reagents_list"])
for i, row in st.session_state.df.iterrows():
    cols = st.columns([5, 1])
    with cols[0]:
        st.markdown(
            f"""
            **{row[t['name']]}**  
            {t['supplier']}: {row[t['supplier']]} | {t['cas_number']}: {row[t['cas_number']]} | {t['expiry_date']}: {row[t['expiry_date']]} | {t['quantity']}: {row[t['quantity']]}
            """
        )
    with cols[1]:
        if st.button(t["delete"], key=f"delete_{i}"):
            st.session_state.delete_index = i

# אישור מחיקה
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

# התראות תוקף
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

# הורדה כ-CSV
st.subheader(t["download"])
buffer = io.StringIO()
st.session_state.df.to_csv(buffer, index=False, encoding='utf-8-sig')
st.download_button(t["download_btn"], buffer.getvalue(), file_name="reagents_inventory.csv", mime="text/csv")
