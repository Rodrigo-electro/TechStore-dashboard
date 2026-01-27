# Codigo para Streamlit, copiar, pegar y guardar como TechStore_app.py, solo este bloque
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="TechStore | Command Center",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZADO (Look & Feel Profesional) ---
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    div.block-container {padding-top: 2rem;}
    .stMetric {background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    h1, h2, h3 {color: #2c3e50;}
    .big-font {font-size: 20px !important; font-weight: bold; color: #34495e;}
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS CACHEADA ---
@st.cache_data
def load_data():
    # En un caso real, estas rutas serían relativas al repo de GitHub
    df_master = pd.read_csv('deployment_artifacts/dashboard_master_data.csv')
    df_sales = pd.read_csv('deployment_artifacts/dashboard_sales_history.csv')
    df_imp = pd.read_csv('deployment_artifacts/feature_importance_churn.csv')
    return df_master, df_sales, df_imp

try:
    df, df_sales, df_imp = load_data()
except:
    st.error("⚠️ Datos no encontrados. Por favor, asegúrese de subir la carpeta 'deployment_artifacts'.")
    st.stop()

# --- SIDEBAR: NAVEGACIÓN Y FILTROS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3594/3594436.png", width=60)
    st.title("TechStore")
    st.markdown("v2.4.0 (Prod)")

    st.divider()

    # Selector de Rol (Seguridad basada en rol simulada)
    role = st.selectbox("Modo de Visualización",
                       ["👤 CEO (Estratégico)",
                        "📢 CMO (Marketing)",
                        "🔧 Tech Lead (MLOps)"])

    st.divider()

    # Filtros Globales
    st.subheader("Filtros Globales")
    segment_filter = st.multiselect("Segmento", df['segmento'].unique(), default=df['segmento'].unique())
    channel_filter = st.multiselect("Canal Preferido", df['canal_preferido'].unique(), default=df['canal_preferido'].unique())

    # Aplicar filtros
    df_filtered = df[df['segmento'].isin(segment_filter) & df['canal_preferido'].isin(channel_filter)]

    st.info(f"Mostrando {len(df_filtered)} clientes filtrados.")

# --- LÓGICA DE VISTAS ---

# ==========================================
# VISTA 1: CEO (ESTRATÉGICA Y FINANCIERA)
# ==========================================
if role == "👤 CEO (Estratégico)":
    st.title("📈 Tablero Ejecutivo: Salud del Negocio")
    st.markdown(f"**Última actualización:** {datetime.now().strftime('%d-%m-%Y')}")

    # 1. KPIs Principales
    col1, col2, col3, col4 = st.columns(4)

    revenue_total = df_filtered['monetary'].sum()
    churn_rate = df_filtered['prediccion_fuga'].mean() * 100
    risk_rev = df_filtered[df_filtered['prediccion_fuga']==1]['monetary'].sum()
    avg_clv = df_filtered['clv_estimado'].mean()

    col1.metric("Ingresos Totales (YTD)", f"${revenue_total:,.0f}", "+12%")
    col2.metric("Tasa de Fuga Proyectada", f"{churn_rate:.1f}%", "-0.5%", delta_color="inverse")
    col3.metric("Ingresos en Riesgo", f"${risk_rev:,.0f}", "High Priority", delta_color="inverse")
    col4.metric("CLV Promedio", f"${avg_clv:,.0f}", "+$50")

    st.markdown("---")

    # 2. Gráficos Estratégicos (Dos columnas)
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Proyección de Ventas vs Real")
        # Gráfico combinado Línea (Ventas) y Barras (Budget)
        fig_sales = make_subplots(specs=[[{"secondary_y": True}]])
        fig_sales.add_trace(
            go.Scatter(x=df_sales['fecha'], y=df_sales['ventas'], name="Ventas Reales"),
            secondary_y=False
        )
        fig_sales.add_trace(
            go.Bar(x=df_sales['fecha'], y=df_sales['marketing_budget'], name="Presupuesto Mkt", opacity=0.3),
            secondary_y=True
        )
        fig_sales.update_layout(title_text="Tendencia de Ventas e Inversión")
        st.plotly_chart(fig_sales, use_container_width=True)

    with c2:
        st.subheader("Distribución de Riesgo")
        fig_pie = px.pie(df_filtered, names='nivel_riesgo', title="Clientes por Nivel de Riesgo",
                         color='nivel_riesgo',
                         color_discrete_map={'Bajo':'#2ecc71', 'Medio':'#f1c40f', 'Alto':'#e74c3c'})
        st.plotly_chart(fig_pie, use_container_width=True)

    # 3. Simulador ROI (Interactivo)
    st.success("🤖 **Simulador de Decisiones Estratégicas**")
    sc1, sc2, sc3 = st.columns(3)
    presupuesto = sc1.number_input("Presupuesto Retención ($)", value=20000, step=1000)
    costo_accion = sc2.number_input("Costo por Acción ($)", value=25)
    tasa_exito = sc3.slider("Tasa de Éxito Estimada (%)", 10, 50, 20) / 100

    clientes_alcanzables = presupuesto // costo_accion
    clientes_riesgo = len(df_filtered[df_filtered['prediccion_fuga']==1])
    impacto_real = min(clientes_alcanzables, clientes_riesgo)
    dinero_salvado = impacto_real * avg_clv * tasa_exito
    roi = ((dinero_salvado - presupuesto) / presupuesto) * 100

    st.markdown(f"""
    <div style='background-color: #d4edda; padding: 10px; border-radius: 5px; color: #155724;'>
        Al invertir <b>${presupuesto:,}</b>, podrías salvar <b>${dinero_salvado:,.0f}</b> generando un ROI de <b>{roi:.1f}%</b>.
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# VISTA 2: CMO (MARKETING & CAMPAÑAS)
# ==========================================
elif role == "📢 CMO (Marketing)":
    st.title("🎯 Centro de Activación de Marketing")

    # Pestañas para organizar flujos de trabajo
    tab1, tab2, tab3 = st.tabs(["📊 Insights de Cliente", "🚨 Prevención de Fuga", "💎 Oportunidades Upsell"])

    with tab1:
        st.subheader("¿Qué define a nuestros segmentos?")
        # Gráfico de burbujas: Satisfacción vs Gasto vs Frecuencia
        fig_bubble = px.scatter(df_filtered, x="satisfaccion", y="monetary",
                                size="frequency", color="segmento",
                                hover_name="cliente_id", size_max=60,
                                title="Mapa de Valor de Clientes")
        st.plotly_chart(fig_bubble, use_container_width=True)

        st.subheader("Drivers de Comportamiento")
        st.bar_chart(df_imp.set_index('feature')['importance'].head(10))

    with tab2:
        st.subheader("Lista de Acción Inmediata (Churn Prevention)")
        # Filtro de clientes en riesgo alto
        risk_list = df_filtered[df_filtered['nivel_riesgo'] == 'Alto'].sort_values('probabilidad_fuga', ascending=False)
        st.dataframe(risk_list[['cliente_id', 'probabilidad_fuga', 'satisfaccion', 'categoria_favorita', 'clv_estimado']].head(50))

        # Botón de descarga real
        csv = risk_list.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar Lista para Email Marketing",
            csv,
            "churn_risk_campaign.csv",
            "text/csv",
            key='download-churn'
        )

    with tab3:
        st.subheader("Clientes Leales para Upselling")
        # Lógica: Clientes leales (Riesgo bajo) con alta satisfacción
        upsell_list = df_filtered[(df_filtered['nivel_riesgo'] == 'Bajo') & (df_filtered['satisfaccion'] > 8)]
        st.write(f"Se encontraron {len(upsell_list)} candidatos ideales para cross-selling.")
        st.dataframe(upsell_list[['cliente_id', 'segmento', 'beneficio_neto', 'categoria_favorita']])

# ==========================================
# VISTA 3: TECH LEAD (MLOPS & AUDITORÍA)
# ==========================================
elif role == "🔧 Tech Lead (MLOps)":
    st.title("⚙️ Panel de Control de Modelos")

    c1, c2 = st.columns(2)
    with c1:
        st.info("Estado del Pipeline: **Activo**")
        st.code("Last Run: 2025-01-23 04:00 UTC\nStatus: SUCCESS\nErrors: 0", language="bash")
    with c2:
        st.warning("Próximo Reentrenamiento: **En 4 días**")
        st.progress(60) # Barra de progreso simulada

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Distribución de Probabilidades (Drift Monitor)")
        fig_hist = px.histogram(df, x="probabilidad_fuga", nbins=50,
                               title="Histograma de Scores", color_discrete_sequence=['#3498db'])
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_r:
        st.subheader("Auditoría de Fairness")
        # Simulación de métrica de bias
        bias_data = df.groupby('segmento')['prediccion_fuga'].mean().reset_index()
        fig_bias = px.bar(bias_data, x='segmento', y='prediccion_fuga',
                          title="Tasa de Positivos por Grupo (Control de Sesgo)")
        # Línea de promedio
        fig_bias.add_hline(y=df['prediccion_fuga'].mean(), line_dash="dot", annotation_text="Promedio Global")
        st.plotly_chart(fig_bias, use_container_width=True)

    st.subheader("Feature Importance Cruda")
    st.json(df_imp.head(10).set_index('feature').to_dict()['importance'])
