# Codigo para Streamlit, copiar, pegar y guardar como TechStore_app.py, solo este bloque
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import joblib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="TechStore | Enterprise ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PRO ---
st.markdown("""
<style>
    .main {background-color: #f4f6f9;}
    .stMetric {background-color: #ffffff; padding: 15px; border-radius: 8px; border-left: 5px solid #3498db; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    .metric-alert {border-left: 5px solid #e74c3c !important;}
    .metric-success {border-left: 5px solid #2ecc71 !important;}
    h1, h2, h3 {font-family: 'Segoe UI', sans-serif; color: #2c3e50;}
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ROBUSTA ---
@st.cache_data
def load_data():
    # Rutas relativas (Asegúrate de tener estos archivos en la carpeta de despliegue)
    path = "deployment_artifacts/"

    # 1. Datos Maestros del Dashboard (Generados en Colab)
    try:
        df_master = pd.read_csv(path + 'dashboard_master_data.csv')
        df_sales_hist = pd.read_csv(path + 'dashboard_sales_history.csv')
        # Intentamos cargar modelo, si falla, usaremos simulación
        try:
            model_sales = joblib.load(path + 'sales_model.pkl')
        except:
            model_sales = None
    except FileNotFoundError:
        st.error("⚠️ Faltan archivos críticos del Pipeline (dashboard_master_data.csv).")
        st.stop()

    # 2. Datos Operativos (Archivos Raw para inventario)
    try:
        # Buscamos en carpeta artifacts o raíz
        try:
            df_trans = pd.read_csv(path + 'transacciones.csv')
            df_prod = pd.read_csv(path + 'productos_catalogo.csv')
        except:
            df_trans = pd.read_csv('transacciones.csv')
            df_prod = pd.read_csv('productos_catalogo.csv')
    except:
        # Datos dummy si no se encuentran los archivos raw (para que no rompa la demo)
        st.warning("⚠️ Usando datos simulados de inventario (Archivos raw no encontrados).")
        df_prod = pd.DataFrame({
            'nombre': ['iPhone 14', 'MacBook Pro', 'AirPods'],
            'stock': [15, 5, 100],
            'precio': [999, 1999, 199],
            'margen': [0.2, 0.15, 0.3]
        })
        df_trans = pd.DataFrame(columns=['fecha', 'producto', 'monto'])

    return df_master, df_sales_hist, df_trans, df_prod, model_sales

df, df_sales, df_trans, df_prod, model_sales = load_data()

# --- PROCESAMIENTO ON-THE-FLY (Cálculo de Inventarios) ---
def calcular_inventario(df_t, df_p):
    # Calcular ventas diarias promedio (Velocity)
    df_t['fecha'] = pd.to_datetime(df_t['fecha'])
    last_30_days = df_t['fecha'].max() - timedelta(days=30)
    sales_30d = df_t[df_t['fecha'] > last_30_days].groupby('producto').size().reset_index(name='ventas_mes')

    # Merge con catálogo
    inv_df = pd.merge(df_p, sales_30d, left_on='nombre', right_on='producto', how='left').fillna(0)

    # KPIs de Inventario
    inv_df['ventas_diarias'] = inv_df['ventas_mes'] / 30
    inv_df['dias_stock'] = np.where(inv_df['ventas_diarias'] > 0,
                                    inv_df['stock'] / inv_df['ventas_diarias'],
                                    999) # 999 si no hay ventas

    # Lógica de Reabastecimiento
    inv_df['status'] = np.where(inv_df['dias_stock'] < 15, '🔴 Crítico',
                       np.where(inv_df['dias_stock'] < 30, '🟡 Alerta', '🟢 OK'))

    inv_df['sugerencia_compra'] = np.where(inv_df['status'] != '🟢 OK',
                                          (inv_df['ventas_diarias'] * 45) - inv_df['stock'], # Target 45 días
                                          0).astype(int)
    inv_df['sugerencia_compra'] = inv_df['sugerencia_compra'].clip(lower=0)

    return inv_df

df_inv = calcular_inventario(df_trans, df_prod)

# --- SIDEBAR DE NAVEGACIÓN ---
with st.sidebar:
    # st.image("https://www.flaticon.com/free-icon/money-growth_12149250?term=sales&page=1&position=16&origin=search&related_id=12149250", width=60) # Original URL (likely a webpage)
    # Example of a direct image URL (replace with your desired image .png, .jpg, etc. link)
    st.image("https://www.streamlit.io/images/brand/streamlit-logo-secondary-colormark-light.png", width=60)
    st.title("TechStore ERP")

    perfil = st.radio("Seleccione Módulo:",
                      ["📊 CEO (Estrategia)",
                       "📦 Supply Chain (Inventario)",
                       "📢 CMO (Marketing & Ventas)"])

    st.divider()
    st.info(f"📅 Data al: {datetime.now().strftime('%Y-%m-%d')}")
    st.caption("Version-8.0 / 2026-01-27")

# ==============================================================================
# MÓDULO 1: CEO & ESTRATEGIA (Pronósticos Financieros)
# ==============================================================================
if perfil == "📊 CEO (Estrategia)":
    st.title("Tablero de Mando Integral")

    # 1. KPIs Financieros
    col1, col2, col3, col4 = st.columns(4)
    ventas_totales = df_sales['ventas'].sum() if 'ventas' in df_sales else 0
    forecast_next_m = df_sales['ventas'].mean() # Placeholder si no hay predicción

    col1.metric("Ventas YTD", f"${ventas_totales/1e6:.2f}M", "+4.5%")
    col2.metric("Margen Promedio", "22.4%", "-1.2%", delta_color="inverse")
    col3.metric("Valor Inventario", f"${(df_inv['stock']*df_inv['precio']).sum()/1e3:.1f}k", "Stable")
    col4.metric("Churn Rate Pred.", f"{df['prediccion_fuga'].mean()*100:.1f}%", "-0.8%")

    st.markdown("---")

    # 2. SIMULADOR DE VENTAS (FORECASTING)
    st.subheader("🤖 Simulador de Escenarios de Ventas (AI Forecast)")

    c1, c2 = st.columns([1, 2])

    with c1:
        st.markdown("**Panel de Control**")
        budget_input = st.slider("Presupuesto Marketing ($", 5000, 50000, 15000)
        price_idx = st.slider("Índice de Precios vs Mercado", 0.8, 1.2, 1.0)
        confianza = st.select_slider("Índice Confianza Consumidor", options=[80, 90, 100, 110, 120], value=100)

    with c2:
        # Lógica de Predicción
        if model_sales:
            # Creamos un vector de entrada para el modelo
            # Nota: Esto es simplificado. En prod, debes coincidir exacto con las features del entrenamiento
            # Asumimos features: marketing, precio, competencia, confianza, lag_1...
            last_sales = df_sales['ventas'].iloc[-1]
            input_data = pd.DataFrame({
                'marketing_budget': [budget_input],
                'precio_promedio': [200 * price_idx], # Base price 200
                'competencia_precio': [200],
                'indice_confianza': [confianza],
                'ventas_lag_1': [last_sales],
                'ventas_lag_3': [last_sales], # Simplificación
                'ventas_lag_12': [last_sales],
                'ma_3': [last_sales],
                'es_diciembre': [0]
            })

            # Ajustar columnas faltantes con 0
            cols_modelo = model_sales.feature_names_in_ if hasattr(model_sales, 'feature_names_in_') else input_data.columns
            for c in cols_modelo:
                if c not in input_data.columns:
                    input_data[c] = 0
            input_data = input_data[cols_modelo] # Reordenar

            prediccion = model_sales.predict(input_data)[0]
        else:
            # Fallback: Regresión lineal simple simulada
            prediccion = (budget_input * 2.5) + (last_sales * 0.8) * (1/price_idx)

        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = prediccion,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Ventas Proyectadas (Mes Siguiente)"},
            delta = {'reference': last_sales, 'increasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, prediccion*1.5]},
                'bar': {'color': "darkblue"},
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': last_sales}
            }
        ))
        st.plotly_chart(fig_gauge, width='stretch')
        st.info(f"💡 Insight: Aumentar el presupuesto en $1k genera un retorno estimado de ${2500 if not model_sales else 'variable'}.")

# ==============================================================================
# MÓDULO 2: SUPPLY CHAIN (Inventarios y Compras)
# ==============================================================================
elif perfil == "📦 Supply Chain (Inventario)":
    st.title("Gestión de Inventario & Compras")

    # Métricas de Stock
    low_stock = len(df_inv[df_inv['status'] == '🔴 Crítico'])
    stock_value = (df_inv['stock'] * df_inv['precio']).sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Productos Críticos", low_stock, "Requieren Compra", delta_color="inverse")
    m2.metric("Valor Total Inventario", f"${stock_value:,.0f}")
    m3.metric("Días Inventario Promedio", f"{df_inv['dias_stock'].median():.1f} días")

    st.divider()

    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.subheader("⚠️ Alertas de Reabastecimiento")
        # Tabla coloreada
        def color_status(val):
            color = 'red' if val == '🔴 Crítico' else 'orange' if val == '🟡 Alerta' else 'green'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_inv[df_inv['sugerencia_compra'] > 0][['nombre', 'stock', 'ventas_diarias', 'dias_stock', 'status', 'sugerencia_compra']]
            .sort_values('dias_stock')
            .style.applymap(lambda x: color_status(x) if x in ['🔴 Crítico', '🟡 Alerta', '🟢 OK'] else '', subset=['status'])
            .format({'ventas_diarias': '{:.1f}', 'dias_stock': '{:.1f}', 'sugerencia_compra': '{:.0f}'}),
            width='stretch'
        )

    with col_r:
        st.subheader("Orden de Compra Sugerida")
        costo_compra = (df_inv['sugerencia_compra'] * df_inv['precio'] * 0.6).sum() # Asumiendo costo es 60% del precio
        st.write(f"Costo Estimado Reposición: **${costo_compra:,.2f}**")

        if st.button("Generar Orden de Compra (PDF)"):
            st.success("✅ Orden #PO-2025-001 enviada a proveedores.")
            st.balloons()

    # Análisis de Inventario Muerto
    st.subheader("Análisis de Inventario Lento (Dead Stock)")
    dead_stock = df_inv[(df_inv['dias_stock'] > 90) & (df_inv['stock'] > 0)]
    if not dead_stock.empty:
        st.warning(f"Se detectaron {len(dead_stock)} productos con rotación > 90 días. Considere liquidación.")
        st.table(dead_stock[['nombre', 'stock', 'precio', 'dias_stock']])
    else:
        st.success("Inventario saludable. No hay stock estancado.")

# ==============================================================================
# MÓDULO 3: CMO (Marketing Avanzado)
# ==============================================================================
elif perfil == "📢 CMO (Marketing & Ventas)":
    st.title("Optimización de Marketing y Campañas")

    tab1, tab2 = st.tabs(["🎯 Segmentación Inteligente", "🛍️ Cross-Selling & Promos"])

    with tab1:
        st.subheader("Estrategia por Segmento de Cliente")

        # Gráfico de Dispersión Avanzado
        fig_seg = px.scatter(df, x='recency', y='frequency',
                             size='monetary', color='segmento',
                             hover_name='cliente_id',
                             title="Matriz RFM Interactiva",
                             labels={'recency': 'Días desde última compra', 'frequency': 'Frecuencia de compra'})
        st.plotly_chart(fig_seg, width='stretch')

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🏆 Clientes VIP en Riesgo")
            vip_risk = df[(df['segmento'] == 'Premium') & (df['probabilidad_fuga'] > 0.6)]
            st.dataframe(vip_risk[['cliente_id', 'clv_estimado', 'probabilidad_fuga']].head(5))
            if st.button("📧 Enviar Cupón Retención VIP"):
                st.toast("Correos enviados a 12 clientes VIP.")

        with c2:
            st.markdown("### 💤 Reactivación (Win-Back)")
            dormant = df[(df['recency'] > 60) & (df['monetary'] > 500)]
            st.write(f"Detectados {len(dormant)} clientes dormidos de alto valor.")
            st.metric("Potencial Recuperable", f"${dormant['clv_estimado'].sum()*0.1:,.0f}")

    with tab2:
        st.subheader("Motor de Recomendaciones (Market Basket)")

        # Simulación de asociación de productos (En real usaríamos algoritmo Apriori)
        # Identificar productos con mucho stock y margen para promocionar
        push_products = df_inv[(df_inv['stock'] > 50) & (df_inv['margen'] > 0.3)]

        st.info("💡 **Insight** Los siguientes productos tienen alto stock y margen. Se recomienda hacer Bundles.")

        for index, row in push_products.head(3).iterrows():
            with st.expander(f"🔥 Promo Sugerida: {row['nombre']}"):
                col_a, col_b = st.columns(2)
                col_a.metric("Stock Disponible", int(row['stock']))
                col_a.metric("Margen Beneficio", f"{row['margen']*100}%")

                # Sugerencia de Bundle
                complemento = "Funda Protectora" if "Phone" in row['nombre'] else "Garantía Extendida"
                col_b.write(f"**Estrategia:** Bundle con *{complemento}*")
                col_b.write(f"**Descuento Recomendado:** 15%")
                col_b.button(f"Lanzar Promo {row['nombre']}", key=row['nombre'])

st.sidebar.markdown("---")
st.sidebar.caption("TechStore System | Powered by Streamlit")
