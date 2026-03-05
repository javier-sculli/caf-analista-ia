"""
Pytest configuration and shared fixtures
"""

import pytest
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.query_engine import QueryEngine
from utils.plot_generator import PlotGenerator


@pytest.fixture(scope="session")
def base_paths():
    """Paths to database and catalog"""
    base_dir = Path(__file__).parent.parent
    return {
        'db_path': base_dir / "data" / "analytics" / "caf_analytics.duckdb",
        'catalog_path': base_dir / "semantic_layer" / "data_catalog.yaml"
    }


@pytest.fixture(scope="session")
def query_engine(base_paths):
    """Initialize QueryEngine once per test session"""
    if not base_paths['db_path'].exists():
        pytest.skip(f"Database not found: {base_paths['db_path']}")

    if not base_paths['catalog_path'].exists():
        pytest.skip(f"Catalog not found: {base_paths['catalog_path']}")

    engine = QueryEngine(
        db_path=base_paths['db_path'],
        catalog_path=base_paths['catalog_path']
    )
    return engine


@pytest.fixture(scope="session")
def plot_generator():
    """Initialize PlotGenerator once per test session"""
    return PlotGenerator()


@pytest.fixture
def example_questions():
    """The 5 example questions from the sidebar"""
    return [
        "Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años",
        "¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?",
        "Mostrame la evolución de cheques vs transferencias electrónicas",
        "¿Cuál es el crecimiento real (deflactado) de los medios de pago electrónicos?",
        "Compará el volumen de pagos electrónicos en los últimos 12 meses"
    ]


@pytest.fixture
def date_helpers():
    """Helper functions for date validations"""
    def is_within_range(date_str, start_date, end_date):
        """Check if date is within range"""
        date = pd.to_datetime(date_str)
        return start_date <= date <= end_date

    def get_months_between(start_date, end_date):
        """Calculate months between two dates"""
        return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

    return {
        'is_within_range': is_within_range,
        'get_months_between': get_months_between,
        'today': datetime.now(),
        'two_years_ago': datetime.now() - timedelta(days=730),
        'one_year_ago': datetime.now() - timedelta(days=365)
    }


@pytest.fixture
def validation_helpers():
    """Helper functions for data validation"""
    def validate_yoy_calculation(df, col_name, yoy_col_name):
        """
        Validate that YoY calculation is correct
        YoY = (value_t - value_t-12) / value_t-12 * 100
        """
        if col_name not in df.columns or yoy_col_name not in df.columns:
            return False, f"Missing columns: {col_name} or {yoy_col_name}"

        # Check if data is sorted by date
        if 'fecha' in df.columns:
            df_sorted = df.sort_values('fecha')
        elif 'fecha_mes' in df.columns:
            df_sorted = df.sort_values('fecha_mes')
        else:
            return False, "No date column found"

        # Validate a few YoY values manually
        errors = []
        for i in range(12, min(15, len(df_sorted))):
            current_val = df_sorted.iloc[i][col_name]
            prev_val = df_sorted.iloc[i-12][col_name]
            calculated_yoy = ((current_val - prev_val) / prev_val * 100) if prev_val != 0 else None
            actual_yoy = df_sorted.iloc[i][yoy_col_name]

            if calculated_yoy is not None and actual_yoy is not None:
                diff = abs(calculated_yoy - actual_yoy)
                if diff > 0.01:  # Allow 0.01% tolerance
                    errors.append(f"Row {i}: Expected {calculated_yoy:.2f}%, got {actual_yoy:.2f}%")

        if errors:
            return False, "; ".join(errors[:3])  # Return first 3 errors

        return True, "YoY calculation valid"

    def validate_deflation(df, nominal_col, real_col, ipc_col='ipc_interanual_pct'):
        """
        Validate that deflation is correctly applied
        real_value = nominal_value / (1 + ipc/100)
        """
        if not all(col in df.columns for col in [nominal_col, real_col, ipc_col]):
            return False, f"Missing columns for deflation validation"

        errors = []
        for i in range(min(5, len(df))):
            nominal = df.iloc[i][nominal_col]
            real = df.iloc[i][real_col]
            ipc = df.iloc[i][ipc_col]

            if pd.notna(nominal) and pd.notna(real) and pd.notna(ipc):
                expected_real = nominal / (1 + ipc/100)
                diff_pct = abs((real - expected_real) / expected_real * 100) if expected_real != 0 else 0

                if diff_pct > 1:  # Allow 1% tolerance
                    errors.append(f"Row {i}: Expected {expected_real:.0f}, got {real:.0f}")

        if errors:
            return False, "; ".join(errors[:3])

        return True, "Deflation calculation valid"

    return {
        'validate_yoy': validate_yoy_calculation,
        'validate_deflation': validate_deflation
    }
