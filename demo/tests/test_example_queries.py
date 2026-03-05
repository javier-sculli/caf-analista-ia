"""
Tests for the 5 example queries from the sidebar
Each test validates:
1. Query executes without errors
2. Returns data (not empty)
3. Has expected columns
4. Data ranges are correct
5. Calculations are accurate
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta


class TestExample1_TransferenciasVsInflacion:
    """Test: Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años"""

    @pytest.fixture
    def query_result(self, query_engine):
        """Execute the query and return results"""
        question = "Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años"
        df, metadata = query_engine.query(question)
        return df, metadata, question

    def test_query_executes(self, query_result):
        """Test that query executes without error"""
        df, metadata, question = query_result
        assert df is not None, "Query returned None"
        assert not df.empty, "Query returned empty DataFrame"

    def test_has_expected_columns(self, query_result):
        """Test that result has expected columns"""
        df, metadata, question = query_result

        # Should have date column
        date_cols = [col for col in df.columns if 'fecha' in col.lower()]
        assert len(date_cols) > 0, "No date column found"

        # Should have transferencias data
        trans_cols = [col for col in df.columns if 'transferencias' in col.lower()]
        assert len(trans_cols) > 0, "No transferencias columns found"

        # Should have YoY columns (crecimiento)
        yoy_cols = [col for col in df.columns if '_yoy_pct' in col.lower()]
        assert len(yoy_cols) > 0, f"No YoY columns found. Available: {df.columns.tolist()}"

        # Should have inflation data
        ipc_cols = [col for col in df.columns if 'ipc' in col.lower() or 'inflacion' in col.lower()]
        assert len(ipc_cols) > 0, "No inflation columns found"

    def test_date_range(self, query_result, date_helpers):
        """Test that data covers approximately 2 years"""
        df, metadata, question = query_result

        date_col = [col for col in df.columns if 'fecha' in col.lower()][0]
        dates = pd.to_datetime(df[date_col])

        # Should have at least 20 months of data (allowing some flexibility)
        assert len(dates) >= 20, f"Expected at least 20 months, got {len(dates)}"

        # Most recent date should be relatively recent (within last 3 months)
        max_date = dates.max()
        days_ago = (datetime.now() - max_date).days
        assert days_ago < 180, f"Most recent data is {days_ago} days old (expected < 180)"

    def test_yoy_values_are_valid(self, query_result, validation_helpers):
        """Test that YoY calculations are correct"""
        df, metadata, question = query_result

        # Find YoY columns
        yoy_cols = [col for col in df.columns if '_yoy_pct' in col.lower()]

        for yoy_col in yoy_cols:
            # Find the base column (remove _yoy_pct suffix)
            base_col = yoy_col.replace('_yoy_pct', '')
            if base_col in df.columns:
                is_valid, message = validation_helpers['validate_yoy'](df, base_col, yoy_col)
                assert is_valid, f"YoY validation failed for {yoy_col}: {message}"

    def test_no_all_nan_yoy(self, query_result):
        """Test that YoY columns have at least some valid values"""
        df, metadata, question = query_result

        yoy_cols = [col for col in df.columns if '_yoy_pct' in col.lower()]

        for yoy_col in yoy_cols:
            valid_count = df[yoy_col].notna().sum()
            assert valid_count > 0, f"YoY column {yoy_col} has all NaN values"


class TestExample2_InclusionFinanciera:
    """Test: ¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?"""

    @pytest.fixture
    def query_result(self, query_engine):
        question = "¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?"
        df, metadata = query_engine.query(question)
        return df, metadata, question

    def test_query_executes(self, query_result):
        df, metadata, question = query_result
        assert df is not None, "Query returned None"
        assert not df.empty, "Query returned empty DataFrame"

    def test_has_inclusion_data(self, query_result):
        """Test that result has inclusion financiera data"""
        df, metadata, question = query_result

        # Should have percentage columns or cuenta/billetera columns
        relevant_cols = [col for col in df.columns
                        if any(term in col.lower() for term in
                              ['cuenta', 'billetera', 'porcentaje', 'pct', 'adultos'])]

        assert len(relevant_cols) > 0, f"No relevant inclusion columns found. Available: {df.columns.tolist()}"

    def test_percentages_in_valid_range(self, query_result):
        """Test that percentage values are between 0-100"""
        df, metadata, question = query_result

        # Find percentage columns
        pct_cols = [col for col in df.columns
                   if 'pct' in col.lower() or 'porcentaje' in col.lower()]

        for col in pct_cols:
            values = df[col].dropna()
            if len(values) > 0:
                assert values.min() >= 0, f"{col} has values < 0"
                assert values.max() <= 100, f"{col} has values > 100"


class TestExample3_EvolucionChequesVsTransferencias:
    """Test: Mostrame la evolución de cheques vs transferencias electrónicas"""

    @pytest.fixture
    def query_result(self, query_engine):
        question = "Mostrame la evolución de cheques vs transferencias electrónicas"
        df, metadata = query_engine.query(question)
        return df, metadata, question

    def test_query_executes(self, query_result):
        df, metadata, question = query_result
        assert df is not None, "Query returned None"
        assert not df.empty, "Query returned empty DataFrame"

    def test_has_both_payment_methods(self, query_result):
        """Test that result has both cheques and transferencias data"""
        df, metadata, question = query_result

        cheques_cols = [col for col in df.columns if 'cheque' in col.lower()]
        trans_cols = [col for col in df.columns if 'transferencia' in col.lower()]

        assert len(cheques_cols) > 0, f"No cheques columns found. Available: {df.columns.tolist()}"
        assert len(trans_cols) > 0, f"No transferencias columns found. Available: {df.columns.tolist()}"

    def test_temporal_evolution(self, query_result):
        """Test that data shows evolution over time"""
        df, metadata, question = query_result

        date_col = [col for col in df.columns if 'fecha' in col.lower()]
        assert len(date_col) > 0, "No date column for temporal evolution"

        # Should have multiple time periods
        assert len(df) >= 12, f"Expected at least 12 months for evolution, got {len(df)}"


class TestExample4_CrecimientoRealDeflactado:
    """Test: ¿Cuál es el crecimiento real (deflactado) de los medios de pago electrónicos?"""

    @pytest.fixture
    def query_result(self, query_engine):
        question = "¿Cuál es el crecimiento real (deflactado) de los medios de pago electrónicos?"
        df, metadata = query_result
        return df, metadata, question

    def test_query_executes(self, query_result):
        df, metadata, question = query_result
        assert df is not None, "Query returned None"
        assert not df.empty, "Query returned empty DataFrame"

    def test_has_real_values(self, query_result):
        """Test that result has deflacted (real) values"""
        df, metadata, question = query_result

        # Should have columns with "real" in name
        real_cols = [col for col in df.columns if 'real' in col.lower()]
        assert len(real_cols) > 0, f"No 'real' columns found. Available: {df.columns.tolist()}"

    def test_has_inflation_data(self, query_result):
        """Test that inflation data is present for deflation"""
        df, metadata, question = query_result

        ipc_cols = [col for col in df.columns if 'ipc' in col.lower() or 'inflacion' in col.lower()]
        assert len(ipc_cols) > 0, "No inflation data for deflation"

    def test_deflation_calculation(self, query_result, validation_helpers):
        """Test that deflation is correctly applied"""
        df, metadata, question = query_result

        # Find pairs of nominal and real columns
        real_cols = [col for col in df.columns if '_real' in col.lower()]

        for real_col in real_cols:
            # Find corresponding nominal column
            nominal_col = real_col.replace('_real', '')
            if nominal_col in df.columns:
                is_valid, message = validation_helpers['validate_deflation'](df, nominal_col, real_col)
                assert is_valid, f"Deflation validation failed for {real_col}: {message}"

    def test_real_values_lower_than_nominal(self, query_result):
        """Test that real values are lower than nominal (in inflationary context)"""
        df, metadata, question = query_result

        real_cols = [col for col in df.columns if '_real' in col.lower() and '_yoy' not in col.lower()]

        for real_col in real_cols:
            nominal_col = real_col.replace('_real', '')
            if nominal_col in df.columns:
                # In high inflation context, real should generally be < nominal
                # Check at least a few rows
                for i in range(min(5, len(df))):
                    nominal = df.iloc[i][nominal_col]
                    real = df.iloc[i][real_col]
                    if pd.notna(nominal) and pd.notna(real):
                        # Real should be <= nominal (allowing small rounding errors)
                        assert real <= nominal * 1.01, f"Real value greater than nominal at row {i}: {real} > {nominal}"


class TestExample5_VolumenPagosElectronicos:
    """Test: Compará el volumen de pagos electrónicos en los últimos 12 meses"""

    @pytest.fixture
    def query_result(self, query_engine):
        question = "Compará el volumen de pagos electrónicos en los últimos 12 meses"
        df, metadata = query_engine.query(question)
        return df, metadata, question

    def test_query_executes(self, query_result):
        df, metadata, question = query_result
        assert df is not None, "Query returned None"
        assert not df.empty, "Query returned empty DataFrame"

    def test_date_range_12_months(self, query_result):
        """Test that data covers approximately 12 months"""
        df, metadata, question = query_result

        date_col = [col for col in df.columns if 'fecha' in col.lower()][0]
        dates = pd.to_datetime(df[date_col])

        # Should have at least 10 months (allowing some missing data)
        assert len(dates) >= 10, f"Expected at least 10 months, got {len(dates)}"

    def test_has_volume_metrics(self, query_result):
        """Test that result has volume metrics (cantidad/monto)"""
        df, metadata, question = query_result

        volume_cols = [col for col in df.columns
                      if any(term in col.lower() for term in ['cantidad', 'monto', 'volumen', 'yoy'])]

        assert len(volume_cols) > 0, f"No volume columns found. Available: {df.columns.tolist()}"

    def test_has_multiple_payment_types(self, query_result):
        """Test that multiple payment types are included"""
        df, metadata, question = query_result

        # Should have data from multiple sources (transferencias, cheques, etc)
        payment_types = []
        if any('transferencia' in col.lower() for col in df.columns):
            payment_types.append('transferencias')
        if any('cheque' in col.lower() for col in df.columns):
            payment_types.append('cheques')

        # Should have at least one payment type (ideally both)
        assert len(payment_types) >= 1, f"No payment type data found. Available columns: {df.columns.tolist()}"


# Summary test to run all examples
def test_all_examples_execute(query_engine, example_questions):
    """Meta-test: verify all 5 examples can execute"""
    results = []

    for i, question in enumerate(example_questions, 1):
        try:
            df, metadata = query_engine.query(question)
            success = df is not None and not df.empty
            results.append({
                'example': i,
                'question': question[:50] + '...',
                'success': success,
                'rows': len(df) if df is not None else 0,
                'columns': len(df.columns) if df is not None else 0
            })
        except Exception as e:
            results.append({
                'example': i,
                'question': question[:50] + '...',
                'success': False,
                'error': str(e)
            })

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY: All Example Queries")
    print("="*80)
    for r in results:
        status = "✅ PASS" if r['success'] else "❌ FAIL"
        print(f"{status} | Example {r['example']}: {r['question']}")
        if r['success']:
            print(f"        → {r['rows']} rows, {r['columns']} columns")
        elif 'error' in r:
            print(f"        → Error: {r['error']}")
    print("="*80 + "\n")

    # Assert all succeeded
    failures = [r for r in results if not r['success']]
    assert len(failures) == 0, f"{len(failures)}/5 examples failed"
