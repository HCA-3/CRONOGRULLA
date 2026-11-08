# 🦢 CronoGrulla — Suite de Estudio de Métodos, Ergonomía e IA

**CronoGrulla** es una plataforma integral de escritorio para ingeniería de métodos, medición del trabajo, análisis biomecánico en 3D, cronometraje asistido por Visión Artificial y balanceo de líneas en ensamblajes industriales (aplicado al proceso de manufactura de grullas de origami).

---

## 📁 Estructura del Repositorio Organizada

El proyecto sigue una arquitectura modular y profesional organizada por responsabilidades:

```text
CRONOGRULLA/
├── main.py                     # Punto de entrada principal y gestor central de vistas
├── iniciar.bat                 # Lanzador rápido en Windows (.venv)
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Documentación general y arquitectura
├── craneflow_data.json         # Base de datos persistente (mediciones y estudios)
├── CronoGrulla.spec            # Configuración de compilación PyInstaller
├── .gitignore                  # Exclusiones de Git (limpio, sin bytecode)
│
├── views/                      # Módulos de Interfaz Gráfica (CustomTkinter)
│   ├── view_dashboard.py       # Panel de control e indicadores globales
│   ├── view_lesiones_3d.py     # Modelo 3D Holográfico de Lesiones Ocupacionales (Astra AI)
│   ├── view_atlas_biomecanico.py # Alias retrocompatible de la vista 3D
│   ├── view_timer.py           # Cronometraje con IA MediaPipe y Therbligs
│   ├── view_models.py          # Gestión de modelos de plegado y PDFs
│   ├── view_operators.py       # Configuración de operarios y balanceo
│   ├── view_tables.py          # Matrices de tiempos observados por ciclo
│   ├── view_stats.py           # Análisis estadístico y cuellos de botella
│   ├── view_sensor_data.py     # Telemetría articular y diagnóstico biomecánico
│   ├── view_standard_time.py   # Cálculo de suplementos y Tiempo Estándar
│   ├── view_comparison.py      # Comparación de operarios y métodos
│   ├── view_media.py           # Galería de evidencia fotográfica
│   ├── view_objectives.py      # Metas de producción y eficiencia
│   ├── view_trash.py           # Papelera de reciclaje y recuperación
│   └── env_table.py            # Editor de factores ambientales
│
├── utils/                      # Utilidades del Sistema
│   ├── pdf_report.py           # Motor de generación de reportes ejecutivos en PDF
│   ├── excel_loader.py         # Importador / exportador de hojas de cálculo
│   └── __init__.py
│
├── models/                     # Modelos de Machine Learning
│   └── therblig_svm_model.pkl  # Clasificador SVM (RBF) para micromovimientos Therblig
│
├── assets/                     # Recursos Gráficos
│   └── mannequin/              # Siluetas y texturas de referencia anatómica
│
├── guias_pdf/                  # Guías de Plegado Oficiales (Modelos de Origami)
│   ├── Grulla_Clásica.pdf
│   ├── Grulla_Tipo_I__Laura.pdf
│   └── _Grulla_5_S_.pdf
│
├── Documentacion/              # Documentación Académica y Material de Soporte
│   ├── informes/               # Informes formales, código y artículos
│   │   ├── Informe Final Métodos.docx
│   │   ├── Codigo.docx
│   │   ├── DOCUMENTACION_CRONOGRULLA.docx
│   │   └── DOCUMENTACION_CRONOGRULLA.md
│   ├── guias_estudio/          # Guías de la asignatura y productividad
│   │   ├── Guía_Medición_de_la_productividad.pdf
│   │   └── l10_estudio_de_movimientos.pdf
│   ├── plantillas/             # Formatos de diagramas y plantillas Excel
│   │   ├── Plantilla de Diagrama Bimanual.jpg
│   │   └── Ejemplo de cálculo de Tiempo Estándar.xlsx
│   └── reportes_muestra/       # Informes PDF de ejemplo generados por el sistema
│       ├── Reporte_Grullas_20260310_1330.pdf
│       ├── Reporte_Metodos_Unificado.pdf
│       └── test_generated_report.pdf
│
├── scripts/                    # Scripts de Análisis, Gráficas y Diagnóstico
│   ├── generate_academic_plot.py # Gráficos para artículo académico
│   ├── generate_bar_chart.py     # Gráficos de barras comparativos
│   ├── generate_biomechanics.py  # Visualizaciones biomecánicas
│   ├── generate_fatigue_plot.py  # Curvas de fatiga acumulada
│   ├── test_cam.py               # Diagnóstico de cámaras web
│   ├── test_mediapipe.py         # Verificación de MediaPipe Hands/Pose
│   ├── debug_pdf.py              # Pruebas de renderizado de reportes
│   └── generar_word_doc.py       # Conversor de documentación técnica a Word
│
├── backups/                    # Copias de Seguridad y Versiones Históricas
│   ├── craneflow_data.json.bak
│   ├── main_backup.py
│   └── programa_legacy/
│
├── Imagenes/                   # Registro Fotográfico de las Tomas de Tiempos
└── media_evidencia/            # Capturas de imagen durante los ciclos de cronometraje
```

---

## 🚀 Cómo Ejecutar la Aplicación

### Desde el Entorno Virtual (Recomendado)
1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecutar la aplicación:
   ```bash
   python main.py
   ```
   *O hacer doble clic en `iniciar.bat` en Windows.*

---

## 🧠 Características Principales

1. **Modelo 3D Holográfico de Lesiones (Estilo Astra AI)**:
   * Visualización interactiva en 360° del tronco superior (waist-up) con anillos vectoriales de contorno y profundidad calculada mediante el algoritmo del pintor.
   * Modelos anatómicos diferenciados para **Mujer ♀** y **Hombre ♂**.
   * Manos anatómicas con **5 dedos articulados** independientes y pinza digital activa sobre la cresta de plegado.
   * Cinemática fisiológica completa: respiración viva (16 rpm), plegado coordinado (hombro, codo, muñeca, mano y dedos) y modo de articulación por zona seleccionada.
   * Panel de proyección clínica a corto y largo plazo (1 mes a 5 años) con diagnósticos CIE-10 (Túnel Carpiano, Epicondilitis, Manguito Rotador, Dedo en Resorte, etc.).
   * Panel redimensionable dinámicamente (hasta 92% de ancho) con scroll suave y botones de ampliación rápida.

2. **Cronometraje Bimanual con Visión Artificial (MediaPipe)**:
   * Detección automática de manos, ángulos de codo y muñeca en tiempo real.
   * Clasificación automática de micromovimientos Therblig (`TOMAR G`, `SOLTAR RL`, `SOSTENER H`, etc.) mediante Support Vector Machines (SVM).

3. **Generación de Reportes Ejecutivos**:
   * Exportación instantánea a PDF de informes consolidados de ingeniería de métodos con diagramas bimanuales, tablas de suplementos, análisis de fatiga y recomendaciones ergonómicas.
