"""
Query Engine: Motor de consultas conversacional con IA
Convierte preguntas en lenguaje natural → SQL → Resultados
"""

import duckdb
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import os
from dotenv import load_dotenv
import anthropic
import sys
import json

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import (
    semantic_logger, planning_logger, sql_logger,
    processing_logger, llm_logger, api_logger
)
from utils.api_fetcher import MacroDataFetcher

# Load environment
load_dotenv()


class QueryEngine:
    """
    Motor de consultas conversacional

    Flujo:
    1. Usuario pregunta en lenguaje natural
    2. Semantic layer: buscar tablas/columnas relevantes
    3. Query planning: decidir qué datos necesita
    4. SQL generation: generar SQL con Claude
    5. Execution: ejecutar SQL en DuckDB
    6. API fetching: traer datos externos si necesario
    7. Data processing: cruzar/calcular métricas
    8. Return: resultados listos para visualizar
    """

    def __init__(
        self,
        db_path: Path,
        catalog_path: Path,
        anthropic_api_key: Optional[str] = None
    ):
        self.db_path = db_path
        self.catalog_path = catalog_path

        # Inicializar componentes
        llm_logger.info("🚀 Inicializando Query Engine")

        # DuckDB
        llm_logger.info(f"   📊 Conectando a DuckDB: {db_path}")
        self.con = duckdb.connect(str(db_path), read_only=True)

        # Semantic Layer (catálogo)
        semantic_logger.info(f"   📚 Cargando catálogo de datos: {catalog_path}")
        with open(catalog_path) as f:
            self.catalog = yaml.safe_load(f)
        semantic_logger.info(f"   ✅ Catálogo cargado: {self.catalog['metadata']['total_tables']} tablas, {self.catalog['metadata']['total_views']} vistas")

        # Claude API
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            llm_logger.warning("   ⚠️  ANTHROPIC_API_KEY no configurada - funcionalidad limitada")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            llm_logger.info("   ✅ Cliente de Anthropic inicializado")

        # API fetcher para datos externos
        self.api_fetcher = MacroDataFetcher()

        llm_logger.info("✅ Query Engine listo")

    def get_catalog_context(self) -> str:
        """
        Genera contexto del catálogo para Claude
        Describe todas las tablas y columnas disponibles
        """
        semantic_logger.info("📋 Generando contexto del catálogo para LLM")

        context_parts = []

        # Tablas
        context_parts.append("# TABLAS DISPONIBLES\n")
        for table in self.catalog['tables']:
            context_parts.append(f"\n## {table['schema']}.{table['name']}")
            context_parts.append(f"Descripción: {table['description']}")
            context_parts.append(f"Granularidad: {table['granularity']}")
            context_parts.append(f"Columna temporal: {table.get('time_column', 'N/A')}")

            context_parts.append("\nColumnas:")
            for col in table['columns']:
                terms = ', '.join(col.get('searchable_terms', []))
                context_parts.append(f"  - {col['name']} ({col['type']}): {col['description']}")
                if terms:
                    context_parts.append(f"    Términos de búsqueda: {terms}")

        # Vistas
        if 'views' in self.catalog:
            context_parts.append("\n\n# VISTAS ANALÍTICAS\n")
            for view in self.catalog['views']:
                context_parts.append(f"\n## {view['schema']}.{view['name']}")
                context_parts.append(f"Descripción: {view['description']}")

        # Relaciones
        if 'relationships' in self.catalog:
            context_parts.append("\n\n# RELACIONES ENTRE TABLAS\n")
            for rel in self.catalog['relationships']:
                context_parts.append(f"- {rel['from_table']} → {rel['to_table']}: {rel['description']}")
                context_parts.append(f"  JOIN: {rel['join_condition']}")

        # Cálculos comunes
        if 'common_calculations' in self.catalog:
            context_parts.append("\n\n# CÁLCULOS COMUNES\n")
            for calc in self.catalog['common_calculations']:
                context_parts.append(f"\n- {calc['name']}: {calc['description']}")
                if 'sql_template' in calc:
                    context_parts.append(f"  SQL: {calc['sql_template']}")

        context = '\n'.join(context_parts)
        semantic_logger.debug(f"   Contexto generado: {len(context)} caracteres")

        return context

    def plan_query(self, question: str) -> Dict:
        """
        Fase 1: Query Planning
        Analiza la pregunta y decide qué datos necesita

        Returns:
            Dict con: {
                'tables_needed': [...]
                'external_data_needed': [...]
                'calculations': [...]
                'reasoning': str
            }
        """
        planning_logger.info(f"🧠 FASE 1: Query Planning")
        planning_logger.info(f"   Pregunta: '{question}'")

        catalog_context = self.get_catalog_context()

        # Prompt para Claude
        planning_prompt = f"""Eres un analista de datos experto. Tu tarea es analizar una pregunta del usuario y planear qué datos necesitas para responderla.

CATÁLOGO DE DATOS INTERNOS (EN BASE DE DATOS):
{catalog_context}

DATOS EXTERNOS DISPONIBLES (VIA API):
- inflacion: IPC mensual e interanual (Argentina)
- tipo_cambio: Cotización oficial USD/ARS
- pib: PIB trimestral de Argentina

PREGUNTA DEL USUARIO:
{question}

Analiza la pregunta y clasifica CUIDADOSAMENTE cada dato:

IMPORTANTE:
- tables_needed: SOLO tablas del catálogo interno (transferencias_inmediatas, cheques, etc.)
- external_data_needed: SOLO datos de APIs (inflacion, tipo_cambio, pib)
- NO mezcles! Si la pregunta menciona "inflación", va en external_data_needed, NO en tables_needed

Responde en formato JSON:
{{
  "tables_needed": ["lista de tablas INTERNAS del catálogo"],
  "external_data_needed": ["lista de datos EXTERNOS: inflacion, tipo_cambio, pib"],
  "calculations": ["lista de cálculos: crecimiento_yoy, deflactar, etc."],
  "time_filters": "descripción del filtro temporal (ej: 'últimos 2 años', 'desde 2023')",
  "reasoning": "explicación breve de tu plan (2-3 líneas)"
}}

Responde SOLO con el JSON, sin texto adicional."""

        llm_logger.info("   📤 Enviando prompt a Claude (planning)")
        llm_logger.debug(f"   Prompt length: {len(planning_prompt)} chars")

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[{"role": "user", "content": planning_prompt}]
            )

            response_text = response.content[0].text
            llm_logger.debug(f"   📥 Respuesta recibida: {len(response_text)} chars")
            llm_logger.debug(f"   Tokens usados: input={response.usage.input_tokens}, output={response.usage.output_tokens}")

            # Parse JSON
            plan = json.loads(response_text)

            planning_logger.info("   ✅ Plan generado:")
            planning_logger.info(f"      Tablas: {plan['tables_needed']}")
            planning_logger.info(f"      Datos externos: {plan['external_data_needed']}")
            planning_logger.info(f"      Cálculos: {plan['calculations']}")
            planning_logger.info(f"      Razonamiento: {plan['reasoning']}")

            return plan

        except Exception as e:
            planning_logger.error(f"   ❌ Error en planning: {e}")
            # Fallback simple
            return {
                'tables_needed': [],
                'external_data_needed': [],
                'calculations': [],
                'reasoning': f'Error: {e}'
            }

    def generate_sql(self, question: str, plan: Dict) -> str:
        """
        Fase 2: SQL Generation
        Genera SQL basado en el plan

        Returns:
            str: Query SQL (puede ser vacío si solo necesita datos externos)
        """
        sql_logger.info(f"💻 FASE 2: SQL Generation")

        # Lista de tablas internas válidas
        valid_internal_tables = [
            'transferencias_inmediatas', 'cheques', 'inclusion_financiera',
            'tipo_cambio', 'credito_por_destino', 'credito_por_tipo'
        ]

        # Filtrar solo tablas internas para SQL generation
        # Remover prefijo de schema si existe (analytics.tabla → tabla)
        internal_tables = []
        for t in plan['tables_needed']:
            # Remover prefijo "analytics." o cualquier schema
            table_name = t.split('.')[-1] if '.' in t else t
            if table_name in valid_internal_tables:
                internal_tables.append(table_name)

        sql_logger.debug(f"   Tablas del plan: {plan['tables_needed']}")
        sql_logger.debug(f"   Tablas internas filtradas: {internal_tables}")

        # Si no hay tablas internas, solo datos externos
        if not internal_tables:
            sql_logger.info("   ℹ️  Solo se necesitan datos externos - no se genera SQL")
            sql_logger.info("   📊 Datos externos a obtener via API en Fase 4")
            return ""  # SQL vacío, todo viene de APIs

        catalog_context = self.get_catalog_context()

        # Prompt para SQL generation
        sql_prompt = f"""Eres un experto en SQL (DuckDB syntax). Genera una query SQL SOLO con datos internos de la base de datos.

CONTEXTO IMPORTANTE:
Esta es FASE 2 de un pipeline de 5 fases. Tu trabajo es generar SQL SOLO para datos internos.
Los datos externos (inflación, PIB, etc.) se obtendrán en FASE 4 via APIs y se combinarán en FASE 5.

CATÁLOGO DE DATOS INTERNOS DISPONIBLES:
{catalog_context}

PREGUNTA ORIGINAL: {question}

TABLAS A USAR (SOLO ESTAS):
- Tablas internas: {internal_tables}
- Filtros temporales: {plan.get('time_filters', 'N/A')}

REGLA CRÍTICA SOBRE JOINS:
Si la lista de "Tablas internas" contiene MÁS DE UNA TABLA, DEBES incluir TODAS en el SQL mediante JOINs:
- Ejemplo: Si las tablas son ['transferencias_inmediatas', 'cheques']
  * DEBES hacer: FROM analytics.transferencias_inmediatas t JOIN analytics.cheques c ON t.fecha = c.fecha
  * NO hagas: FROM analytics.transferencias_inmediatas (esto omite cheques!)
- El JOIN debe ser por la columna 'fecha' (que es común a todas las tablas)
- Incluye columnas relevantes de TODAS las tablas listadas en el SELECT

IMPORTANTE SOBRE VALOR ACTUAL VS SERIE TEMPORAL:
Si la pregunta está en TIEMPO PRESENTE y pide un valor actual (no evolución):
- Preguntas como: "¿Qué porcentaje tiene?", "¿Cuál es el valor actual?", "¿Cuánto hay?"
- SQL: Solo traer el registro MÁS RECIENTE con ORDER BY fecha DESC LIMIT 1
- Ejemplo: "¿Qué porcentaje de adultos tiene cuentas bancarias?" → LIMIT 1 (un solo valor)
- NO apliques filtros temporales (INTERVAL), solo ORDER BY DESC LIMIT 1

Si la pregunta pide EVOLUCIÓN o COMPARACIÓN TEMPORAL:
- Preguntas como: "Evolución de...", "Compará en los últimos...", "Mostrame la tendencia..."
- SQL: Traer serie temporal con WHERE fecha >= ...

IMPORTANTE SOBRE FILTROS TEMPORALES (cuando se pide serie temporal):
Si el plan incluye 'crecimiento_yoy' en calculations, DEBES traer datos EXTRA para el cálculo:
- Para "últimos 12 meses" → trae últimos 24 meses (12 + 12 para YoY)
- Para "últimos 2 años" → trae últimos 36 meses (24 + 12 para YoY)
- Para "últimos 3 años" → trae últimos 48 meses (36 + 12 para YoY)
- Para "último año" → trae últimos 24 meses
- Para un año específico (ej: 2024) → trae 2023 + 2024
REGLA: Siempre agregar 12 meses adicionales al período solicitado cuando hay YoY
Ejemplo: Si piden "últimos 2 años" y hay YoY, usa: WHERE fecha >= CURRENT_DATE - INTERVAL '36 months'

REGLAS ABSOLUTAS - NO NEGOCIABLES:
1. SOLO usa tablas del schema "analytics" listadas arriba
2. PROHIBIDO: No references inflacion, pib, o cualquier dato externo
3. PROHIBIDO: No uses schema "external"
4. Si la pregunta menciona "inflación" o "deflactar", IGNORA esa parte y genera SQL solo para las métricas base
5. Si piden comparar con datos externos, genera SQL solo para los datos internos
6. Todas las comparaciones con datos externos se harán DESPUÉS en Python

SINTAXIS DUCKDB:

FECHAS:
- NO uses DATE() - no existe
- Años específicos: WHERE fecha >= '2024-01-01' AND fecha < '2025-01-01'
- Periodos relativos: WHERE fecha >= CURRENT_DATE - INTERVAL '2 years'
- Funciones: date_trunc('month', fecha), strftime(fecha, '%Y-%m')

CÁLCULOS (NO inventes funciones que no existen):
- Crecimiento YoY: NO existe crecimiento_yoy(). Usa LAG() window function
- Percentiles: percentile_cont(0.5) WITHIN GROUP (ORDER BY col)
- Rankings: row_number() OVER (ORDER BY col)

JOINS (MUY IMPORTANTE):
- SIEMPRE califica las columnas ambiguas con el nombre de la tabla
- En SELECT: usa tabla.columna para columnas que existen en múltiples tablas
- En ORDER BY: usa tabla.fecha, NO solo fecha
- Ejemplo CORRECTO:
  SELECT t.fecha, t.monto, c.cantidad
  FROM analytics.transferencias_inmediatas t
  JOIN analytics.cheques c ON t.fecha = c.fecha
  ORDER BY t.fecha DESC

ORDENAMIENTO Y LÍMITES:
- Ordena por fecha DESC (usa tabla.fecha en JOINs)
- Limita a 100 filas máximo

EJEMPLOS CORRECTOS:

1. Año específico:
Pregunta: "Transferencias del 2024"
SQL: SELECT fecha, transferencias_inmediatas_cantidad, transferencias_inmediatas_monto
     FROM analytics.transferencias_inmediatas
     WHERE fecha >= '2024-01-01' AND fecha < '2025-01-01'
     ORDER BY fecha DESC;

2. Valor ACTUAL (tiempo presente, sin evolución):
Pregunta: "¿Qué porcentaje de adultos tiene cuentas bancarias?"
SQL: SELECT cuentas_bancarias_pct, billeteras_digitales_pct
     FROM analytics.inclusion_financiera
     ORDER BY fecha DESC
     LIMIT 1;
(Nota: Solo el valor más reciente, sin filtro WHERE de fecha)

3. Con crecimiento (NO pidas YoY en SQL, se calculará después en Python):
Pregunta: "Crecimiento de transferencias en 2024"
SQL: SELECT fecha, transferencias_inmediatas_monto
     FROM analytics.transferencias_inmediatas
     WHERE fecha >= '2024-01-01' AND fecha < '2025-01-01'
     ORDER BY fecha DESC;
(El crecimiento YoY se calculará en Python después)

4. Con crecimiento YoY en últimos 12 meses:
Pregunta: "Crecimiento de transferencias últimos 12 meses"
SQL: SELECT fecha, transferencias_inmediatas_monto
     FROM analytics.transferencias_inmediatas
     WHERE fecha >= CURRENT_DATE - INTERVAL '24 months'
     ORDER BY fecha DESC;
(Nota: Usa 24 meses = 12 solicitados + 12 para calcular YoY)

5. Con crecimiento YoY en últimos 2 años:
Pregunta: "Compará crecimiento de transferencias vs inflación en los últimos 2 años"
SQL: SELECT fecha, transferencias_inmediatas_cantidad, transferencias_inmediatas_monto
     FROM analytics.transferencias_inmediatas
     WHERE fecha >= CURRENT_DATE - INTERVAL '36 months'
     ORDER BY fecha DESC;
(Nota: Usa 36 meses = 24 solicitados + 12 para calcular YoY)

6. Con JOIN (CALIFICA las columnas ambiguas):
Pregunta: "Compará volumen de transferencias y cheques últimos 12 meses"
SQL: SELECT
       t.fecha,
       t.transferencias_inmediatas_cantidad,
       t.transferencias_inmediatas_monto,
       c.cheques_compensados_cantidad,
       c.cheques_compensados_monto
     FROM analytics.transferencias_inmediatas t
     JOIN analytics.cheques c ON t.fecha = c.fecha
     WHERE t.fecha >= CURRENT_DATE - INTERVAL '24 months'
     ORDER BY t.fecha DESC;
(Nota: Usa 24 meses en lugar de 12 porque el plan incluye crecimiento_yoy.
 También: t.fecha y c.fecha están calificados, no solo "fecha")

6. Con datos externos:
Pregunta: "Compará transferencias con inflación en 2024"
SQL: SELECT fecha, transferencias_inmediatas_monto, transferencias_inmediatas_cantidad
     FROM analytics.transferencias_inmediatas
     WHERE fecha >= '2024-01-01' AND fecha < '2025-01-01'
     ORDER BY fecha DESC;
(La inflación se agregará via API y el crecimiento se calculará después)

Responde SOLO con el SQL, sin explicaciones ni markdown."""

        llm_logger.info("   📤 Enviando prompt a Claude (SQL generation)")

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2048,
                messages=[{"role": "user", "content": sql_prompt}]
            )

            sql = response.content[0].text.strip()

            # Limpiar SQL (remover markdown si lo puso)
            if sql.startswith("```"):
                lines = sql.split('\n')
                sql = '\n'.join(lines[1:-1])

            sql_logger.info("   ✅ SQL generado:")
            sql_logger.info("   " + "─" * 70)
            for line in sql.split('\n'):
                sql_logger.info(f"   {line}")
            sql_logger.info("   " + "─" * 70)

            llm_logger.debug(f"   Tokens usados: input={response.usage.input_tokens}, output={response.usage.output_tokens}")

            return sql

        except Exception as e:
            sql_logger.error(f"   ❌ Error generando SQL: {e}")
            return ""

    def validate_and_execute_sql(self, sql: str) -> pd.DataFrame:
        """
        Fase 3: SQL Validation & Execution
        Valida y ejecuta el SQL en DuckDB

        Returns:
            DataFrame con resultados
        """
        processing_logger.info("⚡ FASE 3: SQL Execution")

        # Validación básica
        sql_lower = sql.lower()
        dangerous_keywords = ['drop', 'delete', 'truncate', 'insert', 'update', 'alter']

        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                processing_logger.error(f"   ❌ SQL contiene keyword peligroso: {keyword}")
                return pd.DataFrame()

        processing_logger.info("   ✅ SQL validado (no contiene keywords peligrosos)")

        try:
            processing_logger.info("   🔄 Ejecutando query...")

            import time
            start_time = time.time()

            result_df = self.con.execute(sql).fetchdf()

            execution_time = time.time() - start_time

            processing_logger.info(f"   ✅ Query ejecutado en {execution_time:.3f}s")
            processing_logger.info(f"   📊 Resultados: {len(result_df)} filas, {len(result_df.columns)} columnas")

            if len(result_df) > 0:
                processing_logger.debug(f"   Columnas: {list(result_df.columns)}")
                processing_logger.debug(f"   Preview:\n{result_df.head(3).to_string()}")

            return result_df

        except Exception as e:
            processing_logger.error(f"   ❌ Error ejecutando SQL: {e}")
            return pd.DataFrame()

    def fetch_external_data(self, data_needed: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fase 4: External Data Fetching
        Trae datos de APIs externas según lo planeado

        Returns:
            Dict con {data_name: DataFrame}
        """
        if not data_needed:
            return {}

        api_logger.info(f"🌐 FASE 4: Fetching External Data")
        api_logger.info(f"   Datos requeridos: {data_needed}")

        external_data = {}

        for data_name in data_needed:
            if 'inflacion' in data_name.lower():
                api_logger.info("   📊 Fetching inflación...")
                df = self.api_fetcher.get_inflacion_argentina(start_date="2017-01-01")
                external_data['inflacion'] = df
                api_logger.info(f"   ✅ Inflación obtenida: {len(df)} filas")

            elif 'tipo_cambio' in data_name.lower() or 'dolar' in data_name.lower():
                api_logger.info("   📊 Fetching tipo de cambio...")
                df = self.api_fetcher.get_tipo_cambio(start_date="2017-01-01")
                external_data['tipo_cambio'] = df
                api_logger.info(f"   ✅ Tipo de cambio obtenido: {len(df)} filas")

            elif 'pib' in data_name.lower():
                api_logger.info("   📊 Fetching PIB...")
                df = self.api_fetcher.get_pib_argentina()
                external_data['pib'] = df
                api_logger.info(f"   ✅ PIB obtenido: {len(df)} filas")

        return external_data

    def process_and_combine(
        self,
        query_result: pd.DataFrame,
        external_data: Dict[str, pd.DataFrame],
        plan: Dict,
        question: str = ""
    ) -> pd.DataFrame:
        """
        Fase 5: Data Processing & Combination
        Cruza datos internos con externos y calcula métricas

        Returns:
            DataFrame final procesado
        """
        processing_logger.info("🔧 FASE 5: Data Processing")

        # Caso especial: solo datos externos (sin datos internos)
        if query_result.empty and external_data:
            processing_logger.info("   📊 Solo datos externos - retornando directamente")

            # Si solo hay UN tipo de dato externo, retornarlo directamente
            if len(external_data) == 1:
                df_external = list(external_data.values())[0].copy()
                processing_logger.info(f"   ✅ Retornando datos externos: {len(df_external)} filas")
                return df_external

            # Si hay múltiples, combinarlos por fecha
            df_final = None
            for data_name, df_ext in external_data.items():
                df_ext = df_ext.copy()
                df_ext['fecha_mes'] = pd.to_datetime(df_ext['fecha']).dt.to_period('M').dt.to_timestamp()

                if df_final is None:
                    df_final = df_ext
                else:
                    df_final = df_final.merge(df_ext, on='fecha_mes', how='outer')

            processing_logger.info(f"   ✅ Combinados datos externos: {len(df_final)} filas")
            return df_final

        # Si no hay datos para procesar
        if query_result.empty:
            return query_result

        df_final = query_result.copy()

        # Identificar columna de fecha en el resultado
        date_col = None
        for col in ['fecha', 'periodo', 'mes', 'date']:
            if col in df_final.columns:
                date_col = col
                break

        if not date_col:
            processing_logger.warning("   ⚠️  No se encontró columna de fecha para join")
            return df_final

        # Convertir fecha a mensual (primer día del mes) para joins
        df_final['fecha_mes'] = pd.to_datetime(df_final[date_col]).dt.to_period('M').dt.to_timestamp()

        # Joinear inflación si está disponible
        if 'inflacion' in external_data:
            processing_logger.info("   📊 Joineando datos de inflación")

            df_inflacion = external_data['inflacion'].copy()
            df_inflacion['fecha_mes'] = pd.to_datetime(df_inflacion['fecha']).dt.to_period('M').dt.to_timestamp()

            # Join
            df_final = df_final.merge(
                df_inflacion[['fecha_mes', 'ipc_mensual_pct', 'ipc_interanual_pct']],
                on='fecha_mes',
                how='left'
            )

            processing_logger.info(f"   ✅ Inflación joineada: {df_final['ipc_interanual_pct'].notna().sum()} filas con datos")

            # Si necesita deflactar, aplicar
            if 'deflactar' in plan.get('calculations', []):
                processing_logger.info("   💰 Aplicando deflactor a columnas de monto")

                # Identificar columnas de monto para deflactar
                monto_cols = [col for col in df_final.columns if 'monto' in col.lower() and col != 'fecha_mes']

                for col in monto_cols:
                    new_col_name = f"{col}_real"
                    # Deflactar usando IPC acumulado (base = 1.0 en fecha más antigua)
                    df_final[new_col_name] = df_final[col] / (1 + df_final['ipc_interanual_pct']/100)
                    processing_logger.info(f"      Deflactado: {col} → {new_col_name}")

        # Joinear tipo de cambio si está disponible
        if 'tipo_cambio' in external_data:
            processing_logger.info("   📊 Joineando tipo de cambio")

            df_tc = external_data['tipo_cambio'].copy()
            df_tc['fecha_mes'] = pd.to_datetime(df_tc['fecha']).dt.to_period('M').dt.to_timestamp()

            # Agregar tipo de cambio promedio mensual
            df_tc_monthly = df_tc.groupby('fecha_mes')['tipo_cambio_oficial'].mean().reset_index()

            df_final = df_final.merge(
                df_tc_monthly,
                on='fecha_mes',
                how='left'
            )

            processing_logger.info(f"   ✅ Tipo de cambio joineado: {df_final['tipo_cambio_oficial'].notna().sum()} filas con datos")

        # Joinear PIB si está disponible
        if 'pib' in external_data:
            processing_logger.info("   📊 Joineando PIB")

            df_pib = external_data['pib'].copy()
            df_pib['fecha_mes'] = pd.to_datetime(df_pib['fecha']).dt.to_period('M').dt.to_timestamp()

            df_final = df_final.merge(
                df_pib[['fecha_mes', 'pib_millones_ars']],
                on='fecha_mes',
                how='left'
            )

            processing_logger.info(f"   ✅ PIB joineado: {df_final['pib_millones_ars'].notna().sum()} filas con datos")

        # Si necesita calcular crecimiento YoY
        if 'crecimiento_yoy' in plan.get('calculations', []):
            processing_logger.info("   📈 Calculando crecimiento YoY")

            # IMPORTANTE: pct_change() necesita datos ordenados cronológicamente (ASC)
            # Si vienen DESC del SQL, reordenar temporalmente
            original_order = df_final.index.copy()
            df_final = df_final.sort_values('fecha_mes', ascending=True).reset_index(drop=True)
            processing_logger.debug("   📅 Datos reordenados ASC para cálculo YoY")

            # Identificar columnas numéricas para calcular YoY
            numeric_cols = df_final.select_dtypes(include=['int64', 'float64']).columns
            numeric_cols = [col for col in numeric_cols if col not in ['fecha_mes', 'ipc_mensual_pct', 'ipc_interanual_pct']]

            for col in numeric_cols[:3]:  # Limitar a 3 columnas para no saturar
                yoy_col_name = f"{col}_yoy_pct"
                # pct_change(12) = (valor_actual - valor_hace_12_meses) / valor_hace_12_meses * 100
                df_final[yoy_col_name] = df_final[col].pct_change(12) * 100  # 12 meses = YoY
                processing_logger.info(f"      YoY calculado: {col} → {yoy_col_name}")

            processing_logger.debug("   📅 Manteniendo orden cronológico (ASC) para visualización")

            # Filtrar para mostrar solo el período solicitado (no los datos extra para YoY)
            if 'últimos 2 años' in question.lower() or 'últimos dos años' in question.lower():
                # Filtrar últimos 24 meses
                cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=24)
                df_final = df_final[df_final['fecha_mes'] >= cutoff_date]
                processing_logger.info(f"   🔍 Filtrado a últimos 24 meses para visualización: {len(df_final)} filas")
            elif 'últimos 12 meses' in question.lower() or 'último año' in question.lower():
                # Filtrar últimos 12 meses
                cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=12)
                df_final = df_final[df_final['fecha_mes'] >= cutoff_date]
                processing_logger.info(f"   🔍 Filtrado a últimos 12 meses para visualización: {len(df_final)} filas")

        processing_logger.info(f"   ✅ Procesamiento completado: {len(df_final)} filas × {len(df_final.columns)} columnas")

        return df_final

    def query(self, question: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Pipeline completo de consulta

        Args:
            question: Pregunta en lenguaje natural

        Returns:
            (DataFrame con resultados, Dict con metadata del proceso)
        """
        llm_logger.info("="*80)
        llm_logger.info(f"🚀 NUEVA CONSULTA: '{question}'")
        llm_logger.info("="*80)

        metadata = {
            'question': question,
            'plan': None,
            'sql': None,
            'external_data_used': [],
            'processing_steps': []
        }

        # Fase 1: Planning
        plan = self.plan_query(question)
        metadata['plan'] = plan

        if not plan['tables_needed'] and not plan['external_data_needed']:
            llm_logger.warning("⚠️  No se pudieron identificar datos necesarios")
            return pd.DataFrame(), metadata

        # Fase 2: SQL Generation
        sql = self.generate_sql(question, plan)
        metadata['sql'] = sql

        # Fase 3: SQL Execution (solo si hay SQL para ejecutar)
        if sql:
            query_result = self.validate_and_execute_sql(sql)
        else:
            # No hay datos internos, solo externos - crear DataFrame vacío con estructura básica
            llm_logger.info("⏭️  FASE 3: Saltada (no hay SQL interno)")
            query_result = pd.DataFrame({'fecha': []})

        # Fase 4: External Data (si necesario)
        external_data = self.fetch_external_data(plan.get('external_data_needed', []))
        metadata['external_data_used'] = list(external_data.keys())

        # Fase 5: Combine & Process
        final_result = self.process_and_combine(query_result, external_data, plan, question)

        llm_logger.info("="*80)
        llm_logger.info(f"✅ CONSULTA COMPLETADA")
        llm_logger.info(f"   Resultado: {len(final_result)} filas × {len(final_result.columns)} columnas")
        llm_logger.info("="*80)

        return final_result, metadata

    def close(self):
        """Cierra conexiones"""
        if self.con:
            self.con.close()


def main():
    """Test del query engine"""
    llm_logger.info("🧪 TEST QUERY ENGINE")

    # Rutas
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "analytics" / "caf_analytics.duckdb"
    catalog_path = base_dir / "semantic_layer" / "data_catalog.yaml"

    # Verificar que existan
    if not db_path.exists():
        llm_logger.error(f"❌ Database no encontrada: {db_path}")
        llm_logger.info("   Ejecuta primero: python demo/data/01_clean_data.py && python demo/data/02_load_to_duckdb.py")
        return

    if not catalog_path.exists():
        llm_logger.error(f"❌ Catálogo no encontrado: {catalog_path}")
        return

    # Inicializar engine
    engine = QueryEngine(db_path, catalog_path)

    # Test query simple
    question = "¿Cuál es el volumen de transferencias inmediatas en los últimos 12 meses?"

    result, metadata = engine.query(question)

    if not result.empty:
        llm_logger.info("\n📊 RESULTADO:")
        print(result.to_string())

    engine.close()


if __name__ == "__main__":
    main()
