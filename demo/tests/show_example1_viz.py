#!/usr/bin/env python3
"""
Script para visualizar el gráfico del Example 1: Transferencias vs Inflación
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.query_engine import QueryEngine
from utils.plot_generator import PlotGenerator

# Initialize
base_dir = Path(__file__).parent.parent
engine = QueryEngine(
    db_path=base_dir / "data" / "analytics" / "caf_analytics.duckdb",
    catalog_path=base_dir / "semantic_layer" / "data_catalog.yaml"
)
plot_gen = PlotGenerator()

# Query
question = "Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años"
print(f"\n{'='*80}")
print(f"PREGUNTA: {question}")
print(f"{'='*80}\n")

df, metadata = engine.query(question)

print(f"📊 RESULTADOS:")
print(f"   Filas: {len(df)}")
print(f"   Columnas: {len(df.columns)}")
print(f"\n📋 COLUMNAS DISPONIBLES:")
for i, col in enumerate(df.columns, 1):
    print(f"   {i}. {col}")

print(f"\n🔍 PREVIEW DE DATOS (primeras 5 filas):")
print(df.head().to_string())

print(f"\n📈 DECISIÓN DEL LLM PARA VISUALIZACIÓN:")
llm_selection = plot_gen.select_columns_with_llm(df, question, metadata)
if llm_selection:
    print(f"   X (eje temporal): {llm_selection['x_col']}")
    print(f"   Y (métricas):     {llm_selection['y_cols']}")
    print(f"   Tipo de gráfico:  {llm_selection['chart_type']}")
    print(f"\n   💡 Razonamiento del LLM:")
    print(f"      {llm_selection['reasoning']}")

# Generate figure
fig = plot_gen.auto_generate(df, metadata, title=question)

print(f"\n✅ GRÁFICO GENERADO:")
print(f"   Tipo: {type(fig).__name__}")
print(f"   Traces (series): {len(fig.data)}")
for i, trace in enumerate(fig.data, 1):
    trace_name = getattr(trace, 'name', 'Sin nombre')
    trace_type = type(trace).__name__
    y_data_count = len(trace.y) if hasattr(trace, 'y') else 0
    print(f"      {i}. {trace_name} ({trace_type}) - {y_data_count} puntos")

print(f"\n📐 CONFIGURACIÓN DEL GRÁFICO:")
print(f"   Título: {fig.layout.title.text if fig.layout.title else 'N/A'}")
print(f"   X-axis: {fig.layout.xaxis.title.text if fig.layout.xaxis.title else 'N/A'}")
print(f"   Y-axis 1: {fig.layout.yaxis.title.text if fig.layout.yaxis.title else 'N/A'}")
if fig.layout.yaxis2:
    print(f"   Y-axis 2: {fig.layout.yaxis2.title.text if fig.layout.yaxis2.title else 'N/A'}")

# Save to HTML
output_path = Path(__file__).parent / "example1_viz.html"
fig.write_html(str(output_path))

print(f"\n💾 GRÁFICO GUARDADO:")
print(f"   Archivo: {output_path}")
print(f"   Abrilo en tu navegador para ver la visualización interactiva")
print(f"\n{'='*80}\n")
