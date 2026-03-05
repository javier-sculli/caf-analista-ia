# 🏦 PROYECTO DATA & ANALYTICS - CÁMARA ARGENTINA DE FINTECH

**Diagnóstico Inicial y Recomendaciones Arquitectónicas**

---

## 📊 1. DIAGNÓSTICO INICIAL

### 1.1 Inventario de Datos Actual

**Volumen:**
- 11 archivos Excel (.xlsx/.xls)
- Tamaño total: ~2.1 MB
- Datos limpios estimados: 10-20 MB
- **Conclusión: Volumen bajo** - órdenes de magnitud por debajo de requerir soluciones de "big data"

**Fuentes Identificadas:**
- BCRA (Banco Central de la República Argentina) - 100% de los archivos analizados
- Informes regulatorios estandarizados
- Alta confiabilidad institucional

**Categorías de Datos:**

| Categoría | Archivos | Descripción |
|-----------|----------|-------------|
| **Inclusión Financiera** | 2 | Tenencia de cuentas, cobertura poblacional |
| **Crédito** | 2 | Deudores por edad, tipo de asistencia |
| **Medios de Pago** | 5 | Transferencias, extracciones, operaciones electrónicas |
| **Préstamos & Depósitos** | 1 | Sector privado no financiero |
| **Pagos Minoristas** | 1 | Series históricas de cheques, transferencias, tarjetas |

### 1.2 Características de los Datos

**Temporalidad:**
- ✅ Series temporales mensuales
- ✅ Histórico desde ~2017 (8+ años de historia)
- ✅ Actualización mensual aparente
- ⚠️ Algunos archivos son "snapshots" puntuales (ej: junio 2025)

**Granularidad:**
- ✅ Nacional (agregado país)
- ✅ Segmentaciones: edad, tipo de entidad, producto
- ❌ **NO HAY** granularidad provincial/regional en muestra actual
- ❌ **NO HAY** datos individuales (todo agregado)

**Estructura:**
- ⚠️ **Formato "reporte"** - diseñado para lectura humana, no para análisis
- ⚠️ Múltiples filas de encabezado/metadata (1-25 filas según archivo)
- ⚠️ Múltiples hojas por archivo (hasta 49 hojas en Inclusión Financiera)
- ⚠️ Columnas "Unnamed", valores nulos estructurales
- ⚠️ Formatos inconsistentes entre archivos

**Calidad:**
- ✅ Alta confiabilidad (fuente oficial BCRA)
- ✅ Completitud aparentemente buena en datos numéricos
- ⚠️ Requiere limpieza significativa por formato de reporte
- ⚠️ Falta documentación de metadatos (códigos, definiciones)

### 1.3 Problemas Identificados

**🔴 CRÍTICOS:**
1. **Formato no analítico**: Archivos diseñados para informes, no para consumo programático
2. **Falta de normalización**: Cada archivo tiene estructura diferente
3. **Ausencia de catálogo de datos**: No hay diccionario de datos/metadatos
4. **Proceso manual**: Aparentemente se descargan archivos manualmente

**🟡 IMPORTANTES:**
5. **Sin granularidad geográfica**: Limita análisis regional/provincial
6. **Hojas múltiples sin estándar**: Dificulta automatización
7. **Nomenclatura inconsistente**: Columnas sin nombres estándar
8. **Ausencia de IDs**: No hay claves únicas para joins

**🟢 MENORES:**
9. **Volumen pequeño**: Pero puede crecer con nuevas fuentes
10. **Formatos mixtos**: .xls y .xlsx

---

## 🏗️ 2. COMPARACIÓN DE ALTERNATIVAS ARQUITECTÓNICAS

### Opción A: Data Warehouse Tradicional (Snowflake/BigQuery)

**Descripción:**
Plataforma cloud moderna de DW con separación compute/storage.

**✅ PROS:**
- SQL estándar - curva de aprendizaje baja
- Excelente para BI/dashboards
- Escalable linealmente
- Ecosistema maduro de herramientas (dbt, Looker, Tableau)
- Manejo automático de optimizaciones
- Gobernanza y seguridad enterprise

**❌ CONTRAS:**
- **Costos variables difíciles de predecir** para organización sin fines de lucro
- Vendor lock-in (especialmente Snowflake)
- Overkill para volumen actual (<20MB limpios)
- Requiere expertise para optimización de costos
- Costos mínimos mensuales (~$40-200/mes incluso con poco uso)

**💰 Costos Estimados:**
- Snowflake: $2-3 USD por TB-mes storage + $2-4/crédito compute (mínimo ~$40-80/mes)
- BigQuery: $0.02/GB storage + $5/TB queries (~$25-50/mes uso liviano)

**🔧 Complejidad:** Media
- Setup: 2-3 días
- Integración: 1-2 semanas
- Mantenimiento: 2-4 hrs/mes

**📈 Escalabilidad:** Excelente (hasta petabytes)

**✅ Fit para CAF:** 6/10 - Muy buena plataforma pero cara para volumen actual

---

### Opción B: Data Lake / Lakehouse (Delta Lake + Databricks/Open Source)

**Descripción:**
Almacenamiento de archivos (Parquet/Delta) con capa de query engine.

**✅ PROS:**
- Flexibilidad máxima - cualquier tipo de dato
- Ideal para ML/AI futuro
- Open source (Delta Lake sobre Parquet)
- Almacenamiento muy barato (S3/GCS: $0.023/GB-mes)
- Soporta datos estructurados y no estructurados

**❌ CONTRAS:**
- **Curva de aprendizaje empinada** (Spark, Delta Lake)
- Requiere más expertise técnico
- Tooling menos maduro para BI tradicional
- Overkill para datos tabulares simples
- Databricks puede ser costoso ($0.15-0.40/DBU)

**💰 Costos Estimados:**
- Databricks: ~$100-300/mes (community edition gratis pero limitada)
- Open source (Delta + DuckDB/Trino): ~$10-20/mes (solo storage S3)

**🔧 Complejidad:** Alta
- Setup: 1-2 semanas
- Integración: 3-4 semanas
- Mantenimiento: 4-8 hrs/mes

**📈 Escalabilidad:** Excelente (hasta exabytes teóricamente)

**✅ Fit para CAF:** 5/10 - Demasiado complejo para volumen/use cases actuales

---

### Opción C: **RECOMENDADO** - Modern Lakehouse Ligero (DuckDB + dbt + Evidence/Metabase)

**Descripción:**
Stack moderno, open source, optimizado para datasets medianos. DuckDB como motor analítico in-process, dbt para transformaciones, herramienta de BI liviana.

**✅ PROS:**
- **Zero/low cost** - completamente open source
- Extremadamente rápido para datasets <100GB
- No requiere servidor (embedded database)
- SQL estándar ANSI
- Excelente integración con Python/R
- dbt para versionado de transformaciones
- Puede escalar a GB/pequeños TB
- Deployment simple (puede correr en laptop)
- Exporta a Parquet (portabilidad futura)

**❌ CONTRAS:**
- Menos conocido (curva de adopción)
- No es "enterprise" (sin soporte comercial out-of-box)
- Requiere orchestration manual (Airflow/Dagster/Prefect)
- Menos herramientas de gobernanza pre-built
- Single-node (no distribuido)

**💰 Costos Estimados:**
- DuckDB: $0 (open source)
- dbt Core: $0 (open source)
- Evidence.dev/Metabase: $0 (self-hosted) o $20-50/mes (cloud)
- Hosting: $10-30/mes (VPS simple) o $0 (GitHub Actions + S3)
- **TOTAL: $10-80/mes**

**🔧 Complejidad:** Media-Baja
- Setup: 3-5 días
- Integración: 1-2 semanas
- Mantenimiento: 2-3 hrs/mes (después de setup)

**📈 Escalabilidad:** Buena (hasta ~100-200GB, luego migrar a DW distribuido)

**✅ Fit para CAF:** 9/10 - Óptimo para volumen actual, crecimiento futuro, y presupuesto NPO

---

### Opción D: Híbrido - PostgreSQL + dbt + BI Tool

**Descripción:**
PostgreSQL como DW, dbt para transformaciones, Metabase/Superset para BI.

**✅ PROS:**
- Stack conocido y probado
- Ecosistema maduro
- Fácil encontrar talento
- Costos predecibles
- Puede usar managed services (AWS RDS, etc.)

**❌ CONTRAS:**
- Performance limitado vs DuckDB/DW especializados
- Requiere tuning de índices/particiones
- No optimizado para analytics (OLTP focus)
- Costos de RDS managed (mínimo ~$30-50/mes)

**💰 Costos Estimados:**
- PostgreSQL managed (RDS t3.small): ~$30-50/mes
- O self-hosted: $10-20/mes VPS
- dbt + Metabase: $0
- **TOTAL: $10-70/mes**

**🔧 Complejidad:** Media
- Setup: 2-4 días
- Integración: 1-2 semanas
- Mantenimiento: 3-4 hrs/mes

**📈 Escalabilidad:** Moderada (hasta ~500GB-1TB con tuning)

**✅ Fit para CAF:** 7/10 - Sólida opción conservadora

---

## 🎯 3. RECOMENDACIÓN PRINCIPAL

### **Arquitectura Recomendada: Modern Lakehouse Ligero**

**Stack Tecnológico:**

```
┌─────────────────────────────────────────────────────────────┐
│                      CAPA DE CONSUMO                        │
│  • Evidence.dev (dashboards-as-code)                        │
│  • Metabase (exploración ad-hoc)                            │
│  • Jupyter/Observable (análisis avanzado)                   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE TRANSFORMACIÓN                     │
│  • dbt Core (SQL transformations)                           │
│  • Git para versionado                                      │
│  • Tests de calidad integrados                              │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE PROCESAMIENTO                      │
│  • DuckDB (query engine)                                    │
│  • Python pandas (limpieza inicial)                         │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE INGESTA                          │
│  • Python scripts (extracción de Excel)                     │
│  • Prefect/Airflow (orchestration - opcional fase 2)       │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE STORAGE                           │
│  • Raw: S3/GCS (archivos Excel originales)                  │
│  • Staging: Parquet files                                   │
│  • Analytics: DuckDB database files                         │
└─────────────────────────────────────────────────────────────┘
```

### **Justificación:**

**1. Adecuación al Contexto:**
- ✅ Presupuesto NPO: Costos operativos <$50/mes
- ✅ Volumen actual: DuckDB maneja <100GB con excelente performance
- ✅ Skill level: SQL estándar - accesible para equipo con habilidades básicas
- ✅ Autonomía: No dependencia de vendors, 100% portable

**2. Capacidades Técnicas:**
- ✅ Performance: DuckDB es más rápido que Postgres para analytics, comparable a Snowflake en datasets medianos
- ✅ SQL estándar: Transición fácil a BigQuery/Snowflake si escala
- ✅ Versionado: dbt permite version control de toda la lógica
- ✅ Testing: dbt tests para calidad de datos

**3. Evolución Futura:**
- ✅ **Camino de migración claro**: Parquet files → fácil cargar en Snowflake/BigQuery
- ✅ **IA/ML ready**: DuckDB se integra perfectamente con Python, pandas, scikit-learn
- ✅ **Escalabilidad**: Cuando supere ~50GB, migrar a cloud DW es straightforward

**4. Trade-offs Aceptables:**
- ⚠️ No es "enterprise" - pero CAF no necesita enterprise features ahora
- ⚠️ Requiere setup inicial - inversión de 1-2 semanas vs servicios managed
- ⚠️ Single-node - pero 100% suficiente para 5-10 años con volumen proyectado

---

## 🗺️ 4. ROADMAP INCREMENTAL

### **FASE 1: Quick Wins (4-6 semanas) - "Valor Inmediato"**

**Objetivo:** Generar primeros insights sin infraestructura compleja

**Entregables:**
1. **Pipeline de Ingesta Básico**
   - Scripts Python para parsear Excel → Parquet
   - Validación de calidad básica
   - Storage en S3/GCS (o local si presupuesto $0)

2. **Data Mart Inicial**
   - DuckDB database con tablas limpias
   - 3-4 tablas core: medios_pago, inclusion_financiera, credito
   - Documentación de columnas

3. **Dashboard MVP**
   - 5-7 métricas clave del ecosistema
   - Herramienta: Evidence.dev (dashboards-as-code, gratis)
   - KPIs: adopción medios de pago, inclusión financiera, crédito

4. **Informe Mensual Automatizado**
   - Template de reporte para socios
   - Generación automática vía Jupyter Notebook
   - Distribución por email

**Esfuerzo Estimado:** 80-120 horas (1 data engineer part-time)

**Costos:** $10-30/mes (storage)

**Valor Generado:**
- ✅ Primeros dashboards operativos
- ✅ Demostración de valor a stakeholders
- ✅ Reducción de trabajo manual en 60-80%

---

### **FASE 2: Consolidación (8-12 semanas) - "Fundación Sólida"**

**Objetivo:** Escalabilizar y profesionalizar la plataforma

**Entregables:**
1. **dbt Project**
   - Modelos de transformación versionados
   - Tests de calidad de datos (nulls, uniqueness, ranges)
   - Documentación auto-generada
   - Lineage de datos

2. **Orchestration**
   - Prefect/Airflow para automatización
   - Scheduling mensual (alineado con publicación BCRA)
   - Alertas ante fallos
   - Retry logic

3. **Ampliación de Fuentes**
   - Integrar datos de socios (voluntario, anonimizado)
   - APIs de BCRA (si disponibles)
   - Datos complementarios (macro, regulatorios)

4. **BI Self-Service**
   - Metabase para exploración ad-hoc
   - Semantic layer (métricas estándar)
   - Permisos por rol

5. **Data Governance Básico**
   - Catálogo de datos
   - Diccionario de términos
   - Políticas de privacidad/anonimización

**Esfuerzo Estimado:** 200-300 horas

**Costos:** $30-80/mes (storage + compute + BI tool)

**Valor Generado:**
- ✅ Plataforma auto-sostenible
- ✅ Calidad de datos garantizada
- ✅ Socios pueden explorar datos directamente
- ✅ Preparado para escalar

---

### **FASE 3: Analytics Avanzado & IA (12-24 semanas) - "Diferenciación"**

**Objetivo:** Generar insights únicos con IA/ML

**Entregables:**
1. **Benchmarking Inteligente**
   - Clusters de empresas similares (K-means, DBSCAN)
   - Métricas comparativas ajustadas por segmento
   - Detección de outliers

2. **Forecasting**
   - Predicción de tendencias (medios de pago, inclusión)
   - Modelos de series temporales (Prophet, ARIMA)
   - Análisis de estacionalidad

3. **NLP para Regulaciones**
   - Scraping de normativas BCRA/CNV
   - Clasificación de impacto en socios
   - Alertas proactivas

4. **Asistente de Datos (ChatBot)**
   - RAG sobre catálogo de datos
   - Queries en lenguaje natural → SQL
   - Powered by Claude/GPT-4

5. **Data Products**
   - APIs para socios (rate-limited)
   - Exports automatizados
   - Notebooks compartidos

**Esfuerzo Estimado:** 300-500 horas

**Costos:** $50-150/mes (+ costos de LLM APIs ~$20-50/mes)

**Valor Generado:**
- ✅ Diferenciación competitiva para CAF
- ✅ Valor tangible único para socios
- ✅ Posicionamiento como líder de pensamiento

---

## 📈 5. CASOS DE USO PRIORITARIOS

### **Tier 1: Implementar en Fase 1 (Máximo Impacto)**

#### 1. Dashboard Ejecutivo CAF
**Audiencia:** Directorio/Management CAF
**Métricas:**
- Evolución de inclusión financiera (% población bancarizada)
- Adopción de medios de pago electrónicos (YoY growth)
- Volumen de crédito fintech vs tradicional
- Tendencias regulatorias (cantidad de normas por trimestre)

**Valor:** Visibilidad estratégica para toma de decisiones

#### 2. Reporte Mensual del Ecosistema
**Audiencia:** Socios CAF
**Contenido:**
- Top 5 insights del mes
- Cambios regulatorios relevantes
- Benchmarks sectoriales
- Oportunidades identificadas

**Valor:** Mantener a socios informados, justificar membresía

#### 3. Benchmarking de Inclusión Financiera
**Audiencia:** Policy makers, medios, público
**Análisis:**
- Comparación Argentina vs LATAM
- Brechas por segmento (edad, geografía)
- Progreso vs metas nacionales

**Valor:** Posicionar a CAF como referente, influir política pública

---

### **Tier 2: Implementar en Fase 2 (Alto Impacto)**

#### 4. Análisis de Brechas Regionales
**Audiencia:** Socios con presencia regional
**Análisis:**
- Penetración por provincia
- Oportunidades de crecimiento geográfico
- Correlación con variables socioeconómicas

**Valor:** Guiar expansión territorial de socios

**⚠️ NOTA:** Requiere incorporar datos provinciales (no en muestra actual)

#### 5. Monitor de Competencia
**Audiencia:** Socios
**Análisis:**
- Share de mercado por vertical (lending, payments, etc.)
- Velocidad de crecimiento por player
- Análisis de nuevos entrantes

**Valor:** Inteligencia competitiva

**⚠️ NOTA:** Requiere datos de socios o fuentes complementarias

#### 6. Calculadora de ROI de Digitalización
**Audiencia:** Socios tradicionales digitalizándose
**Funcionalidad:**
- Input: tamaño empresa, sector, % digital actual
- Output: costos estimados, ahorro proyectado, timeline

**Valor:** Herramienta de venta para soluciones fintech

---

### **Tier 3: Implementar en Fase 3 (Diferenciación)**

#### 7. Predictor de Tendencias
**Audiencia:** Socios, inversionistas
**Modelo:**
- Forecast de adopción de medios de pago a 12 meses
- Predicción de cambios regulatorios (basado en patterns)
- Identificación de tecnologías emergentes

**Valor:** Ventaja informativa para planificación estratégica

#### 8. Generador de Insights con IA
**Audiencia:** Interna CAF
**Funcionalidad:**
- Análisis automático de nuevos datasets
- Detección de anomalías
- Sugerencia de narrativas para prensa

**Valor:** Escalar capacidad analítica sin aumentar headcount

---

## ❓ 6. PREGUNTAS CRÍTICAS PARA EL CLIENTE

### **Estrategia y Gobernanza**

1. **Audiencias prioritarias:** ¿Cuál es la audiencia #1 para esta plataforma?
   - a) Equipo interno CAF
   - b) Socios (empresas miembro)
   - c) Policy makers / reguladores
   - d) Público / medios

2. **Datos de socios:** ¿Están dispuestos los socios a compartir datos (anonimizados) para enriquecer el análisis?
   - Si sí → alto valor, requiere gobernanza estricta
   - Si no → limitados a datos públicos

3. **Ownership:** ¿Quién será el data owner interno? ¿Hay alguien con skills SQL/Python o necesitamos capacitar?

### **Presupuesto y Recursos**

4. **Presupuesto anual:** ¿Cuál es el budget disponible para tecnología?
   - <$5K/año → Solo open source
   - $5-20K/año → Open source + herramientas managed
   - >$20K/año → Considerar Snowflake/Databricks

5. **Headcount:** ¿Hay capacidad de contratar 1 data engineer/analyst full-time o trabajamos con partners/freelance?

6. **Infraestructura:** ¿Tienen preferencias de cloud (AWS/GCP/Azure) o restricciones (ej: datos no pueden salir de Argentina)?

### **Alcance y Prioridades**

7. **Frecuencia:** ¿Necesitan updates diarios, semanales o mensuales?
   - Mensuales → alineado con BCRA, más fácil
   - Semanales/diarios → requiere fuentes adicionales

8. **Horizontes temporales:** ¿Qué es más importante: análisis histórico (trends) o predicción (forecast)?

9. **Casos de uso:** De los propuestos en sección 5, ¿cuáles son los 3 más valiosos? Esto guía priorización.

### **Técnico**

10. **Fuentes adicionales:** ¿Qué otras fuentes de datos tienen acceso? (Ej: CNV, AFIP, INDEC, datos internacionales)

11. **Seguridad:** ¿Qué nivel de sensibilidad tienen los datos? ¿Requieren compliance específico (ej: GDPR, leyes locales)?

---

## 📋 7. PRÓXIMOS PASOS SUGERIDOS

### **Inmediato (esta semana):**
1. ✅ Revisar este documento con stakeholders clave
2. ✅ Responder preguntas críticas (sección 6)
3. ✅ Validar casos de uso prioritarios
4. ✅ Definir presupuesto preliminar

### **Corto plazo (próximas 2 semanas):**
5. ⏳ Aprobar arquitectura recomendada
6. ⏳ Definir equipo del proyecto (interno + eventual partner)
7. ⏳ Setup de repositorio Git + ambiente de desarrollo
8. ⏳ Kickoff de Fase 1

### **Mediano plazo (1-2 meses):**
9. ⏳ Desarrollo de pipeline MVP (Fase 1)
10. ⏳ Primer dashboard funcional
11. ⏳ Presentación a socios (demostración de valor)
12. ⏳ Planificación detallada de Fase 2

---

## 📚 ANEXOS

### A. Comparación de Costos (Primeros 12 Meses)

| Alternativa | Setup | Mensual | Anual Total | Notas |
|-------------|-------|---------|-------------|-------|
| **DuckDB Stack (recomendado)** | $0 | $30-50 | **$360-600** | Open source + hosting |
| PostgreSQL + dbt | $0 | $40-70 | $480-840 | Managed Postgres |
| BigQuery | $0 | $25-80 | $300-960 | Variable según queries |
| Snowflake | $0 | $80-200 | $960-2,400 | Costos mínimos altos |
| Databricks | $0 | $150-400 | $1,800-4,800 | ML-focused, caro |

### B. Skills Requeridos por Alternativa

| Skill | DuckDB | PostgreSQL | BigQuery | Snowflake |
|-------|--------|------------|----------|-----------|
| SQL | ✅ Básico | ✅ Básico | ✅ Básico | ✅ Básico |
| Python | ✅ Medio | ⚠️ Básico | ⚠️ Básico | ⚠️ Básico |
| Cloud | ⚠️ Básico | ⚠️ Básico | ✅ Medio | ✅ Medio |
| dbt | ✅ Medio | ✅ Medio | ✅ Medio | ✅ Medio |
| DevOps | ⚠️ Básico | ✅ Medio | ⚠️ Básico | ⚠️ Básico |

✅ = Requerido | ⚠️ = Opcional pero útil

### C. Referencias Técnicas

**DuckDB:**
- Web: https://duckdb.org
- Why DuckDB: https://duckdb.org/why_duckdb.html
- Benchmarks: https://duckdblabs.github.io/db-benchmark/

**dbt (Data Build Tool):**
- Web: https://www.getdbt.com
- dbt Core (open source): https://github.com/dbt-labs/dbt-core
- Guía: https://docs.getdbt.com/docs/introduction

**Evidence.dev:**
- Web: https://evidence.dev
- Ejemplos: https://evidence.dev/examples

**Metabase:**
- Web: https://www.metabase.com
- Open source: https://github.com/metabase/metabase

---

**Documento preparado por:** AI Data Architect
**Fecha:** 2026-02-09
**Versión:** 1.0
**Contacto:** [Completar con info de contacto]
