# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

# Конфигурация страницы
st.set_page_config(
    page_title="Диагностика ТЭД",
    page_icon="⚡",
    layout="wide"
)

# Заголовок
st.markdown("<h1 style='text-align: center; color: #1f77b4;'>⚡ Система диагностики ТЭД</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Анализ реактивной ЭДС и межламельного напряжения</p>", unsafe_allow_html=True)
st.markdown("---")

# Боковая панель
st.sidebar.header("📋 Параметры")

ted_type = st.sidebar.radio("Тип ТЭД:", ["НБ-514Е (стандартные)", "Пользовательские"])

if ted_type == "НБ-514Е (стандартные)":
    e_eds_threshold = 5.0
    u_interlamella_threshold = 35.5
    st.sidebar.success("✅ Загружены стандартные параметры НБ-514Е")
else:
    e_eds_threshold = st.sidebar.number_input("Порог ЭДС, В", value=5.0, min_value=1.0, max_value=20.0)
    u_interlamella_threshold = st.sidebar.number_input("Порог межл. напр., В", value=35.5, min_value=10.0, max_value=50.0)

# Основной контент
tab1, tab2, tab3 = st.tabs(["📊 Анализ данных", "ℹ️ Справка", "🧪 Тест"])

with tab1:
    st.header("Загрузка и анализ МСУД")
    
    uploaded_file = st.file_uploader(
        "Загрузите файл МСУД (Excel .xlsx или CSV)",
        type=["xlsx", "csv"]
    )
    
    if uploaded_file is not None:
        try:
            # Загрузка файла
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            st.success("✅ Файл успешно загружен!")
            
            # Информация о файле
            col1, col2, col3 = st.columns(3)
            col1.metric("Записей", len(df))
            col2.metric("Колонок", len(df.columns))
            col3.metric("Размер", f"{uploaded_file.size / 1024:.1f} KB")
            
            st.subheader("Предпросмотр данных:")
            st.dataframe(df.head(20), use_container_width=True)
            
            # Выбор колонок
            st.subheader("Выберите колонки для анализа:")
            cols = df.columns.tolist()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                eds_col = st.selectbox("ЭДС", cols, key="eds")
            with col2:
                inter_col = st.selectbox("Межл. напр.", cols, key="inter")
            with col3:
                uks_col = st.selectbox("Uks", cols, key="uks")
            with col4:
                ib_col = st.selectbox("Ib", cols, key="ib")
            
            # Подготовка данных
            df_analysis = df[[eds_col, inter_col, uks_col, ib_col]].copy()
            df_analysis.columns = ['EDS', 'Interlamella', 'Uks', 'Ib']
            df_analysis = df_analysis.dropna()
            
            st.markdown("---")
            
            # Статистика
            st.subheader("📊 Статистика:")
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("Ср. ЭДС", f"{df_analysis['EDS'].mean():.3f} В")
            with col2:
                st.metric("Макс ЭДС", f"{df_analysis['EDS'].max():.3f} В")
            with col3:
                st.metric("Мин ЭДС", f"{df_analysis['EDS'].min():.3f} В")
            with col4:
                st.metric("Ср. межл.", f"{df_analysis['Interlamella'].mean():.3f} В")
            with col5:
                st.metric("Макс межл.", f"{df_analysis['Interlamella'].max():.3f} В")
            with col6:
                st.metric("Мин межл.", f"{df_analysis['Interlamella'].min():.3f} В")
            
            st.markdown("---")
            
            # Превышения
            st.subheader("⚠️ Превышения пороговых значений:")
            
            exceed_eds = (df_analysis['EDS'] > e_eds_threshold).sum()
            exceed_inter = (df_analysis['Interlamella'] > u_interlamella_threshold).sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Превышений ЭДС", exceed_eds, f"{100*exceed_eds/len(df_analysis):.1f}%")
            with col2:
                st.metric("Превышений межл.", exceed_inter, f"{100*exceed_inter/len(df_analysis):.1f}%")
            with col3:
                st.metric("Порог ЭДС", f"{e_eds_threshold} В")
            with col4:
                st.metric("Порог межл.", f"{u_interlamella_threshold} В")
            
            st.markdown("---")
            
            # Диагностика
            st.subheader("🔍 Диагностика:")
            
            eds_max = df_analysis['EDS'].max()
            inter_max = df_analysis['Interlamella'].max()
            eds_mean = df_analysis['EDS'].mean()
            inter_mean = df_analysis['Interlamella'].mean()
            
            if eds_max > e_eds_threshold * 1.2 or inter_max > u_interlamella_threshold * 1.2:
                st.error("🔴 **КРИТИЧЕСКОЕ СОСТОЯНИЕ** - требуется срочное вмешательство!")
            elif eds_max > e_eds_threshold or inter_max > u_interlamella_threshold:
                st.warning("🟠 **ОПАСНОЕ СОСТОЯНИЕ** - требуется техническое обслуживание!")
            elif eds_mean > 3.5 or inter_mean > 20:
                st.info("🟡 **СРЕДНЕЕ СОСТОЯНИЕ** - рекомендуется плановое обслуживание")
            else:
                st.success("🟢 **НОРМАЛЬНОЕ СОСТОЯНИЕ** - продолжить мониторинг")
            
            st.markdown("---")
            
            # Таблица статистики
            st.subheader("📈 Подробная статистика:")
            
            stats = pd.DataFrame({
                'Параметр': [
                    'Реактивная ЭДС',
                    'Межламельное напряжение',
                    'Напряжение Uks',
                    'Ток Ib'
                ],
                'Среднее': [
                    f"{df_analysis['EDS'].mean():.4f}",
                    f"{df_analysis['Interlamella'].mean():.4f}",
                    f"{df_analysis['Uks'].mean():.4f}",
                    f"{df_analysis['Ib'].mean():.4f}"
                ],
                'Минимум': [
                    f"{df_analysis['EDS'].min():.4f}",
                    f"{df_analysis['Interlamella'].min():.4f}",
                    f"{df_analysis['Uks'].min():.4f}",
                    f"{df_analysis['Ib'].min():.4f}"
                ],
                'Максимум': [
                    f"{df_analysis['EDS'].max():.4f}",
                    f"{df_analysis['Interlamella'].max():.4f}",
                    f"{df_analysis['Uks'].max():.4f}",
                    f"{df_analysis['Ib'].max():.4f}"
                ],
                'Стд. откл.': [
                    f"{df_analysis['EDS'].std():.4f}",
                    f"{df_analysis['Interlamella'].std():.4f}",
                    f"{df_analysis['Uks'].std():.4f}",
                    f"{df_analysis['Ib'].std():.4f}"
                ]
            })
            
            st.dataframe(stats, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Экспорт
            st.subheader("📥 Экспорт результатов:")
            
            result_data = {
                'Параметр': [
                    'Дата анализа',
                    'Состояние',
                    'Средняя ЭДС (В)',
                    'Макс ЭДС (В)',
                    'Среднее межл. напр. (В)',
                    'Макс межл. напр. (В)',
                    'Превышений ЭДС',
                    'Превышений межл. напр.',
                    'Всего записей'
                ],
                'Значение': [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Нормальное" if eds_max <= e_eds_threshold else "Критическое",
                    f"{df_analysis['EDS'].mean():.4f}",
                    f"{df_analysis['EDS'].max():.4f}",
                    f"{df_analysis['Interlamella'].mean():.4f}",
                    f"{df_analysis['Interlamella'].max():.4f}",
                    str(exceed_eds),
                    str(exceed_inter),
                    str(len(df_analysis))
                ]
            }
            
            result_df = pd.DataFrame(result_data)
            csv = result_df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="📊 Скачать результаты (CSV)",
                data=csv,
                file_name=f"ted_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            st.success("✅ Анализ завершён успешно!")
            
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
    else:
        st.info("👆 Загрузите файл МСУД для анализа")

with tab2:
    st.header("ℹ️ Справочная информация")
    
    st.subheader("📖 О системе")
    st.write("""
    Система диагностики предназначена для анализа состояния коллекторно-щеточного аппарата 
    тяговых электродвигателей на основе данных из системы мониторинга и управления двигателем (МСУД).
    
    **Основные параметры:**
    - **Реактивная ЭДС (V)** — характеризует качество коммутации
    - **Межламельное напряжение (U)** — напряжение между коллекторными пластинами
    
    **Методика:** Волчек Т.В., Волчек Р.В. "Разработка методики определения нарушения 
    коммутационной устойчивости коллекторных тяговых электродвигателей"
    """)
    
    st.subheader("📊 Степени искрения (ГОСТ 2582-2013)")
    
    grades = pd.DataFrame({
        'Степень': ['Нормальная', 'Средняя', 'Опасная', 'Критическая'],
        'Статус': ['✅', '🟡', '🟠', '🔴'],
        'Описание': [
            'Нет видимого искрения',
            'Видимое искрение на участках',
            'Значительное искрение',
            'Сильное искрение'
        ]
    })
    
    st.dataframe(grades, use_container_width=True, hide_index=True)
    
    st.subheader("🔧 Параметры ТЭД НБ-514Е")
    
    params = pd.DataFrame({
        'Параметр': [
            'Число витков в секции',
            'Удельная магнитная проводимость',
            'Длина якоря',
            'Линейная скорость коллектора',
            'Число пар полюсов',
            'Порог ЭДС',
            'Порог межл. напр.'
        ],
        'Значение': [
            '164',
            '0.95',
            '0.5 м',
            '25 м/с',
            '4',
            '5 В',
            '35.5 В'
        ]
    })
    
    st.dataframe(params, use_container_width=True, hide_index=True)

with tab3:
    st.header("🧪 Тестовые данные")
    
    if st.button("🔄 Создать и скачать тестовые данные"):
        np.random.seed(42)
        n = 1000
        
        test_data = pd.DataFrame({
            'Время': pd.date_range('2025-01-01', periods=n, freq='1S'),
            'эдс': np.random.gamma(2, 2, n) + np.linspace(0, 2, n),
            'межламельное': np.random.gamma(3, 8, n) + np.linspace(0, 6, n),
            'Uks[1]': np.random.normal(25000, 500, n),
            'Ib[1]': np.random.normal(600, 100, n)
        })
        
        # Добавить выбросы
        outlier_idx = np.random.choice(n, 50, replace=False)
        test_data.loc[outlier_idx, 'эдс'] += np.random.uniform(3, 5, 50)
        test_data.loc[outlier_idx, 'межламельное'] += np.random.uniform(10, 20, 50)
        
        csv_test = test_data.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="📥 Скачать тестовые данные (CSV)",
            data=csv_test,
            file_name="test_ted_data.csv",
            mime="text/csv"
        )
        
        st.success("✅ Тестовые данные готовы!")
        st.dataframe(test_data.head(20), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("""
**Приложение:** Диагностика ТЭД  
**Версия:** 1.0 (упрощённая)  
**Методика:** Волчек Т.В., Волчек Р.В.
""")
