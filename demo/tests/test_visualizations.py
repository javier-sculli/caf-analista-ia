"""
Tests for visualization generation
Validates that graphs are created correctly for each example
"""

import pytest
import plotly.graph_objects as go


class TestVisualizationsGenerate:
    """Test that visualizations generate without errors"""

    @pytest.fixture
    def viz_results(self, query_engine, plot_generator, example_questions):
        """Generate visualizations for all examples"""
        results = []
        for question in example_questions:
            try:
                df, metadata = query_engine.query(question)
                if df is not None and not df.empty:
                    fig = plot_generator.auto_generate(df, metadata, title=question)
                    results.append({
                        'question': question,
                        'df': df,
                        'metadata': metadata,
                        'fig': fig,
                        'success': True
                    })
                else:
                    results.append({
                        'question': question,
                        'success': False,
                        'error': 'Empty dataframe'
                    })
            except Exception as e:
                results.append({
                    'question': question,
                    'success': False,
                    'error': str(e)
                })
        return results

    def test_all_visualizations_generate(self, viz_results):
        """Test that all 5 examples generate visualizations"""
        failures = [r for r in viz_results if not r['success']]

        # Print summary
        print("\n" + "="*80)
        print("VISUALIZATION GENERATION SUMMARY")
        print("="*80)
        for i, r in enumerate(viz_results, 1):
            status = "✅" if r['success'] else "❌"
            print(f"{status} Example {i}: {r['question'][:60]}...")
            if not r['success']:
                print(f"   Error: {r.get('error', 'Unknown')}")
        print("="*80 + "\n")

        assert len(failures) == 0, f"{len(failures)}/5 visualizations failed to generate"

    def test_figures_are_valid(self, viz_results):
        """Test that generated figures are valid Plotly objects"""
        for result in viz_results:
            if result['success']:
                fig = result['fig']
                assert isinstance(fig, go.Figure), f"Not a Plotly Figure: {type(fig)}"

    def test_figures_have_data(self, viz_results):
        """Test that figures contain actual data traces"""
        for result in viz_results:
            if result['success']:
                fig = result['fig']
                assert len(fig.data) > 0, f"Figure has no data traces for: {result['question'][:50]}"

    def test_figures_have_titles(self, viz_results):
        """Test that figures have titles"""
        for result in viz_results:
            if result['success']:
                fig = result['fig']
                title = fig.layout.title.text if fig.layout.title else None
                assert title is not None and len(title) > 0, f"Figure missing title for: {result['question'][:50]}"


class TestVisualizationExample1:
    """Test visualization for Example 1: Transferencias vs Inflación"""

    @pytest.fixture
    def viz_result(self, query_engine, plot_generator):
        question = "Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años"
        df, metadata = query_engine.query(question)
        fig = plot_generator.auto_generate(df, metadata, title=question)
        return df, metadata, fig, question

    def test_chart_type_appropriate(self, viz_result):
        """Test that chart type is appropriate for comparison"""
        df, metadata, fig, question = viz_result

        # Should be either multi_line or dual_axis
        # Check if it has multiple traces (comparing multiple series)
        assert len(fig.data) >= 2, f"Comparison should have at least 2 traces, got {len(fig.data)}"

    def test_has_yoy_and_inflation_traces(self, viz_result):
        """Test that visualization includes YoY and inflation data"""
        df, metadata, fig, question = viz_result

        trace_names = [trace.name for trace in fig.data if hasattr(trace, 'name')]

        # Should have traces for YoY and inflation
        has_yoy = any('yoy' in str(name).lower() or 'transferencia' in str(name).lower()
                     for name in trace_names)
        has_inflation = any('ipc' in str(name).lower() or 'inflacion' in str(name).lower()
                           for name in trace_names)

        assert has_yoy, f"No YoY trace found. Traces: {trace_names}"
        assert has_inflation, f"No inflation trace found. Traces: {trace_names}"


class TestVisualizationExample2:
    """Test visualization for Example 2: Inclusión Financiera"""

    @pytest.fixture
    def viz_result(self, query_engine, plot_generator):
        question = "¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?"
        df, metadata = query_engine.query(question)
        fig = plot_generator.auto_generate(df, metadata, title=question)
        return df, metadata, fig, question

    def test_visualization_generates(self, viz_result):
        """Test that visualization generates successfully"""
        df, metadata, fig, question = viz_result
        assert fig is not None
        assert len(fig.data) > 0


class TestVisualizationExample3:
    """Test visualization for Example 3: Evolución Cheques vs Transferencias"""

    @pytest.fixture
    def viz_result(self, query_engine, plot_generator):
        question = "Mostrame la evolución de cheques vs transferencias electrónicas"
        df, metadata = query_engine.query(question)
        fig = plot_generator.auto_generate(df, metadata, title=question)
        return df, metadata, fig, question

    def test_has_multiple_series(self, viz_result):
        """Test that visualization compares multiple series"""
        df, metadata, fig, question = viz_result

        # Should have at least 2 traces (cheques + transferencias)
        assert len(fig.data) >= 2, f"Evolution comparison should have at least 2 traces, got {len(fig.data)}"

    def test_has_temporal_axis(self, viz_result):
        """Test that x-axis is temporal (dates)"""
        df, metadata, fig, question = viz_result

        # Check that at least one trace has x data (dates)
        has_temporal_data = False
        for trace in fig.data:
            if hasattr(trace, 'x') and trace.x is not None and len(trace.x) > 0:
                has_temporal_data = True
                break

        assert has_temporal_data, "No temporal data found in visualization"


class TestVisualizationExample4:
    """Test visualization for Example 4: Crecimiento Real Deflactado"""

    @pytest.fixture
    def viz_result(self, query_engine, plot_generator):
        question = "¿Cuál es el crecimiento real (deflactado) de los medios de pago electrónicos?"
        df, metadata = query_engine.query(question)
        fig = plot_generator.auto_generate(df, metadata, title=question)
        return df, metadata, fig, question

    def test_visualization_generates(self, viz_result):
        """Test that visualization generates successfully"""
        df, metadata, fig, question = viz_result
        assert fig is not None
        assert len(fig.data) > 0


class TestVisualizationExample5:
    """Test visualization for Example 5: Volumen Pagos Electrónicos"""

    @pytest.fixture
    def viz_result(self, query_engine, plot_generator):
        question = "Compará el volumen de pagos electrónicos en los últimos 12 meses"
        df, metadata = query_engine.query(question)
        fig = plot_generator.auto_generate(df, metadata, title=question)
        return df, metadata, fig, question

    def test_visualization_generates(self, viz_result):
        """Test that visualization generates successfully"""
        df, metadata, fig, question = viz_result
        assert fig is not None
        assert len(fig.data) > 0

    def test_covers_12_months(self, viz_result):
        """Test that visualization covers approximately 12 months"""
        df, metadata, fig, question = viz_result

        # Check x-axis data length
        for trace in fig.data:
            if hasattr(trace, 'x') and trace.x is not None:
                # Should have at least 10 data points (months)
                assert len(trace.x) >= 10, f"Expected at least 10 months of data, got {len(trace.x)}"
                break


class TestVisualizationQuality:
    """Test overall visualization quality across all examples"""

    @pytest.fixture
    def all_figs(self, query_engine, plot_generator, example_questions):
        """Generate all visualizations"""
        figures = []
        for question in example_questions:
            try:
                df, metadata = query_engine.query(question)
                if df is not None and not df.empty:
                    fig = plot_generator.auto_generate(df, metadata, title=question)
                    figures.append(fig)
            except Exception:
                pass
        return figures

    def test_all_have_layouts(self, all_figs):
        """Test that all figures have proper layouts"""
        for fig in all_figs:
            assert fig.layout is not None, "Figure missing layout"

    def test_all_have_axes_labels(self, all_figs):
        """Test that figures have axis labels (when appropriate)"""
        for fig in all_figs:
            # Line charts should have axis labels
            if len(fig.data) > 0 and hasattr(fig.data[0], 'x'):
                # At least x-axis should be defined
                assert fig.layout.xaxis is not None, "Missing x-axis configuration"

    def test_no_empty_figures(self, all_figs):
        """Test that no figure is empty"""
        for fig in all_figs:
            assert len(fig.data) > 0, "Empty figure found"
            # Check that at least one trace has data
            has_data = any(
                hasattr(trace, 'y') and trace.y is not None and len(trace.y) > 0
                for trace in fig.data
            )
            assert has_data, "Figure has traces but no data"


def test_llm_column_selection(query_engine, plot_generator):
    """Test that LLM selects appropriate columns for visualization"""
    question = "Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años"

    df, metadata = query_engine.query(question)

    # Check if LLM is available
    if plot_generator.client is None:
        pytest.skip("LLM not available for column selection")

    # Call the LLM selection method
    selection = plot_generator.select_columns_with_llm(df, question, metadata)

    if selection:
        # Validate selection structure
        assert 'x_col' in selection, "LLM selection missing x_col"
        assert 'y_cols' in selection, "LLM selection missing y_cols"
        assert 'chart_type' in selection, "LLM selection missing chart_type"

        # Validate selected columns exist in df
        assert selection['x_col'] in df.columns, f"Selected x_col '{selection['x_col']}' not in dataframe"
        for y_col in selection['y_cols']:
            assert y_col in df.columns, f"Selected y_col '{y_col}' not in dataframe"

        # Validate chart type is valid
        valid_types = ['line', 'multi_line', 'dual_axis', 'bar']
        assert selection['chart_type'] in valid_types, f"Invalid chart_type: {selection['chart_type']}"

        print(f"\n✅ LLM Column Selection:")
        print(f"   X: {selection['x_col']}")
        print(f"   Y: {selection['y_cols']}")
        print(f"   Type: {selection['chart_type']}")
        print(f"   Reasoning: {selection.get('reasoning', 'N/A')}")
