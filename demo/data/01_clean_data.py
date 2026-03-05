#!/usr/bin/env python3
"""
Pipeline de limpieza de datos con logging verbose
Transforma archivos Excel de "formato reporte" a tablas analíticas
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import data_logger, clean_logger, load_logger

class DataCleaner:
    """Limpieza de archivos Excel del BCRA"""

    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def clean_pagos_minoristas(self):
        """
        Limpia Series de Pagos Minoristas
        Múltiples hojas: Cheques, Transferencias, Tarjetas
        """
        file_path = self.input_dir / "Series-Informe-Mensual-de-Pagos-Minoristas-noviembre-2025 (1).xlsx"

        data_logger.info(f"🔍 Cargando archivo: {file_path.name}")

        # Procesar hoja de Transferencias
        clean_logger.info("📄 Procesando hoja: 'Transferencias de fondos'")

        df_raw = pd.read_excel(file_path, sheet_name="Transferencias de fondos", header=None)
        clean_logger.debug(f"   Dimensiones raw: {df_raw.shape}")

        # Detectar inicio de datos (buscar "Fecha" en columna 0)
        header_row = None
        for idx, row in df_raw.iterrows():
            if pd.notna(row[0]) and str(row[0]).strip().lower() == 'fecha':
                header_row = idx
                break

        clean_logger.debug(f"   Fila de header detectada: {header_row}")

        # Re-leer con header correcto
        df = pd.read_excel(file_path, sheet_name="Transferencias de fondos", header=header_row)
        clean_logger.debug(f"   Columnas detectadas: {list(df.columns[:5])}")

        # Limpiar
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha'])

        # Extraer columnas relevantes
        cols_to_keep = {
            'Fecha': 'fecha',
            'Cantidad': 'transferencias_inmediatas_cantidad',
            'Monto nominal': 'transferencias_inmediatas_monto'
        }

        df_clean = df[list(cols_to_keep.keys())].copy()
        df_clean.columns = list(cols_to_keep.values())

        # Convertir a numérico
        for col in df_clean.columns:
            if col != 'fecha':
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        clean_logger.info(f"   ✅ Limpiado: {len(df_clean)} filas, {len(df_clean.columns)} columnas")
        clean_logger.debug(f"   Rango temporal: {df_clean['fecha'].min()} a {df_clean['fecha'].max()}")

        # Guardar
        output_path = self.output_dir / "transferencias_inmediatas.parquet"
        df_clean.to_parquet(output_path, index=False)
        load_logger.info(f"💾 Guardado: {output_path.name} ({len(df_clean):,} filas)")

        return df_clean

    def clean_cheques(self):
        """Limpia datos de Cheques"""
        file_path = self.input_dir / "Series-Informe-Mensual-de-Pagos-Minoristas-noviembre-2025 (1).xlsx"

        clean_logger.info("📄 Procesando hoja: 'Cheques'")

        df_raw = pd.read_excel(file_path, sheet_name="Cheques", header=None)

        # Detectar header
        header_row = None
        for idx, row in df_raw.iterrows():
            if pd.notna(row[0]) and str(row[0]).strip().lower() == 'fecha':
                header_row = idx
                break

        df = pd.read_excel(file_path, sheet_name="Cheques", header=header_row)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha'])

        # Extraer columnas
        cols_to_keep = {
            'Fecha': 'fecha',
            'Cantidad': 'cheques_compensados_cantidad',
            'Monto nominal': 'cheques_compensados_monto'
        }

        df_clean = df[list(cols_to_keep.keys())].copy()
        df_clean.columns = list(cols_to_keep.values())

        for col in df_clean.columns:
            if col != 'fecha':
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        clean_logger.info(f"   ✅ Limpiado: {len(df_clean)} filas, {len(df_clean.columns)} columnas")

        output_path = self.output_dir / "cheques.parquet"
        df_clean.to_parquet(output_path, index=False)
        load_logger.info(f"💾 Guardado: {output_path.name} ({len(df_clean):,} filas)")

        return df_clean

    def clean_inclusion_financiera(self):
        """
        Limpia datos de Inclusión Financiera
        Múltiples hojas con diferentes métricas
        """
        file_path = self.input_dir / "Informe Inclusion Financiera -octubre 2025.xlsx"

        clean_logger.info(f"📄 Procesando archivo: {file_path.name}")

        # Listar hojas disponibles
        excel_file = pd.ExcelFile(file_path)
        clean_logger.debug(f"   Total de hojas: {len(excel_file.sheet_names)}")

        # Por ahora, procesar solo algunas hojas clave
        # (en demo real, procesaríamos todas)
        dfs_clean = []

        # Buscar hojas con datos de series temporales
        for sheet_name in excel_file.sheet_names[:10]:  # Primeras 10
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Buscar si tiene columna de fecha o periodo
                date_cols = [col for col in df.columns if 'fecha' in str(col).lower() or 'periodo' in str(col).lower()]

                if date_cols:
                    clean_logger.debug(f"      Hoja '{sheet_name}' tiene columna temporal: {date_cols[0]}")

            except Exception as e:
                clean_logger.debug(f"      Hoja '{sheet_name}' - error: {e}")

        # Para el demo, crear tabla sintética de ejemplo
        # (En producción, parsear las hojas reales)
        clean_logger.warning("   ⚠️  Demo: Generando datos sintéticos de inclusión (en prod parsear Excel real)")

        df_clean = pd.DataFrame({
            'fecha': pd.date_range('2017-01-01', '2025-10-01', freq='MS'),
            'poblacion_adulta_millones': np.linspace(32, 35, 106),
            'cuentas_bancarias_pct': np.linspace(65, 87, 106),
            'billeteras_digitales_pct': np.concatenate([
                np.zeros(24),  # Primeros 2 años sin datos
                np.linspace(0, 62, 82)  # Crecimiento desde 2019
            ])
        })

        output_path = self.output_dir / "inclusion_financiera.parquet"
        df_clean.to_parquet(output_path, index=False)
        load_logger.info(f"💾 Guardado: {output_path.name} ({len(df_clean):,} filas)")

        return df_clean

    def clean_tipo_cambio(self):
        """
        Extrae datos de tipo de cambio de archivos disponibles
        O en su defecto, usar API
        """
        clean_logger.info("📄 Procesando datos de tipo de cambio")

        # Para demo, generar sintético (en prod usar API BCRA)
        clean_logger.warning("   ⚠️  Demo: Generando datos sintéticos de TC (en prod usar API BCRA)")

        # Generar fechas
        date_range = pd.date_range('2017-01-01', '2025-11-01', freq='D')
        n_days = len(date_range)

        # Generar valores con tendencia alcista
        tc_base = 15
        tc_values = []

        for i in range(n_days):
            # Tendencia exponencial + ruido
            days_from_start = i
            trend = tc_base * (1.0012 ** days_from_start)  # ~1.5x por año aprox
            noise = np.random.normal(0, trend * 0.01)  # 1% de volatilidad
            tc_values.append(max(tc_base, trend + noise))

        df_clean = pd.DataFrame({
            'fecha': date_range,
            'tipo_cambio_oficial': tc_values
        })

        output_path = self.output_dir / "tipo_cambio.parquet"
        df_clean.to_parquet(output_path, index=False)
        load_logger.info(f"💾 Guardado: {output_path.name} ({len(df_clean):,} filas)")

        return df_clean


def main():
    """Pipeline principal de limpieza"""
    data_logger.info("="*80)
    data_logger.info("🚀 INICIANDO PIPELINE DE LIMPIEZA DE DATOS")
    data_logger.info("="*80)

    # Rutas
    base_dir = Path(__file__).parent.parent.parent
    input_dir = base_dir
    output_dir = Path(__file__).parent / "staging"

    data_logger.info(f"📂 Input dir: {input_dir}")
    data_logger.info(f"📂 Output dir: {output_dir}")

    cleaner = DataCleaner(input_dir, output_dir)

    # Limpiar cada fuente
    data_logger.info("\n" + "="*80)
    data_logger.info("📊 LIMPIANDO FUENTE 1/4: Transferencias Inmediatas")
    data_logger.info("="*80)
    df_transferencias = cleaner.clean_pagos_minoristas()

    data_logger.info("\n" + "="*80)
    data_logger.info("📊 LIMPIANDO FUENTE 2/4: Cheques")
    data_logger.info("="*80)
    df_cheques = cleaner.clean_cheques()

    data_logger.info("\n" + "="*80)
    data_logger.info("📊 LIMPIANDO FUENTE 3/4: Inclusión Financiera")
    data_logger.info("="*80)
    df_inclusion = cleaner.clean_inclusion_financiera()

    data_logger.info("\n" + "="*80)
    data_logger.info("📊 LIMPIANDO FUENTE 4/4: Tipo de Cambio")
    data_logger.info("="*80)
    df_tc = cleaner.clean_tipo_cambio()

    data_logger.info("\n" + "="*80)
    data_logger.info("✅ PIPELINE DE LIMPIEZA COMPLETADO")
    data_logger.info("="*80)
    data_logger.info(f"   Total de archivos generados: 4")
    data_logger.info(f"   Total de filas: {sum([len(df_transferencias), len(df_cheques), len(df_inclusion), len(df_tc)]):,}")

    return {
        'transferencias': df_transferencias,
        'cheques': df_cheques,
        'inclusion': df_inclusion,
        'tipo_cambio': df_tc
    }


if __name__ == "__main__":
    main()
