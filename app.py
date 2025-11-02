import streamlit as st
import pandas as pd

st.set_page_config(page_title="ТЭД Диагностика", layout="wide")
st.title("⚡ Диагностика ТЭД")

st.write("Версия 1.0 - Система диагностики тяговых электродвигателей")

uploaded_file = st.file_uploader("Загрузите МСУД (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    
    st.success("✅ Файл загружен!")
    st.write(f"Размер: {len(df)} строк, {len(df.columns)} колонок")
    st.dataframe(df.head(20))
    
    # Экспорт
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 Скачать (CSV)", csv, "result.csv", "text/csv")
