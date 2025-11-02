# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from io import BytesIO

# ============================================================================
# КОНФИГУРАЦИЯ СТРАНИЦЫ
# ============================================================================
st.set_page_config(
    page_title="Диагностика ТЭД",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# СТИЛИ И ЗАГОЛОВОК
# ============================================================================
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #666666;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">⚡ Система диагностики ТЭД</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Анализ реактивной ЭДС и межламельного напряжения</p>', unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# БОКОВАЯ ПАНЕЛЬ - ПАРАМЕТРЫ ТЭД
# ============================================================================
st.sidebar.header("📋 Параметры ТЭД")
st.sidebar.markdown("---")

# Выбор типа ТЭД
st.sidebar.subheader("Выберите тип ТЭД:")
ted_type = st.sidebar.selectbox(
    "Тип двигателя",
    ["НБ-514Е (автоматически)", "Ввести вручную"]
)

# Параметры НБ-514Е по умолчанию (из статьи Волчека)
default_params = {
    'omega_c': 164,         # Число витков в секции
    'lambda': 0.95,         # Удельная магнитная проводимость
    'l_a': 0.5,             # Длина якоря, м
    'v_k': 25,              # Линейная скорость коллектора, м/с
    'a': 2,                 # Число пар параллельных ветвей
    'p': 4,                 # Число пар полюсов
    't_k': 0.08,            # Коллекторное деление, м
    'u_k': 2,               # Число коллекторных пластин на паз
    'epsilon_k': 0.95,      # Укорочение обмотки
    'gamma': 0.85,          # Коэффициент щеточного перекрытия
    'Phi_p': 0.025,         # Магнитный поток полюса, Вб
    'n': 1500,              # Частота вращения, об/мин
}

if ted_type == "НБ-514Е (автоматически)":
    params = default_params.copy()
    st.sidebar.success("✅ Загружены параметры НБ-514Е")
else:
    st.sidebar.subheader("Введите параметры:")
    params = {
        'omega_c': st.sidebar.number_input("Число витков в секции (ωc)", value=164, min_value=50, max_value=500),
        'lambda': st.sidebar.slider("Удельная магнитная проводимость (λ)", 0.5, 1.5, 0.95, 0.01),
        'l_a': st.sidebar.number_input("Длина якоря, м", value=0.5, min_value=0.1, max_value=2.0, step=0.1),
        'v_k': st.sidebar.number_input("Линейная скорость коллектора, м/с", value=25.0, min_value=10.0, max_value=40.0, step=1.0),
        'a': st.sidebar.number_input("Число пар параллельных ветвей (a)", value=2, min_value=1, max_value=4),
        'p': st.sidebar.number_input("Число пар полюсов (p)", value=4, min_value=2, max_value=8),
        't_k': st.sidebar.number_input("Коллекторное деление, м", value=0.08, min_value=0.01, max_value=0.2, step=0.01),
        'u_k': st.sidebar.number_input("Число коллекторных пластин на паз", value=2, min_value=1, max_value=4),
        'epsilon_k': st.sidebar.slider("Укорочение обмотки (εk)", 0.8, 1.0, 0.95, 0.01),
        'gamma': st.sidebar.slider("Коэффициент щеточного перекрытия (γ)", 0.5, 1.0, 0.85, 0.01),
        'Phi_p': st.sidebar.number_input("Магнитный поток полюса, Вб", value=0.025, min_value=0.01, max_value=0.1, step=0.005),
        'n': st.sidebar.number_input("Частота вращения, об/мин", value=1500, min_value=500, max_value=3000, step=100),
    }

st.sidebar.markdown("---")
st.sidebar.subheader("🔴 Пороги диагностики:")
e_eds_threshold = st.sidebar.number_input("Порог реактивной ЭДС, В", value=5.0, min_value=1.0, max_value=20.0, step=0.5)
u_interlamella_threshold = st.sidebar.number_input("Порог межламельного напряжения, В", value=35.5, min_value=10.0, max_value=50.0, step=1.0)

# ============================================================================
# ОСНОВНОЕ СОДЕРЖИМОЕ - ТАБЛИЦЫ
# ============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Анализ", "📈 Графики", "ℹ️ Справка", "⚙️ Тест"])

with tab1:
    st.header("Загрузка и анализ данных МСУД")
    
    uploaded_file = st.file_uploader(
        "Загрузите файл с данными МСУД (Excel .xlsx или CSV)",
        type=["xlsx", "csv"],
        help="Файл должен содержать колонки с параметрами: Время, Uks, Ib, эдс, межламельное"
    )
    
    if uploaded_file is not None:
        try:
            # Загрузка файла
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            st.success("✅ Файл успешно загружен!")
            
            # Информация о данных
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Записей", len(df))
            with col2:
                st.metric("⏱️ Колонок", len(df.columns))
            with col3:
                st.metric("📁 Размер", f"{uploaded_file.size / 1024:.1f} KB")
            with col4:
                st.metric("✅ Статус", "Готово")
            
            st.subheader("Предпросмотр данных:")
            st.dataframe(df.head(20), use_container_width=True, height=400)
            
            # Выбор колонок для анализа
            st.subheader("📋 Выберите колонки для анализа:")
            col1, col2, col3, col4 = st.columns(4)
            
            columns_list = df.columns.tolist()
            
            with col1:
                uks_col = st.selectbox("Колонка Uks", columns_list, key="uks")
            with col2:
                ib_col = st.selectbox("Колонка Ib", columns_list, key="ib")
            with col3:
                eds_col = st.selectbox("Колонка эдс", columns_list, key="eds")
            with col4:
                interlamella_col = st.selectbox("Колонка межламельное напряжение", columns_list, key="inter")
            
            # Извлечение данных
            df_analysis = df[[uks_col, ib_col, eds_col, interlamella_col]].copy()
            df_analysis.columns = ['Uks', 'Ib', 'EDS', 'Interlamella']
            
            # Очистка от NaN
            df_analysis = df_analysis.dropna()
            
            # СТАТИСТИКА
            st.subheader("📊 Статистика по параметрам:")
            
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                st.metric(
                    "Средняя ЭДС",
                    f"{df_analysis['EDS'].mean():.3f} В",
                    f"Макс: {df_analysis['EDS'].max():.3f} В"
                )
            with stats_col2:
                st.metric(
                    "Среднее межл. напряжение",
                    f"{df_analysis['Interlamella'].mean():.3f} В",
                    f"Макс: {df_analysis['Interlamella'].max():.3f} В"
                )
            with stats_col3:
                exceeding_eds = (df_analysis['EDS'] > e_eds_threshold).sum()
                pct_eds = 100 * exceeding_eds / len(df_analysis)
                st.metric(
                    "Превышений ЭДС",
                    exceeding_eds,
                    f"{pct_eds:.1f}%"
                )
            with stats_col4:
                exceeding_u = (df_analysis['Interlamella'] > u_interlamella_threshold).sum()
                pct_u = 100 * exceeding_u / len(df_analysis)
                st.metric(
                    "Превышений напряжения",
                    exceeding_u,
                    f"{pct_u:.1f}%"
                )
            
            st.markdown("---")
            
            # ДИАГНОСТИКА
            st.subheader("🔍 Диагностика состояния коллектора:")
            
            def get_sparking_grade(eds_mean, u_mean, eds_max, u_max, eds_threshold, u_threshold):
                """Определение степени искрения по ГОСТ 2582-2013"""
                if eds_max > eds_threshold * 1.2 or u_max > u_threshold * 1.2:
                    return "КРИТИЧЕСКОЕ ⚠️", "danger", 4
                elif (eds_max > eds_threshold) or (u_max > u_threshold):
                    return "ОПАСНОЕ 🔴", "warning", 3
                elif eds_mean > 3.5 or u_mean > 20:
                    return "СРЕДНЕЕ 🟡", "info", 2
                else:
                    return "НОРМАЛЬНОЕ ✅", "success", 1
            
            grade, color, severity = get_sparking_grade(
                df_analysis['EDS'].mean(),
                df_analysis['Interlamella'].mean(),
                df_analysis['EDS'].max(),
                df_analysis['Interlamella'].max(),
                e_eds_threshold,
                u_interlamella_threshold
            )
            
            if severity == 4:
                st.error(f"## 🚨 {grade}\nСрочно требуется замена или ремонт ТЭД!")
            elif severity == 3:
                st.warning(f"## ⚠️ {grade}\nТребуется техническое обслуживание в ближайшее время")
            elif severity == 2:
                st.info(f"## 🟡 {grade}\nРекомендуется плановое обслуживание")
            else:
                st.success(f"## ✅ {grade}\nТЭД в нормальном состоянии")
            
            st.markdown("---")
            
            # РЕКОМЕНДАЦИИ
            st.subheader("💡 Рекомендации по обслуживанию:")
            
            recommendations = []
            if df_analysis['EDS'].max() > e_eds_threshold:
                recommendations.append("⚠️ Превышена реактивная ЭДС — проверить щёточный аппарат")
            if df_analysis['Interlamella'].max() > u_interlamella_threshold:
                recommendations.append("⚠️ Превышено межламельное напряжение — риск переброса дуги")
            if exceeding_eds > len(df_analysis) * 0.3:
                recommendations.append("⚠️ Более 30% превышений ЭДС — требуется техническое вмешательство")
            if not recommendations:
                recommendations.append("✅ Специальных рекомендаций нет — продолжить мониторинг")
            
            for rec in recommendations:
                st.write(rec)
            
            st.markdown("---")
            
            # ЭКСПОРТ РЕЗУЛЬТАТОВ
            st.subheader("📥 Экспорт результатов анализа:")
            
            result_df = pd.DataFrame({
                'Параметр': [
                    'Дата анализа',
                    'Состояние',
                    'Средняя ЭДС (В)',
                    'Макс ЭДС (В)',
                    'Среднее межл. напр. (В)',
                    'Макс межл. напр. (В)',
                    'Превышений ЭДС',
                    'Превышений напр.'
                ],
                'Значение': [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    grade.split()[0],
                    f"{df_analysis['EDS'].mean():.3f}",
                    f"{df_analysis['EDS'].max():.3f}",
                    f"{df_analysis['Interlamella'].mean():.3f}",
                    f"{df_analysis['Interlamella'].max():.3f}",
                    str(exceeding_eds),
                    str(exceeding_u)
                ]
            })
            
            csv = result_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📊 Скачать результаты (CSV)",
                data=csv,
                file_name=f"ted_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"❌ Ошибка при загрузке файла: {str(e)}")
    else:
        st.info("👆 Загрузите файл МСУД (Excel или CSV), чтобы начать анализ")

# ============================================================================
# ГРАФИКИ
# ============================================================================
with tab2:
    st.header("📈 Интерактивные графики")
    
    if uploaded_file is not None:
        try:
            # График 1: Реактивная ЭДС
            st.subheader("1. Реактивная ЭДС")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                y=df_analysis['EDS'],
                mode='lines',
                name='Реактивная ЭДС',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            ))
            fig1.add_hline(
                y=e_eds_threshold, 
                line_dash="dash", 
                line_color="red", 
                annotation_text="Порог критичности",
                annotation_position="right"
            )
            fig1.update_layout(
                title="Реактивная ЭДС (V) во времени",
                xaxis_title="Номер отсчёта",
                yaxis_title="ЭДС, В",
                hovermode='x unified',
                height=400,
                template='plotly_white'
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # График 2: Межламельное напряжение
            st.subheader("2. Межламельное напряжение")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                y=df_analysis['Interlamella'],
                mode='lines',
                name='Межламельное напряжение',
                line=dict(color='#ff7f0e', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 127, 14, 0.2)'
            ))
            fig2.add_hline(
                y=u_interlamella_threshold, 
                line_dash="dash", 
                line_color="red", 
                annotation_text="Порог критичности",
                annotation_position="right"
            )
            fig2.update_layout(
                title="Межламельное напряжение (U) во времени",
                xaxis_title="Номер отсчёта",
                yaxis_title="Напряжение, В",
                hovermode='x unified',
                height=400,
                template='plotly_white'
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # График 3: Оба параметра (двойная ось Y)
            st.subheader("3. Оба параметра (двойная ось Y)")
            fig3 = go.Figure()
            
            fig3.add_trace(go.Scatter(
                y=df_analysis['EDS'],
                mode='lines+markers',
                name='Реактивная ЭДС',
                line=dict(color='#1f77b4', width=2),
                yaxis='y1',
                marker=dict(size=4)
            ))
            
            fig3.add_trace(go.Scatter(
                y=df_analysis['Interlamella'],
                mode='lines+markers',
                name='Межламельное напряжение',
                line=dict(color='#ff7f0e', width=2),
                yaxis='y2',
                marker=dict(size=4)
            ))
            
            fig3.update_layout(
                title="Реактивная ЭДС и межламельное напряжение (синхронно)",
                xaxis_title="Номер отсчёта",
                yaxis=dict(
                    title="Реактивная ЭДС, В",
                    titlefont=dict(color="#1f77b4"),
                    tickfont=dict(color="#1f77b4")
                ),
                yaxis2=dict(
                    title="Межламельное напряжение, В",
                    titlefont=dict(color="#ff7f0e"),
                    tickfont=dict(color="#ff7f0e"),
                    overlaying="y",
                    side="right"
                ),
                hovermode='x unified',
                height=400,
                template='plotly_white',
                legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig3, use_container_width=True)
            
            # График 4: Распределение значений
            st.subheader("4. Гистограмма распределения")
            fig4 = go.Figure()
            
            fig4.add_trace(go.Histogram(
                x=df_analysis['EDS'],
                name='Реактивная ЭДС',
                nbinsx=30,
                opacity=0.6,
                marker=dict(color='#1f77b4')
            ))
            
            fig4.add_trace(go.Histogram(
                x=df_analysis['Interlamella'],
                name='Межламельное напряжение',
                nbinsx=30,
                opacity=0.6,
                marker=dict(color='#ff7f0e')
            ))
            
            fig4.update_layout(
                barmode='overlay',
                title='Распределение значений параметров',
                xaxis_title='Значение',
                yaxis_title='Частота',
                height=400,
                template='plotly_white'
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            # График 5: Корреляция
            st.subheader("5. Корреляция между параметрами")
            fig5 = go.Figure(data=go.Scatter(
                x=df_analysis['EDS'],
                y=df_analysis['Interlamella'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=range(len(df_analysis)),
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Время")
                ),
                text=range(len(df_analysis)),
                hovertemplate='<b>Отсчёт %{text}</b><br>ЭДС: %{x:.3f} В<br>Межл. напр.: %{y:.3f} В<extra></extra>'
            ))
            
            fig5.update_layout(
                title='Зависимость между реактивной ЭДС и межламельным напряжением',
                xaxis_title='Реактивная ЭДС, В',
                yaxis_title='Межламельное напряжение, В',
                height=400,
                template='plotly_white'
            )
            st.plotly_chart(fig5, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Ошибка при построении графиков: {str(e)}")
    else:
        st.info("👆 Сначала загрузите файл на вкладке 'Анализ'")

# ============================================================================
# СПРАВКА
# ============================================================================
with tab3:
    st.header("ℹ️ Справочная информация")
    
    st.subheader("📖 О системе диагностики")
    st.markdown("""
    Система предназначена для **диагностики состояния коллекторно-щеточного аппарата** тяговых электродвигателей (ТЭД) 
    на основе анализа:
    
    - **Реактивной ЭДС** — наведённой ЭДС в переходящих витках якоря
    - **Межламельного напряжения** — напряжения между соседними коллекторными пластинами
    
    Методика основана на работе **Волчека Т.В. и Волчека Р.В.** "Разработка методики определения нарушения 
    коммутационной устойчивости коллекторных тяговых электродвигателей"
    """)
    
    st.subheader("⚡ Параметры ТЭД НБ-514Е (текущие)")
    params_df = pd.DataFrame(list(params.items()), columns=['Параметр', 'Значение'])
    params_df['Описание'] = [
        'Число витков в секции',
        'Удельная магнитная проводимость',
        'Длина якоря, м',
        'Линейная скорость коллектора, м/с',
        'Число пар параллельных ветвей',
        'Число пар полюсов',
        'Коллекторное деление, м',
        'Число коллекторных пластин на паз',
        'Укорочение обмотки',
        'Коэффициент щеточного перекрытия',
        'Магнитный поток полюса, Вб',
        'Частота вращения, об/мин'
    ]
    st.dataframe(params_df, use_container_width=True, hide_index=True)
    
    st.subheader("🔍 Интерпретация результатов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Реактивная ЭДС (V)**
        - Характеризует качество коммутации
        - Высокие значения указывают на нарушение коммутации
        - Связана с переключением тока в якоре
        - Единица измерения: Вольты (В)
        """)
    
    with col2:
        st.markdown("""
        **Межламельное напряжение (U)**
        - Напряжение между соседними коллекторными пластинами
        - Высокие значения увеличивают риск электрической дуги
        - Прямо влияет на искрение на коллекторе
        - Единица измерения: Вольты (В)
        """)
    
    st.subheader("📊 Степени искрения (ГОСТ 2582-2013)")
    grades_data = {
        'Степень': ['Нормальная', 'Средняя', 'Опасная', 'Критическая'],
        'Статус': ['✅', '🟡', '🟠', '🔴'],
        'Описание': [
            'Нет видимого искрения, работа в норме',
            'Видимое искрение на небольших участках коллектора',
            'Значительное искрение, требуется обслуживание',
            'Сильное искрение, высокий риск отказа'
        ],
        'Действие': [
            'Продолжить мониторинг',
            'Плановое обслуживание',
            'Техническое обслуживание СРОЧНО',
            'Замена/Ремонт необходимы НЕМЕДЛЕННО'
        ]
    }
    grades_df = pd.DataFrame(grades_data)
    st.dataframe(grades_df, use_container_width=True, hide_index=True)
    
    st.subheader("📚 Дополнительная информация")
    st.markdown("""
    - **Источник методики:** Статья "Разработка методики определения нарушения коммутационной устойчивости коллекторных 
      тяговых электродвигателей" (Волчек Т.В., Волчек Р.В.)
    - **Применение:** Диагностика ТЭД электровозов класса НБ-514Е
    - **Данные:** МСУД (Система мониторинга и управления двигателем)
    - **Версия приложения:** 1.0
    - **Дата создания:** 2025
    """)

# ============================================================================
# ТЕСТИРОВАНИЕ
# ============================================================================
with tab4:
    st.header("⚙️ Тестовые данные и настройки")
    
    st.subheader("📋 Сгенерировать тестовые данные")
    
    if st.button("🔄 Создать тестовый набор данных"):
        # Генерация тестовых данных
        np.random.seed(42)
        n_samples = 1000
        
        test_data = pd.DataFrame({
            'Время': pd.date_range('2025-01-01', periods=n_samples, freq='1S'),
            'Uks[1]': np.random.normal(25000, 500, n_samples),
            'Ib[1]': np.random.normal(600, 100, n_samples),
            'Ud1[1]': np.random.normal(1000, 50, n_samples),
            'I1[1]': np.random.normal(800, 150, n_samples),
            'эдс': np.random.gamma(2, 2, n_samples),
            'межламельное': np.random.gamma(3, 8, n_samples)
        })
        
        # Добавляем тренд к ЭДС (постепенное увеличение)
        trend = np.linspace(0, 2, n_samples)
        test_data['эдс'] += trend
        test_data['межламельное'] += trend * 3
        
        # Добавляем несколько выбросов
        outlier_indices = np.random.choice(n_samples, 50, replace=False)
        test_data.loc[outlier_indices, 'эдс'] += np.random.uniform(3, 5, 50)
        test_data.loc[outlier_indices, 'межламельное'] += np.random.uniform(10, 20, 50)
        
        # Скачивание
        csv_test = test_data.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Скачать тестовые данные (CSV)",
            data=csv_test,
            file_name="test_ted_data.csv",
            mime="text/csv"
        )
        
        st.success("✅ Тестовые данные созданы! Нажмите кнопку выше для скачивания.")
        st.dataframe(test_data.head(20), use_container_width=True)
    
    st.subheader("🔧 Техническая информация")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Приложение:**")
        st.write("- Streamlit 1.28+")
        st.write("- Python 3.8+")
        st.write("- Plotly для графиков")
        st.write("- Pandas для обработки данных")
    
    with col2:
        st.write("**Поддерживаемые форматы:**")
        st.write("- Excel (.xlsx)")
        st.write("- CSV (.csv)")
        st.write("- Максимальный размер: 200 MB")

st.sidebar.markdown("---")
st.sidebar.info(
    "**Разработано:** Система диагностики ТЭД\n\n"
    "**Версия:** 1.0\n\n"
    "**Методика:** Волчек Т.В., Волчек Р.В."
)