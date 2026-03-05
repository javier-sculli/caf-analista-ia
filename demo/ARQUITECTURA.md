# Arquitectura del Sistema - CAF Analytics Demo

## Vista de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USUARIO FINAL                                 │
│                  (Analista de Cámara de Fintech)                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Pregunta en lenguaje natural
                             │ "¿Cuál es el crecimiento de
                             │  transferencias vs inflación?"
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INTERFAZ WEB (Streamlit)                        │
│                                                                     │
│  • Barra lateral con ejemplos predefinidos                         │
│  • Campo de texto para preguntas personalizadas                    │
│  • Panel principal para mostrar gráficos                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Envía pregunta
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  MOTOR DE CONSULTAS INTELIGENTE                     │
│                                                                     │
│  ┌─────────────────┐   ┌──────────────────┐   ┌────────────────┐  │
│  │ Claude AI       │   │ Catálogo de      │   │ Base de Datos  │  │
│  │ (Análisis)      │──▶│ Datos Semántico  │──▶│ (DuckDB)       │  │
│  │                 │   │                  │   │                │  │
│  │ • Interpreta    │   │ • Define tablas  │   │ • Transferencias│  │
│  │   la pregunta   │   │ • Define métricas│   │ • Cheques      │  │
│  │ • Decide qué    │   │ • Reglas de      │   │ • Inclusión    │  │
│  │   datos usar    │   │   cálculo        │   │   financiera   │  │
│  │ • Genera plan   │   │                  │   │                │  │
│  └─────────────────┘   └──────────────────┘   └────────────────┘  │
│                                                                     │
│  Resultado: Tabla con datos relevantes                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Tabla de datos
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 GENERADOR DE GRÁFICOS AUTOMÁTICO                    │
│                                                                     │
│  ┌─────────────────┐                    ┌──────────────────┐       │
│  │ Claude AI       │                    │ Plotly           │       │
│  │ (Visualización) │───────────────────▶│ (Motor gráfico)  │       │
│  │                 │                    │                  │       │
│  │ • Analiza datos │                    │ • Líneas         │       │
│  │ • Selecciona    │                    │ • Barras         │       │
│  │   tipo de       │                    │ • Doble eje      │       │
│  │   gráfico       │                    │ • Interactivos   │       │
│  │ • Elige colores │                    │                  │       │
│  └─────────────────┘                    └──────────────────┘       │
│                                                                     │
│  Resultado: Gráfico interactivo HTML                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Gráfico renderizado
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INTERFAZ WEB (Streamlit)                        │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                                                            │    │
│  │        📊 Gráfico Interactivo                             │    │
│  │                                                            │    │
│  │    • Usuario puede hacer zoom                             │    │
│  │    • Ver valores al pasar el mouse                        │    │
│  │    • Exportar como imagen                                 │    │
│  │                                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ¿Cómo Funciona?

### 1. El Usuario Hace una Pregunta
El analista escribe su pregunta en lenguaje natural, tal como hablaría con un colega:
- "¿Cómo evolucionaron las transferencias vs la inflación en los últimos 2 años?"
- "¿Qué porcentaje de adultos tiene cuentas bancarias?"
- "Comparame cheques y transferencias"

### 2. Sistema Inteligente Interpreta y Busca Datos
El sistema utiliza **Claude AI** (inteligencia artificial de Anthropic) para:
- Entender lo que el usuario está preguntando
- Decidir qué datos necesita de la base de datos
- Traer solo la información relevante
- Calcular métricas si es necesario (ej: crecimiento año contra año)

**¿Qué datos tiene el sistema?**
- Transferencias inmediatas (monto, cantidad, crecimiento)
- Cheques compensados
- Inflación argentina (INDEC)
- Inclusión financiera (cuentas bancarias vs billeteras digitales)

### 3. Generación Automática del Gráfico
Una vez obtenidos los datos, el sistema:
- Analiza qué tipo de visualización es más apropiada
- Selecciona automáticamente las columnas correctas
- Genera un gráfico profesional e interactivo
- Aplica colores y formato consistente

### 4. Usuario Interactúa con el Resultado
El analista ve el gráfico en su navegador y puede:
- Hacer zoom para ver períodos específicos
- Pasar el mouse para ver valores exactos
- Comparar múltiples métricas
- Exportar el gráfico como imagen

---

## Ventajas de Esta Arquitectura

### Para el Usuario Final
✅ **Sin código**: No necesita saber programación ni SQL
✅ **Lenguaje natural**: Pregunta como hablaría normalmente
✅ **Rápido**: Respuestas en segundos, no horas
✅ **Flexible**: No limitado a reportes predefinidos
✅ **Interactivo**: Gráficos dinámicos que se pueden explorar

### Para la Organización
✅ **Escalable**: Fácil agregar nuevas fuentes de datos
✅ **Mantenible**: Un solo catálogo define todas las métricas
✅ **Auditable**: Cada consulta queda registrada con su lógica
✅ **Consistente**: Todos usan las mismas definiciones de métricas
✅ **Actualizable**: Los datos nuevos se reflejan automáticamente

---

## Componentes Técnicos Clave

### Claude AI (Anthropic)
Motor de inteligencia artificial que interpreta preguntas, genera planes de análisis, y selecciona visualizaciones apropiadas.

### DuckDB
Base de datos analítica ultra-rápida que almacena y procesa los datos financieros.

### Catálogo Semántico
Documento que define todas las tablas, columnas, métricas y reglas de negocio en un solo lugar.

### Streamlit
Framework web que crea la interfaz visual sin necesidad de código frontend complejo.

### Plotly
Biblioteca de gráficos interactivos de nivel profesional.

---

## Flujo de una Consulta Típica

```
Pregunta: "Crecimiento de transferencias vs inflación últimos 2 años"
         ↓
Step 1: Claude AI interpreta
        • Necesito: transferencias (monto)
        • Necesito: inflación (mensual)
        • Período: 24 meses
        • Cálculo: YoY % (año contra año)
         ↓
Step 2: Busca en base de datos
        • Trae 36 meses de transferencias (24 + 12 para calcular YoY)
        • Trae 36 meses de inflación
        • Une ambas tablas por fecha
         ↓
Step 3: Procesa los datos
        • Calcula crecimiento YoY
        • Filtra a últimos 24 meses
        • Formatea fechas
         ↓
Step 4: Claude AI selecciona visualización
        • Tipo: Gráfico de líneas doble eje
        • Eje izquierdo: Transferencias (%)
        • Eje derecho: Inflación (%)
        • Ambas líneas superpuestas para comparar
         ↓
Step 5: Genera gráfico
        • Plotly crea HTML interactivo
        • Aplica colores corporativos
        • Agrega tooltips con valores
         ↓
Resultado: Gráfico listo en 3-5 segundos
```

---

## Preguntas Frecuentes

**¿Qué pasa si el usuario hace una pregunta que no se puede responder?**
El sistema le indica qué datos no están disponibles y sugiere preguntas similares que sí puede responder.

**¿Se pueden agregar nuevas fuentes de datos?**
Sí, solo se actualiza el catálogo semántico y se cargan los datos. No requiere cambios en el código.

**¿Los gráficos se pueden personalizar?**
Los colores y estilos son consistentes automáticamente, pero se pueden ajustar en la configuración.

**¿Se pueden guardar los análisis?**
Los gráficos se pueden exportar como imágenes PNG. En una versión futura se podrían guardar "consultas favoritas".

**¿Qué tan preciso es el sistema?**
Todos los cálculos están validados con tests automatizados que verifican la corrección matemática (YoY, deflación, etc).

---

## Contacto

Para consultas técnicas o sugerencias de mejora, contactar al equipo de desarrollo.
