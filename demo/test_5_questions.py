#!/usr/bin/env python3
"""
Test de las 5 preguntas de ejemplo para el demo
Valida que el sistema funcione end-to-end
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from utils.query_engine import QueryEngine
from utils.plot_generator import PlotGenerator
from utils.logger import llm_logger

# Las 5 preguntas de ejemplo del demo
DEMO_QUESTIONS = [
    "Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años",
    "¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?",
    "Mostrame la evolución de cheques vs transferencias electrónicas",
    "¿Cuál es el crecimiento real (deflactado) de los medios de pago electrónicos?",
    "Compará el volumen de pagos electrónicos en los últimos 12 meses"
]


def test_question(engine, plot_generator, question, question_num):
    """Testea una pregunta"""
    llm_logger.info("\n" + "="*80)
    llm_logger.info(f"🧪 TEST {question_num}/5")
    llm_logger.info(f"   Pregunta: '{question}'")
    llm_logger.info("="*80)

    try:
        # Ejecutar query
        result_df, metadata = engine.query(question)

        if result_df.empty:
            llm_logger.warning(f"   ⚠️  Sin resultados")
            return False

        # Generar gráfico
        fig = plot_generator.auto_generate(result_df, metadata, title=question)

        # Guardar gráfico
        output_dir = Path(__file__).parent / "test_outputs"
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / f"question_{question_num}.html"
        fig.write_html(str(output_path))

        llm_logger.info(f"   ✅ Test {question_num} exitoso")
        llm_logger.info(f"   📊 Resultado: {len(result_df)} filas")
        llm_logger.info(f"   💾 Gráfico guardado: {output_path}")

        return True

    except Exception as e:
        llm_logger.error(f"   ❌ Test {question_num} falló: {e}")
        return False


def main():
    """Test de las 5 preguntas"""
    llm_logger.info("\n" + "="*80)
    llm_logger.info("🧪 TEST DE 5 PREGUNTAS DE EJEMPLO")
    llm_logger.info("="*80)

    # Rutas
    base_dir = Path(__file__).parent
    db_path = base_dir / "data" / "analytics" / "caf_analytics.duckdb"
    catalog_path = base_dir / "semantic_layer" / "data_catalog.yaml"

    # Verificar archivos
    if not db_path.exists():
        llm_logger.error(f"❌ Database no encontrada: {db_path}")
        llm_logger.info("   Ejecuta: python demo/setup.py")
        return False

    if not catalog_path.exists():
        llm_logger.error(f"❌ Catálogo no encontrado: {catalog_path}")
        return False

    # Inicializar
    llm_logger.info("\n📋 Inicializando componentes...")
    engine = QueryEngine(db_path, catalog_path)
    plot_generator = PlotGenerator()

    # Ejecutar tests
    results = []

    for i, question in enumerate(DEMO_QUESTIONS, 1):
        success = test_question(engine, plot_generator, question, i)
        results.append((i, question, success))

    # Resumen
    llm_logger.info("\n" + "="*80)
    llm_logger.info("📊 RESUMEN DE TESTS")
    llm_logger.info("="*80)

    passed = sum(1 for _, _, success in results if success)
    total = len(results)

    for num, question, success in results:
        status = "✅" if success else "❌"
        llm_logger.info(f"   {status} Test {num}: {question[:60]}...")

    llm_logger.info(f"\n   Total: {passed}/{total} tests exitosos ({passed/total*100:.0f}%)")

    # Cerrar
    engine.close()

    if passed == total:
        llm_logger.info("\n🎉 TODOS LOS TESTS PASARON")
        llm_logger.info(f"   Ver gráficos en: demo/test_outputs/")
        return True
    else:
        llm_logger.warning(f"\n⚠️  {total-passed} tests fallaron")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
