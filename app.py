import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="ניהול מלאי ריאגנטים", layout="wide")

@st.cache_data
def init_data():
    return pd.DataFrame(columns=[
        "שם הריאגנט", "ספק", "מספר קטלוגי", "מספר CAS", "מספר פנימי",
        "מספר אצווה", "תאריך קבלה", "תוקף", "כמות במלאי", "תאריך פתיחה"
    ])

if "df" not in st.session_state:
    st.session_state.df = init_data()

if "delete_index" not in st.session_state:
    st.session_state.delete_index = None

st.title("📦 ניהול מלאי ריאגנטים במעבדה")

# טופס הוספה
with st.form("form_add"):
    cols = st.columns(2)
    name = cols[0].text_input("שם הריאגנט")
    supplier = cols[1].text_input("ספק")

    cols = st.columns(2)
    catalog_number = cols[0].text_input("מספר קטלוגי")
    cas_number = cols[1].text_input("מספר CAS")

    cols = st.columns(2)
    internal_id = cols[0].text_input("מספר פנימי")
    batch_number = cols[1].text_input("מספר אצווה")

    cols = st.columns(2)
    received_date = cols[0].date_input("תאריך קבלה", value=datetime.today())
    expiry_date = cols[1].date_input("תוקף")

    cols = st.columns(2)
    quantity = cols[0].number_input("כמות במלאי", min_value=0.0, format="%.2f")
    open_date = cols[1].date_input("תאריך פתיחה", value=datetime.today())

    submitted = st.form_submit_button("➕ הוסף ריאגנט")
    if submitted:
        new_row = pd.DataFrame([[
            name, supplier, catalog_number, cas_number, internal_id,
            batch_number, received_date, expiry_date, quantity, open_date
        ]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.success("✔️ נוסף!")

# טבלת ריאגנטים עם מחיקה
st.subheader("📋 רשימת ריאגנטים")
for i, row in st.session_state.df.iterrows():
    cols = st.columns([5, 1])
    with cols[0]:
        st.markdown(
            f"""
            **{row['שם הריאגנט']}**  
            ספק: {row['ספק']} | CAS: {row['מספר CAS']} | תוקף: {row['תוקף']} | כמות: {row['כמות במלאי']}
            """
        )
    with cols[1]:
        if st.button("🗑️ מחק", key=f"delete_{i}"):
            st.session_state.delete_index = i

# אישור מחיקה
if st.session_state.delete_index is not None:
    index = st.session_state.delete_index
    st.error(f"האם אתה בטוח שברצונך למחוק את הריאגנט: **{st.session_state.df.loc[index, 'שם הריאגנט']}**?")
    col_confirm = st.columns(2)
    if col_confirm[0].button("✅ כן, מחק", key="confirm_delete"):
        st.session_state.df = st.session_state.df.drop(index=index).reset_index(drop=True)
        st.session_state.delete_index = None
        st.success("הריאגנט נמחק בהצלחה.")
        st.rerun()
    if col_confirm[1].button("❌ ביטול", key="cancel_delete"):
        st.session_state.delete_index = None
        st.info("המחיקה בוטלה.")

# התראות תוקף
st.subheader("⚠️ התראות: תוקפים קרובים")
today = datetime.today().date()
df_ale_
