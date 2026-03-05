# Test Suite - CAF Analytics Demo

Suite de tests para validar el correcto funcionamiento de las queries y visualizaciones del demo de Cámara Argentina de Fintech.

## Estructura

```
tests/
├── __init__.py                    # Package marker
├── conftest.py                    # Fixtures compartidos (pytest)
├── test_example_queries.py        # Tests para las 5 queries del sidebar
├── test_visualizations.py         # Tests para generación de gráficos
├── run_tests.py                   # Runner principal
└── README.md                      # Esta documentación
```

## Instalación

Primero, instalá pytest:

```bash
pip install pytest pytest-cov
```

## Cómo correr los tests

### Opción 1: Script runner (recomendado)

```bash
cd demo
python3 tests/run_tests.py
```

Este script corre todos los tests y genera un reporte detallado.

### Opción 2: pytest directo

**Todos los tests:**
```bash
cd demo
python3 -m pytest tests/ -v
```

**Solo tests de queries:**
```bash
python3 -m pytest tests/test_example_queries.py -v
```

**Solo tests de visualizaciones:**
```bash
python3 -m pytest tests/test_visualizations.py -v
```

**Un test específico:**
```bash
python3 -m pytest tests/test_example_queries.py::TestExample1_TransferenciasVsInflacion -v
```

**Con output detallado:**
```bash
python3 -m pytest tests/ -v -s
```

**Con coverage report:**
```bash
python3 -m pytest tests/ --cov=utils --cov-report=html
```

## Qué valida cada archivo

### `test_example_queries.py`

Valida las **5 queries del sidebar**:

1. **Transferencias vs Inflación (2 años)**
   - ✅ Query ejecuta sin errores
   - ✅ Tiene columnas esperadas (fecha, transferencias, YoY, inflación)
   - ✅ Rango temporal correcto (~24 meses)
   - ✅ Cálculos YoY son correctos
   - ✅ YoY tiene valores válidos (no todo NaN)

2. **Inclusión Financiera (cuentas vs billeteras)**
   - ✅ Query ejecuta sin errores
   - ✅ Tiene datos de inclusión financiera
   - ✅ Porcentajes están entre 0-100

3. **Evolución Cheques vs Transferencias**
   - ✅ Query ejecuta sin errores
   - ✅ Tiene datos de ambos medios de pago
   - ✅ Datos temporales (evolución)

4. **Crecimiento Real Deflactado**
   - ✅ Query ejecuta sin errores
   - ✅ Tiene valores "real" (deflactados)
   - ✅ Tiene datos de inflación
   - ✅ Cálculo de deflación es correcto
   - ✅ Valores reales < nominales (en contexto inflacionario)

5. **Volumen Pagos Electrónicos (12 meses)**
   - ✅ Query ejecuta sin errores
   - ✅ Rango temporal ~12 meses
   - ✅ Tiene métricas de volumen
   - ✅ Incluye múltiples tipos de pago

### `test_visualizations.py`

Valida la **generación de gráficos**:

- ✅ Todos los ejemplos generan visualizaciones sin errores
- ✅ Los figures son objetos Plotly válidos
- ✅ Los figures tienen datos (traces)
- ✅ Los figures tienen títulos
- ✅ Tipos de gráfico apropiados (line, multi_line, dual_axis)
- ✅ Gráficos tienen ejes definidos
- ✅ LLM selecciona columnas correctas

## Helpers de validación

El archivo `conftest.py` incluye helpers reutilizables:

### `validation_helpers['validate_yoy']`

Valida que el cálculo YoY sea correcto:
```python
YoY% = (valor_actual - valor_12_meses_atras) / valor_12_meses_atras * 100
```

### `validation_helpers['validate_deflation']`

Valida que el deflactor esté correctamente aplicado:
```python
valor_real = valor_nominal / (1 + ipc/100)
```

### `date_helpers`

Helpers para validar rangos temporales:
- `is_within_range()`: Verifica si fecha está en rango
- `get_months_between()`: Calcula meses entre fechas
- `today`, `two_years_ago`, `one_year_ago`: Fechas de referencia

## Interpretando los resultados

### ✅ Todos los tests pasan

```
========================== 25 passed in 15.23s ==========================
```

¡Perfecto! Todo funciona correctamente.

### ❌ Algunos tests fallan

```
FAILED tests/test_example_queries.py::TestExample1::test_yoy_values_are_valid
```

**Qué significa**: El cálculo de YoY no es correcto para el ejemplo 1.

**Cómo debuggear**:
1. Correr solo ese test con `-v -s` para ver el output:
   ```bash
   python3 -m pytest tests/test_example_queries.py::TestExample1::test_yoy_values_are_valid -v -s
   ```

2. Revisar el mensaje de error que explica qué salió mal:
   ```
   AssertionError: YoY validation failed for transferencias_monto_yoy_pct:
   Row 12: Expected 25.30%, got -25.30%
   ```

3. Esto indicaría que el cálculo está invertido (datos en orden incorrecto).

## Tests continuos (CI)

Para integrar con CI/CD (GitHub Actions, etc):

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest
      - run: python3 demo/tests/run_tests.py
```

## Troubleshooting

### Error: "No module named 'pytest'"

```bash
pip install pytest
```

### Error: "Database not found"

Asegurate de haber corrido el setup primero:
```bash
python3 demo/setup.py
```

### Error: "ANTHROPIC_API_KEY not configured"

Los tests usan tu API key de `.env`. Si no tenés una:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." > demo/.env
```

### Tests muy lentos

Los tests llaman a la API de Claude. Para acelerar:
- Usar mock/fixtures en lugar de llamadas reales
- Cachear resultados de queries repetitivas
- Correr solo un subset de tests durante desarrollo

## Agregando nuevos tests

### Para una nueva query:

```python
class TestExample6_MiNuevaQuery:
    """Test: Descripción de la query"""

    @pytest.fixture
    def query_result(self, query_engine):
        question = "Mi pregunta nueva"
        df, metadata = query_engine.query(question)
        return df, metadata, question

    def test_query_executes(self, query_result):
        df, metadata, question = query_result
        assert df is not None
        assert not df.empty

    def test_mi_validacion_especifica(self, query_result):
        df, metadata, question = query_result
        # Tus validaciones custom aquí
        assert 'columna_esperada' in df.columns
```

### Para una nueva visualización:

```python
class TestVisualizationExample6:
    """Test visualization for Example 6"""

    @pytest.fixture
    def viz_result(self, query_engine, plot_generator):
        question = "Mi pregunta nueva"
        df, metadata = query_engine.query(question)
        fig = plot_generator.auto_generate(df, metadata, title=question)
        return df, metadata, fig, question

    def test_visualization_generates(self, viz_result):
        df, metadata, fig, question = viz_result
        assert fig is not None
        assert len(fig.data) > 0
```

## Métricas objetivo

| Métrica | Objetivo | Actual |
|---------|----------|--------|
| Tests totales | 30+ | 35 |
| Coverage queries | >90% | TBD |
| Coverage visualizations | >80% | TBD |
| Tiempo ejecución | <30s | TBD |

## Contacto

Para reportar bugs o sugerir mejoras a los tests, contactar al equipo de desarrollo.
