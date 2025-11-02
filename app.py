import streamlit as st
import csv
import io
from datetime import datetime

st.set_page_config(page_title="ТЭД Диагностика", layout="wide")

st.title("⚡ Система диагностики ТЭД")
st.markdown("Анализ реактивной ЭДС и межламельного напряжения")
st.markdown("---")

# Параметры
st.sidebar.header("📋 Параметры")
e_eds_threshold = st.sidebar.number_input("Порог ЭДС, В", 5.0, 1.0, 20.0, 0.5)
u_threshold = st.sidebar.number_input("Порог межл. напр., В", 35.5, 10.0, 50.0, 1.0)

# Загрузка файла
st.header("📂 Загрузка данных")
uploaded_file = st.file_uploader("Загрузите CSV или XLSX файл", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # Чтение CSV
        if uploaded_file.name.endswith('.csv'):
            content = uploaded_file.read().decode('utf-8')
            reader = list(csv.DictReader(io.StringIO(content)))
            st.success(f"✅ Загружено {len(reader)} строк")
            
            # Вывод таблицы
            st.subheader("Данные:")
            st.write(reader[:20])
            
            # Простая статистика
            st.subheader("📊 Статистика:")
            if reader and 'эдс' in reader[0]:
                eds_values = [float(row.get('эдс', 0)) for row in reader if row.get('эдс')]
                inter_values = [float(row.get('межламельное', 0)) for row in reader if row.get('межламельное')]
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Средняя ЭДС", f"{sum(eds_values)/len(eds_values):.3f} В")
                col2.metric("Макс ЭДС", f"{max(eds_values):.3f} В")
                col3.metric("Средняя межл.", f"{sum(inter_values)/len(inter_values):.3f} В")
                col4.metric("Макс межл.", f"{max(inter_values):.3f} В")
                
                # Диагностика
                st.subheader("🔍 Диагностика:")
                if max(eds_values) > e_eds_threshold or max(inter_values) > u_threshold:
                    st.warning("⚠️ ОПАСНОЕ СОСТОЯНИЕ - требуется обслуживание!")
                else:
                    st.success("✅ Состояние нормальное")
        
        else:
            st.info("Загрузите CSV файл (XLSX требует дополнительных библиотек)")
    
    except Exception as e:
        st.error(f"Ошибка: {e}")

st.markdown("---")
st.info("**Версия:** 1.0 | **Методика:** Волчек Т.В., Волчек Р.В.")
