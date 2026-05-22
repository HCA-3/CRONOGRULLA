# 📋 DOCUMENTACIÓN TÉCNICA — CronoGrulla
**Sistema de Ingeniería de Métodos y Estudio de Tiempos**  
Versión: 1.0 | Fecha: Abril 2026 | Universidad Católica

---

## 1. DESCRIPCIÓN GENERAL

**CronoGrulla** es una aplicación de escritorio desarrollada en Python orientada al estudio de tiempos y movimientos en procesos de manufactura de origami (grullas de papel). Combina cronometría industrial, análisis ergonómico mediante visión artificial (MediaPipe), gestión de operarios, y generación de reportes PDF bajo metodologías de ingeniería de métodos (Maytag, TOC, Therbligs).

### Tecnologías utilizadas

| Librería | Uso |
|---|---|
| `customtkinter` | Interfaz gráfica moderna (modo oscuro) |
| `opencv-python` | Captura y procesamiento de video |
| `mediapipe` | Detección de pose y manos (IA) |
| `numpy` | Cálculos estadísticos |
| `matplotlib` | Gráficas de rendimiento |
| `fpdf` | Generación de reportes PDF |
| `Pillow` | Manejo de imágenes |
| `pandas` | Exportación a Excel |
| `qrcode` | Generación de QR en reportes |

---

## 2. ESTRUCTURA DEL PROYECTO

```
ingenieria de metodos/
├── main.py                  # Punto de entrada, clase principal CraneFlowApp
├── requirements.txt         # Dependencias del proyecto
├── craneflow_data.json      # Base de datos local (JSON)
├── views/                   # Módulos de pantallas
│   ├── view_dashboard.py
│   ├── view_models.py
│   ├── view_operators.py
│   ├── view_timer.py
│   ├── view_tables.py
│   ├── view_stats.py
│   ├── view_media.py
│   ├── view_sensor_data.py
│   ├── view_comparison.py
│   ├── view_standard_time.py
│   ├── view_trash.py
│   └── env_table.py
├── utils/
│   └── pdf_report.py        # Motor de generación PDF
├── media_evidencia/         # Fotos capturadas automáticamente
├── guias_pdf/               # PDFs de modelos subidos
└── Documentacion/           # Esta documentación
```

---

## 3. MÓDULO PRINCIPAL — `main.py`

### Clase: `CraneFlowApp`
Hereda de `ctk.CTk`. Es el controlador principal de la aplicación.

**Atributos clave:**

| Atributo | Tipo | Descripción |
|---|---|---|
| `data` | dict | Datos cargados desde `craneflow_data.json` |
| `data_file` | str | Ruta al archivo de persistencia |
| `models` | dict | Diccionario de modelos de origami registrados |
| `current_model_name` | str | Nombre del modelo activo |
| `operator_data` | list | Lista de nombres de operarios |
| `line_config` | dict | Mapeo tarea → operario |
| `pdf_manager` | PDFManager | Instancia del generador de reportes |
| `DEFAULT_ACTIVITIES` | list | 12 pasos de la Grulla Clásica |

**Métodos principales:**

| Método | Descripción |
|---|---|
| `load_data()` | Carga `craneflow_data.json`; crea estructura vacía si no existe |
| `save_data()` | Serializa y guarda todos los datos al JSON |
| `update_current_model_vars()` | Sincroniza `ACTIVITIES` y `FULL_DESCRIPTIONS` con el modelo activo |
| `change_model_from_menu(name)` | Cambia el modelo activo y redirige al cronómetro |
| `setup_ui()` | Construye la barra lateral y el contenedor principal |
| `toggle_sidebar()` | Muestra/oculta la barra de navegación lateral |
| `show_*()` | Métodos de navegación (uno por cada vista) |

**Flujo de inicio:**
```
__init__ → load_data() → setup_ui() → show_operators_setup() o show_dashboard()
```

---

## 4. VISTAS (views/)

### 4.1 `view_dashboard.py` — Panel de Control

Muestra 3 tarjetas KPI calculadas en tiempo real:
- **Ciclos Completados**: `len(measurements)`
- **Tiempo Promedio**: media de `total_time` de todas las mediciones
- **Operarios Activos**: `len(operator_data)`

También presenta un banner informativo sobre el balanceo de línea.

---

### 4.2 `view_models.py` — Gestión de Modelos de Origami

Permite crear, editar, eliminar y activar modelos de origami personalizados.

**Operaciones:**

| Operación | Método | Descripción |
|---|---|---|
| Crear modelo | `open_steps_editor()` | Abre editor de pasos para nuevo modelo |
| Guardar pasos | `save_new_model(name)` | Valida y persiste el nuevo modelo |
| Editar pasos | `open_edit_steps_editor(model)` | Carga pasos existentes para edición |
| Activar modelo | `activate_model(name)` | Cambia el modelo activo globalmente |
| Eliminar | `delete_model(name)` | No permite eliminar "Grulla Clásica" |
| Subir PDF | `upload_pdf_guide(model)` | Copia PDF al directorio `guias_pdf/` |
| Ver PDF | `open_pdf_guide(model)` | Abre el PDF con el visor del sistema OS |

**Regla de negocio:** El modelo base "Grulla Clásica" no puede ser eliminado.

---

### 4.3 `view_operators.py` — Configuración del Equipo

Configura la cantidad de operarios y distribuye las tareas automáticamente.

**Algoritmo de distribución:**
```python
base = 12 // num_ops      # Tareas base por operario
rem  = 12 % num_ops       # Tareas extra para los primeros operarios
# Los primeros 'rem' operarios reciben (base+1) tareas
```

**Componentes UI:**
- `OptionMenu` para seleccionar número de operarios (1–12)
- Campos de texto para nombres
- Panel derecho con preview de distribución en tiempo real

---

### 4.4 `view_timer.py` — Cronómetro con Sensor de Movimiento ⭐

Este es el módulo más complejo. Integra cronometría, visión artificial y ergonomía.

#### 4.4.1 Clases

**`StudySetupDialog`**: Diálogo de configuración antes de iniciar un estudio.
- Ingreso de meta de grullas
- Lecturas de Luxómetro (lx) y Sonómetro (dB) por rango de tiempo
- Selección de Modo Flujo Balanceado

**`TimerView`**: Vista principal del cronómetro.

#### 4.4.2 Sensor de Movimiento — MediaPipe

El sistema usa **MediaPipe Holistic** para análisis en tiempo real:

```
Cámara → cv2.VideoCapture → MediaPipe Holistic → Análisis → Trigger
```

**Inicialización en hilo separado (`init_mediapipe`):**
```python
mp.solutions.holistic.Holistic(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
```

**Parámetros de cámara (DirectShow / Windows):**
- Resolución: 640×480 px
- Codec: MJPG
- FPS de procesamiento: 25 (ciclo cada 40 ms)

#### 4.4.3 Análisis Ergonómico

Detecta ángulos de codo usando landmarks de pose:

| Articulación | Landmarks (índices MediaPipe) |
|---|---|
| Brazo Derecho | Hombro(12) → Codo(14) → Muñeca(16) |
| Brazo Izquierdo | Hombro(11) → Codo(13) → Muñeca(15) |

**Fórmula del ángulo:**
```python
radians = arctan2(C.y-B.y, C.x-B.x) - arctan2(A.y-B.y, A.x-B.x)
angle = abs(radians * 180 / π)
if angle > 180: angle = 360 - angle
```

Los ángulos se acumulan en `ergo_log` durante cada tarea y se promedian al hacer el trigger.

#### 4.4.4 Detección de Therbligs

Detecta dos micro-movimientos básicos (Therbligs de Gilbreth):

| Therblig | Símbolo | Condición |
|---|---|---|
| **Coger (Grasp)** | G | Distancia pulgar–índice < 0.06 (norm.) |
| **Soltar (Release)** | RL | Distancia pulgar–índice ≥ 0.06 |

```python
d = distancia(landmark[4], landmark[8])  # Pulgar e Índice
```

#### 4.4.5 Sistema de Trigger por Zonas

El frame se divide en N zonas horizontales (una por operario):

```
|  ZONA Op.1  |  ZONA Op.2  |  ZONA Op.3  |
|   x1..x2   |   x1..x2   |   x1..x2   |
|   y1=20    |   y1=20    |   y1=20    |
|   y2=110   |   y2=110   |   y2=110   |
```

**Modo IA (MediaPipe activo):** Activa zona si el tip del dedo índice entra en ella.  
**Modo Fallback (sin IA):** Detecta cambio de píxeles > 10% en la zona.

**Debounce:** 2.5 segundos entre triggers del mismo operario.

#### 4.4.6 Modo Flujo Balanceado

Simula una línea de producción escalonada:
- Solo el Operario 1 inicia activo
- Al terminar su primera grulla, se activa el Operario 2 automáticamente
- Cada operario se activa en cascada
- Se registra `global_lead_time` y tiempos por estación

#### 4.4.7 Estructura de datos de una medición

```json
{
  "model": "Grulla Clásica",
  "lux_data": [{"range": "8:00-10:00", "value": 450}],
  "db_data": [{"range": "8:00-10:00", "value": 62}],
  "is_flow_mode": true,
  "global_lead_time": 185.3,
  "op_station_times": {"Operador 1": 60.2, "Operador 2": 65.1},
  "total_time": 125.4,
  "splits": [
    {
      "duration": 12.5,
      "activity": "Paso 1: Diagonal y mitad",
      "operator": "Operador 1",
      "evidence": "media_evidencia/Evidencia_Op1_G1_P1_1234567.jpg",
      "therblig": "✊ COGER (G)",
      "ergo_summary": {
        "avg_elbow_r": 112.3,
        "avg_elbow_l": 108.7
      }
    }
  ]
}
```

---

### 4.5 `view_tables.py` — Matriz de Tiempos

Muestra la tabla de tiempos por ciclo en formato matricial:

```
| Ciclo | Vol | P1 | P2 | ... | P12 | TOTAL |
```

**Funciones:**
- `update_table_view(model)`: Renderiza tabla filtrada por modelo
- `delete_last_measurement()`: Mueve último ciclo a papelera (no elimina)
- `export_table_excel()`: Exporta tabla a `.xlsx` con pandas

---

### 4.6 `view_stats.py` — Análisis de Rendimiento

Genera un gráfico de barras con **tiempo promedio por tarea** usando matplotlib embebido en Tkinter (`FigureCanvasTkAgg`).

- Selector de modelo (segmented button)
- Cálculo: `avg[i] = sum(splits[i].duration) / count`
- Eje X: Número de tarea (T1–T12)
- Eje Y: Segundos

---

### 4.7 `view_sensor_data.py` — Datos del Sensor de Movimiento

Tabla de resumen ergonómico de todas las mediciones:

| Columna | Fuente |
|---|---|
| Operador | `split.operator` |
| Tarea | `split.activity` |
| Ángulo Codo D. | `ergo_summary.avg_elbow_r` |
| Ángulo Codo I. | `ergo_summary.avg_elbow_l` |
| Therblig | `split.therblig` |
| Evaluación Postural | Calculada en tiempo real |

**Criterios de evaluación postural:**

| Rango (promedio ambos codos) | Estado |
|---|---|
| 80° – 130° | ✅ Óptimo |
| 60° – 150° | ⚠️ Precaución |
| Fuera de rango | 🚨 Riesgo |

---

### 4.8 `view_comparison.py` — Comparativa de Operarios

Compara el rendimiento entre operarios con métricas estadísticas:

| Columna | Cálculo |
|---|---|
| Ciclos (N) | Número de splits del operario |
| T. Promedio | `np.mean(tiempos)` |
| T. Mínimo | `np.min(tiempos)` |
| T. Máximo | `np.max(tiempos)` |
| Eficiencia | `(mejor_avg / avg_operario) × 100` |

**Clasificación de eficiencia:**
- ≥ 90% → ⭐ Excelente
- ≥ 75% → ✅ Óptimo
- < 75% → ⚠️ Mejorable

---

### 4.9 `view_standard_time.py` — Tiempo Estándar

Implementa la metodología de estudio de tiempos con factores de calificación y suplementos.

**Fórmulas:**
```
Tiempo Normal  (TN) = Promedio × (Calificación / 100)
Tiempo Estándar(TS) = TN × (1 + Suplementos / 100)
```

**Tabla resultante por tarea:**

| Campo | Descripción |
|---|---|
| N | Número de observaciones |
| Avg (X̄) | Tiempo promedio observado |
| Rango (R) | Max − Min |
| R/X (%) | Indicador de variabilidad |
| T. Normal | Tiempo calificado |
| Suplementos | % aplicado (por defecto 12%) |
| T. Estándar | Tiempo final con suplementos |

**Criterio Maytag** (advertencia en naranja):
- Si duración ≤ 2 min y N < 10 observaciones → muestra advertencia
- Si duración > 2 min y N < 5 observaciones → muestra advertencia

**Resultado final:** Σ TS = suma de tiempos estándar de todas las tareas.

---

### 4.10 `view_media.py` — Galería de Evidencia Visual

Muestra las fotos capturadas automáticamente durante los estudios.

**Panel izquierdo:** Lista scrollable de ciclos registrados.  
**Panel derecho:** Detalle del ciclo seleccionado:
- Foto de evidencia por paso
- Incidentes registrados con timestamp
- Lecturas de ambiente (Luxómetro / Sonómetro) editables
- Campo de volumen (unidades producidas)

**Función Merge de ciclos:** Fusiona varios ciclos en un "super-ciclo" sumando duraciones y consolidando evidencias. Solo permite fusionar ciclos del mismo modelo.

---

### 4.11 `view_trash.py` — Papelera

Muestra ciclos eliminados y permite restaurarlos o eliminarlos definitivamente. Los datos van a `data["trash"]` al ser borrados desde la tabla.

---

### 4.12 `env_table.py` — Editor de Variables Ambientales

Widget reutilizable para ingresar lecturas de Luxómetro y Sonómetro.

| Campo | Descripción |
|---|---|
| Rango horario | Ej: "8:00 – 10:00" |
| Valor | Nivel medido (lx o dB) |

Métodos: `get_data()` → lista de dicts, `load_data(list)` → carga existentes.

---

## 5. MOTOR DE REPORTES — `utils/pdf_report.py`

### Clase: `PDFManager`

Genera dos tipos de PDFs:

#### 5.1 `generate_instructions_pdf()` — Manual de Instrucciones
PDF con las instrucciones paso a paso del modelo activo, incluyendo descripción detallada de cada paso.

#### 5.2 `generate_pdf()` — Informe Técnico Completo

Informe de ingeniería con las siguientes secciones:

1. **Portada** — Nombre del modelo, fecha, número de ciclos
2. **Resumen Ejecutivo** — KPIs globales
3. **Análisis Ambiental** — Luxómetro y Sonómetro con interpretación
4. **Matriz de Tiempos** — Tabla de todos los ciclos y pasos
5. **Análisis Estadístico** — Promedios, rangos, variabilidad por tarea
6. **Tiempo Estándar** — Tabla con TN y TS bajo metodología Maytag
7. **Análisis Ergonómico (Sensor)** — Ángulos de codo y Therbligs
8. **Comparativa de Operarios** — Tabla de eficiencias relativas
9. **Análisis de Flujo** — Comparativa flujo secuencial vs. balanceado (TOC)
10. **Análisis Muda/Mura/Muri** — Desperdicio, variabilidad, sobrecarga
11. **Evidencia Fotográfica** — Fotos capturadas por paso

---

## 6. PERSISTENCIA DE DATOS

### Archivo: `craneflow_data.json`

```json
{
  "operators": ["Op1", "Op2"],
  "line_config": {"0": "Op1", "1": "Op1", ..., "11": "Op2"},
  "current_model": "Grulla Clásica",
  "models": {
    "Grulla Clásica": {
      "activities": ["Paso 1...", "Paso 2...", ...],
      "descriptions": ["Descripción 1...", ...],
      "pdf_guide": "guias_pdf/Grulla_Clasica.pdf"
    }
  },
  "measurements": [ ...ciclos... ],
  "trash": [ ...ciclos eliminados... ]
}
```

**No requiere base de datos externa.** Todo se persiste localmente en JSON.

---

## 7. INSTALACIÓN Y EJECUCIÓN

### Requisitos
- Python 3.9+
- Windows 10/11 (probado en Windows)
- Cámara web (integrada o USB)

### Instalación

```bash
# 1. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
python main.py
```

### `requirements.txt`
```
customtkinter
fpdf
matplotlib
numpy
opencv-python
mediapipe
pillow
qrcode[pil]
pandas
```

---

## 8. FLUJO DE USO COMPLETO

```
1. Inicio
   └─ Si no hay operarios/config → Pantalla de Configuración del Equipo
   └─ Si hay datos → Dashboard

2. Configurar Equipo (view_operators)
   └─ Seleccionar N operarios → Asignar nombres → Generar Distribución

3. Seleccionar Modelo (view_models)
   └─ Usar "Grulla Clásica" o crear uno nuevo

4. Iniciar Estudio (view_timer)
   └─ Elegir cámara → Configurar meta y variables ambientales
   └─ IA inicializa MediaPipe en segundo plano
   └─ Mover mano a la zona del operario para registrar cada paso
   └─ Al completar todos los pasos y grullas → guarda automáticamente

5. Revisar Datos
   └─ Tabla de Tiempos → ver/exportar Excel
   └─ Estadísticas → gráfica por tarea
   └─ Sensor → ángulos ergonómicos
   └─ Comparativa → eficiencia de operarios
   └─ Tiempo Estándar → cálculo de TS con Maytag

6. Exportar
   └─ PDF Manual de Instrucciones
   └─ PDF Informe Técnico Completo
```

---

## 9. DIAGRAMA DE MÓDULOS

```
main.py (CraneFlowApp)
├── views/view_dashboard.py       ← KPIs globales
├── views/view_models.py          ← CRUD de modelos de origami
├── views/view_operators.py       ← Configuración del equipo
├── views/view_timer.py           ← Cronómetro + Sensor IA (núcleo)
│   └── views/env_table.py        ← Editor de variables ambientales
├── views/view_tables.py          ← Matriz de tiempos / Excel
├── views/view_stats.py           ← Gráficas matplotlib
├── views/view_sensor_data.py     ← Resumen ergonómico (ángulos)
├── views/view_comparison.py      ← Comparativa de operarios
├── views/view_standard_time.py   ← Cálculo TS (Maytag)
├── views/view_media.py           ← Galería de evidencia fotográfica
├── views/view_trash.py           ← Papelera / restauración
└── utils/pdf_report.py           ← Generación de reportes PDF
```

---

## 10. NOTAS TÉCNICAS

- **Threading:** MediaPipe se inicializa en un hilo daemon para no bloquear la UI.
- **Debounce de trigger:** Mínimo 2.5 s entre registros del mismo operario para evitar doble conteo.
- **Fallback sin cámara:** Si MediaPipe falla, el sistema detecta movimiento por diferencia de píxeles entre frames.
- **Visibilidad de landmarks:** Solo se calcula el ángulo si `landmark.visibility > 0.5`.
- **FPS objetivo:** 25 fps (ciclo de 40 ms con `self.after(40, update_loop)`).
- **Persistencia segura:** El JSON se escribe con `ensure_ascii=False` para soporte de tildes y caracteres especiales.

---

*Documentación generada automáticamente — CronoGrulla v1.0 — Ingeniería Industrial, Universidad Católica*
