# CronoGrulla - Estudio de Métodos Aplicado

CronoGrulla es una aplicación de escritorio diseñada para facilitar el estudio de tiempos, movimientos y balanceo de líneas en procesos de ensamblaje o manufactura (como el plegado de grullas de origami). 

El código original monolítico de ~1400 líneas fue refactorizado y separado en distintas clases dentro de múltiples módulos para lograr una arquitectura mucho más limpia, mantenible y escalable, sin perder ninguna de sus funciones.

## Estructura del Código (Refactorizada)

La aplicación ha sido reescrita en los siguientes archivos y carpetas (arquitectura Modular UI / MVC):

- `main.py`: Punto de entrada de la aplicación. Contiene la clase `CraneFlowApp` que administra el estado central, persistencia y la navegación principal entre vistas.
- `utils/pdf_report.py`: Contiene las clases `PremiumReportPDF` y `PDFManager` que abordan lógica pesada para la generación de reportes y manuales en PDF.
- `views/view_dashboard.py`: Interfaz principal con tarjetas estadísticas.
- `views/view_models.py`: Administrador de modelos, instrucciones personalizadas de flujo y carga de PDFs adjuntos.
- `views/view_operators.py`: Configuración del personal y balanceo de carga automático.
- `views/view_timer.py`: Módulo del cronómetro, tracking de ciclos, operarios en tiempo real y registro de errores/eventos (QC).
- `views/view_tables.py`: Matrices en tabla para ver las mediciones tomadas agrupadas por ciclos.
- `views/view_stats.py`: Gráficos de barras que visualizan promedios y posibles cuellos de botella por estación de trabajo.

## Cómo Ejecutar (Ejecutable e Instalador)

Para facilitar su uso sin necesidad de Python ni consola de comandos, hemos creado un ejecutable y un instalador para Windows.

### 1. Opción de Instalador Automático
Puedes distribuir el archivo `Instalador_CronoGrulla.zip` ubicado en la carpeta `dist`. Dile a los usuarios que:
1. Extraigan el archivo zip (`Clic derecho -> Extraer todo...`).
2. Hagan doble clic sobre `install.bat`.
3. ¡Listo! El instalador creará un acceso directo de CronoGrulla directamente en su Escritorio, enlazado de forma oculta y segura.

### 2. Opción de Ejecutable (Archivo Único)
Si prefieres no instalar nada, puedes utilizar directamente el archivo `.exe`:
1. Ve a la carpeta `dist` en los archivos originales.
2. Copia el archivo `CronoGrulla.exe` a tu Escritorio o donde prefieras.
3. Ábrelo con doble clic.

> **⚠️ Nota de Datos:** Si ya tenías datos guardados sobre tus operarios, tiempos y modelos, no olvides colocar el archivo `craneflow_data.json` en la misma ubicación donde pegues o instales tu ejecutable para que retome tus datos anteriores. De otra forma, el programa iniciará limpio.

## Cómo Ejecutar (Desde Código Fuente)

Si eres desarrollador, asegúrate de tener instaladas las dependencias:
```bash
pip install -r requirements.txt
```

Simplemente ejecuta:
```bash
python main.py
```

Sus archivos de datos y guías adjuntas se mantendrán sincronizados en la misma ubicación que el ejecutable o script principal.
