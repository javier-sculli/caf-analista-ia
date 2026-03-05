#!/usr/bin/env python3
"""
Script de análisis exploratorio de datos para Cámara Argentina de Fintech
Analiza archivos Excel para entender estructura, calidad y características
"""

import pandas as pd
import os
import glob
from pathlib import Path

def analyze_excel_file(filepath):
    """Analiza un archivo Excel y retorna información estructural"""
    filename = os.path.basename(filepath)
    print(f"\n{'='*80}")
    print(f"📊 ARCHIVO: {filename}")
    print(f"{'='*80}")

    try:
        # Detectar si es .xls o .xlsx
        if filepath.endswith('.xls'):
            excel_file = pd.ExcelFile(filepath, engine='xlrd')
        else:
            excel_file = pd.ExcelFile(filepath, engine='openpyxl')

        print(f"📑 Hojas encontradas: {len(excel_file.sheet_names)}")
        print(f"   {', '.join(excel_file.sheet_names[:5])}")
        if len(excel_file.sheet_names) > 5:
            print(f"   ... y {len(excel_file.sheet_names) - 5} más")

        # Analizar cada hoja
        for sheet_name in excel_file.sheet_names[:3]:  # Primeras 3 hojas
            print(f"\n  📄 Hoja: '{sheet_name}'")
            df = pd.read_excel(filepath, sheet_name=sheet_name)

            print(f"     Dimensiones: {df.shape[0]:,} filas × {df.shape[1]} columnas")
            print(f"     Columnas: {list(df.columns[:8])}")
            if len(df.columns) > 8:
                print(f"              ... y {len(df.columns) - 8} más")

            # Tipos de datos
            print(f"\n     Tipos de datos:")
            type_counts = df.dtypes.value_counts()
            for dtype, count in type_counts.items():
                print(f"       - {dtype}: {count} columnas")

            # Valores nulos
            null_counts = df.isnull().sum()
            cols_with_nulls = null_counts[null_counts > 0]
            if len(cols_with_nulls) > 0:
                print(f"\n     ⚠️  Valores nulos encontrados en {len(cols_with_nulls)} columnas:")
                for col, count in cols_with_nulls.head(5).items():
                    pct = (count / len(df)) * 100
                    print(f"       - {col}: {count:,} ({pct:.1f}%)")
            else:
                print(f"\n     ✅ Sin valores nulos")

            # Muestra de datos
            print(f"\n     Vista previa (primeras 3 filas):")
            print(df.head(3).to_string(max_cols=6, max_colwidth=20))

            # Detectar dimensión temporal
            date_cols = df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                print(f"\n     📅 Columnas temporales detectadas: {list(date_cols)}")
                for col in date_cols:
                    if not df[col].isnull().all():
                        print(f"        Rango: {df[col].min()} a {df[col].max()}")

            # Buscar columnas que parezcan fechas por nombre
            potential_date_cols = [col for col in df.columns if any(term in str(col).lower()
                                 for term in ['fecha', 'date', 'periodo', 'mes', 'año', 'trimestre'])]
            if potential_date_cols and len(date_cols) == 0:
                print(f"\n     📅 Posibles columnas temporales (por nombre): {potential_date_cols[:3]}")

        if len(excel_file.sheet_names) > 3:
            print(f"\n  ... ({len(excel_file.sheet_names) - 3} hojas adicionales no mostradas)")

    except Exception as e:
        print(f"❌ Error analizando {filename}: {str(e)}")

def main():
    print("🏦 ANÁLISIS DE DATOS - CÁMARA ARGENTINA DE FINTECH")
    print("="*80)

    # Obtener todos los archivos Excel
    excel_files = sorted(glob.glob("*.xlsx") + glob.glob("*.xls"))

    print(f"\n📁 Total de archivos encontrados: {len(excel_files)}")
    print(f"   Tamaño total: {sum(os.path.getsize(f) for f in excel_files) / 1024 / 1024:.2f} MB")

    # Categorizar archivos por temática
    print("\n📋 Categorías identificadas:")
    categories = {
        'Inclusión Financiera': [],
        'Crédito': [],
        'Medios de Pago': [],
        'Depósitos': []
    }

    for f in excel_files:
        fname = os.path.basename(f).lower()
        if 'inclusion' in fname or 'cuenta' in fname or 'tenencia' in fname:
            categories['Inclusión Financiera'].append(f)
        elif 'deudor' in fname or 'préstamo' in fname or 'crédito' in fname:
            categories['Crédito'].append(f)
        elif 'pago' in fname or 'extraccion' in fname or 'operacion' in fname:
            categories['Medios de Pago'].append(f)
        elif 'depósito' in fname:
            categories['Depósitos'].append(f)

    for cat, files in categories.items():
        if files:
            print(f"   • {cat}: {len(files)} archivo(s)")

    # Analizar archivos representativos de cada categoría
    representative_files = [
        "Informe Inclusion Financiera -octubre 2025.xlsx",
        "Deudores del sistema financiero ampliado por rango etario_ junio 2025.xlsx",
        "Series-Informe-Mensual-de-Pagos-Minoristas-noviembre-2025 (1).xlsx",
        "Préstamos y depósitos del sector privado no financiero por tipo de titular.xls"
    ]

    print("\n" + "="*80)
    print("📊 ANÁLISIS DETALLADO DE ARCHIVOS REPRESENTATIVOS")
    print("="*80)

    for filename in representative_files:
        if os.path.exists(filename):
            analyze_excel_file(filename)

    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()
