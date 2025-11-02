# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Диагностика ТЭД", layout="wide", page_icon="⚡")

st.title("⚡ Система диагностики ТЭД")
st.markdown("Анализ реактивной ЭДС и межламельного напряжения")
st.markdown("---")

st.sidebar.header("📋 Параметры")
e_eds_threshold = st.sidebar.number_input("Порог ЭДС, В", min_value=1.0, max_value=20.0, value=5.0, step=0.5)
u_threshold = st.sidebar.number_input("Порог межл. напр., В", min_value=10.0, max_value=50.0, value=35.5, step=1.0)

st.header("📂 Загрузка данных МСУД")
uploaded_file = st.file_uploader("Загрузите файл МСУД (Excel .xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ Файл успешно загружен!")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Записей", len(df))
        col2.metric("📋 Колонок", len(df.columns))
        col3.metric("📁 Размер", f"{len(df) * len(df.columns)} ячеек")
        
        st.markdown("---")
        
        st.subheader("Выберите колонки для анализа:")
        cols = df.columns.tolist()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            eds_col = st.selectbox("Колонка ЭДС", cols, key="eds")
        with col2:
            inter_col = st.selectbox("Колонка межл. напр.", cols, key="inter")
        with col3:
            uks_col = st.selectbox("Колонка Uks", cols, key="uks")
        with col4:
            ib_col = st.selectbox("Колонка Ib", cols, key="ib")
        
        df_analysis = df[[eds_col, inter_col, uks_col, ib_col]].copy()
        df_analysis.columns = ['EDS', 'Interlamella', 'Uks', 'Ib']
        df_analysis = df_analysis.dropna()
        
        st.markdown("---")
        
        st.subheader("📊 Статистика")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Ср. ЭДС", f"{df_analysis['EDS'].mean():.3f} В")
        col2.metric("Макс ЭДС", f"{df_analysis['EDS'].max():.3f} В")
        col3.metric("Мин ЭДС", f"{df_analysis['EDS'].min():.3f} В")
        col4.metric("Ср. межл.", f"{df_analysis['Interlamella'].mean():.3f} В")
        col5.metric("Макс межл.", f"{df_analysis['Interlamella'].max():.3f} В")
        col6.metric("Мин межл.", f"{df_analysis['Interlamella'].min():.3f} В")
        
        st.markdown("---")
        
        st.subheader("🔍 Диагностика")
        
        exceed_eds = (df_analysis['EDS'] > e_eds_threshold).sum()
        exceed_inter = (df_analysis['Interlamella'] > u_threshold).sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Превышений ЭДС", exceed_eds, f"{100*exceed_eds/len(df_analysis):.1f}%")
        with col2:
            st.metric("Превышений межл.", exceed_inter, f"{100*exceed_inter/len(df_analysis):.1f}%")
        
        if df_analysis['EDS'].max() > e_eds_threshold * 1.2 or df_analysis['Interlamella'].max() > u_threshold * 1.2:
            st.error("🔴 КРИТИЧЕСКОЕ СОСТОЯНИЕ - требуется срочное вмешательство!")
        elif df_analysis['EDS'].max() > e_eds_threshold or df_analysis['Interlamella'].max() > u_threshold:
            st.warning("🟠 ОПАСНОЕ СОСТОЯНИЕ - требуется техническое обслуживание!")
        elif df_analysis['EDS'].mean() > 3.5 or df_analysis['Interlamella'].mean() > 20:
            st.info("🟡 СРЕДНЕЕ СОСТОЯНИЕ - рекомендуется плановое обслуживание")
        else:
            st.success("🟢 НОРМАЛЬНОЕ СОСТОЯНИЕ - продолжить мониторинг")
        
        st.markdown("---")
        
        st.subheader("📈 Интерактивные графики")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["ЭДС", "Межл. напр.", "Оба (двойная ось)", "Гистограмма", "Корреляция"])
        
        with tab1:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(y=df_analysis['EDS'], mode='lines', name='ЭДС', line=dict(color='#1f77b4', width=2), fill='tozeroy'))
            fig1.add_hline(y=e_eds_threshold, line_dash="dash", line_color="red", annotation_text="Порог")
            fig1.update_layout(title="Реактивная ЭДС", xaxis_title="Отсчёт", yaxis_title="ЭДС, В", height=400)
            st.plotly_chart(fig1, use_container_width=True)
        
        with tab2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(y=df_analysis['Interlamella'], mode='lines', name='Межл. напр.', line=dict(color='#ff7f0e', width=2), fill='tozeroy'))
            fig2.add_hline(y=u_threshold, line_dash="dash", line_color="red", annotation_text="Порог")
            fig2.update_layout(title="Межламельное напряжение", xaxis_title="Отсчёт", yaxis_title="Напр., В", height=400)
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(y=df_analysis['EDS'], mode='lines', name='ЭДС', line=dict(color='#1f77b4'), yaxis='y1'))
            fig3.add_trace(go.Scatter(y=df_analysis['Interlamella'], mode='lines', name='Межл. напр.', line=dict(color='#ff7f0e'), yaxis='y2'))
            fig3.update_layout(
                title="ЭДС и межл. напр. (синхронно)",
                xaxis_title="Отсчёт",
                yaxis=dict(title="ЭДС, В"),
                yaxis2=dict(title="Межл. напр., В", overlaying="y", side="right"),
                height=400
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with tab4:
            fig4 = go.Figure()
            fig4.add_trace(go.Histogram(x=df_analysis['EDS'], nbinsx=30, name='ЭДС', opacity=0.6))
            fig4.add_trace(go.Histogram(x=df_analysis['Interlamella'], nbinsx=30, name='Межл. напр.', opacity=0.6))
            fig4.update_layout(barmode='overlay', title='Распределение значений', height=400)
            st.plotly_chart(fig4, use_container_width=True)
        
        with tab5:
            fig5 = go.Figure(data=go.Scatter(
                x=df_analysis['EDS'], 
                y=df_analysis['Interlamella'], 
                mode='markers', 
                marker=dict(size=6, color='#2ca02c')
            ))
            fig5.update_layout(title='Корреляция ЭДС и межл. напр.', xaxis_title='ЭДС, В', yaxis_title='Межл. напр., В', height=400)
            st.plotly_chart(fig5, use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("📥 Экспорт результатов")
        result_data = {
            'Параметр': ['Дата', 'Состояние', 'Ср. ЭДС', 'Макс ЭДС', 'Ср. межл.', 'Макс межл.', 'Превышений ЭДС', 'Превышений межл.'],
            'Значение': [
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Норма" if df_analysis['EDS'].max() <= e_eds_threshold else "Критика",
                f"{df_analysis['EDS'].mean():.4f}",
                f"{df_analysis['EDS'].max():.4f}",
                f"{df_analysis['Interlamella'].mean():.4f}",
                f"{df_analysis['Interlamella'].max():.4f}",
                str(exceed_eds),
                str(exceed_inter)
            ]
        }
        result_df = pd.DataFrame(result_data)
        csv = result_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📊 Скачать результаты (CSV)", csv, f"ted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
        
    except Exception as e:
        st.error(f"❌ Ошибка: {str(e)}")
else:
    st.info("👆 Загрузите файл МСУД для начала анализа")

st.sidebar.markdown("---")
st.sidebar.info("**Версия:** 1.0\n**Методика:** Волчек Т.В., Волчек Р.В.")
