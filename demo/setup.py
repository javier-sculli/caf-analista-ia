#!/usr/bin/env python3
"""
Setup Script - Ejecuta todo el pipeline de preparación del demo
1. Limpia datos de Excel
2. Carga a DuckDB
3. Valida que todo funcione
"""

import sys
from pathlib import Path
import subprocess

# Add to path
sys.path.append(str(Path(__file__).parent))
from utils.logger import data_logger, llm_logger

def run_step(step_name: str, script_path: Path, description: str):
    """Ejecuta un paso del setup"""
    llm_logger.info("="*80)
    llm_logger.info(f"📌 PASO: {step_name}")
    llm_logger.info(f"   {description}")
    llm_logger.info("="*80)

    if not script_path.exists():
        llm_logger.error(f"❌ Script no encontrado: {script_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False  # Mostrar output en consola
        )
        llm_logger.info(f"✅ {step_name} completado exitosamente")
        return True

    except subprocess.CalledProcessError as e:
        llm_logger.error(f"❌ Error en {step_name}: {e}")
        return False


def verify_requirements():
    """Verifica que las dependencias estén instaladas"""
    llm_logger.info("🔍 Verificando dependencias...")

    required_packages = [
        'pandas', 'duckdb', 'anthropic', 'plotly', 'streamlit',
        'pyyaml', 'requests', 'loguru', 'openpyxl', 'xlrd'
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        llm_logger.warning(f"⚠️  Paquetes faltantes: {', '.join(missing)}")
        llm_logger.info("   Instalando dependencias...")

        requirements_file = Path(__file__).parent / "requirements.txt"

        if requirements_file.exists():
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                    check=True
                )
                llm_logger.info("   ✅ Dependencias instaladas")
            except subprocess.CalledProcessError:
                llm_logger.error("   ❌ Error instalando dependencias")
                return False
        else:
            llm_logger.error(f"   ❌ requirements.txt no encontrado: {requirements_file}")
            return False

    else:
        llm_logger.info("   ✅ Todas las dependencias están instaladas")

    return True


def verify_api_key():
    """Verifica que la API key de Anthropic esté configurada"""
    llm_logger.info("🔑 Verificando API key de Anthropic...")

    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        llm_logger.warning("⚠️  ANTHROPIC_API_KEY no configurada")
        llm_logger.info("   Para habilitar funcionalidad completa:")
        llm_logger.info("   1. Copia .env.example a .env")
        llm_logger.info("   2. Agrega tu API key de Anthropic")
        llm_logger.info("   3. Obtén una key en: https://console.anthropic.com/")
        return False
    else:
        llm_logger.info(f"   ✅ API key configurada (empieza con: {api_key[:10]}...)")
        return True


def main():
    """Pipeline principal de setup"""
    print("\n")
    llm_logger.info("="*80)
    llm_logger.info("🚀 SETUP - DEMO ANALISTA IA CONVERSACIONAL")
    llm_logger.info("   Cámara Argentina de Fintech")
    llm_logger.info("="*80)
    print("\n")

    base_dir = Path(__file__).parent

    # Paso 0: Verificar dependencias
    if not verify_requirements():
        llm_logger.error("❌ Setup fallido: dependencias faltantes")
        return False

    # Paso 0.5: Verificar API key (warning pero no bloqueante)
    has_api_key = verify_api_key()
    if not has_api_key:
        llm_logger.warning("⚠️  Continuando sin API key (funcionalidad limitada)")

    # Paso 1: Limpiar datos
    step1_script = base_dir / "data" / "01_clean_data.py"
    if not run_step(
        "1/2 - Data Cleaning",
        step1_script,
        "Extrae y limpia datos de archivos Excel → Parquet"
    ):
        return False

    # Paso 2: Cargar a DuckDB
    step2_script = base_dir / "data" / "02_load_to_duckdb.py"
    if not run_step(
        "2/2 - Load to DuckDB",
        step2_script,
        "Carga datos limpios a DuckDB y crea vistas analíticas"
    ):
        return False

    # Verificación final
    llm_logger.info("\n" + "="*80)
    llm_logger.info("🔍 VERIFICACIÓN FINAL")
    llm_logger.info("="*80)

    db_path = base_dir / "data" / "analytics" / "caf_analytics.duckdb"
    catalog_path = base_dir / "semantic_layer" / "data_catalog.yaml"

    checks = [
        (db_path, "Base de datos DuckDB"),
        (catalog_path, "Catálogo de datos YAML"),
        (base_dir / "data" / "staging" / "transferencias_inmediatas.parquet", "Datos de transferencias"),
        (base_dir / "data" / "staging" / "cheques.parquet", "Datos de cheques"),
    ]

    all_ok = True
    for path, description in checks:
        if path.exists():
            size_kb = path.stat().st_size / 1024
            llm_logger.info(f"   ✅ {description}: {size_kb:.1f} KB")
        else:
            llm_logger.error(f"   ❌ {description}: NO ENCONTRADO")
            all_ok = False

    if all_ok:
        llm_logger.info("\n" + "="*80)
        llm_logger.info("🎉 SETUP COMPLETADO EXITOSAMENTE")
        llm_logger.info("="*80)
        llm_logger.info("\n📋 PRÓXIMOS PASOS:")
        llm_logger.info("\n   1. Para lanzar la UI de chat:")
        llm_logger.info("      streamlit run demo/ui/chat_app.py")
        llm_logger.info("\n   2. Para testear el query engine:")
        llm_logger.info("      python demo/utils/query_engine.py")
        llm_logger.info("\n   3. Para testear visualizaciones:")
        llm_logger.info("      python demo/utils/plot_generator.py")
        llm_logger.info("\n" + "="*80)
        return True
    else:
        llm_logger.error("\n❌ SETUP INCOMPLETO - Revisa los errores arriba")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
