# ⚡ Quick Start - Demo en 5 Minutos

## 🚀 Pasos para ejecutar el demo

### 1. Configurar API Key (2 min)

```bash
cd /Users/javiersculli/dev/caf/demo

# Copiar template
cp .env.example .env

# Editar .env y agregar tu API key de Anthropic:
# ANTHROPIC_API_KEY=sk-ant-api03-...
```

**Obtener API key:** https://console.anthropic.com/

---

### 2. Ejecutar Setup (2 min)

```bash
cd /Users/javiersculli/dev/caf
python demo/setup.py
```

Esto:
- ✅ Instala dependencias
- ✅ Limpia datos Excel → Parquet
- ✅ Carga a DuckDB
- ✅ Valida todo

**Output esperado:**
```
🎉 SETUP COMPLETADO EXITOSAMENTE
✅ Base de datos DuckDB: 245.3 KB
✅ Catálogo de datos YAML: 12.1 KB
```

---

### 3. Lanzar Chat UI (1 min)

```bash
streamlit run demo/ui/chat_app.py
```

Abre automáticamente en: `http://localhost:8501`

---

### 4. Probar Preguntas de Ejemplo

En la interfaz web, prueba estas preguntas:

1. **"Compará el crecimiento de transferencias inmediatas vs inflación en los últimos 2 años"**
   → Gráfico dual-axis, cruza datos internos + API inflación

2. **"¿Qué porcentaje de adultos tiene cuentas bancarias vs billeteras digitales?"**
   → Comparación de inclusión tradicional vs digital

3. **"Mostrame la evolución de cheques vs transferencias electrónicas"**
   → Declive de medios tradicionales vs crecimiento digital

4. **"¿Cuál es el crecimiento real (deflactado) de los medios de pago electrónicos?"**
   → Crecimiento ajustado por inflación

5. **"Compará el volumen de pagos electrónicos en los últimos 12 meses"**
   → Análisis reciente de tendencias

---

## 🔍 Ver Logs Verbose

En la terminal donde corriste `streamlit run`, verás logs detallados:

```
14:23:45 | INFO | LLM_ORCHESTRATION | 🚀 NUEVA CONSULTA
14:23:46 | INFO | SEMANTIC_LAYER    | 📋 Generando contexto del catálogo
14:23:47 | INFO | QUERY_PLANNING    | 🧠 FASE 1: Query Planning
14:23:48 | INFO | SQL_GENERATION    | 💻 FASE 2: SQL Generation
14:23:49 | INFO | API_FETCHING      | 🌐 FASE 4: Fetching inflación
14:23:50 | INFO | VISUALIZATION     | 🎨 Generando gráfico
```

**Cada capa del sistema está loggeada con color y timestamp.**

---

## 🧪 Test Automatizado (Opcional)

Para validar las 5 preguntas sin UI:

```bash
python demo/test_5_questions.py
```

Genera gráficos en `demo/test_outputs/`

---

## ⚠️ Troubleshooting

**Problema:** "ANTHROPIC_API_KEY no configurada"
→ Editar `demo/.env` y agregar la key

**Problema:** "Database no encontrada"
→ Ejecutar `python demo/setup.py`

**Problema:** "ModuleNotFoundError"
→ Ejecutar `pip install -r demo/requirements.txt`

---

## 📚 Más Info

Ver **[README.md](README.md)** completo para:
- Arquitectura detallada
- Explicación de componentes
- Roadmap a producción
- Costos estimados

---

**¿Listo? → `streamlit run demo/ui/chat_app.py` 🚀**
