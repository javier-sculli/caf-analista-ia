#!/usr/bin/env python3
"""
Análisis profundo de estructura de datos
Detecta granularidad, periodicidad y estructura real de datos
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re

def find_data_start(df):
    """Encuentra donde empiezan los datos reales (después de encabezados)"""
    for idx, row in df.iterrows():
        # Buscar fila que contenga "Fecha" o fechas reales
        row_str = ' '.join([str(x) for x in row if pd.notna(x)]).lower()
        if 'fecha' in row_str or any(str(x).count('-') == 2 for x in row if pd.notna(x)):
            return idx
    return 0

def analyze_temporal_granularity(dates):
    """Analiza la granularidad temporal de una serie de fechas"""
    if len(dates) < 2:
        return "Insuficientes datos"

    dates = pd.to_datetime(dates, errors='coerce').dropna().sort_values()
    if len(dates) < 2:
        return "Fechas inválidas"

    diffs = dates.diff().dropna()
    avg_diff = diffs.mean()

    if avg_diff.days < 2:
        return "Diaria"
    elif avg_diff.days < 10:
        return "Semanal"
    elif avg_diff.days < 40:
        return "Mensual"
    elif avg_diff.days < 120:
        return "Trimestral"
    else:
        return "Anual o irregular"

def deep_analyze_file(filepath, sheet_name):
    """Análisis profundo de un archivo/hoja específica"""
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)

        # Encontrar inicio de datos
        data_start = find_data_start(df)

        # Re-leer con el header correcto
        df_clean = pd.read_excel(filepath, sheet_name=sheet_name, header=data_start)

        # Detectar columna de fecha
        date_col = None
        for col in df_clean.columns:
            col_str = str(col).lower()
            if 'fecha' in col_str or 'date' in col_str:
                date_col = col
                break

        # Si no hay columna explícita, buscar en primera columna
        if date_col is None and len(df_clean.columns) > 0:
            first_col = df_clean.iloc[:, 0]
            # Intentar convertir a fecha
            try:
                test_dates = pd.to_datetime(first_col, errors='coerce')
                if test_dates.notna().sum() > len(first_col) * 0.5:  # Si >50% son fechas
                    date_col = df_clean.columns[0]
            except:
                pass

        result = {
            'filas_encabezado': data_start,
            'filas_datos': len(df_clean),
            'columnas': len(df_clean.columns),
            'columna_fecha': str(date_col) if date_col else "No detectada",
            'periodo': None,
            'fecha_min': None,
            'fecha_max': None,
            'granularidad': None,
            'dimensiones_detectadas': []
        }

        if date_col:
            dates = pd.to_datetime(df_clean[date_col], errors='coerce').dropna()
            if len(dates) > 0:
                result['fecha_min'] = dates.min()
                result['fecha_max'] = dates.max()
                result['periodo'] = f"{(dates.max() - dates.min()).days / 365.25:.1f} años"
                result['granularidad'] = analyze_temporal_granularity(dates)

        # Detectar dimensiones (columnas que parecen categorías)
        for col in df_clean.columns[:20]:  # Primeras 20 columnas
            col_str = str(col).lower()
            if any(dim in col_str for dim in ['provincia', 'region', 'tipo', 'sector', 'categoria',
                                               'genero', 'edad', 'rango', 'segmento']):
                result['dimensiones_detectadas'].append(str(col))

        return result

    except Exception as e:
        return {'error': str(e)}

def main():
    print("🔍 ANÁLISIS PROFUNDO DE ESTRUCTURA DE DATOS")
    print("="*80)

    # Archivos clave para analizar en detalle
    files_to_analyze = [
        ("Series-Informe-Mensual-de-Pagos-Minoristas-noviembre-2025 (1).xlsx", "Cheques"),
        ("Series-Informe-Mensual-de-Pagos-Minoristas-noviembre-2025 (1).xlsx", "Transferencias de fondos"),
        ("Préstamos y depósitos del sector privado no financiero por tipo de titular.xls", "Prest-Tot"),
        ("Deudores del sistema financiero ampliado por rango etario_ junio 2025.xlsx", "4.1.2"),
    ]

    for filepath, sheet in files_to_analyze:
        print(f"\n{'='*80}")
        print(f"📄 {filepath}")
        print(f"   Hoja: {sheet}")
        print(f"{'='*80}")

        result = deep_analyze_file(filepath, sheet)

        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   📊 Filas de encabezado/metadata: {result['filas_encabezado']}")
            print(f"   📊 Filas de datos útiles: {result['filas_datos']:,}")
            print(f"   📊 Columnas: {result['columnas']}")
            print(f"   📅 Columna temporal: {result['columna_fecha']}")

            if result['fecha_min']:
                print(f"   📅 Rango temporal: {result['fecha_min'].strftime('%Y-%m-%d')} a {result['fecha_max'].strftime('%Y-%m-%d')}")
                print(f"   📅 Período cubierto: {result['periodo']}")
                print(f"   📅 Granularidad: {result['granularidad']}")

            if result['dimensiones_detectadas']:
                print(f"   🏷️  Dimensiones detectadas: {', '.join(result['dimensiones_detectadas'][:5])}")

    # Análisis de volumen total
    print(f"\n{'='*80}")
    print("📊 RESUMEN DE VOLUMETRÍA")
    print(f"{'='*80}")

    # Informe de inclusión financiera (muchas hojas)
    try:
        excel_file = pd.ExcelFile("Informe Inclusion Financiera -octubre 2025.xlsx")
        total_rows = 0
        sheets_with_data = 0

        for sheet in excel_file.sheet_names[:10]:  # Primeras 10 hojas
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet)
                if len(df) > 5:  # Más de 5 filas (para filtrar hojas vacías/índice)
                    total_rows += len(df)
                    sheets_with_data += 1
            except:
                pass

        print(f"   📁 Informe Inclusión Financiera:")
        print(f"      - Total de hojas: {len(excel_file.sheet_names)}")
        print(f"      - Hojas con datos (muestra de 10): {sheets_with_data}")
        print(f"      - Filas aprox. (muestra): {total_rows:,}")

    except Exception as e:
        print(f"   ❌ Error analizando volumetría: {e}")

    print(f"\n{'='*80}")
    print("🎯 OBSERVACIONES CLAVE")
    print(f"{'='*80}")
    print("""
    1. FORMATO DE DATOS:
       • Los archivos tienen formato de "reporte" no de base de datos
       • Múltiples filas de encabezado y metadata
       • Requieren limpieza significativa para uso analítico

    2. PERIODICIDAD:
       • Series temporales mensuales (principalmente)
       • Datos históricos desde ~2017 en algunos casos
       • Actualización aparentemente mensual

    3. GRANULARIDAD:
       • Nacional (agregado país)
       • Algunas segmentaciones: edad, tipo de entidad, producto
       • NO se observa granularidad provincial/regional en esta muestra

    4. VOLUMEN:
       • Archivos individuales pequeños (< 1MB cada uno)
       • Múltiples hojas por archivo (hasta 49 hojas)
       • Volumen total estimado: < 100MB de datos raw
       • Post-procesamiento: probablemente < 10-20MB de datos limpios

    5. FUENTE:
       • Claramente datos de BCRA (Banco Central)
       • Informes regulatorios estandarizados
       • Alta confiabilidad pero formato poco amigable
    """)

    print("\n✅ Análisis completado\n")

if __name__ == "__main__":
    main()
