# 🤖 Demo: Analista de Datos IA Conversacional

**Cámara Argentina de Fintech**

Demo de un sistema de analytics conversacional que permite hacer preguntas en lenguaje natural sobre datos del ecosistema fintech argentino y obtener visualizaciones automáticas.

---

## 🎯 ¿Qué hace este demo?

Este sistema te permite preguntar cosas como:

- *"Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años"*
- *"¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?"*
- *"Mostrame la evolución de cheques vs transferencias electrónicas"*

Y el sistema:
1. **Entiende** tu pregunta
2. **Busca** qué datos necesita (internos + externos)
3. **Genera SQL** automáticamente
4. **Cruza** múltiples fuentes
5. **Calcula** métricas (crecimientos, deflactado, etc.)
6. **Visualiza** en gráficos interactivos
7. **Responde** con insights

---

## 📊 Datos Incluidos

### Datos Internos (BCRA):
- 📈 **Transferencias inmediatas** (2017-2025, mensual)
- 📄 **Cheques compensados** (2017-2025, mensual)
- 💳 **Inclusión financiera** (bancarización, billeteras digitales)

### Datos Externos (APIs):
- 📉 **Inflación** (IPC mensual e interanual)
- 💱 **Tipo de cambio** (oficial ARS/USD)
- 📊 **PIB** (trimestral)

---

## 🚀 Instalación y Setup

### Prerequisitos

- Python 3.9+
- pip
- Archivos Excel del proyecto (ya están en `/Users/javiersculli/dev/caf/`)

### Paso 1: Configurar API Key de Anthropic

Para usar la funcionalidad completa (text-to-SQL con Claude), necesitás una API key de Anthropic.

1. **Obtener API key:**
   - Ir a https://console.anthropic.com/
   - Crear cuenta (o login)
   - Generar API key en "API Keys"

2. **Configurar en el proyecto:**
   ```bash
   cd /Users/javiersculli/dev/caf/demo
   cp .env.example .env
   ```

3. **Editar `.env` y agregar tu key:**
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-tu-key-aqui
   ```

### Paso 2: Ejecutar Setup Automático

Este script instala dependencias, limpia datos y carga todo a DuckDB:

```bash
cd /Users/javiersculli/dev/caf
python demo/setup.py
```

**Qué hace el setup:**
- ✅ Instala dependencias (pandas, duckdb, anthropic, plotly, streamlit, etc.)
- ✅ Limpia archivos Excel → formato analítico (Parquet)
- ✅ Carga datos a DuckDB
- ✅ Crea vistas analíticas
- ✅ Valida que todo esté OK

**Output esperado:**
```
🎉 SETUP COMPLETADO EXITOSAMENTE
✅ Base de datos DuckDB: 245.3 KB
✅ Catálogo de datos YAML: 12.1 KB
✅ Datos de transferencias: 18.4 KB
✅ Datos de cheques: 15.2 KB
```

---

## 💬 Uso: Chat UI

### Lanzar la interfaz de chat:

```bash
streamlit run demo/ui/chat_app.py
```

Esto abre una interfaz web en `http://localhost:8501`

### Interfaz:

- **Input de pregunta:** Escribe tu consulta en lenguaje natural
- **Botón "Consultar":** Ejecuta la query
- **Sidebar:** Preguntas de ejemplo (click para usar)
- **Tabs:**
  - 📊 **Visualización:** Gráfico interactivo generado automáticamente
  - 🗂️ **Datos:** Tabla con los datos raw
  - 🔍 **Detalles Técnicos:** SQL generado, plan de ejecución, logs

### Logging Verbose:

En la consola donde corriste `streamlit run`, verás logs detallados de cada capa:

```
14:23:45 | INFO     | LLM_ORCHESTRATION    | 🚀 NUEVA CONSULTA: 'Compará transferencias vs inflación'
14:23:46 | INFO     | SEMANTIC_LAYER       | 📋 Generando contexto del catálogo para LLM
14:23:47 | INFO     | QUERY_PLANNING       | 🧠 FASE 1: Query Planning
14:23:48 | INFO     | SQL_GENERATION       | 💻 FASE 2: SQL Generation
14:23:48 | INFO     | DATA_PROCESSING      | ⚡ FASE 3: SQL Execution
14:23:49 | INFO     | API_FETCHING         | 🌐 FASE 4: Fetching External Data
14:23:49 | INFO     | DATA_PROCESSING      | 🔧 FASE 5: Data Processing
14:23:50 | INFO     | VISUALIZATION        | 🎨 GENERACIÓN AUTOMÁTICA DE GRÁFICO
```

---

## 🧪 Testing Individual de Componentes

### Test 1: Pipeline de datos

```bash
# Limpiar datos
python demo/data/01_clean_data.py

# Cargar a DuckDB
python demo/data/02_load_to_duckdb.py
```

### Test 2: API Fetcher (datos externos)

```bash
python demo/utils/api_fetcher.py
```

### Test 3: Query Engine (text-to-SQL)

```bash
python demo/utils/query_engine.py
```

**Nota:** Requiere `ANTHROPIC_API_KEY` configurada

### Test 4: Plot Generator (visualizaciones)

```bash
python demo/utils/plot_generator.py
```

Genera `demo/test_plot.html` que puedes abrir en el browser.

---

## 📋 Preguntas de Ejemplo para el Demo

### Fáciles (para empezar):

1. **"¿Cuál es el volumen de transferencias inmediatas en 2024?"**
   - Filtra por año
   - Muestra serie temporal

2. **"Mostrame la cantidad de cheques compensados en los últimos 12 meses"**
   - Filtra reciente
   - Gráfico de línea simple

### Intermedias (cruces de datos):

3. **"Comparáel crecimiento de transferencias inmediatas vs inflación en los últimos 2 años"**
   - JOIN entre datos internos + API inflación
   - Gráfico dual-axis
   - Calcula crecimiento YoY

4. **"¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?"**
   - Datos de inclusión financiera
   - Comparación de dos series
   - Gráfico multi-line

### Avanzadas (múltiples fuentes + cálculos):

5. **"Mostrame la evolución de cheques vs transferencias electrónicas en términos reales (deflactados por inflación)"**
   - JOIN 3 tablas: transferencias + cheques + inflación
   - Cálculo de deflactor
   - Comparación temporal
   - Gráfico multi-line con valores reales

---

## 🏗️ Arquitectura del Sistema

```
Usuario pregunta en lenguaje natural
              ↓
    [Streamlit Chat UI]
              ↓
    [Query Engine] ← [Semantic Layer (YAML catalog)]
              ↓
    Fase 1: Query Planning (Claude decide qué datos necesita)
              ↓
    Fase 2: SQL Generation (genera SQL con Claude)
              ↓
    Fase 3: SQL Execution (ejecuta en DuckDB)
              ↓
    Fase 4: External Data Fetching (APIs: inflación, TC, PIB)
              ↓
    Fase 5: Data Processing (cruza, calcula métricas)
              ↓
    [Plot Generator] (detecta tipo de gráfico y genera)
              ↓
    Respuesta: DataFrame + Plot + Metadata
              ↓
    [Streamlit muestra resultado]
```

### Componentes Clave:

1. **Semantic Layer (`semantic_layer/data_catalog.yaml`)**
   - Catálogo completo de todas las tablas y columnas
   - Describe relaciones, cálculos comunes, términos de búsqueda
   - La IA usa esto para entender qué datos hay disponibles

2. **Query Engine (`utils/query_engine.py`)**
   - Orquesta todo el flujo
   - Usa Claude para interpretar pregunta → planear → generar SQL
   - Logging verbose de cada fase

3. **API Fetcher (`utils/api_fetcher.py`)**
   - Trae datos externos (inflación, TC, PIB)
   - Caché local para no llamar APIs repetidamente
   - *En producción: reemplazar datos sintéticos por APIs reales*

4. **Plot Generator (`utils/plot_generator.py`)**
   - Detecta automáticamente tipo de gráfico apropiado
   - Genera con Plotly (interactivo)
   - Maneja casos especiales (dual-axis, etc.)

5. **Logger (`utils/logger.py`)**
   - Sistema de logging multi-capa
   - Color-coded por componente
   - Salida a consola + archivo

---

## 📁 Estructura del Proyecto

```
demo/
├── data/
│   ├── 01_clean_data.py          # Pipeline de limpieza
│   ├── 02_load_to_duckdb.py      # Carga a DuckDB
│   ├── staging/                   # Archivos Parquet intermedios
│   ├── analytics/
│   │   └── caf_analytics.duckdb  # Base de datos analítica
│   └── cache/                     # Cache de APIs externas
│
├── semantic_layer/
│   └── data_catalog.yaml          # Catálogo de datos (CRÍTICO)
│
├── utils/
│   ├── logger.py                  # Sistema de logging verbose
│   ├── query_engine.py            # Motor de consultas (text-to-SQL)
│   ├── api_fetcher.py             # APIs externas
│   └── plot_generator.py          # Generador de gráficos
│
├── ui/
│   └── chat_app.py                # Interfaz de chat (Streamlit)
│
├── logs/                          # Logs de ejecución
├── setup.py                       # Setup automático
├── requirements.txt               # Dependencias
├── .env.example                   # Template de variables de entorno
└── README.md                      # Este archivo
```

---

## 🔧 Troubleshooting

### Problema: "ANTHROPIC_API_KEY no configurada"

**Solución:**
1. Crear archivo `.env` en `/Users/javiersculli/dev/caf/demo/`
2. Agregar: `ANTHROPIC_API_KEY=sk-ant-api03-...`

### Problema: "Database no encontrada"

**Solución:**
```bash
python demo/setup.py
```

### Problema: "ModuleNotFoundError: No module named 'X'"

**Solución:**
```bash
pip install -r demo/requirements.txt
```

### Problema: "SQL generado es incorrecto"

**Causa:** Claude a veces comete errores en SQL complejo

**Solución:**
- Ver el SQL en tab "Detalles Técnicos" de la UI
- Refrasear la pregunta de forma más específica
- Agregar más contexto al `data_catalog.yaml`

### Problema: "Query muy lenta"

**Causa:** DuckDB puede ser lento en primeras queries (compilación)

**Solución:**
- Segunda query del mismo tipo será mucho más rápida
- Si persiste: revisar índices o simplificar query

---

## 💰 Costos Estimados

### Con uso REAL (no demo):

**Mensual (uso moderado - 100 queries/día):**
- Claude API: ~$18-50/mes (según complejidad de queries)
- Hosting (si deploya a producción): $20-40/mes
- APIs externas: $0-50/mes (depende de cuáles uses)
- **Total: $38-140/mes**

**Optimizaciones de costo:**
- Cache agresivo de queries comunes → reduce 60-80% de llamadas LLM
- Usar Claude Haiku para queries simples (80% más barato)
- Batch queries donde sea posible

---

## 📈 Roadmap: De Demo a Producción

### Para producción necesitarías:

**1. Datos reales (no sintéticos):**
- [ ] Integrar APIs reales de INDEC (inflación)
- [ ] API de BCRA (tipo de cambio, estadísticas)
- [ ] Agregar más fuentes (datos de socios, regulaciones, etc.)

**2. Robustez:**
- [ ] Manejo de errores más completo
- [ ] Retry logic para APIs
- [ ] Validación de SQL más estricta
- [ ] Rate limiting

**3. Performance:**
- [ ] Cache Redis para queries frecuentes
- [ ] Pre-computar métricas comunes
- [ ] Índices optimizados en DuckDB

**4. Features:**
- [ ] Multi-turn conversations (memoria de contexto)
- [ ] Export de resultados (PDF, PPT)
- [ ] Scheduled reports
- [ ] Alertas proactivas

**5. Deployment:**
- [ ] Dockerizar
- [ ] Deploy a cloud (AWS/GCP/Azure)
- [ ] CI/CD pipeline
- [ ] Monitoring (Sentry, Datadog, etc.)

**6. Seguridad:**
- [ ] Autenticación de usuarios
- [ ] Permisos por rol
- [ ] Audit logs
- [ ] Encriptación de datos sensibles

---

## 🤝 Contribución / Feedback

Este es un demo para mostrar el potencial del approach.

Para feedback o mejoras:
1. Revisar logs verbose para entender qué hace cada capa
2. Modificar `data_catalog.yaml` para agregar más contexto
3. Experimentar con prompts en `query_engine.py`
4. Probar diferentes tipos de preguntas

---

## 📄 Licencia

Demo interno - Cámara Argentina de Fintech

---

## 🎓 Referencias

**Tecnologías usadas:**
- [DuckDB](https://duckdb.org/) - Analytics database
- [Anthropic Claude](https://www.anthropic.com/) - LLM para text-to-SQL
- [Plotly](https://plotly.com/python/) - Visualizaciones interactivas
- [Streamlit](https://streamlit.io/) - UI de chat
- [Pandas](https://pandas.pydata.org/) - Procesamiento de datos
- [Loguru](https://github.com/Delgan/loguru) - Logging

**Papers/Artículos relevantes:**
- [Text-to-SQL with LLMs](https://arxiv.org/abs/2204.00498)
- [Semantic Layers for Analytics](https://www.getdbt.com/analytics-engineering/modular-data-modeling-technique/)

---

**¿Preguntas?** Ver logs verbose o revisar código con comentarios detallados.
