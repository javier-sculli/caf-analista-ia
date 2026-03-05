"""
Chat UI - Interfaz conversacional para analista de datos IA
Powered by Streamlit
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

# Cargar API key desde Streamlit secrets si está disponible (Streamlit Cloud)
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

from utils.query_engine import QueryEngine
from utils.plot_generator import PlotGenerator
from utils.logger import llm_logger

# Page config
st.set_page_config(
    page_title="Analista IA - Cámara Argentina de Fintech",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        padding-bottom: 2rem;
    }
    .example-question {
        background-color: #f0f8ff;
        border-left: 4px solid #1f77b4;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        cursor: pointer;
    }
    .example-question:hover {
        background-color: #e6f3ff;
    }
    .metrics-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .log-container {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'query_engine' not in st.session_state:
    st.session_state.query_engine = None
if 'plot_generator' not in st.session_state:
    st.session_state.plot_generator = PlotGenerator()
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'current_result' not in st.session_state:
    st.session_state.current_result = None


def initialize_engine():
    """Inicializa el query engine"""
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "analytics" / "caf_analytics.duckdb"
    catalog_path = base_dir / "semantic_layer" / "data_catalog.yaml"

    if not db_path.exists():
        st.error(f"❌ Base de datos no encontrada: {db_path}")
        st.info("Por favor ejecuta el setup primero: `python demo/setup.py`")
        return None

    if not catalog_path.exists():
        st.error(f"❌ Catálogo no encontrado: {catalog_path}")
        return None

    try:
        engine = QueryEngine(db_path, catalog_path)
        return engine
    except Exception as e:
        st.error(f"Error inicializando engine: {e}")
        return None


def render_header():
    """Render app header"""
    st.markdown('<div class="main-header">🏦 Analista de Datos IA</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Cámara Argentina de Fintech</div>', unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar():
    """Render sidebar with examples and info"""
    with st.sidebar:
        st.header("💡 Preguntas de Ejemplo")

        examples = [
            "Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años",
            "¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?",
            "Mostrame la evolución de cheques vs transferencias electrónicas",
            "¿Cuál es el crecimiento real (deflactado) de los medios de pago electrónicos?",
            "Compará el volumen de pagos electrónicos en los últimos 12 meses"
        ]

        for i, example in enumerate(examples):
            if st.button(f"📌 {example[:50]}...", key=f"example_{i}", use_container_width=True):
                st.session_state.current_question = example
                st.session_state.auto_submit = True

        st.markdown("---")

        st.header("ℹ️ Información")
        st.markdown("""
        **Datos Disponibles:**
        - 📊 Transferencias inmediatas (2017-2025)
        - 📄 Cheques compensados (2017-2025)
        - 💳 Inclusión financiera
        - 📈 Inflación (IPC)
        - 💱 Tipo de cambio

        **Capacidades:**
        - ✅ Cruces automáticos entre fuentes
        - ✅ Ajuste por inflación
        - ✅ Cálculo de crecimientos YoY
        - ✅ Visualizaciones automáticas
        """)

        st.markdown("---")

        # Mostrar logs en sidebar
        with st.expander("🔍 Ver Logs Detallados", expanded=False):
            if st.session_state.current_result:
                metadata = st.session_state.current_result.get('metadata', {})

                st.subheader("Plan de Query")
                if metadata.get('plan'):
                    st.json(metadata['plan'])

                st.subheader("SQL Generado")
                if metadata.get('sql'):
                    st.code(metadata['sql'], language='sql')


def process_question(question: str):
    """Procesa una pregunta y retorna resultado"""

    # Inicializar engine si no está
    if st.session_state.query_engine is None:
        with st.spinner("⚙️ Inicializando Query Engine..."):
            st.session_state.query_engine = initialize_engine()

    if st.session_state.query_engine is None:
        st.error("❌ No se pudo inicializar el Query Engine. Revisa los logs en la terminal.")
        return None

    # Mostrar spinner
    with st.spinner("🤔 Analizando pregunta..."):
        try:
            # Ejecutar query
            result_df, metadata = st.session_state.query_engine.query(question)

            if result_df.empty:
                st.warning("⚠️ No se encontraron resultados para esta pregunta")
                return None

            # Generar gráfico
            with st.spinner("🎨 Generando visualización..."):
                fig = st.session_state.plot_generator.auto_generate(
                    result_df,
                    metadata,
                    title=question
                )

            # Guardar en historial
            result = {
                'question': question,
                'data': result_df,
                'plot': fig,
                'metadata': metadata
            }

            st.session_state.conversation_history.append(result)
            st.session_state.current_result = result

            return result

        except Exception as e:
            st.error(f"❌ Error procesando pregunta: {e}")
            llm_logger.error(f"Error: {e}")
            return None


def render_result(result):
    """Render resultado de una query"""
    if not result:
        return

    data = result['data']
    plot = result['plot']
    metadata = result['metadata']

    # Tabs para organizar info
    tab1, tab2, tab3 = st.tabs(["📊 Visualización", "🗂️ Datos", "🔍 Detalles Técnicos"])

    with tab1:
        st.plotly_chart(plot, use_container_width=True)

        # Métricas clave si hay
        if len(data) > 0:
            cols = st.columns(4)
            numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns[:4]

            for i, col in enumerate(numeric_cols):
                with cols[i]:
                    value = data[col].iloc[-1] if len(data) > 0 else 0
                    # Formatear según magnitud
                    if abs(value) >= 1e9:
                        formatted = f"${value/1e9:.2f}B"
                    elif abs(value) >= 1e6:
                        formatted = f"${value/1e6:.2f}M"
                    elif abs(value) >= 1e3:
                        formatted = f"${value/1e3:.1f}K"
                    else:
                        formatted = f"{value:.2f}"

                    st.metric(col.replace('_', ' ').title(), formatted)

    with tab2:
        st.dataframe(data, use_container_width=True)

        # Botón de descarga
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"datos_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Plan de Ejecución")
            plan = metadata.get('plan', {})
            st.json(plan)

        with col2:
            st.subheader("SQL Generado")
            sql = metadata.get('sql', '')
            st.code(sql, language='sql')

        st.subheader("Datos Externos Utilizados")
        external_data = metadata.get('external_data_used', [])
        if external_data:
            st.write(", ".join(external_data))
        else:
            st.write("Ninguno")


def main():
    """Main app"""
    render_header()

    # Sidebar
    render_sidebar()

    # Main content
    st.header("💬 Hacé tu consulta")

    # Input de pregunta
    if 'current_question' in st.session_state:
        question_default = st.session_state.current_question
        del st.session_state.current_question
    else:
        question_default = ""

    question = st.text_input(
        "Pregunta:",
        value=question_default,
        placeholder="Ej: ¿Cómo evolucionaron las transferencias en 2024?",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        submit_button = st.button("🚀 Consultar", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Limpiar Historial", use_container_width=True)

    # Auto-submit si viene de ejemplo del sidebar
    auto_submit = st.session_state.get('auto_submit', False)
    if auto_submit:
        st.session_state.auto_submit = False
        submit_button = True
        question = question_default  # Usar la pregunta del ejemplo

    if clear_button:
        st.session_state.conversation_history = []
        st.session_state.current_result = None
        st.rerun()

    # Procesar pregunta
    if submit_button and question:
        # Limpiar historial anterior (cada consulta empieza de cero)
        st.session_state.conversation_history = []
        st.session_state.current_result = None

        process_question(question)

    # Mostrar resultado actual
    st.markdown("---")

    if st.session_state.current_result:
        st.subheader(f"📊 Resultado: {st.session_state.current_result['question']}")
        render_result(st.session_state.current_result)
    else:
        st.info("👆 Hacé una consulta arriba para empezar")


if __name__ == "__main__":
    main()
