"""
Logger configurado para verbose output
Muestra cada capa del sistema trabajando
"""

import sys
from loguru import logger
from pathlib import Path

# Configuración de logging verbose
logger.remove()  # Remover handler default

# Console logger (verbose)
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[layer]: <20}</cyan> | <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

# File logger (para análisis posterior)
logger.add(
    Path(__file__).parent.parent / "logs" / "demo_{time}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[layer]: <20} | {message}",
    level="DEBUG",
    rotation="10 MB"
)

def get_logger(layer_name: str):
    """
    Retorna logger con contexto de capa

    Capas del sistema:
    - DATA_INGESTION: Carga de archivos Excel
    - DATA_CLEANING: Limpieza y normalización
    - DATA_LOADING: Carga a DuckDB
    - SEMANTIC_LAYER: Búsqueda de metadatos
    - QUERY_PLANNING: Decisión de qué datos necesita
    - SQL_GENERATION: Generación de SQL
    - API_FETCHING: Llamadas a APIs externas
    - DATA_PROCESSING: Cruces y cálculos
    - VISUALIZATION: Generación de gráficos
    - LLM_ORCHESTRATION: Coordinación con Claude
    """
    return logger.bind(layer=layer_name)

# Crear loggers para cada capa
data_logger = get_logger("DATA_INGESTION")
clean_logger = get_logger("DATA_CLEANING")
load_logger = get_logger("DATA_LOADING")
semantic_logger = get_logger("SEMANTIC_LAYER")
planning_logger = get_logger("QUERY_PLANNING")
sql_logger = get_logger("SQL_GENERATION")
api_logger = get_logger("API_FETCHING")
processing_logger = get_logger("DATA_PROCESSING")
viz_logger = get_logger("VISUALIZATION")
llm_logger = get_logger("LLM_ORCHESTRATION")
