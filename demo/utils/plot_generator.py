"""
Plot Generator: Generación automática de visualizaciones
Convierte DataFrames en gráficos relevantes según el contexto
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Optional
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import anthropic
import json

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import viz_logger

# Load environment
load_dotenv()


class PlotGenerator:
    """
    Generador inteligente de visualizaciones

    Detecta el tipo de datos y genera el gráfico más apropiado:
    - Series temporales → Line chart
    - Comparaciones → Bar chart
    - Distribuciones → Histogram
    - Correlaciones → Scatter plot
    - Múltiples series → Multi-line o dual-axis
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        viz_logger.info("🎨 Inicializando Plot Generator")

        # Tema/estilo
        self.template = "plotly_white"
        self.colors = px.colors.qualitative.Set2

        # Claude API para decisiones inteligentes de visualización
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            viz_logger.warning("   ⚠️  ANTHROPIC_API_KEY no configurada - usando lógica simple")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            viz_logger.info("   ✅ Cliente de Anthropic inicializado")

        viz_logger.info("   ✅ Plot Generator listo")

    def detect_plot_type(self, df: pd.DataFrame, metadata: Dict) -> str:
        """
        Detecta qué tipo de gráfico es más apropiado

        Args:
            df: DataFrame con datos
            metadata: Metadata de la query (plan, pregunta, etc.)

        Returns:
            str: Tipo de plot ('line', 'bar', 'scatter', 'multi_line', etc.)
        """
        viz_logger.info("🔍 Detectando tipo de gráfico apropiado")

        # Analizar columnas
        has_date = any(df[col].dtype in ['datetime64[ns]', 'datetime64'] for col in df.columns if col in df.columns)
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        n_numeric = len(numeric_cols)

        viz_logger.debug(f"   Tiene fecha: {has_date}")
        viz_logger.debug(f"   Columnas numéricas: {n_numeric} ({numeric_cols})")

        # Lógica de detección
        if has_date and n_numeric >= 1:
            plot_type = 'line' if n_numeric == 1 else 'multi_line'
            viz_logger.info(f"   📊 Tipo detectado: {plot_type} (serie temporal)")

        elif n_numeric == 2 and not has_date:
            plot_type = 'scatter'
            viz_logger.info(f"   📊 Tipo detectado: scatter (correlación)")

        elif n_numeric >= 1:
            plot_type = 'bar'
            viz_logger.info(f"   📊 Tipo detectado: bar (comparación)")

        else:
            plot_type = 'table'
            viz_logger.info(f"   📊 Tipo detectado: table (sin datos numéricos para graficar)")

        return plot_type

    def create_line_chart(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_cols: list,
        title: str = "",
        yaxis_title: str = "Valor"
    ) -> go.Figure:
        """
        Crea gráfico de líneas (simple o múltiple)

        Args:
            df: DataFrame
            x_col: Columna X (usualmente fecha)
            y_cols: Lista de columnas Y
            title: Título del gráfico
            yaxis_title: Título del eje Y

        Returns:
            plotly Figure
        """
        viz_logger.info(f"📈 Creando line chart")
        viz_logger.debug(f"   X: {x_col}, Y: {y_cols}")

        fig = go.Figure()

        for i, y_col in enumerate(y_cols):
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                name=y_col,
                line=dict(color=self.colors[i % len(self.colors)], width=2),
                marker=dict(size=4)
            ))

        fig.update_layout(
            title=title,
            xaxis_title=x_col.capitalize(),
            yaxis_title=yaxis_title,
            template=self.template,
            hovermode='x unified',
            height=500
        )

        viz_logger.info("   ✅ Line chart creado")
        return fig

    def create_dual_axis_chart(
        self,
        df: pd.DataFrame,
        x_col: str,
        y1_col: str,
        y2_col: str,
        title: str = "",
        y1_title: str = "Eje 1",
        y2_title: str = "Eje 2"
    ) -> go.Figure:
        """
        Crea gráfico con doble eje Y (útil para comparar métricas con diferentes escalas)

        Ejemplo: Transferencias (en millones) vs Inflación (%)
        """
        viz_logger.info(f"📊 Creando dual-axis chart")
        viz_logger.debug(f"   X: {x_col}, Y1: {y1_col}, Y2: {y2_col}")

        fig = go.Figure()

        # Primera serie (eje izquierdo)
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y1_col],
            mode='lines+markers',
            name=y1_col,
            line=dict(color=self.colors[0], width=2),
            yaxis='y'
        ))

        # Segunda serie (eje derecho)
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y2_col],
            mode='lines+markers',
            name=y2_col,
            line=dict(color=self.colors[1], width=2),
            yaxis='y2'
        ))

        fig.update_layout(
            title=title,
            xaxis=dict(
                title=x_col.capitalize(),
                domain=[0, 1]  # Ocupa todo el ancho
            ),
            yaxis=dict(
                title=y1_title,
                side='left',
                anchor='x'  # Anclado al eje X
            ),
            yaxis2=dict(
                title=y2_title,
                side='right',
                overlaying='y',  # Se solapa con el eje Y1
                anchor='x'  # Anclado al mismo eje X
            ),
            template=self.template,
            hovermode='x unified',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        viz_logger.info("   ✅ Dual-axis chart creado")
        return fig

    def create_bar_chart(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str = "",
        orientation: str = 'v'
    ) -> go.Figure:
        """
        Crea gráfico de barras

        Args:
            orientation: 'v' (vertical) o 'h' (horizontal)
        """
        viz_logger.info(f"📊 Creando bar chart")

        if orientation == 'v':
            fig = go.Figure(go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker_color=self.colors[0]
            ))
        else:
            fig = go.Figure(go.Bar(
                x=df[y_col],
                y=df[x_col],
                marker_color=self.colors[0],
                orientation='h'
            ))

        fig.update_layout(
            title=title,
            template=self.template,
            height=500
        )

        viz_logger.info("   ✅ Bar chart creado")
        return fig

    def create_comparison_chart(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_cols: list,
        title: str = "",
        chart_type: str = 'grouped'
    ) -> go.Figure:
        """
        Crea gráfico de comparación (barras agrupadas o apiladas)

        Args:
            chart_type: 'grouped' o 'stacked'
        """
        viz_logger.info(f"📊 Creando comparison chart ({chart_type})")

        fig = go.Figure()

        for i, y_col in enumerate(y_cols):
            fig.add_trace(go.Bar(
                x=df[x_col],
                y=df[y_col],
                name=y_col,
                marker_color=self.colors[i % len(self.colors)]
            ))

        barmode = 'stack' if chart_type == 'stacked' else 'group'

        fig.update_layout(
            title=title,
            barmode=barmode,
            template=self.template,
            height=500
        )

        viz_logger.info("   ✅ Comparison chart creado")
        return fig

    def select_columns_with_llm(
        self,
        df: pd.DataFrame,
        question: str,
        metadata: Dict
    ) -> Dict:
        """
        Usa el LLM para decidir inteligentemente qué columnas graficar
        basándose en la pregunta original del usuario

        Args:
            df: DataFrame con datos
            question: Pregunta original del usuario
            metadata: Metadata con contexto adicional

        Returns:
            Dict con: {
                'x_col': nombre de columna X,
                'y_cols': lista de columnas Y,
                'chart_type': tipo de gráfico,
                'reasoning': explicación
            }
        """
        viz_logger.info("🤖 Consultando LLM para selección inteligente de columnas")

        if not self.client:
            viz_logger.warning("   ⚠️  Cliente LLM no disponible - usando lógica simple")
            return None

        # Preparar información del DataFrame
        columns_info = []
        date_cols = []
        numeric_cols = []

        for col in df.columns:
            dtype = str(df[col].dtype)
            sample_values = df[col].head(3).tolist()

            col_info = {
                'name': col,
                'type': dtype,
                'sample': str(sample_values)
            }

            if df[col].dtype in ['datetime64[ns]', 'datetime64', 'object']:
                date_cols.append(col)
                col_info['category'] = 'temporal'
            elif df[col].dtype in ['int64', 'float64']:
                numeric_cols.append(col)
                col_info['category'] = 'numeric'
            else:
                col_info['category'] = 'other'

            columns_info.append(col_info)

        # Crear prompt para el LLM
        plan_info = json.dumps(metadata.get('plan', {}), indent=2, ensure_ascii=False)

        prompt = f"""Eres un experto en visualización de datos. Tu tarea es decidir qué columnas graficar basándote en la pregunta del usuario.

PREGUNTA DEL USUARIO:
{question}

COLUMNAS DISPONIBLES:
{json.dumps(columns_info, indent=2, ensure_ascii=False)}

CONTEXTO ADICIONAL:
- Total filas: {len(df)}
- Plan de query: {plan_info}

INSTRUCCIONES:
1. Analiza la pregunta del usuario para entender QUÉ quiere visualizar
2. Identifica las columnas más relevantes para responder su pregunta
3. Prioriza:
   - Si pregunta por CRECIMIENTO/COMPARACIÓN → usar columnas _yoy_pct
   - Si pregunta por VALORES ABSOLUTOS → usar columnas base (monto, cantidad)
   - Si menciona INFLACIÓN (REGLA CRÍTICA - LEER CON ATENCIÓN):
     * SIEMPRE USA POR DEFECTO: ipc_mensual_pct (inflación mensual/mes a mes)
     * SOLO si el usuario dice TEXTUALMENTE "inflación interanual", "inflación anual" o "IPC anual": ipc_interanual_pct
     * PROHIBIDO usar ipc_interanual_pct si el usuario solo dice "inflación" sin el calificativo "interanual"
     * Ejemplo: "crecimiento vs inflación" → USA ipc_mensual_pct (NO interanual)
     * Ejemplo: "crecimiento vs inflación interanual" → USA ipc_interanual_pct
4. Elige el tipo de gráfico apropiado:
   - 'line': UNA sola serie temporal
   - 'multi_line': múltiples series CON LA MISMA ESCALA (ej: varios YoY %)
   - 'dual_axis': DOS métricas con ESCALAS MUY DIFERENTES (ej: millones vs %, cantidad vs %, monto vs inflación)
   - 'bar': comparaciones categóricas

IMPORTANTE SOBRE DUAL_AXIS:
- Usa 'dual_axis' cuando las dos métricas tienen unidades/escalas completamente diferentes
- Ejemplos que NECESITAN dual_axis:
  * Monto en millones vs Inflación en % → escalas diferentes
  * Cantidad (miles) vs YoY % → escalas diferentes
  * Transferencias_monto (millones) vs transferencias_monto_yoy_pct (%) → escalas diferentes
- Ejemplos que NO necesitan dual_axis (usa multi_line):
  * transferencias_yoy_pct vs cheques_yoy_pct → ambos son %, misma escala
  * ipc_interanual_pct vs otro_indicador_pct → ambos son %, misma escala

Responde SOLO con JSON (sin markdown, sin explicaciones):
{{
  "x_col": "nombre_columna_x",
  "y_cols": ["col1", "col2"],
  "chart_type": "line|multi_line|dual_axis|bar",
  "reasoning": "breve explicación de tu decisión"
}}"""

        viz_logger.debug(f"   📤 Enviando prompt a Claude")

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()
            viz_logger.debug(f"   📥 Respuesta del LLM: {response_text}")

            # Parsear respuesta JSON
            selection = json.loads(response_text)

            viz_logger.info(f"   ✅ Selección del LLM:")
            viz_logger.info(f"      X: {selection['x_col']}")
            viz_logger.info(f"      Y: {selection['y_cols']}")
            viz_logger.info(f"      Tipo: {selection['chart_type']}")
            viz_logger.info(f"      Razón: {selection['reasoning']}")

            return selection

        except Exception as e:
            import traceback
            viz_logger.error(f"   ❌ Error consultando LLM: {e}")
            viz_logger.debug(f"   Traceback: {traceback.format_exc()}")
            return None

    def auto_generate(
        self,
        df: pd.DataFrame,
        metadata: Dict,
        title: Optional[str] = None
    ) -> go.Figure:
        """
        Generación automática de gráfico
        Analiza los datos y metadata para crear el gráfico más apropiado

        Args:
            df: DataFrame con resultados
            metadata: Metadata de la query
            title: Título custom (opcional)

        Returns:
            plotly Figure
        """
        viz_logger.info("🎨 GENERACIÓN AUTOMÁTICA DE GRÁFICO")

        if df.empty:
            viz_logger.warning("   ⚠️  DataFrame vacío - no se puede graficar")
            return self._create_empty_plot("Sin datos para visualizar")

        # Intentar selección inteligente con LLM
        question = metadata.get('question', '')
        llm_selection = self.select_columns_with_llm(df, question, metadata)

        if llm_selection:
            # Usar selección del LLM
            x_col = llm_selection['x_col']
            y_cols = llm_selection['y_cols']
            plot_type = llm_selection['chart_type']

            # Si LLM retornó None para x_col, crear índice numérico
            if x_col is None or x_col not in df.columns:
                df = df.copy()  # Avoid modifying original
                df['_index'] = range(len(df))
                x_col = '_index'
                viz_logger.info(f"   ℹ️  No hay columna temporal, usando índice numérico como eje X")

            viz_logger.info(f"   🤖 Usando selección del LLM")
        else:
            # Fallback: lógica simple si LLM no está disponible
            viz_logger.info("   📊 Usando lógica de fallback (sin LLM)")

            # Detectar tipo de gráfico
            plot_type = self.detect_plot_type(df, metadata)

            # Encontrar columnas relevantes
            date_cols = [col for col in df.columns if df[col].dtype in ['datetime64[ns]', 'datetime64', 'object']]
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

            if not date_cols and len(df.columns) > 0:
                # Usar primera columna como X
                date_cols = [df.columns[0]]

            x_col = date_cols[0] if date_cols else None

            # Lógica simple: priorizar YoY cuando exista
            yoy_cols = [col for col in numeric_cols if '_yoy_pct' in col.lower() or 'crecimiento' in col.lower()]
            # Priorizar inflación MENSUAL por defecto
            ipc_cols = [col for col in numeric_cols if 'ipc_mensual' in col.lower()]
            if not ipc_cols:  # Fallback a interanual solo si no hay mensual
                ipc_cols = [col for col in numeric_cols if 'ipc_interanual' in col.lower()]

            if yoy_cols or ipc_cols:
                y_cols = (yoy_cols + ipc_cols)[:3]
            else:
                y_cols = numeric_cols[:3]

        viz_logger.debug(f"   Columnas seleccionadas: X={x_col}, Y={y_cols}")

        # Generar título si no se proveyó
        if not title:
            question = metadata.get('question', 'Resultado')
            title = question[:80] + ('...' if len(question) > 80 else '')

        # Crear gráfico según tipo detectado
        if plot_type == 'line' and len(y_cols) == 1:
            fig = self.create_line_chart(df, x_col, y_cols, title=title)

        elif plot_type == 'dual_axis' and len(y_cols) >= 2:
            # Dual axis: dos métricas con escalas diferentes
            viz_logger.info(f"   📊 Creando gráfico dual-axis para escalas diferentes")
            y1_col = y_cols[0]
            y2_col = y_cols[1]

            # Títulos inteligentes para los ejes
            y1_title = y1_col.replace('_', ' ').title()
            y2_title = y2_col.replace('_', ' ').title()

            # Casos especiales para títulos más amigables
            if 'yoy_pct' in y1_col.lower():
                y1_title = y1_col.replace('_yoy_pct', ' (YoY %)').replace('_', ' ').title()
            if 'yoy_pct' in y2_col.lower():
                y2_title = y2_col.replace('_yoy_pct', ' (YoY %)').replace('_', ' ').title()
            if 'ipc_interanual' in y2_col.lower():
                y2_title = "Inflación (%)"

            fig = self.create_dual_axis_chart(
                df, x_col, y1_col, y2_col,
                title=title,
                y1_title=y1_title,
                y2_title=y2_title
            )

        elif plot_type == 'multi_line' and len(y_cols) >= 2:
            # Multi-line: múltiples series en la misma escala
            fig = self.create_line_chart(df, x_col, y_cols, title=title)

        elif plot_type == 'bar':
            fig = self.create_bar_chart(df, x_col, y_cols[0] if y_cols else df.columns[1], title=title)

        else:
            # Fallback: tabla o gráfico simple
            if x_col and y_cols:
                if len(y_cols) >= 2:
                    # Si hay 2+ columnas, intentar dual-axis por defecto
                    fig = self.create_dual_axis_chart(
                        df, x_col, y_cols[0], y_cols[1],
                        title=title,
                        y1_title=y_cols[0],
                        y2_title=y_cols[1]
                    )
                else:
                    fig = self.create_line_chart(df, x_col, y_cols[:1], title=title)
            else:
                fig = self._create_empty_plot("Datos no graficables")

        return fig

    def _create_empty_plot(self, message: str) -> go.Figure:
        """Crea un plot vacío con mensaje"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(template=self.template)
        return fig


def main():
    """Test del plot generator"""
    viz_logger.info("🧪 TEST PLOT GENERATOR")

    # Crear datos de prueba
    import numpy as np
    dates = pd.date_range('2023-01-01', '2025-12-01', freq='MS')
    df = pd.DataFrame({
        'fecha': dates,
        'transferencias_monto': np.cumsum(np.random.randn(len(dates)) * 100 + 500),
        'ipc_interanual_pct': np.random.rand(len(dates)) * 50 + 100
    })

    generator = PlotGenerator()

    metadata = {
        'question': '¿Cómo evolucionaron las transferencias vs la inflación?',
        'plan': {}
    }

    fig = generator.auto_generate(df, metadata)

    viz_logger.info("✅ Gráfico generado")

    # Guardar como HTML para ver
    output_path = Path(__file__).parent.parent / "test_plot.html"
    fig.write_html(str(output_path))
    viz_logger.info(f"💾 Gráfico guardado en: {output_path}")


if __name__ == "__main__":
    main()
