import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

FILE_NAME = "reagents_inventory.xlsx"

if os.path.exists(FILE_NAME):
    df = pd.read_excel(FILE_NAME)
else:
    df = pd.DataFrame(columns=[
        "שם הריאגנט", "ספק", "מספר קטלוגי", "מספר CAS", "מספר פנימי",
        "מספר אצווה", "תאריך קבלה", "תוקף", "כמות במלאי", "תאריך פתיחה"
    ])

st.title("ניהול מלאי ריאגנטים במעבדה")

# טופס הזנת ריאגנט
with st.form("add_form"):
    name = st.text_input("שם הריאגנט")
    supplier = st.text_input("ספק")
    catalog_number = st.text_input("מספר קטלוגי")
    cas_number = st.text_input("מספר CAS")
    internal_id = st.text_input("מספר פנימי של המעבדה")
    batch_number = st.text_input("מספר אצווה")
    received_date = st.date_input("תאריך קבלה למעבדה", value=datetime.today())
    expiry_date = st.date_input("תוקף")
    quantity = st.number_input("כמות במלאי", min_value=0.0, format="%.2f")
    open_date = st.date_input("תאריך פתיחה", value=datetime.today())

    submitted = st.form_submit_button("הוסף")
    if submitted:
        new_row = pd.DataFrame([[
            name, supplier, catalog_number, cas_number, internal_id,
            batch_number, received_date, expiry_date, quantity, open_date
        ]], columns=df.columns)

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        st.success("הריאגנט נוסף בהצלחה!")

# טבלת תצוגה
st.subheader("רשימת ריאגנטים")
st.dataframe(df)

# בדיקת תוקפים קרובים
st.subheader("התראות על תוקף קרוב (פחות מ-60 יום)")
today = datetime.today().date()
df['תוקף'] = pd.to_datetime(df['תוקף'], errors='coerce').dt.date
alert_df = df[df['תוקף'].notna() & (df['תוקף'] <= today + timedelta(days=60))]

if not alert_df.empty:
    st.warning("יש ריאגנטים שתוקפם מתקרב:")
    st.dataframe(alert_df)
else:
    st.success("אין ריאגנטים שתוקפם תוך חודשיים.")
