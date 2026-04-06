# CronoGrulla - Estudio de Métodos Aplicado

CronoGrulla es una aplicación de escritorio diseñada para facilitar el estudio de tiempos, movimientos y balanceo de líneas en procesos de ensamblaje o manufactura (como el plegado de grullas de origami). 

El código original monolítico de ~1400 líneas fue refactorizado y separado en distintas clases dentro de múltiples módulos para lograr una arquitectura mucho más limpia, mantenible y escalable, sin perder ninguna de sus funciones.

## Estructura del Código (Refactorizada)

La aplicación ha sido reescrita en los siguientes archivos y carpetas (arquitectura Modular UI / MVC):

- `main.py`: Punto de entrada que administra el estado central, persistencia y la navegación principal entre vistas. Ahora incluye una **Barra Lateral Colapsable** para maximizar el área de trabajo.
- `utils/pdf_report.py`: Lógica avanzada para la generación de reportes y manuales industriales en PDF.
- `views/view_dashboard.py`: Interfaz principal con tarjetas estadísticas de rendimiento.
- `views/view_models.py`: Gestor de modelos de origami, instrucciones y carga de PDFs guía.
- `views/view_operators.py`: Configuración de equipo de trabajo y balanceo de carga entre estaciones.
- `views/view_timer.py`: **Módulo Vision Pro 6.0**. Incorpora cronometraje manos libres mediante detección de movimiento en zona, "Modo Enfoque" centrado en el paso actual con descripción detallada, y captura automática de evidencia fotográfica.
- `views/view_media.py`: **Galería de Evidencia Visual**. Nueva sección que consolida todas las fotografías tomadas en los estudios, permitiendo auditar errores de operarios con pruebas visuales claras.
- `views/view_tables.py`: Matrices de tiempos recolectados por ciclos.
- `views/view_stats.py`: Gráficos dinámicos para análisis de cuellos de botella y promedios.

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
