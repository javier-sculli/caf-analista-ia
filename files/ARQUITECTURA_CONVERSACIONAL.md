# 🤖 ARQUITECTURA: ANALISTA DE DATOS CONVERSACIONAL

## 🎯 Caso de Uso Principal

**Usuario pregunta:**
> "Compará el crecimiento de transferencias inmediatas vs la inflación en los últimos 2 años"

**Sistema hace:**
1. Entiende que necesita: datos de transferencias (BCRA) + inflación (INDEC o API)
2. Genera SQL para extraer transferencias del DuckDB
3. Llama API externa para inflación
4. Cruza ambos datasets
5. Calcula tasas de crecimiento YoY
6. Genera gráfico comparativo (líneas duales)
7. Responde en lenguaje natural con insights: *"Las transferencias crecieron 240% mientras la inflación fue 180%, mostrando crecimiento real del 60%..."*

---

## 🏛️ Arquitectura Técnica

```
┌─────────────────────────────────────────────────────────────────┐
│                      CAPA DE INTERACCIÓN                        │
│                                                                 │
│  • Chat UI (Streamlit/Panel/Chainlit)                         │
│  • Slack Bot (opcional - para uso interno rápido)             │
│  • API REST (para integraciones futuras)                      │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE IA/ORCHESTRATION                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ LLM con Function Calling (Claude 3.5 Sonnet / GPT-4o)   │  │
│  │  • Interpreta pregunta en lenguaje natural              │  │
│  │  • Decide qué herramientas usar                         │  │
│  │  • Genera narrativa de respuesta                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Agent Orchestrator (LangGraph / CrewAI)                 │  │
│  │  • Planea pasos del análisis                            │  │
│  │  • Maneja conversaciones multi-turn                     │  │
│  │  • Cache de resultados comunes                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      CAPA DE HERRAMIENTAS                       │
│                                                                 │
│  ┌────────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ SQL Generator      │  │ Data Fetcher    │  │ Plotter     │ │
│  │ (Text-to-SQL)      │  │ (APIs externas) │  │ (Plotly)    │ │
│  │                    │  │                 │  │             │ │
│  │ • Vanna.ai o       │  │ • Inflación     │  │ • Line      │ │
│  │   LangChain SQL    │  │ • PIB           │  │ • Bar       │ │
│  │ • Validación SQL   │  │ • Tipo cambio   │  │ • Scatter   │ │
│  │ • Query optimizer  │  │ • BCRA API      │  │ • Heatmap   │ │
│  └────────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                                 │
│  ┌────────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Calculator         │  │ Comparator      │  │ Forecaster  │ │
│  │ (numpy/pandas)     │  │ (benchmarking)  │  │ (Prophet)   │ │
│  └────────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     SEMANTIC LAYER (CRÍTICO)                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Data Catalog con Metadatos Enriquecidos                 │  │
│  │                                                          │  │
│  │ Para cada tabla/métrica:                                │  │
│  │  • Nombre natural: "transferencias inmediatas"          │  │
│  │  • Nombre técnico: medios_pago.transferencias_inm       │  │
│  │  • Descripción: "Transferencias push en pesos..."       │  │
│  │  • Dimensiones: fecha, tipo, canal                      │  │
│  │  • Unidad: cantidad, monto_nominal_pesos                │  │
│  │  • Granularidad: mensual                                │  │
│  │  • Fuente: BCRA Informe Pagos Minoristas                │  │
│  │  • Actualización: mensual (fin de mes +15 días)         │  │
│  │  • Relaciones: JOIN con inflacion ON fecha             │  │
│  │  • Ejemplos de preguntas: "¿Cómo evolucionaron...?"    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Embeddings de metadatos (RAG) para búsqueda semántica         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  CAPA DE DATOS (sin cambios)                    │
│                                                                 │
│  • DuckDB (datos internos limpios)                            │
│  • Parquet files (staging)                                     │
│  • dbt (transformaciones base)                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  FUENTES DE DATOS                               │
│                                                                 │
│  INTERNAS:                    EXTERNAS (APIs):                 │
│  • Archivos Excel BCRA       • BCRA Estadísticas API           │
│  • (Datos futuros socios)    • INDEC (inflación, PIB)          │
│                               • Banco Mundial                   │
│                               • Trading Economics               │
│                               • Alpha Vantage (mercados)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Cambios Clave vs Arquitectura Anterior

| Aspecto | Arquitectura Anterior | Nueva Arquitectura |
|---------|----------------------|-------------------|
| **Interfaz principal** | Dashboards fijos | Chat conversacional |
| **Queries** | Pre-definidas en dbt | Generadas dinámicamente |
| **Visualizaciones** | Dashboard estático | Gráficos on-demand |
| **Fuentes externas** | Nice-to-have (Fase 3) | **Crítico Fase 1** |
| **Semantic layer** | Opcional | **Indispensable** |
| **LLM** | Fase 3 (nice-to-have) | **Core Fase 1** |
| **Complejidad** | Media-baja | **Media-alta** |
| **Valor diferencial** | Medio | **Muy alto** |

---

## 🔧 Stack Tecnológico Actualizado

### Core Engine:
- **LLM:** Claude 3.5 Sonnet (mejor para análisis) o GPT-4o
- **Orchestration:** LangGraph (para agentes complejos) o LangChain
- **Text-to-SQL:** Vanna.ai (especializado) o custom con Claude
- **Data Query:** DuckDB (sin cambios - excelente para queries ad-hoc)
- **Data Prep:** dbt Core (preparar datos base)

### UI/Interacción:
- **Chat Interface:** Streamlit (rápido) o Chainlit (específico para AI chat)
- **Visualizaciones:** Plotly (interactivo) o Altair (declarativo)
- **Optional:** Slack Bot para queries rápidas desde Slack

### Datos Externos:
- **APIs:**
  - BCRA Estadísticas: https://www.bcra.gob.ar/PublicacionesEstadisticas/APIs.asp
  - INDEC (web scraping o manual)
  - World Bank API: https://data.worldbank.org/indicator
  - Trading Economics API: https://tradingeconomics.com/api
- **Caché:** Redis o SQLite para no llamar APIs repetidamente

### Semantic Layer:
- **Catálogo:** YAML files + embeddings (ChromaDB/FAISS)
- **RAG:** LlamaIndex o LangChain para búsqueda semántica de metadatos

---

## 📊 Ejemplos de Uso Real

### Ejemplo 1: Comparación con Inflación
**Usuario:**
> "Mostrame el crecimiento de pagos con QR vs inflación en 2024"

**Sistema:**
1. Busca "pagos con QR" en catálogo → encuentra `medios_pago.transferencias_qr`
2. Busca "inflación" → identifica necesita API externa (INDEC IPC)
3. Genera SQL: `SELECT fecha, sum(cantidad) FROM medios_pago WHERE tipo='QR' AND fecha >= '2024-01-01'`
4. Llama INDEC API para IPC mensual 2024
5. Calcula YoY growth de ambas series
6. Genera gráfico dual-axis (líneas)
7. Responde:
```
"En 2024, los pagos con QR crecieron 156% YoY,
mientras la inflación fue 211%. En términos reales,
los pagos QR decrecieron -26% (deflactados).

Sin embargo, desde julio se observa recuperación:
+8% real en el segundo semestre."

[GRÁFICO: línea azul QR nominal, línea roja inflación,
 área sombreada = QR real]
```

---

### Ejemplo 2: Análisis de Brecha
**Usuario:**
> "¿Qué porcentaje de adultos usa billeteras digitales vs cuentas bancarias tradicionales?"

**Sistema:**
1. Identifica dos métricas: `inclusion.billeteras_digitales_pct`, `inclusion.cuentas_bancarias_pct`
2. Genera SQL con UNION de ambas series
3. Calcula brecha = cuentas_banc - billeteras_dig
4. Detecta tendencia: brecha cerrándose 3.2% anual
5. Responde:
```
"Actualmente (jun 2025):
• Cuentas bancarias: 87% de adultos
• Billeteras digitales: 62% de adultos
• Brecha: 25 puntos porcentuales

Tendencia: La brecha se reduce ~3.2pp/año.
A este ritmo, en 2032 tendrían penetración similar (~95%).

[GRÁFICO: área apilada mostrando evolución 2017-2025]
```

---

### Ejemplo 3: Benchmarking Regional
**Usuario:**
> "Comparanos con Brasil y Chile en inclusión financiera"

**Sistema:**
1. Busca datos locales: `inclusion.poblacion_bancarizada_pct`
2. Identifica necesita datos externos → World Bank API
3. Fetches: `FX.OWN.TOTL.ZS` (account ownership) para ARG, BRA, CHL
4. Normaliza y joinea por año
5. Calcula posición relativa y gap
6. Responde:
```
"Inclusión Financiera (% adultos con cuenta, 2024):
• Chile: 91% 🥇
• Brasil: 84% 🥈
• Argentina: 76% 🥉

Gap vs líder: -15pp

Sin embargo, Argentina lidera en adopción de
medios digitales: 62% usa billeteras (vs 38% Brasil).

[GRÁFICO: barras horizontales + sparklines de evolución]
```

---

## 💰 Costos Actualizados

### Costos Mensuales Estimados:

| Componente | Costo Mes |
|------------|-----------|
| **Hosting (VPS/Cloud Run)** | $20-40 |
| **Storage (S3/GCS)** | $5-10 |
| **LLM API (Claude/OpenAI)** | $30-150 |
| **APIs externas** | $0-50 |
| **Total** | **$55-250/mes** |

**Desglose LLM:**
- Claude 3.5 Sonnet: $3/1M input tokens, $15/1M output
- Uso estimado: 100 queries/día × 2K tokens input + 500 output × 30 días = $18/mes
- Con picos: $30-150/mes

**Optimizaciones de costo:**
- Cache de queries comunes (reduce 60-80% de llamadas LLM)
- Usar Claude 3.5 Haiku para queries simples ($0.80/1M input)
- Batch queries cuando posible

### Comparación Anual:

| Solución | Año 1 | Capacidades IA |
|----------|-------|----------------|
| **Conversational (nueva)** | $660-3,000 | ✅ Full AI chat |
| Dashboards tradicionales | $360-600 | ❌ Sin IA |
| Snowflake + BI | $2,400+ | ⚠️ IA add-on costoso |

---

## 🗺️ Roadmap Revisado

### FASE 1: MVP Conversacional (6-8 semanas) - "Demostrar Viabilidad"

**Semanas 1-2: Fundación de Datos**
- ✅ Pipeline de ingesta (Excel → Parquet → DuckDB)
- ✅ dbt models para 5-6 tablas core limpias
- ✅ Integración de 2-3 APIs externas críticas (inflación, PIB)

**Semanas 3-4: Semantic Layer**
- ✅ Catálogo de datos en YAML (todas las tablas/métricas)
- ✅ Embeddings de metadatos
- ✅ RAG search funcional

**Semanas 5-6: Chat Engine**
- ✅ Text-to-SQL básico (con Vanna.ai o custom)
- ✅ Function calling para APIs externas
- ✅ Plotting automático (Plotly)
- ✅ Chat UI con Streamlit

**Semanas 7-8: Refinamiento**
- ✅ Validación de SQL generado (evitar errores)
- ✅ Mejora de prompts para interpretación
- ✅ Cache de queries comunes
- ✅ 10-15 ejemplos de preguntas funcionando bien

**Entregable Fase 1:**
- Chat funcional con 80-90% de accuracy en preguntas comunes
- 5-6 datasets integrados
- 3-4 fuentes externas
- Documentación de metadatos completa

**Inversión:** $500-800 (setup) + $60-180/mes (operación)

---

### FASE 2: Producción & Escalado (8-10 semanas) - "Robusto y Confiable"

**Mejoras de Calidad:**
- ✅ Manejo de errores robusto (SQL inválido, APIs caídas)
- ✅ Multi-turn conversations (seguimiento de contexto)
- ✅ Memory de sesión (recordar preguntas anteriores)
- ✅ Sugerencias de preguntas relacionadas

**Capacidades Avanzadas:**
- ✅ Análisis estadístico (correlaciones, regresiones)
- ✅ Forecasting básico (Prophet para tendencias)
- ✅ Comparaciones automáticas (benchmarking)
- ✅ Export de resultados (PDF, Excel, PNG)

**Operación:**
- ✅ Monitoring de uso y costos LLM
- ✅ A/B testing de prompts
- ✅ Dashboard de métricas del sistema
- ✅ Feedback loop (thumbs up/down en respuestas)

**Data Expansion:**
- ✅ Incorporar 10-15 datasets adicionales
- ✅ Integrar datos de socios (si aprueban)
- ✅ Web scraping de regulaciones (BCRA, CNV)

**Entregable Fase 2:**
- Sistema en producción con >95% uptime
- 20+ datasets integrados
- 50+ preguntas tipo validadas
- SLA de respuesta <10 segundos

**Inversión:** $1,200-1,800 (desarrollo) + $100-250/mes (operación)

---

### FASE 3: Inteligencia Avanzada (12+ semanas) - "Proactivo y Predictivo"

**IA Proactiva:**
- ✅ Alertas inteligentes ("Anomalía detectada en...")
- ✅ Insights automáticos semanales/mensuales
- ✅ Sugerencia de análisis basados en contexto

**Capacidades Avanzadas:**
- ✅ Análisis de sentimiento en regulaciones
- ✅ Detección de patrones/correlaciones ocultas
- ✅ Simulaciones ("¿Qué pasaría si...?")
- ✅ Explicabilidad (por qué recomienda algo)

**Multimodalidad:**
- ✅ Subir PDFs/imágenes de reportes → extraer datos
- ✅ Reconocimiento de tablas en screenshots
- ✅ Generación de presentaciones automáticas

**Integración:**
- ✅ Slack Bot para queries rápidas
- ✅ API pública (rate-limited) para socios
- ✅ Webhooks para alimentar otros sistemas

**Entregable Fase 3:**
- Sistema "inteligente" que anticipa necesidades
- Capacidades únicas en el mercado
- ROI medible para socios

**Inversión:** $2,000-3,000 (desarrollo) + $150-300/mes (operación)

---

## 🎯 Ventajas de Este Enfoque

### vs Dashboards Tradicionales:
- ✅ **Flexibilidad infinita**: No estás limitado a visualizaciones pre-definidas
- ✅ **Curva de aprendizaje cero**: Preguntar en lenguaje natural vs aprender interfaz de BI
- ✅ **Insights emergentes**: Descubrir relaciones no anticipadas
- ✅ **Personalización**: Cada usuario pregunta lo que necesita

### vs Contratar Analistas:
- ✅ **Costo:** $60-180/mes vs $3-5K/mes analista
- ✅ **Velocidad:** Respuesta en segundos vs horas/días
- ✅ **Disponibilidad:** 24/7 vs horario laboral
- ✅ **Escalabilidad:** Múltiples usuarios simultáneos

### vs Soluciones Enterprise (ThoughtSpot, etc.):
- ✅ **Costo:** $1-3K/año vs $50-100K/año
- ✅ **Customización:** Total control vs vendor lock-in
- ✅ **Datos propios:** Integrar cualquier fuente vs limitaciones vendor

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Accuracy del Text-to-SQL
**Problema:** SQL generado puede ser incorrecto (columnas wrong, lógica mal)
**Mitigación:**
- Validación SQL antes de ejecutar
- Sandbox queries (timeout, read-only)
- Human-in-the-loop para queries complejas primera vez
- Feedback loop: corregir errores → fine-tune prompts

### Riesgo 2: Costos LLM Variables
**Problema:** Uso alto puede disparar costos ($500+ en mes pico)
**Mitigación:**
- Rate limiting por usuario (10-20 queries/día gratis, luego paid)
- Cache agresivo (60-80% hit rate esperado)
- Usar modelos baratos para queries simples (Haiku)
- Budget alerts en $100, $200, $300

### Riesgo 3: Dependencia de APIs Externas
**Problema:** API de inflación caída → sistema no funciona
**Mitigación:**
- Caché local de datos históricos (90 días)
- Fallback a fuentes alternativas
- Degradación graceful (usar datos desactualizados con advertencia)

### Riesgo 4: Privacidad/Seguridad
**Problema:** Datos sensibles expuestos en chat logs
**Mitigación:**
- Anonimización antes de enviar a LLM (si hay datos de socios)
- Logs locales (no enviar a OpenAI/Anthropic si sensible)
- Self-hosted LLM para datos ultra-sensibles (costo +$500-1K/mes)

---

## ✅ Recomendación Final

**SÍ, 100% factible y es el enfoque correcto para el use case que describís.**

### Por qué es la solución ideal:
1. **Alineado con necesidades reales**: Ad-hoc exploration vs reportes fijos
2. **Alto valor percibido**: "Magia" de IA conversacional impresiona
3. **Escalable**: Empezar con 5 datasets, crecer a 50+ sin cambiar arquitectura
4. **Diferenciador**: Pocas cámaras/asociaciones tienen esto

### Camino recomendado:
1. **Arrancar con MVP en 6-8 semanas** (Fase 1)
2. **Demostrar valor rápido**: 10-15 preguntas clave funcionando
3. **Iterar basado en uso real**: Ver qué preguntan más, mejorar eso
4. **Escalar a producción** (Fase 2) solo si se valida

### Inversión total Año 1:
- **Setup:** $500-800
- **Operación:** $660-2,160/año ($55-180/mes promedio)
- **Total:** $1,200-3,000 (vs $2,400-4,800 soluciones enterprise)

### Next steps:
1. ¿Te armo un demo/prototype en 1-2 días con tus archivos Excel?
2. Defino las 10 preguntas prioritarias que quieren poder responder
3. Identifico qué APIs externas necesitamos integrar
4. Estimamos esfuerzo específico según recursos disponibles

---

**TL;DR:**
Tu visión de "ChatGPT para datos de Fintech" es 100% el camino. Cambia la arquitectura de "BI tradicional" a "Analista IA Conversacional". Costo similar (~$1-3K/año), pero valor 10x mayor para uso ad-hoc exploratorio. Stack: DuckDB + Claude/GPT-4 + Vanna.ai + Plotly + APIs macro. Factible en 6-8 semanas para MVP.
