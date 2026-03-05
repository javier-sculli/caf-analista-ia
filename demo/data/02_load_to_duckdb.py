#!/usr/bin/env python3
"""
Carga de datos limpios a DuckDB
DuckDB actúa como analytics database in-process
"""

import duckdb
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import load_logger, data_logger

class DuckDBLoader:
    """Carga datos a DuckDB con logging detallado"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.con = None

    def connect(self):
        """Conecta a DuckDB"""
        load_logger.info(f"🔌 Conectando a DuckDB: {self.db_path}")
        self.con = duckdb.connect(str(self.db_path))
        load_logger.info("   ✅ Conexión establecida")

        # Configurar extensiones útiles
        load_logger.debug("   Configurando extensiones DuckDB...")
        self.con.execute("INSTALL httpfs; LOAD httpfs;")  # Para S3 futuro
        load_logger.debug("   ✅ httpfs cargado")

        return self.con

    def create_schema(self):
        """Crea schema analytics"""
        load_logger.info("🏗️  Creando schema 'analytics'")
        self.con.execute("CREATE SCHEMA IF NOT EXISTS analytics")
        load_logger.info("   ✅ Schema creado")

    def load_table(self, parquet_path: Path, table_name: str, schema: str = "analytics"):
        """
        Carga un archivo Parquet como tabla en DuckDB

        Args:
            parquet_path: Path al archivo .parquet
            table_name: Nombre de la tabla en DuckDB
            schema: Schema (default: analytics)
        """
        load_logger.info(f"📥 Cargando tabla: {schema}.{table_name}")
        load_logger.debug(f"   Origen: {parquet_path}")

        # Leer parquet para log
        df = pd.read_parquet(parquet_path)
        load_logger.debug(f"   Filas: {len(df):,}, Columnas: {len(df.columns)}")
        load_logger.debug(f"   Columnas: {list(df.columns)}")

        # Crear tabla desde Parquet (DuckDB es muy eficiente con Parquet)
        self.con.execute(f"""
            CREATE OR REPLACE TABLE {schema}.{table_name} AS
            SELECT * FROM read_parquet('{parquet_path}')
        """)

        # Verificar
        count = self.con.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}").fetchone()[0]
        load_logger.info(f"   ✅ Tabla creada: {count:,} filas")

        # Mostrar sample
        sample = self.con.execute(f"SELECT * FROM {schema}.{table_name} LIMIT 3").fetchdf()
        load_logger.debug(f"   Sample de datos:\n{sample.to_string(max_cols=5)}")

    def create_views(self):
        """
        Crea vistas útiles para queries comunes
        """
        load_logger.info("🔍 Creando vistas analíticas")

        # Vista: Datos mensuales de medios de pago (join transferencias + cheques)
        load_logger.debug("   Creando vista: medios_pago_mensual")
        self.con.execute("""
            CREATE OR REPLACE VIEW analytics.medios_pago_mensual AS
            SELECT
                t.fecha,
                t.transferencias_inmediatas_cantidad,
                t.transferencias_inmediatas_monto,
                c.cheques_compensados_cantidad,
                c.cheques_compensados_monto,
                -- Total electrónico (transferencias)
                t.transferencias_inmediatas_monto as monto_electronico,
                -- Total tradicional (cheques)
                c.cheques_compensados_monto as monto_tradicional,
                -- Ratio electrónico vs tradicional
                ROUND(t.transferencias_inmediatas_monto::FLOAT / NULLIF(c.cheques_compensados_monto, 0), 2) as ratio_electronico_tradicional
            FROM analytics.transferencias_inmediatas t
            LEFT JOIN analytics.cheques c ON t.fecha = c.fecha
            ORDER BY t.fecha
        """)
        load_logger.info("   ✅ Vista creada: medios_pago_mensual")

        # Vista: Métricas de inclusión con cálculos derivados
        load_logger.debug("   Creando vista: inclusion_metricas")
        self.con.execute("""
            CREATE OR REPLACE VIEW analytics.inclusion_metricas AS
            SELECT
                fecha,
                poblacion_adulta_millones,
                cuentas_bancarias_pct,
                billeteras_digitales_pct,
                -- Población en millones con cada producto
                ROUND(poblacion_adulta_millones * cuentas_bancarias_pct / 100, 2) as poblacion_bancarizada_millones,
                ROUND(poblacion_adulta_millones * billeteras_digitales_pct / 100, 2) as poblacion_billeteras_millones,
                -- Brecha
                ROUND(cuentas_bancarias_pct - billeteras_digitales_pct, 1) as brecha_bancarizacion_digital_pp
            FROM analytics.inclusion_financiera
            ORDER BY fecha
        """)
        load_logger.info("   ✅ Vista creada: inclusion_metricas")

    def create_indexes(self):
        """Crea índices para performance"""
        load_logger.info("⚡ Creando índices para performance")

        # DuckDB crea índices automáticamente en muchos casos,
        # pero podemos ayudar con algunas hints

        # Por ahora, verificar que las columnas de fecha estén bien
        tables = ['transferencias_inmediatas', 'cheques', 'inclusion_financiera', 'tipo_cambio']

        for table in tables:
            try:
                stats = self.con.execute(f"""
                    SELECT
                        MIN(fecha) as min_fecha,
                        MAX(fecha) as max_fecha,
                        COUNT(*) as filas
                    FROM analytics.{table}
                """).fetchone()

                load_logger.debug(f"   {table}: {stats[2]:,} filas, rango {stats[0]} a {stats[1]}")

            except Exception as e:
                load_logger.warning(f"   ⚠️  Error verificando {table}: {e}")

        load_logger.info("   ✅ Índices verificados")

    def get_catalog_info(self):
        """Retorna información del catálogo de datos"""
        load_logger.info("📋 Generando catálogo de datos")

        # Listar todas las tablas
        tables = self.con.execute("""
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'analytics'
            ORDER BY table_name
        """).fetchdf()

        load_logger.info(f"   Tablas y vistas en analytics: {len(tables)}")

        for _, row in tables.iterrows():
            load_logger.debug(f"   - {row['table_name']} ({row['table_type']})")

        return tables

    def close(self):
        """Cierra conexión"""
        if self.con:
            load_logger.info("🔌 Cerrando conexión a DuckDB")
            self.con.close()


def main():
    """Pipeline principal de carga"""
    data_logger.info("="*80)
    data_logger.info("🚀 INICIANDO CARGA A DUCKDB")
    data_logger.info("="*80)

    # Rutas
    staging_dir = Path(__file__).parent / "staging"
    analytics_dir = Path(__file__).parent / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)

    db_path = analytics_dir / "caf_analytics.duckdb"

    # Inicializar loader
    loader = DuckDBLoader(db_path)
    loader.connect()

    # Crear schema
    loader.create_schema()

    # Cargar tablas
    load_logger.info("\n" + "="*80)
    load_logger.info("📊 CARGANDO TABLAS BASE")
    load_logger.info("="*80)

    parquet_files = {
        'transferencias_inmediatas': staging_dir / 'transferencias_inmediatas.parquet',
        'cheques': staging_dir / 'cheques.parquet',
        'inclusion_financiera': staging_dir / 'inclusion_financiera.parquet',
        'tipo_cambio': staging_dir / 'tipo_cambio.parquet'
    }

    for table_name, parquet_path in parquet_files.items():
        if parquet_path.exists():
            loader.load_table(parquet_path, table_name)
        else:
            load_logger.warning(f"   ⚠️  Archivo no encontrado: {parquet_path}")

    # Crear vistas analíticas
    load_logger.info("\n" + "="*80)
    load_logger.info("🔍 CREANDO VISTAS ANALÍTICAS")
    load_logger.info("="*80)
    loader.create_views()

    # Crear índices
    load_logger.info("\n" + "="*80)
    load_logger.info("⚡ OPTIMIZANDO PERFORMANCE")
    load_logger.info("="*80)
    loader.create_indexes()

    # Mostrar catálogo
    load_logger.info("\n" + "="*80)
    load_logger.info("📋 CATÁLOGO DE DATOS")
    load_logger.info("="*80)
    catalog = loader.get_catalog_info()

    # Query de prueba
    load_logger.info("\n" + "="*80)
    load_logger.info("🧪 TEST QUERY")
    load_logger.info("="*80)

    test_query = """
        SELECT
            fecha,
            transferencias_inmediatas_monto / 1e6 as transferencias_millones,
            cheques_compensados_monto / 1e6 as cheques_millones,
            ratio_electronico_tradicional
        FROM analytics.medios_pago_mensual
        WHERE fecha >= '2024-01-01'
        ORDER BY fecha DESC
        LIMIT 5
    """

    load_logger.debug("   Query:\n" + test_query)
    result = loader.con.execute(test_query).fetchdf()
    load_logger.info("   Resultado:\n" + result.to_string())

    # Cerrar
    loader.close()

    data_logger.info("\n" + "="*80)
    data_logger.info("✅ CARGA A DUCKDB COMPLETADA")
    data_logger.info("="*80)
    data_logger.info(f"   Base de datos: {db_path}")
    data_logger.info(f"   Tamaño: {db_path.stat().st_size / 1024:.2f} KB")


if __name__ == "__main__":
    main()
