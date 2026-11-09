import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import json
import math
import time
import os
from PIL import Image, ImageTk

class ModeloLesiones3DView(ctk.CTkFrame):
    """
    Modelo 3D de Lesiones & Biomecánica Ocupacional.
    Maniquí anatómico 3D de alta fidelidad para el tronco superior (cuello, hombros, codos, muñecas y manos)
    con rotación interactiva en 360 grados, contornos diferenciados para hombre y mujer basados en
    los modelos fotorrealistas de maniquí de taller ergonómico, mapa de calor térmico articular
    y simulación predictiva de daño musculoesquelético acumulado en el tiempo (CIE-10).
    Panel clínico ultra-ampliable (hasta 92%) y desplazamiento de barras completamente funcional.
    """
    
    ROTATION_TEXTURE_MAP = {
        "male": {
            0: "male_front.png",
            45: "male_persp.png",
            90: "male_side_left.png",       # Perfil D (orientado a la derecha)
            135: "male_back_persp.png",     # 3/4 Espalda D
            180: "male_back.png",           # Espalda completa
            225: "male_back_persp_left.png",# 3/4 Espalda I
            270: "male_side.png",           # Perfil I (orientado a la izquierda)
            315: "male_persp_left.png"      # 3/4 Frente I
        },
        "female": {
            0: "female_front.png",
            45: "female_persp.png",
            90: "female_side.png",          # Perfil D (orientado a la derecha)
            135: "female_back_persp.png",   # 3/4 Espalda D
            180: "female_back.png",         # Espalda completa
            225: "female_back_persp_left.png", # 3/4 Espalda I
            270: "female_side_left.png",    # Perfil I (orientado a la izquierda)
            315: "female_persp_left.png"    # 3/4 Frente I
        }
    }

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        # Estado de proyección 3D
        self.yaw = math.radians(0)      # Rotación horizontal (0 a 360°)
        self.pitch = math.radians(0)    # Inclinación vertical (-35° a +35°)
        self.zoom_level = 1.05
        self.pan_x = 0
        self.pan_y = 0
        
        # Arrastre e interactividad
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self.auto_rotate = False
        self.auto_rotate_id = None
        
        # Estado de cinemática y animación humana (Respiración y Plegado)
        self.human_motion_mode = tk.StringVar(value="🫁 Respiración")
        self.anim_start_time = time.time()
        self.anim_timer_id = None
        self.is_animating = False
        
        # Parámetros seleccionados
        self.selected_operator = tk.StringVar(value="Todos")
        self.selected_gender = tk.StringVar(value="Femenino")
        self.selected_horizon = tk.StringVar(value="1 Año")
        self.selected_zone = tk.StringVar(value="dedos_r")
        self.visual_layer_mode = tk.StringVar(value="⚡ Completo (Músculos+Esqueleto)")
        
        # Parámetros biomecánicos de entrada ISO 11226
        self.param_trunk = 15.0
        self.param_neck = 22.0
        self.param_sh_l = 25.0
        self.param_sh_r = 40.0
        self.param_dur = 25.0
        self.param_fatigue_f = 0.42
        
        # Simulación de turno laboral dinámico
        self.is_shift_simulating = False
        self.sim_shift_time = 0.0
        
        # Widgets de telemetría muscular
        self.muscle_bars = {}
        self.muscle_val_labels = {}
        
        # Proporción de distribución: 38% Maniquí / 62% Panel Clínico para legibilidad óptima
        self.left_weight = 38
        self.right_weight = 62
        
        # Horizontes temporales para proyección clínica
        self.HORIZONS = ["1 Mes", "3 Meses", "6 Meses", "1 Año", "2 Años", "3 Años", "5 Años"]
        self.HORIZON_MONTHS = {
            "1 Mes": 1, "3 Meses": 3, "6 Meses": 6, "1 Año": 12,
            "2 Años": 24, "3 Años": 36, "5 Años": 60
        }
        
        # Cargar texturas fotorrealistas de maniquíes 3D
        self.mannequin_base_images = {}
        self._cached_photo = None
        self._load_mannequin_textures()

        # Base de datos patológica laboral (CIE-10)
        self.PATHOLOGIES_DB = self._init_pathologies_db()
        
        # Cargar métricas reales del estudio
        self.refresh_metrics()
        self.build_ui()
        self.after(60, self._start_animation_loop)

    def _load_mannequin_textures(self):
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "mannequin")
        if not os.path.exists(assets_dir):
            return
        for fname in os.listdir(assets_dir):
            if fname.endswith(".png") and not fname.endswith("_raw.png"):
                p = os.path.join(assets_dir, fname)
                try:
                    self.mannequin_base_images[fname] = Image.open(p)
                except Exception as e:
                    print(f"Error cargando textura de maniquí {fname}: {e}")

    def _init_pathologies_db(self):
        return {
            "dedos_r": {
                "name": "Dedos Mano Derecha (Pulgar e Índice - Pinza Digital)",
                "tissue": "Poleas Flexoras A1-A2, Tendones Flexor Largo del Pulgar y Flexor Profundo del Índice",
                "subt": "Pinza digital de doblado y presión puntual repetitiva en asentar marcas",
                "stages": {
                    1: {"cie": "M79.2 Neuralgia digital focal por compresión", "desc": "Sensación de entumecimiento y fatiga en yemas de dedos índice y pulgar.", "risk": "LEVE", "eva": "2/10", "color": "#2ecc71"},
                    3: {"cie": "M65.3 Dedo en resorte incipiente (Pulgar / Índice)", "desc": "Engrosamiento de la polea A1 con leve chasquido y fricción al extender.", "risk": "MODERADO", "eva": "4/10", "color": "#f1c40f"},
                    6: {"cie": "M65.3 Tenosinovitis estenosante digital (Trigger Finger)", "desc": "Bloqueo mecánico doloroso que requiere desbloqueo pasivo para abrir los dedos.", "risk": "ALTO", "eva": "5.5/10", "color": "#e67e22"},
                    12: {"cie": "M65.3 Nódulo tendinoso flexor con bloqueo crónico", "desc": "Incapacidad para pinza fina de precisión. Pérdida severa de destreza motriz.", "risk": "ALTO / CRÍTICO", "eva": "7/10", "color": "#e74c3c"},
                    36: {"cie": "M19.0 Artrosis interfalángica distal precoz", "desc": "Desgaste del cartílago articular y dolor continuo al presionar marcas de origami.", "risk": "MUY CRÍTICO", "eva": "8/10", "color": "#962d22"},
                    60: {"cie": "M20.0 Deformidad articular fija y anquilosis interfalángica", "desc": "Pérdida irreversible de función motriz y pinza digital ocupacional.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
                }
            },
            "mano_r": {
                "name": "Mano Derecha (Palma y Eminencia Tenar)",
                "tissue": "Músculos Tenares (Abductor, Oponente, Flexor Corto), Aponeurosis Palmar",
                "subt": "Microtrauma y compresión palmar repetida contra marcas y solapas",
                "stages": {
                    1: {"cie": "M70.9 Fatiga muscular tenar aguda", "desc": "Pesadez en base del pulgar al final de turnos de plegado.", "risk": "LEVE", "eva": "2/10", "color": "#2ecc71"},
                    3: {"cie": "M72.0 Fascitis palmar superficial incipiente", "desc": "Hipersensibilidad e inflamación de la fascia palmar media.", "risk": "MODERADO", "eva": "3.5/10", "color": "#f1c40f"},
                    6: {"cie": "M70.0 Sinovitis crepitante palmar", "desc": "Crujido y dolor mecánico al cerrar la palma de la mano contra el papel.", "risk": "ALTO", "eva": "5/10", "color": "#e67e22"},
                    12: {"cie": "G56.0 Neuropatía motora de rama recurrente tenar", "desc": "Debilidad de abducción y oposición del pulgar.", "risk": "ALTO / CRÍTICO", "eva": "6.5/10", "color": "#e74c3c"},
                    36: {"cie": "M72.0 Nódulos palmares fibróticos pre-Dupuytren", "desc": "Bandas tensas retráctiles en palma de la mano.", "risk": "MUY CRÍTICO", "eva": "8/10", "color": "#962d22"},
                    60: {"cie": "M18.0 Rizartrosis severa con pérdida de pinza tenar", "desc": "Subluxación articular trapecio-metacarpiana e incapacidad laboral.", "risk": "INCAPACITANTE", "eva": "9/10", "color": "#78281f"}
                }
            },
            "dedos_l": {
                "name": "Dedos Mano Izquierda (Pinza Estabilizadora)",
                "tissue": "Ligamentos Colaterales Interfalángicos, Tendones Flexores y Extensores",
                "subt": "Fijación isométrica estática continua de las esquinas del papel",
                "stages": {
                    1: {"cie": "M79.1 Mialgia de interóseos y lumbricales", "desc": "Dolor sordo por contracción mantenida de sujeción.", "risk": "LEVE", "eva": "1.5/10", "color": "#2ecc71"},
                    3: {"cie": "M65.8 Tenosinovitis interfalángica incipiente", "desc": "Edema digital leve matutino y fatiga precoz.", "risk": "MODERADO", "eva": "3/10", "color": "#f1c40f"},
                    6: {"cie": "M65.9 Entesopatía digital subaguda", "desc": "Dolor al ejercer fuerza de contra-apoyo sobre la mesa.", "risk": "MODERADO", "eva": "4.5/10", "color": "#f1c40f"},
                    12: {"cie": "M65.3 Dedo en resorte digital medio e índice", "desc": "Resistencia elástica y dolor al extender dedos izquierdos.", "risk": "ALTO", "eva": "6/10", "color": "#e67e22"},
                    36: {"cie": "M19.0 Formación precoz de nódulos interfalángicos", "desc": "Engrosamiento articular óseo reactivo por sobrecarga.", "risk": "CRÍTICO", "eva": "7.5/10", "color": "#e74c3c"},
                    60: {"cie": "M20.1 Contractura en flexión y rigidez digital", "desc": "Limitación articular fija permanente de dedos de la mano izquierda.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
                }
            },
            "mano_l": {
                "name": "Mano Izquierda (Palma y Región Hipotenar)",
                "tissue": "Músculos Hipotenares, Canal de Guyón, Aponeurosis Palmar",
                "subt": "Apoyo estático prolongado y contra-fuerza de fijación",
                "stages": {
                    1: {"cie": "M70.9 Tensión muscular hipotenar", "desc": "Tensión en borde cubital externo de la mano.", "risk": "LEVE", "eva": "1/10", "color": "#2ecc71"},
                    3: {"cie": "G56.2 Compresión cubital en Canal de Guyón Leve", "desc": "Hormigueo en borde palmar del 4to y 5to dedo al apoyar.", "risk": "MODERADO", "eva": "3/10", "color": "#f1c40f"},
                    6: {"cie": "M72.2 Fibromatosis palmar incipiente", "desc": "Endurecimiento de tejidos blandos de apoyo hipotenar.", "risk": "MODERADO", "eva": "4.5/10", "color": "#f1c40f"},
                    12: {"cie": "G56.2 Síndrome del Martillo Hipotenar Laboral", "desc": "Isquemia digital por microtraumatismo repetido de apoyo.", "risk": "ALTO", "eva": "6/10", "color": "#e67e22"},
                    36: {"cie": "G56.2 Neuropatía cubital axonal distal", "desc": "Pérdida de fuerza intrínseca y atrofia hipotenar.", "risk": "CRÍTICO", "eva": "7.5/10", "color": "#e74c3c"},
                    60: {"cie": "M18.1 Artrosis carpo-metacarpiana bilateral", "desc": "Rigidez articular mecánica permanente e incapacidad ocupacional.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
                }
            },
            "muñeca_r": {
                "name": "Muñeca y Mano Derecha",
                "tissue": "Túnel Carpiano, Ligamento Transverso, Tendones Flexores Superficiales y Profundos",
                "subt": "Alta repetitividad en Therblig TOMAR (G) con pinza digital continua",
                "stages": {
                    1: {"cie": "M65.8 Tenosinovitis incipiente de muñeca", "desc": "Microinflamación de vainas sinoviales. Dolor sordo y ligera rigidez articular al final de la jornada.", "risk": "LEVE", "eva": "2/10", "color": "#2ecc71"},
                    3: {"cie": "M65.9 Tenosinovitis subaguda de flexores", "desc": "Edema peritendinoso continuo. Parestesias nocturnas leves en dedos índice y medio. Molestia al reiniciar el doblado.", "risk": "MODERADO", "eva": "4/10", "color": "#f1c40f"},
                    6: {"cie": "G56.0 Síndrome del Túnel Carpiano Grado I", "desc": "Presión intracarpiana elevada (>30 mmHg). Signos de Tinel y Phalen positivos. Pérdida del 10% de fuerza de pinza.", "risk": "ALTO", "eva": "5/10", "color": "#e67e22"},
                    12: {"cie": "G56.0 Síndrome del Túnel Carpiano Grado II", "desc": "Compresión crónica del nervio mediano. Enlentecimiento de velocidad de conducción motora. Pérdida de destreza motriz fina.", "risk": "ALTO / CRÍTICO", "eva": "7/10", "color": "#e74c3c"},
                    36: {"cie": "G56.0 STC Severo + M19.0 Rizartrosis secundaria", "desc": "Neuropatía compresiva axonotmésica con atrofia de eminencia tenar. Degeneración articular trapecio-metacarpiana. Incapacidad laboral.", "risk": "MUY CRÍTICO", "eva": "8/10", "color": "#962d22"},
                    60: {"cie": "G56.0 Daño Estructural Permanente / Cirugía Requerida", "desc": "Pérdida irreversible de fibras axonales del nervio mediano. Secuelas neurológicas permanentes e indemnización o reubicación.", "risk": "INCAPACITANTE", "eva": "9/10", "color": "#78281f"}
                }
            },
            "muñeca_l": {
                "name": "Muñeca y Mano Izquierda",
                "tissue": "Tendones Flexores, Vaina Sinovial, Aponeurosis Palmar",
                "subt": "Sujeción isométrica y contra-apoyo de fijación en doblado",
                "stages": {
                    1: {"cie": "M70.9 Fatiga muscular localizada", "desc": "Tensión palmar leve por fijación estática de la hoja.", "risk": "LEVE", "eva": "1/10", "color": "#2ecc71"},
                    6: {"cie": "M65.4 Tendinitis de De Quervain incipiente", "desc": "Tensión en tendones abductor largo y extensor corto del pulgar.", "risk": "MODERADO", "eva": "4/10", "color": "#f1c40f"},
                    12: {"cie": "G56.0 Síndrome de Túnel Carpiano Izquierdo Leve", "desc": "Entumecimiento esporádico matutino y fatiga prematura.", "risk": "ALTO", "eva": "6/10", "color": "#e67e22"},
                    36: {"cie": "M65.3 Dedo en resorte / Tenosinovitis nodular", "desc": "Fricción del tendón flexor bajo polea A1 con bloqueo doloroso.", "risk": "CRÍTICO", "eva": "7/10", "color": "#e74c3c"},
                    60: {"cie": "M18.1 Artrosis carpo-metacarpiana bilateral", "desc": "Rigidez articular irreversible y dolor mecánico continuo.", "risk": "INCAPACITANTE", "eva": "8/10", "color": "#78281f"}
                }
            },
            "codo_r": {
                "name": "Codo Derecho (Epicóndilo & Epitróclea)",
                "tissue": "Tendón Conjunto de Extensores de Muñeca, Nervio Radial y Cubital",
                "subt": "Tensión por ángulos de codo desviados y fuerza de presión repetitiva",
                "stages": {
                    1: {"cie": "M77.1 Mialgia de extensores de antebrazo", "desc": "Sobrecarga en inserción perióstica epicondílea.", "risk": "LEVE", "eva": "2/10", "color": "#2ecc71"},
                    6: {"cie": "M77.1 Epicondilitis Lateral (Codo de Tenista Laboral)", "desc": "Microroturas en tendón extensor radial corto del carpo. Dolor agudo al presionar marcas de pliegue.", "risk": "ALTO", "eva": "5/10", "color": "#e67e22"},
                    12: {"cie": "M77.1 Epicondilalgia Crónica Recalcitrante", "desc": "Angiofibrodisplasia y desorganización de fibras de colágeno. Dificultad para levantar cargas ligeras.", "risk": "CRÍTICO", "eva": "7/10", "color": "#e74c3c"},
                    36: {"cie": "M77.1 Tendinosis con Desgarro Intrasustancia", "desc": "Engrosamiento y necrosis focal del tendón. Pérdida funcional motora.", "risk": "MUY CRÍTICO", "eva": "8/10", "color": "#962d22"},
                    60: {"cie": "M77.1 Artrosis Radio-Capitelar Postraumática", "desc": "Desgaste del cartílago articular y limitación permanente de prono-supinación.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
                }
            },
            "codo_l": {
                "name": "Codo Izquierdo (Articulación Húmero-Cubital)",
                "tissue": "Cápsula Articular, Nervio Cubital en Canal Epitrocleo-Olecraneano",
                "subt": "Tensión estática mantenida en flexión angular prolongada",
                "stages": {
                    1: {"cie": "M70.9 Fatiga postural del bíceps braquial", "desc": "Contractura de fijación postural.", "risk": "LEVE", "eva": "1/10", "color": "#2ecc71"},
                    6: {"cie": "G56.2 Neuropatía Cubital Leve en el Codo", "desc": "Hormigueo en borde cubital de la mano y 5to dedo al apoyar codo.", "risk": "MODERADO", "eva": "3/10", "color": "#f1c40f"},
                    12: {"cie": "M77.0 Epitrocleitis Medial (Codo de Golfista)", "desc": "Inflamación de los tendones flexores y pronador redondo.", "risk": "ALTO", "eva": "6/10", "color": "#e67e22"},
                    36: {"cie": "G56.2 Síndrome del Canal Cubital Moderado", "desc": "Compresión axonal y debilidad intrínseca de la mano.", "risk": "CRÍTICO", "eva": "7/10", "color": "#e74c3c"},
                    60: {"cie": "M19.0 Sinovitis y Rigidez Articular del Codo", "desc": "Pérdida de los últimos 15° de extensión articular.", "risk": "INCAPACITANTE", "eva": "8/10", "color": "#78281f"}
                }
            },
            "cuello": {
                "name": "Columna Cervical & Músculo Trapecio",
                "tissue": "Vértebras C1-C7, Músculos Esplenio, Trapecio Superior, Elevador de la Escápula",
                "subt": "Flexión anterior de cuello sostenida (>25°) hacia la mesa de doblado",
                "stages": {
                    1: {"cie": "M54.2 Cervicalgia tensional aguda", "desc": "Espasmo muscular en trapecios superiores por postura estática.", "risk": "LEVE", "eva": "2/10", "color": "#2ecc71"},
                    6: {"cie": "M54.2 Síndrome Miofascial Cervico-Dorsal", "desc": "Puntos gatillo miofasciales activos en trapecios y romboides. Cefaleas tensionales frecuentes.", "risk": "MODERADO", "eva": "5/10", "color": "#f1c40f"},
                    12: {"cie": "M50.3 Rectificación de la Lordosis Cervical", "desc": "Contractura permanente que anula la curvatura fisiológica cervical. Parestesias irradiadas a hombros.", "risk": "ALTO", "eva": "6.5/10", "color": "#e67e22"},
                    36: {"cie": "M50.2 Hernia Discal Cervical C5-C6 Incipiente", "desc": "Deshidratación discal y protusión con compresión radicular.", "risk": "CRÍTICO", "eva": "8/10", "color": "#e74c3c"},
                    60: {"cie": "M50.1 Radiculopatía Cervical Crónica Severa", "desc": "Pérdida de reflejos miotáticos y atrofia muscular deltoidea.", "risk": "INCAPACITANTE", "eva": "9/10", "color": "#78281f"}
                }
            },
            "hombro_r": {
                "name": "Hombro Derecho (Manguito Rotador)",
                "tissue": "Tendón del Supraespinoso, Espacio Subacromial, Bolsa Subdeltoidea",
                "subt": "Abducción mantenida y microtraumatismo por movimientos repetidos",
                "stages": {
                    1: {"cie": "M75.8 Sobrecarga del deltoides anterior", "desc": "Tensión muscular al elevar y manipular el origami.", "risk": "LEVE", "eva": "1/10", "color": "#2ecc71"},
                    6: {"cie": "M75.1 Síndrome de Pinzamiento Subacromial Leve", "desc": "Fricción del tendón supraespinoso bajo el acromion al elevar el brazo.", "risk": "MODERADO", "eva": "4/10", "color": "#f1c40f"},
                    12: {"cie": "M75.1 Tendinitis del Manguito Rotador", "desc": "Inflamación del tendón supraespinoso con arco doloroso entre 60° y 120°.", "risk": "ALTO", "eva": "6/10", "color": "#e67e22"},
                    36: {"cie": "M75.5 Bursitis Subdeltoidea y Calcificación Tendinosa", "desc": "Dolor nocturno al dormir sobre el lado derecho y debilidad.", "risk": "CRÍTICO", "eva": "7.5/10", "color": "#e74c3c"},
                    60: {"cie": "M75.1 Rotura Parcial/Total del Tendón Supraespinoso", "desc": "Pérdida severa de la fuerza de abducción y limitación de rango de movimiento.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
                }
            },
            "hombro_l": {
                "name": "Hombro Izquierdo (Estabilizador Escapular)",
                "tissue": "Músculos Fijadores Escapulares, Tendón Bicipital",
                "subt": "Contracción isométrica estabilizadora prolongada",
                "stages": {
                    1: {"cie": "M70.9 Fatiga periescapular", "desc": "Molestia postural al mantener la posición de trabajo.", "risk": "LEVE", "eva": "1/10", "color": "#2ecc71"},
                    6: {"cie": "M75.2 Tendinitis de la Porción Larga del Bíceps", "desc": "Sensibilidad dolorosa en la corredera bicipital.", "risk": "MODERADO", "eva": "3.5/10", "color": "#f1c40f"},
                    12: {"cie": "M75.4 Síndrome de Fricción Escapular", "desc": "Crepitación dolorosa al mover la escápula sobre la parrilla costal.", "risk": "ALTO", "eva": "5.5/10", "color": "#e67e22"},
                    36: {"cie": "M75.1 Tendinopatía Degenerativa del Manguito", "desc": "Disminución de masa muscular y limitación de rotación interna.", "risk": "CRÍTICO", "eva": "7/10", "color": "#e74c3c"},
                    60: {"cie": "M75.0 Capsulitis Adhesiva (Hombro Congelado)", "desc": "Rigidez articular severa con pérdida de movilidad glenohumeral.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
                }
            },
            "espalda_alta": {
                "name": "Espalda Alta (Columna Torácica T1-T8 & Escápulas)",
                "tissue": "Musculatura Paravertebral Torácica, Músculos Romboides y Dorsal Ancho",
                "subt": "Hipercifosis postural prolongada por postura sentada sin apoyo dorsal",
                "stages": {
                    1: {"cie": "M54.6 Dorsalgia postural funcional", "desc": "Sensación de fatiga y quemazón interescapular.", "risk": "LEVE", "eva": "2/10", "color": "#2ecc71"},
                    6: {"cie": "M54.6 Dorsalgia con Contractura Paravertebral", "desc": "Bandas tensas palpables entre escápula y columna.", "risk": "MODERADO", "eva": "4/10", "color": "#f1c40f"},
                    12: {"cie": "M40.0 Hipercifosis Postural Fijada", "desc": "Sobrecarga discal anterior con pérdida de movilidad de extensión torácica.", "risk": "ALTO", "eva": "6/10", "color": "#e67e22"},
                    36: {"cie": "M42.1 Osteocondrosis Intervertebral Torácica", "desc": "Disminución de altura discal y formación de osteofitos anteriores.", "risk": "CRÍTICO", "eva": "7/10", "color": "#e74c3c"},
                    60: {"cie": "M54.6 Artrosis Facetaria Torácica Severa", "desc": "Dolor torácico mecánico incapacitante con restricción de expansión costal.", "risk": "INCAPACITANTE", "eva": "8/10", "color": "#78281f"}
                }
            }
        }

    def refresh_metrics(self):
        """Calcula las métricas reales para el operario o conjunto de operarios seleccionados."""
        measurements = self.app.data.get("measurements", [])
        op_sel = self.selected_operator.get()
        
        r_angles, l_angles, therbligs, db_levels, lux_levels = [], [], [], [], []
        total_time = 0.0
        cycles_count = 0
        
        for m in measurements:
            for lx in m.get("lux_data", []):
                try: lux_levels.append(float(lx.get("val", 0)))
                except: pass
            for db in m.get("db_data", []):
                try: db_levels.append(float(db.get("val", 0)))
                except: pass
                
            splits = m.get("splits", [])
            for s in splits:
                if op_sel == "Todos" or s.get("operator") == op_sel:
                    ergo = s.get("ergo_summary", {})
                    if ergo.get("avg_elbow_r", 0) > 0: r_angles.append(ergo["avg_elbow_r"])
                    if ergo.get("avg_elbow_l", 0) > 0: l_angles.append(ergo["avg_elbow_l"])
                    if s.get("therblig"): therbligs.append(s["therblig"])
                    if s.get("db_level", 0) > 0: db_levels.append(s["db_level"])
                    total_time += s.get("duration", 0)
                    cycles_count += 1

        self.metrics = {
            "avg_elbow_r": float(np.mean(r_angles)) if r_angles else 98.0,
            "avg_elbow_l": float(np.mean(l_angles)) if l_angles else 95.0,
            "tomar_count": sum(1 for t in therbligs if "TOMAR" in str(t)),
            "soltar_count": sum(1 for t in therbligs if "SOLTAR" in str(t)),
            "total_therbligs": len(therbligs),
            "avg_lux": float(np.mean(lux_levels)) if lux_levels else 480.0,
            "avg_db": float(np.mean(db_levels)) if db_levels else 55.0,
            "total_time": total_time,
            "sample_count": cycles_count
        }

        # Calcular severidad de afectación por zona (0.0 a 1.0)
        self.zone_impacts = self._compute_zone_impacts()

    def _compute_zone_impacts(self):
        m = self.metrics
        gender = self.selected_gender.get()
        
        k_carpal = 1.25 if gender == "Femenino" else 1.0
        k_neck   = 1.20 if gender == "Femenino" else 1.05
        k_elbow  = 1.00 if gender == "Femenino" else 1.15
        
        dev_r = abs(m["avg_elbow_r"] - 105.0) / 35.0
        dev_l = abs(m["avg_elbow_l"] - 105.0) / 35.0
        
        total_th = max(1, m["total_therbligs"])
        tomar_ratio = m["tomar_count"] / total_th
        
        lux_penalty = max(0.0, (400.0 - m["avg_lux"]) / 300.0) if m["avg_lux"] < 400 else 0.0
        db_penalty = max(0.0, (m["avg_db"] - 65.0) / 30.0) if m["avg_db"] > 65 else 0.0

        return {
            "dedos_r": min(1.0, (0.48 + (tomar_ratio * 0.52)) * k_carpal),
            "mano_r": min(1.0, (0.42 + (tomar_ratio * 0.48) + (dev_r * 0.10)) * k_carpal),
            "muñeca_r": min(1.0, (0.40 + (tomar_ratio * 0.45) + (dev_r * 0.15)) * k_carpal),
            "dedos_l": min(1.0, (0.32 + (tomar_ratio * 0.38)) * (k_carpal * 0.9)),
            "mano_l": min(1.0, (0.30 + (tomar_ratio * 0.35) + (dev_l * 0.10)) * (k_carpal * 0.9)),
            "muñeca_l": min(1.0, (0.30 + (tomar_ratio * 0.35) + (dev_l * 0.15)) * (k_carpal * 0.9)),
            "codo_r": min(1.0, (0.35 + (dev_r * 0.55) + (tomar_ratio * 0.15)) * k_elbow),
            "codo_l": min(1.0, (0.30 + (dev_l * 0.50) + (tomar_ratio * 0.15)) * k_elbow),
            "cuello": min(1.0, (0.45 + (lux_penalty * 0.35) + (db_penalty * 0.20)) * k_neck),
            "hombro_r": min(1.0, (0.35 + (dev_r * 0.35) + (db_penalty * 0.15))),
            "hombro_l": min(1.0, (0.30 + (dev_l * 0.30) + (db_penalty * 0.15))),
            "espalda_alta": min(1.0, (0.40 + (lux_penalty * 0.30) + (db_penalty * 0.15)))
        }

    # ── MOTOR BIOMECÁNICO ISO 11226 Y SISTEMA MUSCULAR 3D ─────────────────────
    def compute_iso_muscle_risks(self):
        """Calcula el riesgo de fatiga musculoesquelética (0.0 a 1.0) para los 10 grupos musculares según norma ISO 11226."""
        m = self.metrics
        trunk = getattr(self, "param_trunk", 15.0)
        neck = getattr(self, "param_neck", 22.0)
        sh_l = getattr(self, "param_sh_l", 25.0)
        sh_r = getattr(self, "param_sh_r", 40.0)
        el_l = m.get("avg_elbow_l", 98.0)
        el_r = m.get("avg_elbow_r", 101.0)
        dur = getattr(self, "param_dur", 25.0)
        f_idx = getattr(self, "param_fatigue_f", 0.42)

        if getattr(self, "is_shift_simulating", False):
            st = getattr(self, "sim_shift_time", 0.0)
            p = min(1.0, max(0.0, st / 30.0))
            f_idx = min(1.0, 0.15 + (0.70 * p))
            dur = p * 45.0
            sh_r = 25.0 + 55.0 * p + 10.0 * math.sin(st * 1.5)
            trunk = 12.0 + 30.0 * p + 4.0 * math.cos(st)
            neck = 15.0 + 25.0 * p

        def lin(x, o, c):
            return max(0.0, min(1.0, (x - o) / (c - o)))

        def elb(e):
            diff = 60.0 - e if e < 60.0 else (e - 100.0 if e > 100.0 else 0.0)
            return lin(diff, 0.0, 50.0)

        tr = lin(trunk, 20.0, 60.0)
        nk = lin(neck, 25.0, 60.0)
        s_l = lin(sh_l, 20.0, 60.0)
        s_r = lin(sh_r, 20.0, 60.0)
        e_l = elb(el_l)
        e_r = elb(el_r)
        d = max(0.0, min(1.0, dur / 30.0))

        def fuse(a):
            r = 0.5 * a + 0.35 * f_idx + 0.15 * d
            if f_idx >= 0.75 or a >= 1.0:
                r = max(r, 0.75)
            return max(0.0, min(1.0, r))

        return {
            "trapL": fuse(0.65 * s_l + 0.35 * nk),
            "trapR": fuse(0.65 * s_r + 0.35 * nk),
            "delL":  fuse(s_l),
            "delR":  fuse(s_r),
            "bicL":  fuse(0.6 * e_l + 0.4 * s_l),
            "bicR":  fuse(0.6 * e_r + 0.4 * s_r),
            "triL":  fuse(0.4 * e_l + 0.6 * s_l),
            "triR":  fuse(0.4 * e_r + 0.6 * s_r),
            "erL":   fuse(tr),
            "erR":   fuse(tr)
        }

    def get_risk_color(self, score_0_to_1):
        """Retorna código de color hexadecimal según nivel de riesgo ISO 11226."""
        s = max(0.0, min(1.0, score_0_to_1))
        if s < 0.35:
            return "#10b981"
        elif s < 0.65:
            return "#f59e0b"
        else:
            return "#ef4444"

    def toggle_shift_simulation(self):
        """Inicia o detiene la simulación progresiva de un turno laboral."""
        self.is_shift_simulating = not self.is_shift_simulating
        if self.is_shift_simulating:
            self.sim_shift_time = 0.0
            if hasattr(self, "btn_sim_shift") and self.btn_sim_shift.winfo_exists():
                self.btn_sim_shift.configure(text="⏸ Pausar Turno", fg_color="#ef4444")
            self._start_animation_loop()
        else:
            if hasattr(self, "btn_sim_shift") and self.btn_sim_shift.winfo_exists():
                self.btn_sim_shift.configure(text="▶ Simular Turno", fg_color="#0284c7")

    def apply_scenario_preset(self, scen_key):
        """Aplica un escenario ergonómico predefinido."""
        presets = {
            "neutral": {"trunk": 5.0, "neck": 8.0, "sh_l": 10.0, "sh_r": 12.0, "dur": 5.0, "F": 0.15},
            "reach":   {"trunk": 25.0, "neck": 25.0, "sh_l": 60.0, "sh_r": 85.0, "dur": 18.0, "F": 0.52},
            "fold":    {"trunk": 20.0, "neck": 30.0, "sh_l": 20.0, "sh_r": 35.0, "dur": 32.0, "F": 0.65},
            "critical":{"trunk": 55.0, "neck": 48.0, "sh_l": 75.0, "sh_r": 95.0, "dur": 45.0, "F": 0.84}
        }
        data = presets.get(scen_key, presets["neutral"])
        self.is_shift_simulating = False
        if hasattr(self, "btn_sim_shift") and self.btn_sim_shift.winfo_exists():
            self.btn_sim_shift.configure(text="▶ Simular Turno", fg_color="#0284c7")
        self.param_trunk = data["trunk"]
        self.param_neck = data["neck"]
        self.param_sh_l = data["sh_l"]
        self.param_sh_r = data["sh_r"]
        self.param_dur = data["dur"]
        self.param_fatigue_f = data["F"]
        self.draw_mannequin_3d()
        self.update_diagnostic_panel()

    def open_webgl_atlas(self):
        """Exporta el estado biomecánico actual y abre el visor interactivo Three.js WebGL en el navegador."""
        import webbrowser
        try:
            state = {
                "operator": self.selected_operator.get(),
                "gender": self.selected_gender.get(),
                "trunk": getattr(self, "param_trunk", 18.0),
                "neck": getattr(self, "param_neck", 28.0),
                "shL": getattr(self, "param_sh_l", 25.0),
                "shR": getattr(self, "param_sh_r", 40.0),
                "elL": self.metrics.get("avg_elbow_l", 98.0),
                "elR": self.metrics.get("avg_elbow_r", 101.0),
                "dur": getattr(self, "param_dur", 25.0),
                "F": getattr(self, "param_fatigue_f", 0.45),
                "therblig": "✊ TOMAR (G)" if self.metrics.get("tomar_count", 0) > self.metrics.get("soltar_count", 0) else "🖐️ SOLTAR (RL)"
            }
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
            os.makedirs(assets_dir, exist_ok=True)
            json_path = os.path.join(assets_dir, "cronogrulla_current_state.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
                
            desktop_html = r"c:\Users\dsant\Desktop\atlas3d_cronogrulla.html"
            assets_html = os.path.join(assets_dir, "atlas3d_cronogrulla.html")
            target_html = desktop_html if os.path.exists(desktop_html) else assets_html
            
            if os.name == 'nt' and os.path.exists(target_html):
                try:
                    os.startfile(target_html)
                except Exception:
                    webbrowser.open_new_tab(f"file:///{target_html.replace(os.sep, '/')}")
            else:
                webbrowser.open_new_tab(f"file:///{target_html.replace(os.sep, '/')}")
        except Exception as e:
            print(f"[ModeloLesiones3D] Error abriendo Atlas 3D WebGL: {e}")

    def _build_muscle_geometry_3d(self, sh_l, sh_r, el_l, el_r, wr_l, wr_r, spine_pts, neck_dy, shoulder_dy, rk, eff_yaw, eff_pitch):
        """Construye las mallas 3D poligonales de los 10 grupos musculares (ISO 11226) con sombreado de profundidad."""
        muscle_items = []
        
        # 1. Deltoides Izquierdo y Derecho (Capuchón tridimensional sobre el hombro)
        for side, sh_pos, el_pos, s_key, sx in [("L", sh_l, el_l, "delL", -1.0), ("R", sh_r, el_r, "delR", 1.0)]:
            r_val = rk.get(s_key, 0.45)
            col = self.get_risk_color(r_val)
            dx, dy, dz = el_pos[0] - sh_pos[0], el_pos[1] - sh_pos[1], el_pos[2] - sh_pos[2]
            
            top_pt = (sh_pos[0], sh_pos[1] - 8, sh_pos[2])
            ant_pt = (sh_pos[0] + sx * 16, sh_pos[1] + 8, sh_pos[2] + 16)
            lat_pt = (sh_pos[0] + sx * 22, sh_pos[1] + 16, sh_pos[2])
            post_pt = (sh_pos[0] + sx * 16, sh_pos[1] + 8, sh_pos[2] - 16)
            ins_pt = (sh_pos[0] + dx * 0.35, sh_pos[1] + dy * 0.35, sh_pos[2] + dz * 0.35)
            
            faces = [
                [top_pt, ant_pt, lat_pt, ins_pt],
                [top_pt, lat_pt, post_pt, ins_pt]
            ]
            for face in faces:
                avg_z = np.mean([self.rotate_point_3d(p[0], p[1], p[2], eff_yaw, eff_pitch)[2] for p in face])
                fill_col = col if avg_z > -40 else "#091728"
                muscle_items.append({
                    "type": "polygon",
                    "points": face,
                    "z": avg_z + 3,
                    "fill": fill_col,
                    "outline": col,
                    "width": 2 if avg_z > 0 else 1,
                    "muscle_key": s_key
                })

        # 2. Bíceps Braquial (Vientre anterior con abultamiento dinámico en flexión)
        for side, sh_pos, el_pos, s_key, sx in [("L", sh_l, el_l, "bicL", -1.0), ("R", sh_r, el_r, "bicR", 1.0)]:
            r_val = rk.get(s_key, 0.45)
            col = self.get_risk_color(r_val)
            mid_x = (sh_pos[0] + el_pos[0]) / 2.0
            mid_y = (sh_pos[1] + el_pos[1]) / 2.0
            mid_z = (sh_pos[2] + el_pos[2]) / 2.0
            
            bic_pts = [
                (sh_pos[0] + sx * 6, sh_pos[1] + 18, sh_pos[2] + 10),
                (mid_x + sx * 10, mid_y, mid_z + 18),
                (el_pos[0] + sx * 4, el_pos[1] - 8, el_pos[2] + 12),
                (mid_x - sx * 4, mid_y, mid_z + 14)
            ]
            avg_z = np.mean([self.rotate_point_3d(p[0], p[1], p[2], eff_yaw, eff_pitch)[2] for p in bic_pts])
            muscle_items.append({
                "type": "polygon",
                "points": bic_pts,
                "z": avg_z + 4,
                "fill": col if avg_z > -40 else "#081524",
                "outline": col,
                "width": 2 if avg_z > 0 else 1,
                "muscle_key": s_key
            })

        # 3. Tríceps Braquial (Vientre posterior)
        for side, sh_pos, el_pos, s_key, sx in [("L", sh_l, el_l, "triL", -1.0), ("R", sh_r, el_r, "triR", 1.0)]:
            r_val = rk.get(s_key, 0.45)
            col = self.get_risk_color(r_val)
            mid_x = (sh_pos[0] + el_pos[0]) / 2.0
            mid_y = (sh_pos[1] + el_pos[1]) / 2.0
            mid_z = (sh_pos[2] + el_pos[2]) / 2.0
            
            tri_pts = [
                (sh_pos[0] + sx * 4, sh_pos[1] + 16, sh_pos[2] - 10),
                (mid_x + sx * 8, mid_y, mid_z - 18),
                (el_pos[0] + sx * 2, el_pos[1] - 6, el_pos[2] - 12),
                (mid_x - sx * 4, mid_y, mid_z - 14)
            ]
            avg_z = np.mean([self.rotate_point_3d(p[0], p[1], p[2], eff_yaw, eff_pitch)[2] for p in tri_pts])
            muscle_items.append({
                "type": "polygon",
                "points": tri_pts,
                "z": avg_z + 2,
                "fill": col if avg_z > -40 else "#081524",
                "outline": col,
                "width": 2 if avg_z > 0 else 1,
                "muscle_key": s_key
            })

        # 4. Trapecios (Manto dorsal cervical/escapular)
        for side, sh_pos, s_key, sx in [("L", sh_l, "trapL", -1.0), ("R", sh_r, "trapR", 1.0)]:
            r_val = rk.get(s_key, 0.45)
            col = self.get_risk_color(r_val)
            trap_pts = [
                (0, -110 + neck_dy, -14),
                (0, -70 + shoulder_dy * 0.5, -24),
                (sh_pos[0] * 0.72, sh_pos[1] - 4, sh_pos[2] - 14),
                (0, 15, -30)
            ]
            avg_z = np.mean([self.rotate_point_3d(p[0], p[1], p[2], eff_yaw, eff_pitch)[2] for p in trap_pts])
            muscle_items.append({
                "type": "polygon",
                "points": trap_pts,
                "z": avg_z + 1,
                "fill": col if avg_z > -40 else "#071220",
                "outline": col,
                "width": 2 if avg_z > 0 else 1,
                "muscle_key": s_key
            })

        # 5. Erectores Espinales / Paravertebrales Dorsales
        for side, s_key, sx in [("L", "erL", -1.0), ("R", "erR", 1.0)]:
            r_val = rk.get(s_key, 0.45)
            col = self.get_risk_color(r_val)
            er_pts = [
                (sx * 10, -50, -28),
                (sx * 16, -50, -28),
                (sx * 16, 85, -26),
                (sx * 10, 85, -26)
            ]
            avg_z = np.mean([self.rotate_point_3d(p[0], p[1], p[2], eff_yaw, eff_pitch)[2] for p in er_pts])
            muscle_items.append({
                "type": "polygon",
                "points": er_pts,
                "z": avg_z + 1,
                "fill": col if avg_z > -40 else "#06101c",
                "outline": col,
                "width": 2 if avg_z > 0 else 1,
                "muscle_key": s_key
            })

        return muscle_items


    def build_ui(self):
        # ── 1. ENCABEZADO Y CONTROLES ─────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color=("#ffffff", "#1e293b"), corner_radius=12)
        top_bar.pack(fill="x", padx=15, pady=(10, 5))
        
        title_f = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_f.pack(side="left", padx=15, pady=8)
        
        ctk.CTkLabel(title_f, text="🦴 MODELO 3D DE LESIONES & BIOMECÁNICA", 
                     font=ctk.CTkFont(size=16, weight="bold"), text_color="#3498db").pack(anchor="w")
        ctk.CTkLabel(title_f, text="Maniquí 3D Interactivo (Rotación 360° · Cinemática Humana & Respiración · Contornos Hombre / Mujer · Daño Osteomuscular)", 
                     font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(anchor="w")

        controls_f = ctk.CTkFrame(top_bar, fg_color="transparent")
        controls_f.pack(side="right", padx=15, pady=8)
        
        # Botón Rápido de Maximización del Panel Clínico
        self.btn_top_expand = ctk.CTkButton(controls_f, text="⛶ Ampliar Panel", command=self.toggle_panel_expand, 
                                            width=110, height=28, fg_color="#2563eb", hover_color="#1d4ed8",
                                            font=ctk.CTkFont(size=11, weight="bold"))
        self.btn_top_expand.pack(side="left", padx=(0, 6))

        # Botón Lanzador Atlas 3D WebGL (Three.js)
        self.btn_webgl_atlas = ctk.CTkButton(controls_f, text="🌐 Atlas 3D Web", command=self.open_webgl_atlas, 
                                             width=110, height=28, fg_color="#0284c7", hover_color="#0369a1",
                                             font=ctk.CTkFont(size=11, weight="bold"))
        self.btn_webgl_atlas.pack(side="left", padx=(0, 8))

        # Operario
        ctk.CTkLabel(controls_f, text="Operario:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        op_list = ["Todos"] + [str(o if isinstance(o, str) else o.get("name")) for o in self.app.operator_data]
        self.combo_op = ctk.CTkOptionMenu(controls_f, values=op_list, variable=self.selected_operator,
                                          command=self.on_param_changed, width=110, height=28)
        self.combo_op.pack(side="left", padx=(0, 8))

        # Género (Contorno de Maniquí: Hombre / Mujer)
        ctk.CTkLabel(controls_f, text="Contorno:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.btn_gender = ctk.CTkSegmentedButton(controls_f, values=["Mujer ♀", "Hombre ♂"],
                                                  command=self.on_gender_toggled, height=28)
        self.btn_gender.set("Mujer ♀" if self.selected_gender.get() == "Femenino" else "Hombre ♂")
        self.btn_gender.pack(side="left", padx=(0, 8))

        # Selector de Cinemática Humana (Respiración / Plegado Completo / Articular Zona / Estático)
        ctk.CTkLabel(controls_f, text="Movimiento:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.combo_motion = ctk.CTkOptionMenu(
            controls_f,
            values=["🫁 Respiración", "⚙️ Plegado Completo (Hombro-Codo-Mano-Dedos)", "🎯 Articular Zona Seleccionada", "⏸ Estático"],
            command=self.on_motion_mode_changed,
            width=190, height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#059669", button_color="#047857", button_hover_color="#065f46"
        )
        self.combo_motion.set("🫁 Respiración")
        self.combo_motion.pack(side="left", padx=(0, 8))

        # Botón Auto-Giro 360°
        self.btn_autorotate = ctk.CTkButton(controls_f, text="▶ Giro 360°", command=self.toggle_autorotate, 
                                           width=85, height=28, fg_color="#6366f1", hover_color="#4f46e5")
        self.btn_autorotate.pack(side="left", padx=(0, 6))

        # Reset Vista 3D
        btn_reset = ctk.CTkButton(controls_f, text="🔄 Reset", command=self.reset_view_3d, 
                                  width=68, height=28, fg_color="#475569", hover_color="#64748b")
        btn_reset.pack(side="left")

        # ── 2. CONTENEDOR PRINCIPAL CON SEPARADOR REDIMENSIONABLE Y AMPLIACIÓN ──
        self.content_f = ctk.CTkFrame(self, fg_color="transparent")
        self.content_f.pack(fill="both", expand=True, padx=12, pady=5)
        
        # Grid unificado para redimensionamiento porcentual exacto sin bloqueos
        self.content_f.grid_columnconfigure(0, weight=self.left_weight, uniform="main_cols")
        self.content_f.grid_columnconfigure(1, weight=0) # Barra separadora arrastrable
        self.content_f.grid_columnconfigure(2, weight=self.right_weight, uniform="main_cols")
        self.content_f.grid_rowconfigure(0, weight=1)

        # ── PANEL IZQUIERDO: VISUALIZADOR DEL MANIQUÍ 3D ──────────────────────
        left_box = ctk.CTkFrame(self.content_f, fg_color=("#ffffff", "#0f172a"), corner_radius=12)
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        self.left_box = left_box
        
        # Barra superior compacta con Selector de Perspectivas 360° y Zoom
        rot_bar = ctk.CTkFrame(left_box, fg_color="transparent", height=35)
        rot_bar.pack(fill="x", padx=8, pady=(6, 2))
        
        ctk.CTkLabel(rot_bar, text="Vista:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(4, 4))
        
        self.combo_view = ctk.CTkOptionMenu(
            rot_bar,
            values=["👤 Frente (0°)", "📐 Persp. D (45°)", "📐 Perfil D (90°)", "🔙 Espalda (180°)", "📐 Perfil I (270°)", "📐 Persp. I (315°)", "🔝 Cenital"],
            command=self.on_view_preset_selected,
            width=130, height=26, font=ctk.CTkFont(size=10, weight="bold")
        )
        self.combo_view.pack(side="left", padx=(0, 4))

        # Selector de Capa Visual (Músculos 3D + Esqueleto)
        ctk.CTkLabel(rot_bar, text="Capa:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(6, 3))
        self.combo_layer_mode = ctk.CTkOptionMenu(
            rot_bar,
            values=["⚡ Completo (Músculos+Esqueleto)", "💪 Músculos 3D (ISO 11226)", "🦴 Esqueleto & Holograma", "🔬 Rayos X"],
            command=lambda v: self.draw_mannequin_3d(),
            variable=self.visual_layer_mode,
            width=175, height=26, font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#1e293b", button_color="#334155"
        )
        self.combo_layer_mode.pack(side="left", padx=(0, 4))

        # Controles de Zoom
        ctk.CTkButton(rot_bar, text="➕", command=self.zoom_in, width=28, height=24, 
                      fg_color="#3498db", hover_color="#2980b9").pack(side="right", padx=1)
        ctk.CTkButton(rot_bar, text="➖", command=self.zoom_out, width=28, height=24, 
                      fg_color="#3498db", hover_color="#2980b9").pack(side="right", padx=1)

        # Canvas 3D
        self.canvas_w = 400
        self.canvas_h = 450
        self.canvas = tk.Canvas(left_box, bg="#070d19", highlightthickness=0, cursor="fleur")
        self.canvas.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        
        # Eventos del Canvas: Rotación 360° con ratón, rueda de zoom y clics en articulaciones
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_canvas_wheel)
        self.canvas.bind("<Configure>", lambda e: self.draw_mannequin_3d())

        # Instrucción de uso
        hint_lbl = ctk.CTkLabel(left_box, text="💡 Arrastra el ratón para rotar en 360° · Rueda para Zoom",
                                font=ctk.CTkFont(size=10, slant="italic"), text_color="#64748b")
        hint_lbl.pack(pady=(0, 4))

        # ── SEPARADOR ARRASTRABLE HORIZONTAL (SPLITTER INTERACTIVO) ───────────
        self.splitter = ctk.CTkFrame(self.content_f, width=14, fg_color=("#94a3b8", "#334155"), corner_radius=6, cursor="sb_h_double_arrow")
        self.splitter.grid(row=0, column=1, sticky="ns", padx=2, pady=10)
        
        lbl_grip = ctk.CTkLabel(self.splitter, text="⋮", font=ctk.CTkFont(size=16, weight="bold"), text_color="#38bdf8")
        lbl_grip.pack(expand=True)
        
        self.splitter.bind("<Enter>", lambda e: self.splitter.configure(fg_color="#38bdf8"))
        self.splitter.bind("<Leave>", lambda e: self.splitter.configure(fg_color=("#94a3b8", "#334155")))
        self.splitter.bind("<ButtonPress-1>", self.on_splitter_press)
        self.splitter.bind("<B1-Motion>", self.on_splitter_drag)
        self.splitter.bind("<ButtonRelease-1>", self.on_splitter_release)
        lbl_grip.bind("<B1-Motion>", self.on_splitter_drag)
        lbl_grip.bind("<ButtonRelease-1>", self.on_splitter_release)

        # ── PANEL DERECHO: SIMULACIÓN TEMPORAL Y DIAGNÓSTICO PATOLÓGICO ───────
        right_box = ctk.CTkScrollableFrame(
            self.content_f, fg_color=("#ffffff", "#1e293b"), corner_radius=12,
            scrollbar_button_color="#38bdf8", scrollbar_button_hover_color="#0284c7"
        )
        right_box.grid(row=0, column=2, sticky="nsew", padx=(2, 0), pady=0)
        self.right_box = right_box
        right_box.bind("<Configure>", self.on_right_box_configure)

        # 1. Barra de control de tamaño del panel clínico (Botones de Ampliación de 2 Filas)
        size_bar = ctk.CTkFrame(right_box, fg_color=("#f1f5f9", "#0f172a"), corner_radius=10)
        size_bar.pack(fill="x", padx=10, pady=(6, 6))
        
        # Fila 1: Título del panel
        s_row1 = ctk.CTkFrame(size_bar, fg_color="transparent")
        s_row1.pack(fill="x", padx=10, pady=(6, 4))
        ctk.CTkLabel(s_row1, text="📋 PANEL CLÍNICO Y DIAGNÓSTICO", 
                     font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8").pack(side="left")
        
        self.lbl_panel_pct = ctk.CTkLabel(s_row1, text=f"Ancho actual: {self.right_weight}%", 
                                           font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8")
        self.lbl_panel_pct.pack(side="right")

        # Fila 2: Presets Rápidos de Ampliación
        s_row2 = ctk.CTkFrame(size_bar, fg_color="transparent")
        s_row2.pack(fill="x", padx=10, pady=(0, 6))
        
        ctk.CTkLabel(s_row2, text="Ampliación:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 6))
        
        presets = [
            ("◱ 50%", 50),
            ("⛶ 65%", 65),
            ("⛶ 75% Amplio", 75),
            ("⛶ 85% Máximo", 85),
            ("◀ 92% Pantalla Completa", 92)
        ]
        for label, ratio in presets:
            b = ctk.CTkButton(s_row2, text=label, command=lambda r=ratio: self.set_split_percent(r),
                              height=26, fg_color=("#e2e8f0", "#1e293b"), text_color=("#1e293b", "#f8fafc"),
                              hover_color=("#cbd5e1", "#334155"), font=ctk.CTkFont(size=10, weight="bold"))
            b.pack(side="left", padx=2, fill="x", expand=True)

        # 2. Proyección Temporal (Botones amplios de 2 filas para que no se corten los textos)
        time_card = ctk.CTkFrame(right_box, fg_color=("#f1f5f9", "#0f172a"), corner_radius=10)
        time_card.pack(fill="x", padx=10, pady=(4, 8))
        
        ctk.CTkLabel(time_card, text="⏱️ SIMULACIÓN TEMPORAL DE LESIONES:", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8").pack(anchor="w", padx=10, pady=(8, 2))
        self.lbl_time_sub = ctk.CTkLabel(time_card, text="¿Cómo repercute en el cuerpo seguir trabajando con este método a lo largo del tiempo?", 
                                         font=ctk.CTkFont(size=11), text_color="#94a3b8", anchor="w", justify="left")
        self.lbl_time_sub.pack(fill="x", padx=10, pady=(0, 6))
        
        # Fila 1: Corto Plazo (1 a 6 meses)
        row1_f = ctk.CTkFrame(time_card, fg_color="transparent")
        row1_f.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(row1_f, text="Corto Plazo:", font=ctk.CTkFont(size=11, weight="bold"), width=85, anchor="w").pack(side="left")
        self.seg_time_short = ctk.CTkSegmentedButton(row1_f, values=["1 Mes", "3 Meses", "6 Meses"], 
                                                      command=self.on_short_horizon_selected, height=30)
        self.seg_time_short.pack(side="left", fill="x", expand=True)

        # Fila 2: Largo Plazo (1 a 5 años)
        row2_f = ctk.CTkFrame(time_card, fg_color="transparent")
        row2_f.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(row2_f, text="Largo Plazo:", font=ctk.CTkFont(size=11, weight="bold"), width=85, anchor="w").pack(side="left")
        self.seg_time_long = ctk.CTkSegmentedButton(row2_f, values=["1 Año", "2 Años", "3 Años", "5 Años"], 
                                                     command=self.on_long_horizon_selected, height=30)
        self.seg_time_long.pack(side="left", fill="x", expand=True)
        
        # Sincronizar selección inicial
        self._sync_horizon_buttons(self.selected_horizon.get())

        # Barra de Daño Global Acumulado
        score_f = ctk.CTkFrame(time_card, fg_color="transparent")
        score_f.pack(fill="x", padx=10, pady=(0, 6))
        
        ctk.CTkLabel(score_f, text="Índice de Sobrecarga Global:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.lbl_global_score = ctk.CTkLabel(score_f, text="68% (Riesgo Alto)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#e67e22")
        self.lbl_global_score.pack(side="right")
        
        self.prog_bar = ctk.CTkProgressBar(time_card, height=10, progress_color="#e67e22")
        self.prog_bar.set(0.68)
        self.prog_bar.pack(fill="x", padx=10, pady=(0, 8))

        # ── SECCIÓN MUSCULAR & BIOMECÁNICA ISO 11226 ──────────────────────────
        muscle_card = ctk.CTkFrame(right_box, fg_color=("#f1f5f9", "#0f172a"), corner_radius=10)
        muscle_card.pack(fill="x", padx=10, pady=(4, 8))
        self.muscle_card = muscle_card
        
        m_head_f = ctk.CTkFrame(muscle_card, fg_color="transparent")
        m_head_f.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(m_head_f, text="💪 TELEMETRÍA MUSCULAR (ISO 11226)", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8").pack(side="left")
                     
        self.lbl_iso_global = ctk.CTkLabel(m_head_f, text="Fatiga F: 0.42", 
                                           font=ctk.CTkFont(size=11, weight="bold"), text_color="#f59e0b")
        self.lbl_iso_global.pack(side="right")
        
        # Botones de Simulación de Turno y Escenarios Rápidos
        m_btn_f = ctk.CTkFrame(muscle_card, fg_color="transparent")
        m_btn_f.pack(fill="x", padx=10, pady=(0, 6))
        
        self.btn_sim_shift = ctk.CTkButton(m_btn_f, text="▶ Simular Turno", command=self.toggle_shift_simulation,
                                           height=26, fg_color="#0284c7", hover_color="#0369a1",
                                           font=ctk.CTkFont(size=10, weight="bold"))
        self.btn_sim_shift.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        btn_reset_scen = ctk.CTkButton(m_btn_f, text="🔄 Reset Postura", command=lambda: self.apply_scenario_preset("neutral"),
                                       height=26, fg_color="#334155", hover_color="#475569",
                                       font=ctk.CTkFont(size=10, weight="bold"))
        btn_reset_scen.pack(side="left", fill="x", expand=True)

        # Fila de Escenarios
        scen_f = ctk.CTkFrame(muscle_card, fg_color="transparent")
        scen_f.pack(fill="x", padx=10, pady=(0, 8))
        scens = [
            ("🟢 Neutra", "neutral"),
            ("🟡 Alcance", "reach"),
            ("🟠 Plegado", "fold"),
            ("🔴 Crítica", "critical")
        ]
        for s_lbl, s_key in scens:
            b = ctk.CTkButton(scen_f, text=s_lbl, command=lambda k=s_key: self.apply_scenario_preset(k),
                              height=22, fg_color=("#e2e8f0", "#1e293b"), text_color=("#1e293b", "#f8fafc"),
                              hover_color=("#cbd5e1", "#334155"), font=ctk.CTkFont(size=9, weight="bold"))
            b.pack(side="left", fill="x", expand=True, padx=1)

        # Contenedor de barras para los 10 grupos musculares
        m_bars_f = ctk.CTkFrame(muscle_card, fg_color=("#ffffff", "#1e293b"), corner_radius=8)
        m_bars_f.pack(fill="x", padx=10, pady=(0, 8))
        
        muscle_names = [
            ("trapL", "Trapecio Izq."), ("trapR", "Trapecio Der."),
            ("delL", "Deltoides Izq."), ("delR", "Deltoides Der."),
            ("bicL", "Bíceps Izq."), ("bicR", "Bíceps Der."),
            ("triL", "Tríceps Izq."), ("triR", "Tríceps Der."),
            ("erL", "Erector Espinal I."), ("erR", "Erector Espinal D.")
        ]
        
        for k, name in muscle_names:
            row = ctk.CTkFrame(m_bars_f, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            
            lbl_n = ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=10, weight="bold"), width=105, anchor="w")
            lbl_n.pack(side="left")
            
            pbar = ctk.CTkProgressBar(row, height=8, progress_color="#10b981")
            pbar.set(0.2)
            pbar.pack(side="left", fill="x", expand=True, padx=6)
            
            lbl_v = ctk.CTkLabel(row, text="20%", font=ctk.CTkFont(size=10, weight="bold"), width=32, anchor="e")
            lbl_v.pack(side="right")
            
            self.muscle_bars[k] = pbar
            self.muscle_val_labels[k] = lbl_v

        # 3. Tarjeta de Diagnóstico Patológico (Zona Seleccionada)
        self.diag_card = ctk.CTkFrame(right_box, fg_color=("#f1f5f9", "#0f172a"), corner_radius=10)
        self.diag_card.pack(fill="x", padx=10, pady=4)
        
        self.lbl_zone_name = ctk.CTkLabel(self.diag_card, text="MUÑECA Y MANO DERECHA", 
                                          font=ctk.CTkFont(size=14, weight="bold"), text_color="#e74c3c",
                                          anchor="w", justify="left")
        self.lbl_zone_name.pack(fill="x", padx=12, pady=(10, 2))
        
        self.lbl_zone_tissue = ctk.CTkLabel(self.diag_card, text="Túnel Carpiano, Tendones Flexores", 
                                           font=ctk.CTkFont(size=11, slant="italic"), text_color="#94a3b8",
                                           anchor="w", justify="left")
        self.lbl_zone_tissue.pack(fill="x", padx=12, pady=(0, 6))

        # Métricas Reales en Bloques Independientes (No solapan nunca)
        metrics_box = ctk.CTkFrame(self.diag_card, fg_color=("#ffffff", "#1e293b"), corner_radius=8)
        metrics_box.pack(fill="x", padx=10, pady=4)
        
        # Bloque 1: Ángulo articular
        m_f1 = ctk.CTkFrame(metrics_box, fg_color=("#f8fafc", "#0f172a"), corner_radius=6)
        m_f1.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(m_f1, text="📐 Ángulo articular registrado:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8").pack(anchor="w", padx=8, pady=(4, 1))
        self.lbl_zone_angle = ctk.CTkLabel(m_f1, text="95.1° (Flexión activa)", font=ctk.CTkFont(size=11), text_color=("#1e293b", "#e2e8f0"), anchor="w", justify="left")
        self.lbl_zone_angle.pack(fill="x", padx=8, pady=(0, 4))
        
        # Bloque 2: Micromovimiento Therblig
        m_f2 = ctk.CTkFrame(metrics_box, fg_color=("#f8fafc", "#0f172a"), corner_radius=6)
        m_f2.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(m_f2, text="✊ Micromovimiento (Therblig):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#c084fc").pack(anchor="w", padx=8, pady=(4, 1))
        self.lbl_zone_therblig = ctk.CTkLabel(m_f2, text="TOMAR (G) 100%", font=ctk.CTkFont(size=11), text_color=("#1e293b", "#e2e8f0"), anchor="w", justify="left")
        self.lbl_zone_therblig.pack(fill="x", padx=8, pady=(0, 4))
        
        # Bloque 3: Susceptibilidad por Género
        m_f3 = ctk.CTkFrame(metrics_box, fg_color=("#f8fafc", "#0f172a"), corner_radius=6)
        m_f3.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(m_f3, text="🧬 Susceptibilidad anatómica por género:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#34d399").pack(anchor="w", padx=8, pady=(4, 1))
        self.lbl_zone_gender = ctk.CTkLabel(m_f3, text="+25% vulnerabilidad en túnel carpiano femenino", font=ctk.CTkFont(size=11), text_color=("#1e293b", "#e2e8f0"), anchor="w", justify="left")
        self.lbl_zone_gender.pack(fill="x", padx=8, pady=(0, 4))

        # Proyección Clínica / Pronóstico Médico Ocupacional (CIE-10)
        prognosis_f = ctk.CTkFrame(self.diag_card, fg_color=("#ffffff", "#1e293b"), corner_radius=8)
        prognosis_f.pack(fill="x", padx=10, pady=(6, 10))
        
        ctk.CTkLabel(prognosis_f, text="🩺 Diagnóstico Proyectado en Salud Ocupacional:", 
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="#f1c40f").pack(anchor="w", padx=10, pady=(8, 2))
        
        self.lbl_diag_cie = ctk.CTkLabel(prognosis_f, text="CIE-10: G56.0 Síndrome del Túnel Carpiano Grado II", 
                                         font=ctk.CTkFont(size=12, weight="bold"), text_color="#e74c3c", anchor="w", justify="left")
        self.lbl_diag_cie.pack(fill="x", padx=10, pady=2)
        
        self.lbl_diag_desc = ctk.CTkLabel(prognosis_f, text="Descripción clínica detallada...", 
                                          font=ctk.CTkFont(size=11), text_color=("#475569", "#cbd5e1"), 
                                          anchor="w", justify="left")
        self.lbl_diag_desc.pack(fill="x", padx=10, pady=(2, 8))

        # Escala de Dolor Proyectado (EVA)
        eva_f = ctk.CTkFrame(prognosis_f, fg_color=("#f8fafc", "#0f172a"), corner_radius=6)
        eva_f.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(eva_f, text="Nivel Dolor Proyectado (Escala EVA):", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8, pady=4)
        self.lbl_eva = ctk.CTkLabel(eva_f, text="7 / 10 — Nivel Severo", font=ctk.CTkFont(size=11, weight="bold"), text_color="#e74c3c")
        self.lbl_eva.pack(side="right", padx=8, pady=4)

        # 4. Medidas Correctivas de Ingeniería de Métodos
        recom_card = ctk.CTkFrame(right_box, fg_color=("#f1f5f9", "#0f172a"), corner_radius=10)
        recom_card.pack(fill="x", padx=10, pady=(4, 10))
        
        ctk.CTkLabel(recom_card, text="🛡️ Intervenciones Ergonómicas Preventivas:", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#2ecc71").pack(anchor="w", padx=10, pady=(8, 4))
        
        self.lbl_recom_text = ctk.CTkLabel(recom_card, text="", font=ctk.CTkFont(size=11), 
                                           text_color=("#334155", "#94a3b8"), justify="left")
        self.lbl_recom_text.pack(fill="x", padx=10, pady=(0, 10))

        # Actualizar datos
        self.update_diagnostic_panel()
        
        # Enlazar eventos de desplazamiento de rueda del ratón y teclado a todo el árbol del panel
        self._bind_scroll_recursive(self.right_box)

    # ── VINCULACIÓN DEL DESPLAZAMIENTO RECURSIVO (RUEDA Y BARRAS) ───────────────
    def _bind_scroll_recursive(self, widget):
        """Enlaza el desplazamiento de la rueda del ratón a cada elemento hijo del panel."""
        def _on_wheel(e):
            if hasattr(self, 'right_box') and self.right_box.winfo_exists():
                delta = -1 * int(e.delta / 40) if e.delta else 0
                try:
                    self.right_box._parent_canvas.yview_scroll(delta, "units")
                except Exception:
                    pass
            return "break"
            
        def _on_wheel_up(e):
            if hasattr(self, 'right_box') and self.right_box.winfo_exists():
                try:
                    self.right_box._parent_canvas.yview_scroll(-2, "units")
                except Exception:
                    pass
            return "break"
            
        def _on_wheel_down(e):
            if hasattr(self, 'right_box') and self.right_box.winfo_exists():
                try:
                    self.right_box._parent_canvas.yview_scroll(2, "units")
                except Exception:
                    pass
            return "break"

        try:
            widget.bind("<MouseWheel>", _on_wheel, add="+")
            widget.bind("<Button-4>", _on_wheel_up, add="+")
            widget.bind("<Button-5>", _on_wheel_down, add="+")
        except Exception:
            pass
            
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child)

    # ── MÉTODOS DE REDIMENSIONAMIENTO DEL PANEL CLÍNICO ───────────────────────
    def on_splitter_press(self, event):
        self.splitter_start_x = event.x_root
        self.splitter.configure(fg_color="#38bdf8")

    def on_splitter_drag(self, event):
        total_w = self.content_f.winfo_width()
        if total_w < 350: return
        
        mouse_x = event.x_root - self.content_f.winfo_rootx()
        left_pct = int(max(8, min(80, (mouse_x / float(total_w)) * 100)))
        right_pct = 100 - left_pct
        
        self.set_split_percent(right_pct)

    def on_splitter_release(self, event):
        self.splitter.configure(fg_color=("#94a3b8", "#334155"))

    def set_split_percent(self, right_pct):
        """Ajusta el porcentaje de ancho del panel de diagnóstico (hasta 92% máx)."""
        self.right_weight = max(20, min(92, right_pct))
        self.left_weight = 100 - self.right_weight
        
        self.content_f.grid_columnconfigure(0, weight=self.left_weight, uniform="main_cols")
        self.content_f.grid_columnconfigure(1, weight=0)
        self.content_f.grid_columnconfigure(2, weight=self.right_weight, uniform="main_cols")
        
        if hasattr(self, 'lbl_panel_pct') and self.lbl_panel_pct.winfo_exists():
            self.lbl_panel_pct.configure(text=f"Ancho actual: {self.right_weight}%")
            
        self.update_idletasks()
        self.draw_mannequin_3d()
        self._update_expand_button_state()

    def toggle_panel_expand(self):
        """Alterna entre vista equilibrada (50%) y vista amplia (75%)."""
        if self.right_weight < 70:
            self.set_split_percent(75)
        else:
            self.set_split_percent(50)

    def _update_expand_button_state(self):
        txt = "◱ Reducir (50%)" if self.right_weight >= 70 else "⛶ Ampliar (75%)"
        col = "#f59e0b" if self.right_weight >= 70 else "#2563eb"
        hcol = "#d97706" if self.right_weight >= 70 else "#1d4ed8"
        
        if hasattr(self, 'btn_top_expand') and self.btn_top_expand.winfo_exists():
            self.btn_top_expand.configure(text=txt, fg_color=col, hover_color=hcol)

    def on_right_box_configure(self, event):
        """Ajusta dinámicamente el salto de línea de todos los textos al cambiar el ancho del panel."""
        avail_w = max(220, event.width - 50)
        labels_to_wrap = [
            self.lbl_zone_name, self.lbl_zone_tissue, self.lbl_diag_cie, 
            self.lbl_diag_desc, self.lbl_recom_text, self.lbl_zone_angle,
            self.lbl_zone_therblig, self.lbl_zone_gender, self.lbl_time_sub
        ]
        for lbl in labels_to_wrap:
            if hasattr(lbl, '_name') or lbl.winfo_exists():
                try:
                    lbl.configure(wraplength=avail_w)
                except Exception:
                    pass

    # ── MÉTODOS DE HORIZONTE TEMPORAL EN 2 FILAS ──────────────────────────────
    def on_short_horizon_selected(self, val):
        if val:
            if hasattr(self, 'seg_time_long'):
                self.seg_time_long.set("")
            self.on_horizon_changed(val)

    def on_long_horizon_selected(self, val):
        if val:
            if hasattr(self, 'seg_time_short'):
                self.seg_time_short.set("")
            self.on_horizon_changed(val)

    def _sync_horizon_buttons(self, val):
        if val in ["1 Mes", "3 Meses", "6 Meses"]:
            if hasattr(self, 'seg_time_short'): self.seg_time_short.set(val)
            if hasattr(self, 'seg_time_long'): self.seg_time_long.set("")
        else:
            if hasattr(self, 'seg_time_short'): self.seg_time_short.set("")
            if hasattr(self, 'seg_time_long'): self.seg_time_long.set(val)

    # ── MÉTODOS DE ANIMACIÓN, CINEMÁTICA HUMANA Y ROTACIÓN 360° ───────────────
    def set_angles(self, yaw_deg, pitch_deg):
        self.yaw = math.radians(yaw_deg)
        self.pitch = math.radians(pitch_deg)
        self.draw_mannequin_3d()

    def on_view_preset_selected(self, val):
        if "0°" in val or "Frente" in val:
            self.set_angles(0, 0)
        elif "45°" in val:
            self.set_angles(45, 0)
        elif "90°" in val:
            self.set_angles(90, 0)
        elif "180°" in val or "Espalda" in val:
            self.set_angles(180, 0)
        elif "270°" in val:
            self.set_angles(270, 0)
        elif "315°" in val:
            self.set_angles(315, 0)
        elif "Cenital" in val:
            self.set_angles(25, 30)

    def on_motion_mode_changed(self, val):
        self.human_motion_mode.set(val)
        if "Respiración" in val:
            self.combo_motion.configure(fg_color="#059669", button_color="#047857", button_hover_color="#065f46")
            self._start_animation_loop()
        elif "Plegado" in val or "Trabajo" in val:
            self.combo_motion.configure(fg_color="#7c3aed", button_color="#6d28d9", button_hover_color="#5b21b6")
            self._start_animation_loop()
        elif "Articular" in val or "Zona" in val:
            self.combo_motion.configure(fg_color="#d97706", button_color="#b45309", button_hover_color="#92400e")
            self._start_animation_loop()
        else:
            self.combo_motion.configure(fg_color="#475569", button_color="#334155", button_hover_color="#1e293b")
            if not self.auto_rotate and self.anim_timer_id:
                try:
                    self.after_cancel(self.anim_timer_id)
                except Exception:
                    pass
                self.anim_timer_id = None
                self.is_animating = False
            self.draw_mannequin_3d()

    def _start_animation_loop(self):
        if not self.is_animating:
            self.is_animating = True
            if self.anim_timer_id:
                try:
                    self.after_cancel(self.anim_timer_id)
                except Exception:
                    pass
            self.anim_timer_id = self.after(33, self._anim_loop)

    def _anim_loop(self):
        mode = self.human_motion_mode.get()
        needs_anim = (mode != "⏸ Estático" or self.auto_rotate or getattr(self, "is_shift_simulating", False))
        
        if not needs_anim:
            self.is_animating = False
            self.anim_timer_id = None
            return

        self.is_animating = True
        
        # 1. Simulación de turno laboral acumulativo si está activa
        if getattr(self, "is_shift_simulating", False):
            self.sim_shift_time += 0.033
            if self.sim_shift_time > 35.0:
                self.sim_shift_time = 0.0
            
        # 2. Giro 360° automático si está activo (incremento suave por frame)
        if self.auto_rotate:
            self.yaw = (self.yaw + math.radians(1.6)) % (2 * math.pi)
            
        # 3. Renderizar maniquí con cinemática humana viva
        self.draw_mannequin_3d()
        
        # 4. Próximo fotograma a ~30 FPS (33 ms)
        self.anim_timer_id = self.after(33, self._anim_loop)

    def toggle_autorotate(self):
        self.auto_rotate = not self.auto_rotate
        if self.auto_rotate:
            self.btn_autorotate.configure(text="⏸ Pausar", fg_color="#ef4444")
            self._start_animation_loop()
        else:
            self.btn_autorotate.configure(text="▶ Giro 360°", fg_color="#6366f1")
            if self.human_motion_mode.get() == "⏸ Estático" and self.anim_timer_id:
                try:
                    self.after_cancel(self.anim_timer_id)
                except Exception:
                    pass
                self.anim_timer_id = None
                self.is_animating = False

    def on_gender_toggled(self, val):
        self.selected_gender.set("Femenino" if "Mujer" in val else "Masculino")
        self.refresh_metrics()
        self.draw_mannequin_3d()
        self.update_diagnostic_panel()

    def on_param_changed(self, _=None):
        op = self.selected_operator.get().lower()
        if op != "todos":
            if any(f in op for f in ["laura", "maria", "ana", "paula", "sofia", "diana"]):
                self.selected_gender.set("Femenino")
                self.btn_gender.set("Mujer ♀")
            elif any(m in op for m in ["diego", "david", "carlos", "juan", "pedro"]):
                self.selected_gender.set("Masculino")
                self.btn_gender.set("Hombre ♂")
                
        self.refresh_metrics()
        self.draw_mannequin_3d()
        self.update_diagnostic_panel()

    def on_horizon_changed(self, val):
        self.selected_horizon.set(val)
        self._sync_horizon_buttons(val)
        self.draw_mannequin_3d()
        self.update_diagnostic_panel()

    def zoom_in(self):
        self.zoom_level = min(3.0, self.zoom_level * 1.2)
        self.draw_mannequin_3d()

    def zoom_out(self):
        self.zoom_level = max(0.5, self.zoom_level / 1.2)
        self.draw_mannequin_3d()

    def reset_view_3d(self):
        self.yaw = math.radians(0)
        self.pitch = math.radians(0)
        self.zoom_level = 1.05
        self.pan_x = 0
        self.pan_y = 0
        self.draw_mannequin_3d()

    def on_canvas_press(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = False

    def on_canvas_drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        if abs(dx) > 1 or abs(dy) > 1:
            self.is_dragging = True
            # Arrastre horizontal -> Rotación en Yaw (360°)
            self.yaw = (self.yaw + dx * 0.012) % (2 * math.pi)
            # Arrastre vertical -> Inclinación leve en Pitch (-35° a +35°)
            self.pitch = max(math.radians(-35), min(math.radians(35), self.pitch - dy * 0.01))
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.draw_mannequin_3d()

    def on_canvas_release(self, event):
        if not self.is_dragging:
            clicked_zone = self.detect_hotspot_click(event.x, event.y)
            if clicked_zone:
                self.selected_zone.set(clicked_zone)
                self.draw_mannequin_3d()
                self.update_diagnostic_panel()

    def on_canvas_wheel(self, event):
        factor = 1.15 if event.delta > 0 else 0.85
        self.zoom_level = max(0.5, min(3.0, self.zoom_level * factor))
        self.draw_mannequin_3d()

    # ── MOTOR DE TRANSFORMACIÓN Y PROYECCIÓN 3D ────────────────────────────────
    def rotate_point_3d(self, x, y, z, yaw=None, pitch=None):
        """Rota un punto (x, y, z) en espacio euclidiano según Yaw y Pitch."""
        curr_yaw = self.yaw if yaw is None else yaw
        curr_pitch = self.pitch if pitch is None else pitch
        
        # 1. Rotación alrededor del eje Y (Yaw 360°)
        cos_y = math.cos(curr_yaw)
        sin_y = math.sin(curr_yaw)
        x1 = x * cos_y - z * sin_y
        z1 = x * sin_y + z * cos_y
        
        # 2. Rotación alrededor del eje X (Pitch)
        cos_p = math.cos(curr_pitch)
        sin_p = math.sin(curr_pitch)
        y2 = y * cos_p - z1 * sin_p
        z2 = y * sin_p + z1 * cos_p
        
        return x1, y2, z2

    def project_3d(self, x, y, z, cx, cy, fov=650, yaw=None, pitch=None):
        """Aplica perspectiva 3D calibrada a las dimensiones del maniquí holográfico."""
        rx, ry, rz = self.rotate_point_3d(x, y, z, yaw, pitch)
        scale = (fov / (fov + rz)) * self.zoom_level
        u = cx + rx * scale + self.pan_x
        v = cy + ry * scale + self.pan_y
        return u, v, rz

    def _compute_hand_and_fingers(self, wrist_pos, hand_pos, is_right=True, fold_factor=0.0):
        """
        Calcula la anatomía 3D realista de la mano con 5 dedos articulados (Pulgar, Índice, Medio, Anular, Meñique)
        y el polígono metacarpiano de la palma. En modo plegado, el pulgar y el índice ejecutan la pinza digital (TOMAR G).
        """
        wx, wy, wz = wrist_pos
        hx, hy, hz = hand_pos
        
        # Vector longitudinal del carpo a la palma
        dx, dy, dz = hx - wx, hy - wy, hz - wz
        len_d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
        fx, fy, fz = dx / len_d, dy / len_d, dz / len_d
        
        # Vector lateral (perpendicular en el plano palmar)
        sign = 1.0 if is_right else -1.0
        rx, ry, rz = -sign * fz, 0.0, sign * fx
        len_r = math.sqrt(rx*rx + ry*ry + rz*rz) or 1.0
        rx, ry, rz = rx / len_r, ry / len_r, rz / len_r
        
        # Vector normal a la palma (dorsal / volar)
        nx = fy * rz - fz * ry
        ny = fz * rx - fx * rz
        nz = fx * ry - fy * rx
        len_n = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
        nx, ny, nz = nx / len_n, ny / len_n, nz / len_n

        # Contorno perimetral del carpo / metacarpo (palma 3D)
        palm_pts = [
            (wx - rx * 6.0, wy, wz - rz * 6.0),
            (wx + rx * 6.0, wy, wz + rz * 6.0),
            (hx + rx * 10.0, hy, hz + rz * 10.0),
            (hx - rx * 8.0, hy, hz - rz * 8.0)
        ]
        
        fingers = {}
        
        # 1. Pulgar (Thumb - 3 articulaciones con oposición activa hacia el índice)
        pinch_curl = fold_factor * 11.0 if is_right else 0.0
        thumb_base = (wx - rx * 5.0 + fx * 5.0, wy + fy * 5.0, wz - rz * 5.0 + fz * 5.0)
        thumb_mid  = (thumb_base[0] - rx * 8.0 + fx * 10.0 - nx * 3.0, 
                      thumb_base[1] + fy * 10.0, 
                      thumb_base[2] - rz * 8.0 + fz * 10.0 - nz * 3.0)
        thumb_tip  = (thumb_mid[0] + rx * pinch_curl + fx * 7.0 + nx * (3.0 if is_right else 0.0), 
                      thumb_mid[1] + fy * 7.0 + (fold_factor * 5.0 if is_right else 0.0), 
                      thumb_mid[2] + rz * pinch_curl + fz * 7.0 + nz * (3.0 if is_right else 0.0))
        fingers["pulgar"] = [thumb_base, thumb_mid, thumb_tip]
        
        # 2. Índice (Index - articulación de flexión hacia el pulgar para cierre de pinza de precisión)
        curl_idx = fold_factor * 6.0 if is_right else 0.0
        idx_base = (hx - rx * 5.0, hy, hz - rz * 5.0)
        idx_mid  = (idx_base[0] + fx * 10.0 - rx * (curl_idx * 0.5), 
                    idx_base[1] + fy * 10.0 + (curl_idx * 0.5), 
                    idx_base[2] + fz * 10.0 - rz * (curl_idx * 0.5))
        idx_tip  = (idx_mid[0] + fx * 8.0 - rx * curl_idx, 
                    idx_mid[1] + fy * 8.0 + (curl_idx * 1.1), 
                    idx_mid[2] + fz * 8.0 - rz * curl_idx)
        fingers["indice"] = [idx_base, idx_mid, idx_tip]
        
        # 3. Medio (Middle - soporte lateral de pinza)
        mid_base = (hx - rx * 1.0, hy, hz - rz * 1.0)
        mid_mid  = (mid_base[0] + fx * 12.0, mid_base[1] + fy * 12.0 + (fold_factor * 3.5 if is_right else 0.0), mid_base[2] + fz * 12.0)
        mid_tip  = (mid_mid[0] + fx * 10.0, mid_mid[1] + fy * 10.0 + (fold_factor * 4.5 if is_right else 0.0), mid_mid[2] + fz * 10.0)
        fingers["medio"] = [mid_base, mid_mid, mid_tip]
        
        # 4. Anular (Ring)
        ring_base = (hx + rx * 3.0, hy, hz + rz * 3.0)
        ring_mid  = (ring_base[0] + fx * 10.0, ring_base[1] + fy * 10.0 + (fold_factor * 2.8 if is_right else 0.0), ring_base[2] + fz * 10.0)
        ring_tip  = (ring_mid[0] + fx * 8.0, ring_mid[1] + fy * 8.0 + (fold_factor * 3.8 if is_right else 0.0), ring_mid[2] + fz * 8.0)
        fingers["anular"] = [ring_base, ring_mid, ring_tip]
        
        # 5. Meñique (Pinky)
        pinky_base = (hx + rx * 7.0, hy, hz + rz * 7.0)
        pinky_mid  = (pinky_base[0] + fx * 8.0, pinky_base[1] + fy * 8.0 + (fold_factor * 2.0 if is_right else 0.0), pinky_base[2] + fz * 8.0)
        pinky_tip  = (pinky_mid[0] + fx * 6.0, pinky_mid[1] + fy * 6.0 + (fold_factor * 2.5 if is_right else 0.0), pinky_mid[2] + fz * 6.0)
        fingers["menique"] = [pinky_base, pinky_mid, pinky_tip]
        
        return palm_pts, fingers

    # ── DIBUJO DEL MANIQUÍ ANATÓMICO 3D (HOLOGRÁFICO DE ANILLOS / ASTRA AI) ────
    def draw_mannequin_3d(self):
        c = self.canvas
        c.delete("all")
        
        w = c.winfo_width() or self.canvas_w
        h = c.winfo_height() or self.canvas_h
        cx = w / 2.0
        cy = (h / 2.0) - 10
        
        gender = self.selected_gender.get()
        is_female = (gender == "Femenino")
        op_name = self.selected_operator.get()

        # ── CÁLCULOS DE CINEMÁTICA HUMANA VIVA (RESPIRACIÓN, PULSO, PLEGADO Y ARTICULACIÓN) ──
        now = time.time() - self.anim_start_time
        mode_val = self.human_motion_mode.get()
        is_motion = (mode_val != "⏸ Estático")
        is_work = ("Plegado" in mode_val or "Trabajo" in mode_val)
        is_artic = ("Articular" in mode_val or "Zona" in mode_val)
        sel_zone = self.selected_zone.get()

        # 1. Respiración biológica (~16 rpm) y micro-balance postural fisiológico
        if is_motion:
            b_phase = now * 1.68
            s_b = math.sin(b_phase)
            breathe_dy = s_b * 3.2
            chest_scale = 1.0 + (s_b * 0.022)
            shoulder_dy = -s_b * 2.4
            neck_dy = -s_b * 1.4
            
            # Micro-oscilación postural natural (involuntaria, viva)
            sway_yaw = math.sin(now * 0.75) * math.radians(0.7)
            sway_pitch = math.cos(now * 0.55) * math.radians(0.4)
            heart_pulse = max(0.0, math.sin(now * 7.5)) ** 3
        else:
            breathe_dy = 0.0
            chest_scale = 1.0
            shoulder_dy = 0.0
            neck_dy = 0.0
            sway_yaw = 0.0
            sway_pitch = 0.0
            heart_pulse = 0.0

        # Ciclos rítmicos de movimiento
        w_phase = now * 2.1 # Ciclo de ~3.0 seg por plegado
        fold_cycle = (math.sin(w_phase - math.pi / 2.0) + 1.0) / 2.0  # 0.0 a 1.0
        artic_cycle = (math.sin(now * 2.8) + 1.0) / 2.0             # 0.0 a 1.0 para zona seleccionada

        # Factor de trabajo para todo el brazo en modo Plegado
        fold_factor = fold_cycle if is_work else 0.0
        neck_tilt = fold_factor * 4.0 if is_work else (artic_cycle * 8.0 if (is_artic and sel_zone == "cuello") else 0.0)

        eff_yaw = self.yaw + sway_yaw
        eff_pitch = self.pitch + sway_pitch

        # 1. Rejilla de Fondo 3D y Brújula de Orientación
        self._draw_background_grid(c, w, h)
        self._draw_compass_3d(c, 45, h - 45, eff_yaw)

        # 2. Definición Geométrica del Maniquí Holográfico 3D (Tronco Superior Waist-Up)
        sh_w = 98.0 if is_female else 125.0
        sh_drop = 65.0
        waist_w = 48.0 if is_female else 68.0
        hip_w = 78.0 if is_female else 74.0
        neck_r = 16.0 if is_female else 22.0
        bust_z = 32.0 if is_female else 16.0

        # Anillos transversales del torso (Y, Radio X, Radio Z, Offset Z) con modulación respiratoria
        torso_rings_def = [
            (-85 + neck_dy, (neck_r * 1.5) * chest_scale, (neck_r * 1.3) * chest_scale, -4),
            (-65 + shoulder_dy * 0.7, (sh_w * 0.75) * chest_scale, 34 * chest_scale, 0),
            (-35 + breathe_dy * 0.5, (74 if is_female else 92) * chest_scale, 42 * chest_scale, bust_z * 0.8),
            (-5 + breathe_dy * 0.3, (68 if is_female else 86) * chest_scale, 38 * chest_scale, bust_z),
            (25 + breathe_dy * 0.2, (58 if is_female else 78) * chest_scale, 34 * chest_scale, 4),
            (65, waist_w, 28 if is_female else 34, 0),
            (95, waist_w + 12, 32 if is_female else 36, 0),
            (130, hip_w, 36 if is_female else 40, -2)
        ]

        render_queue = []

        # ── A. Anillos de sección del torso ────────────────────────────────
        for y_lvl, rx, rz, off_z in torso_rings_def:
            pts_ring = []
            num_pts = 18
            for i in range(num_pts):
                theta = 2 * math.pi * i / num_pts
                px = rx * math.cos(theta)
                pz = rz * math.sin(theta) + off_z
                pts_ring.append((px, y_lvl, pz))
            
            avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in pts_ring])
            render_queue.append({
                "type": "ring",
                "points": pts_ring,
                "z": avg_z,
                "color": "#1e3a5f" if avg_z < 0 else "#38bdf8",
                "width": 1 if avg_z < 0 else 2
            })

        # ── B. Contornos de Busto (Mujer) o Pectorales (Hombre) ────────────
        if is_female:
            for side in [-1, 1]:
                bx = side * 28.0
                by = -20.0 + (breathe_dy * 0.4)
                bz = 38.0 * chest_scale
                pts_bust = []
                for a in np.linspace(0, 2*math.pi, 14):
                    pts_bust.append((bx + 16*math.cos(a), by + 16*math.sin(a), bz + 10*math.sin(a)))
                avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in pts_bust])
                render_queue.append({
                    "type": "polygon",
                    "points": pts_bust,
                    "z": avg_z,
                    "fill": "#0f233d" if avg_z > 0 else "#091424",
                    "outline": "#38bdf8" if avg_z > 0 else "#1e3a5f",
                    "width": 2 if avg_z > 0 else 1
                })
        else:
            for side in [-1, 1]:
                pts_pec = [
                    (side * 8, -45 + shoulder_dy * 0.5, 28 * chest_scale),
                    (side * 52, -45 + shoulder_dy * 0.5, 28 * chest_scale),
                    (side * 48, -8, 30 * chest_scale),
                    (side * 8, -8, 28 * chest_scale)
                ]
                avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in pts_pec])
                render_queue.append({
                    "type": "polygon",
                    "points": pts_pec,
                    "z": avg_z,
                    "fill": "#0f233d" if avg_z > 0 else "#091424",
                    "outline": "#38bdf8" if avg_z > 0 else "#1e3a5f",
                    "width": 2 if avg_z > 0 else 1
                })

        # ── C. Cabeza de Maniquí 3D (Anillos de latitud y visor) ───────────
        head_cy = -145.0 + neck_dy + neck_tilt
        head_rx = 28.0 if is_female else 34.0
        head_ry = 38.0
        head_rz = 30.0
        
        for h_step in [-22, -8, 8, 22]:
            rad_fac = math.cos(h_step / 35.0)
            pts_head_ring = []
            for i in range(16):
                theta = 2 * math.pi * i / 16
                px = head_rx * rad_fac * math.cos(theta)
                pz = head_rz * rad_fac * math.sin(theta)
                pts_head_ring.append((px, head_cy + h_step, pz))
            avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in pts_head_ring])
            render_queue.append({
                "type": "ring",
                "points": pts_head_ring,
                "z": avg_z,
                "color": "#60a5fa" if avg_z > 0 else "#1e3a5f",
                "width": 1 if avg_z < 0 else 2
            })

        # Línea central facial / visor
        face_pts = [
            (0, head_cy - head_ry * 0.7, head_rz * 0.8),
            (0, head_cy - 4, head_rz * 1.1),
            (0, head_cy + head_ry * 0.5, head_rz * 0.7),
            (0, head_cy + head_ry * 0.8, 0)
        ]
        avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in face_pts])
        render_queue.append({
            "type": "line_strip",
            "points": face_pts,
            "z": avg_z,
            "color": "#93c5fd" if avg_z > 0 else "#1e3a5f",
            "width": 2
        })

        # ── D. Columna Vertebral y Escápulas ───────────────────────────────
        spine_pts = [
            (0, -95 + neck_dy, -12),
            (0, -65 + shoulder_dy * 0.5, -28),
            (0, -30, -32),
            (0, 10, -34),
            (0, 50, -30),
            (0, 90, -25),
            (0, 130, -18)
        ]
        avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in spine_pts])
        render_queue.append({
            "type": "line_strip",
            "points": spine_pts,
            "z": avg_z,
            "color": "#38bdf8" if avg_z > 0 else "#1e293b",
            "width": 3 if avg_z > 0 else 1,
            "dash": (4, 3)
        })

        for side in [-1, 1]:
            scap_pts = [
                (side * 20, -55 + shoulder_dy * 0.6, -28),
                (side * 52, -50 + shoulder_dy * 0.6, -26),
                (side * 28, -10, -30)
            ]
            avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in scap_pts])
            render_queue.append({
                "type": "polygon",
                "points": scap_pts,
                "z": avg_z,
                "fill": "#0e1e33" if avg_z > 0 else "#08101a",
                "outline": "#38bdf8" if avg_z > 0 else "#1e293b",
                "width": 2 if avg_z > 0 else 1
            })

        # ── E. Extremidades Superiores con Cinemática Coordinada (Hombro, Codo, Muñeca, Mano y Dedos) ─
        # Conexión directa con la regla ergonómica:
        # "en el hombro se debe mover ese hombro si es el codo, muñecas o manos tambien deben de moverse"

        # 1. Movilidad activa del hombro
        sh_move_r = fold_factor
        if is_artic and ("hombro_r" in sel_zone or sel_zone == "hombro_r"):
            sh_move_r = max(sh_move_r, artic_cycle)
        
        sh_move_l = 0.0
        if is_artic and ("hombro_l" in sel_zone):
            sh_move_l = artic_cycle

        # Hombro izquierdo
        sh_pos_l = (-sh_w + (sh_move_l * 14.0), -sh_drop + shoulder_dy + (sh_move_l * 6.0), sh_move_l * 14.0)

        # Hombro derecho: aducción medial (-X), descenso clavicular (+Y), flexión anterior (+Z)
        sh_delta_x = -sh_move_r * 14.0
        sh_delta_y = sh_move_r * 7.0
        sh_delta_z = sh_move_r * 16.0
        sh_pos_r = (sh_w + sh_delta_x, -sh_drop + shoulder_dy + sh_delta_y, sh_delta_z)

        # 2. Movilidad activa del codo
        codo_move_r = fold_factor
        if is_artic and ("codo_r" in sel_zone):
            codo_move_r = max(codo_move_r, artic_cycle)
        cur_ang_r = 108.0 - (codo_move_r * 28.0)
        rad_r = math.radians(cur_ang_r)

        codo_move_l = 0.0
        if is_artic and ("codo_l" in sel_zone):
            codo_move_l = artic_cycle
        cur_ang_l = self.metrics["avg_elbow_l"] - (codo_move_l * 25.0)
        rad_l = math.radians(cur_ang_l)

        elbow_pos_l = (sh_pos_l[0] - 22.0 + (codo_move_l * 14.0), 
                       sh_pos_l[1] + 85.0 - (codo_move_l * 10.0), 
                       12.0 + math.cos(rad_l) * 20.0 + (codo_move_l * 16.0))

        elbow_pos_r = (sh_pos_r[0] + 20.0 - (codo_move_r * 16.0), 
                       sh_pos_r[1] + 85.0 - (codo_move_r * 14.0), 
                       15.0 + math.cos(rad_r) * 20.0 + (codo_move_r * 22.0))

        # 3. Movilidad activa de la muñeca
        wrist_move_r = fold_factor
        if is_artic and ("muñeca_r" in sel_zone):
            wrist_move_r = max(wrist_move_r, artic_cycle)

        wrist_move_l = 0.0
        if is_artic and ("muñeca_l" in sel_zone):
            wrist_move_l = artic_cycle

        wrist_pos_l = (elbow_pos_l[0] + 38.0 - (wrist_move_l * 16.0), 
                       elbow_pos_l[1] + 75.0 - (wrist_move_l * 12.0), 
                       elbow_pos_l[2] + 45.0 + (wrist_move_l * 20.0))

        wrist_pos_r = (elbow_pos_r[0] - 38.0 - (wrist_move_r * 28.0), 
                       elbow_pos_r[1] + 75.0 - (wrist_move_r * 22.0), 
                       elbow_pos_r[2] + 45.0 + (wrist_move_r * 28.0))

        # 4. Movilidad activa de la mano (carpo y palma)
        hand_move_r = fold_factor
        if is_artic and ("mano_r" in sel_zone or "dedos_r" in sel_zone):
            hand_move_r = max(hand_move_r, artic_cycle)

        hand_move_l = 0.0
        if is_artic and ("mano_l" in sel_zone or "dedos_l" in sel_zone):
            hand_move_l = artic_cycle

        hand_pos_l = (wrist_pos_l[0] + 24.0 - (hand_move_l * 8.0), 
                      wrist_pos_l[1] + 28.0 - (hand_move_l * 6.0), 
                      wrist_pos_l[2] + 15.0 + (hand_move_l * 10.0))

        hand_pos_r = (wrist_pos_r[0] - 24.0 - (hand_move_r * 12.0), 
                      wrist_pos_r[1] + 28.0 - (hand_move_r * 10.0), 
                      wrist_pos_r[2] + 15.0 + (hand_move_r * 16.0))

        # 5. Brazos y Antebrazos (Líneas óseas principales)
        segments = [
            (sh_pos_l, elbow_pos_l, 4), (sh_pos_r, elbow_pos_r, 4),
            (elbow_pos_l, wrist_pos_l, 3), (elbow_pos_r, wrist_pos_r, 3),
            (wrist_pos_l, hand_pos_l, 2), (wrist_pos_r, hand_pos_r, 2)
        ]
        for p1, p2, w_seg in segments:
            avg_z = (self.rotate_point_3d(*p1, eff_yaw, eff_pitch)[2] + self.rotate_point_3d(*p2, eff_yaw, eff_pitch)[2]) / 2.0
            render_queue.append({
                "type": "segment", "p1": p1, "p2": p2, "z": avg_z,
                "color": "#38bdf8" if avg_z > 0 else "#1e3a5f", "width": w_seg if avg_z > 0 else 1
            })

        # 6. Cálculo Anatómico Realista de Manos y 5 Dedos Articulados
        fold_factor_r = fold_factor
        if is_artic and ("dedos_r" in sel_zone or "mano_r" in sel_zone):
            fold_factor_r = max(fold_factor_r, artic_cycle)

        fold_factor_l = (artic_cycle if (is_artic and ("dedos_l" in sel_zone or "mano_l" in sel_zone)) else 0.0)

        palm_l, fng_l = self._compute_hand_and_fingers(wrist_pos_l, hand_pos_l, is_right=False, fold_factor=fold_factor_l)
        palm_r, fng_r = self._compute_hand_and_fingers(wrist_pos_r, hand_pos_r, is_right=True, fold_factor=fold_factor_r)

        # Añadir palmas a la cola de renderizado
        for palm_pts, is_r in [(palm_l, False), (palm_r, True)]:
            avg_z_palm = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in palm_pts])
            render_queue.append({
                "type": "polygon",
                "points": palm_pts,
                "z": avg_z_palm,
                "fill": "#0f233d" if avg_z_palm > 0 else "#091424",
                "outline": "#38bdf8" if avg_z_palm > 0 else "#1e3a5f",
                "width": 1
            })

        # Añadir 5 dedos articulados para cada mano
        for fingers, is_r in [(fng_l, False), (fng_r, True)]:
            for f_name, f_pts in fingers.items():
                avg_z_fng = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in f_pts])
                is_active_pinch = (is_r and f_name in ["pulgar", "indice"])
                col = "#38bdf8" if avg_z_fng > 0 else "#1e3a5f"
                if is_active_pinch and fold_factor_r > 0.4:
                    col = "#f43f5e" if fold_factor_r > 0.75 else "#fbbf24"
                
                render_queue.append({
                    "type": "finger_line",
                    "points": f_pts,
                    "z": avg_z_fng,
                    "color": col,
                    "width": 2 if is_active_pinch else 1
                })

        # ── 6.B. Capa Muscular ISO 11226 (Volúmenes 3D con Sombreado de Fatiga) ──
        v_mode = self.visual_layer_mode.get() if hasattr(self, 'visual_layer_mode') else "⚡ Completo (Músculos+Esqueleto)"
        show_muscles = ("Músculo" in v_mode or "Completo" in v_mode)
        
        iso_risks = self.compute_iso_muscle_risks()
        
        # Sincronizar barras y valores de telemetría muscular en el panel
        if hasattr(self, 'muscle_bars') and self.muscle_bars:
            for mk, val in iso_risks.items():
                pbar = self.muscle_bars.get(mk)
                lbl_v = self.muscle_val_labels.get(mk)
                if pbar and pbar.winfo_exists():
                    pbar.set(val)
                    pbar.configure(progress_color=self.get_risk_color(val))
                if lbl_v and lbl_v.winfo_exists():
                    lbl_v.configure(text=f"{int(val * 100)}%", text_color=self.get_risk_color(val))

        if hasattr(self, 'lbl_iso_global') and self.lbl_iso_global.winfo_exists():
            f_val = getattr(self, "param_fatigue_f", 0.42)
            if getattr(self, "is_shift_simulating", False):
                st = getattr(self, "sim_shift_time", 0.0)
                p = min(1.0, max(0.0, st / 30.0))
                f_val = min(1.0, 0.15 + (0.70 * p))
            f_col = "#ef4444" if f_val >= 0.75 else ("#f59e0b" if f_val >= 0.45 else "#10b981")
            self.lbl_iso_global.configure(text=f"Fatiga F: {f_val:.2f}", text_color=f_col)

        if show_muscles:
            muscle_items = self._build_muscle_geometry_3d(
                sh_pos_l, sh_pos_r, elbow_pos_l, elbow_pos_r, wrist_pos_l, wrist_pos_r,
                spine_pts, neck_dy, shoulder_dy, iso_risks, eff_yaw, eff_pitch
            )
            render_queue.extend(muscle_items)

        # 7. Mesa de Trabajo y Hoja de Origami Holográfica en 3D
        paper_y = 125.0
        paper_pts = [
            (5.0, paper_y, 45.0),
            (75.0, paper_y, 65.0),
            (25.0, paper_y, 115.0),
            (-45.0, paper_y, 95.0)
        ]
        avg_z_paper = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in paper_pts])
        render_queue.append({
            "type": "polygon",
            "points": paper_pts,
            "z": avg_z_paper - 2,
            "fill": "#071221",
            "outline": "#1e3a8a",
            "width": 1
        })
        crease_pts = [
            (15.0, paper_y - 1, 55.0),
            (50.0, paper_y - 1, 90.0)
        ]
        render_queue.append({
            "type": "line_strip",
            "points": crease_pts,
            "z": avg_z_paper - 1,
            "color": "#38bdf8",
            "width": 2,
            "dash": (4, 3)
        })

        # ── F. Hotspots Articulares de Lesión en el Espacio 3D ─────────────
        # El hotspot de dedos_r se acopla EXACTAMENTE al punto de contacto de la pinza (pulgar e índice)
        t_tip_r = fng_r["pulgar"][-1]
        i_tip_r = fng_r["indice"][-1]
        dedos_pos_r = ((t_tip_r[0] + i_tip_r[0]) / 2.0, (t_tip_r[1] + i_tip_r[1]) / 2.0, (t_tip_r[2] + i_tip_r[2]) / 2.0)

        # Dedos izquierdos acoplados a las yemas estabilizadoras
        i_tip_l = fng_l["indice"][-1]
        m_tip_l = fng_l["medio"][-1]
        dedos_pos_l = ((i_tip_l[0] + m_tip_l[0]) / 2.0, (i_tip_l[1] + m_tip_l[1]) / 2.0, (i_tip_l[2] + m_tip_l[2]) / 2.0)

        time_mult = self._get_time_multiplier()
        self.projected_hotspots = {}

        hotspots_3d = {
            "cuello":       (0, -90 + neck_dy + neck_tilt, -5, 24),
            "hombro_l":     (sh_pos_l[0], sh_pos_l[1], sh_pos_l[2], 26),
            "hombro_r":     (sh_pos_r[0], sh_pos_r[1], sh_pos_r[2], 26),
            "codo_l":       (elbow_pos_l[0], elbow_pos_l[1], elbow_pos_l[2], 24),
            "codo_r":       (elbow_pos_r[0], elbow_pos_r[1], elbow_pos_r[2], 24),
            "muñeca_l":     (wrist_pos_l[0], wrist_pos_l[1], wrist_pos_l[2], 22),
            "muñeca_r":     (wrist_pos_r[0], wrist_pos_r[1], wrist_pos_r[2], 22),
            "mano_l":       (hand_pos_l[0], hand_pos_l[1], hand_pos_l[2], 20),
            "mano_r":       (hand_pos_r[0], hand_pos_r[1], hand_pos_r[2], 20),
            "dedos_l":      (dedos_pos_l[0], dedos_pos_l[1], dedos_pos_l[2], 19),
            "dedos_r":      (dedos_pos_r[0], dedos_pos_r[1], dedos_pos_r[2], 19),
            "espalda_alta": (0, -25, -34, 25)
        }

        for z_key, (hx, hy, hz, hr) in hotspots_3d.items():
            u, v, rz = self.project_3d(hx, hy, hz, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
            base_imp = self.zone_impacts.get(z_key, 0.4)
            curr_imp = min(1.0, base_imp * time_mult)
            color = self._get_heat_color(curr_imp)
            is_active = (z_key == self.selected_zone.get())
            
            self.projected_hotspots[z_key] = (u, v, hr * self.zoom_level, rz)
            render_queue.append({
                "type": "hotspot",
                "u": u, "v": v, "r": hr * self.zoom_level, "z": rz,
                "color": color, "key": z_key, "active": is_active
            })

        # ── 3. ORDENAR POR PROFUNDIDAD Z Y RENDERIZAR EN CANVAS (Painter's Alg) ─
        render_queue.sort(key=lambda item: item["z"])

        for item in render_queue:
            t = item["type"]
            
            if t == "ring":
                proj_pts = []
                for pt in item["points"]:
                    u, v, _ = self.project_3d(*pt, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                    proj_pts.extend([u, v])
                if len(proj_pts) >= 4:
                    c.create_polygon(proj_pts, fill="", outline=item["color"], 
                                     width=item["width"], smooth=True)
                                     
            elif t == "polygon":
                proj_pts = []
                for pt in item["points"]:
                    u, v, _ = self.project_3d(*pt, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                    proj_pts.extend([u, v])
                if len(proj_pts) >= 6:
                    c.create_polygon(proj_pts, fill=item["fill"], outline=item["outline"], 
                                     width=item["width"], smooth=True)

            elif t == "line_strip":
                proj_pts = []
                for pt in item["points"]:
                    u, v, _ = self.project_3d(*pt, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                    proj_pts.extend([u, v])
                if len(proj_pts) >= 4:
                    dash = item.get("dash")
                    c.create_line(proj_pts, fill=item["color"], width=item["width"], dash=dash, smooth=True)

            elif t == "finger_line":
                proj_pts = []
                for pt in item["points"]:
                    u, v, _ = self.project_3d(*pt, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                    proj_pts.extend([u, v])
                if len(proj_pts) >= 4:
                    c.create_line(proj_pts, fill=item["color"], width=item["width"], capstyle="round", joinstyle="round", smooth=True)
                if len(proj_pts) >= 2:
                    u_tip, v_tip = proj_pts[-2], proj_pts[-1]
                    r_bead = 2.2 * self.zoom_level
                    c.create_oval(u_tip - r_bead, v_tip - r_bead, u_tip + r_bead, v_tip + r_bead, fill=item["color"], outline="")

            elif t == "segment":
                u1, v1, _ = self.project_3d(*item["p1"], cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                u2, v2, _ = self.project_3d(*item["p2"], cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                c.create_line(u1, v1, u2, v2, fill=item["color"], width=item["width"], capstyle="round")

            elif t == "hotspot":
                u, v, hr, rz = item["u"], item["v"], item["r"], item["z"]
                col = item["color"]
                
                # Ajustar brillo / tamaño por profundidad + pulso vascular
                depth_alpha = max(0.4, min(1.0, (rz + 200) / 400.0))
                eff_r = hr * depth_alpha * (1.0 + 0.18 * heart_pulse)
                
                # Anillo exterior punteado pulsante
                outer_mult = 1.5 + (0.35 * heart_pulse)
                c.create_oval(u - eff_r * outer_mult, v - eff_r * outer_mult, 
                              u + eff_r * outer_mult, v + eff_r * outer_mult,
                              outline=col, fill="", width=2 if (heart_pulse > 0.4 and rz > -20) else 1, 
                              dash=(3, 3))
                # Anillo medio sólido
                c.create_oval(u - eff_r * 1.0, v - eff_r * 1.0, u + eff_r * 1.0, v + eff_r * 1.0,
                              outline=col, fill="", width=2)
                # Núcleo brillante
                c.create_oval(u - eff_r * 0.45, v - eff_r * 0.45, u + eff_r * 0.45, v + eff_r * 0.45,
                              outline="", fill=col)

                # Resaltado de inspección activa (Idéntico a la imagen de referencia del usuario)
                if item["active"]:
                    c.create_oval(u - eff_r * 1.9, v - eff_r * 1.9, u + eff_r * 1.9, v + eff_r * 1.9,
                                  outline="#ffffff", width=2)
                    c.create_rectangle(u - 4, v - 11, u + 84, v + 9, fill="#070d19", outline="", width=0)
                    c.create_text(u + 40, v - 1, text="▶ INSPECCIÓN", fill="#ffffff", font=("Helvetica", 9, "bold"))

        # ── 4. Badges de Información 3D, Operario y Estado ────────────────
        yaw_deg = int(math.degrees(eff_yaw)) % 360
        pitch_deg = int(math.degrees(eff_pitch))
        
        view_label = "VISTA FRONTAL (0°)" if (yaw_deg < 22 or yaw_deg >= 338) else                      "PERSPECTIVA DERECHA (45°)" if (22 <= yaw_deg < 68) else                      "PERFIL DERECHO (90°)" if (68 <= yaw_deg < 112) else                      "PERSPECTIVA POSTERIOR D. (135°)" if (112 <= yaw_deg < 158) else                      "VISTA POSTERIOR / ESPALDA (180°)" if (158 <= yaw_deg < 202) else                      "PERSPECTIVA POSTERIOR I. (225°)" if (202 <= yaw_deg < 248) else                      "PERFIL IZQUIERDO (270°)" if (248 <= yaw_deg < 292) else                      "PERSPECTIVA IZQUIERDA (315°)"

        if w >= 220:
            c.create_text(20, 20, anchor="w", 
                          text=f"🔭 {view_label}  |  Giro: {yaw_deg}°",
                          fill="#38bdf8", font=("Helvetica", 10, "bold"))
            
            pinch_pct = int(fold_factor_r * 100)
            if getattr(self, "is_shift_simulating", False):
                f_sim = min(1.0, 0.15 + (0.70 * (self.sim_shift_time / 30.0)))
                status_txt = f"⚡ SIMULACIÓN TURNO ACTIVA · Fatiga F: {f_sim:.2f} · Telemetría ISO 11226 Músculos 3D"
                status_col = "#ef4444" if f_sim >= 0.75 else "#f59e0b"
            elif is_work:
                status_txt = f"⚙️ PLEGADO COORDINADO · Hombro + Codo {cur_ang_r:.1f}° + Muñeca + Dedos ({pinch_pct}%)"
                status_col = "#c084fc"
            elif is_artic:
                z_name = self.PATHOLOGIES_DB.get(sel_zone, {}).get("name", sel_zone)
                status_txt = f"🎯 ARTICULACIÓN ACTIVA · {z_name} ({int(artic_cycle * 100)}%)"
                status_col = "#fbbf24"
            elif is_motion:
                status_txt = "🫁 RESPIRACIÓN BIOLÓGICA (16 rpm · Pulso: 72 bpm)"
                status_col = "#34d399"
            else:
                status_txt = "⏸ POSTURA ESTÁTICA EN REPOSO"
                status_col = "#94a3b8"
                
            c.create_text(20, 38, anchor="w",
                          text=status_txt, fill=status_col, font=("Helvetica", 9, "bold"))

            # Nombre de operario en la esquina inferior izquierda (idéntico a la imagen)
            c.create_text(25, h - 30, anchor="w",
                          text=f"Operario: {op_name}",
                          fill="#64748b", font=("Helvetica", 10, "bold"))
                          
            c.create_text(20, h - 12, anchor="w", 
                          text=f"{'Mujer ♀' if is_female else 'Hombre ♂'}  |  Zoom: {int(self.zoom_level*100)}%",
                          fill="#475569", font=("Helvetica", 8))

    def _draw_background_grid(self, c, w, h):
        for x in range(0, w, 40):
            c.create_line(x, 0, x, h, fill="#0c1626", width=1)
        for y in range(0, h, 40):
            c.create_line(0, y, w, y, fill="#0c1626", width=1)

    def _draw_compass_3d(self, c, cx, cy, eff_yaw=None):
        """Dibuja una brújula 3D que indica hacia dónde mira el maniquí en 360°."""
        r = 20
        curr_y = self.yaw if eff_yaw is None else eff_yaw
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1e293b", fill="#0b1320", width=1)
        dir_x = math.sin(curr_y) * r * 0.85
        dir_z = -math.cos(curr_y) * r * 0.85
        c.create_line(cx, cy, cx + dir_x, cy + dir_z, fill="#38bdf8", width=2, arrow="last")
        c.create_text(cx, cy + r + 9, text="360°", fill="#64748b", font=("Helvetica", 8))

    def _get_time_multiplier(self):
        months = self.HORIZON_MONTHS.get(self.selected_horizon.get(), 12)
        if months <= 1: return 0.55
        elif months <= 3: return 0.70
        elif months <= 6: return 0.85
        elif months <= 12: return 1.00
        elif months <= 24: return 1.15
        elif months <= 36: return 1.30
        else: return 1.45

    def _get_heat_color(self, val):
        if val < 0.40: return "#2ecc71"
        elif val < 0.65: return "#f1c40f"
        elif val < 0.82: return "#e67e22"
        elif val < 0.92: return "#e74c3c"
        else: return "#991b1b"

    def detect_hotspot_click(self, x, y):
        """Busca el hotspot más cercano a las coordenadas de pantalla."""
        closest_key = None
        min_dist = 9999
        for z_key, (hx, hy, hr, rz) in getattr(self, 'projected_hotspots', {}).items():
            dist = math.sqrt((x - hx)**2 + (y - hy)**2)
            if dist <= hr * 2.2 and dist < min_dist:
                min_dist = dist
                closest_key = z_key
        return closest_key

    # ── ACTUALIZACIÓN DEL PANEL DE DIAGNÓSTICO Y PROYECCIÓN TEMPORAL ──────────
    def update_diagnostic_panel(self):
        z_key = self.selected_zone.get()
        data = self.PATHOLOGIES_DB.get(z_key, self.PATHOLOGIES_DB["muñeca_r"])
        months = self.HORIZON_MONTHS.get(self.selected_horizon.get(), 12)
        gender = self.selected_gender.get()

        self.lbl_zone_name.configure(text=data["name"].upper())
        self.lbl_zone_tissue.configure(text=f"Estructuras afectadas: {data['tissue']}")

        if "codo" in z_key:
            ang = self.metrics["avg_elbow_r"] if "r" in z_key else self.metrics["avg_elbow_l"]
            desc_ang = 'Flexión excesiva' if ang < 80 else 'Rango aceptable' if ang <= 130 else 'Extensión forzada'
            self.lbl_zone_angle.configure(text=f"{ang:.1f}° — {desc_ang}")
            self.lbl_zone_therblig.configure(text="Tensión isométrica y sobrecarga epicondílea")
            self.lbl_zone_gender.configure(text="+15% momento palanca en hombres" if gender == "Masculino" else "Ángulo cubital valgo +3° en mujeres")
        elif "dedos" in z_key:
            tomar_pct = int((self.metrics["tomar_count"] / max(1, self.metrics["total_therbligs"])) * 100)
            if "r" in z_key:
                self.lbl_zone_angle.configure(text="Pinza digital activa (Pulgar-Índice en asentar pliegues)")
                self.lbl_zone_therblig.configure(text=f"TOMAR (G) {tomar_pct}% · Presión estenótica directa")
                self.lbl_zone_gender.configure(text="+30% microtraumatismo por menor grosor cutáneo en mujeres" if gender == "Femenino" else "+15% tensión en polea A1 por fuerza motriz en hombres")
            else:
                self.lbl_zone_angle.configure(text="Pinza de sujeción isométrica estática (Dedos 1 a 4)")
                self.lbl_zone_therblig.configure(text="Fijación continua contra mesa de trabajo")
                self.lbl_zone_gender.configure(text="Mayor susceptibilidad a contracturas por tensión estática")
        elif "mano" in z_key:
            if "r" in z_key:
                self.lbl_zone_angle.configure(text="Compresión palmar continua en marcas y solapas")
                self.lbl_zone_therblig.configure(text="Fricción de aponeurosis y musculatura tenar")
                self.lbl_zone_gender.configure(text="+20% vulnerabilidad por menor masa tenar en mujeres" if gender == "Femenino" else "Mayor rigidez fascial palmar en hombres")
            else:
                self.lbl_zone_angle.configure(text="Apoyo estático en región hipotenar")
                self.lbl_zone_therblig.configure(text="Presión sostenida sobre Canal de Guyón")
                self.lbl_zone_gender.configure(text="Sobrecarga compresiva por contra-apoyo continuo")
        elif "muñeca" in z_key:
            tomar_pct = int((self.metrics["tomar_count"] / max(1, self.metrics["total_therbligs"])) * 100)
            self.lbl_zone_angle.configure(text="Presión palmar activa en marcas y pliegues")
            self.lbl_zone_therblig.configure(text=f"TOMAR (G) {tomar_pct}% · Repetitividad continua")
            self.lbl_zone_gender.configure(text="+25% vulnerabilidad en túnel carpiano femenino" if gender == "Femenino" else "Mayor rigidez tendinosa en hombres")
        elif "cuello" in z_key:
            self.lbl_zone_angle.configure(text="Flexión cervical sostenida ~32° hacia la mesa")
            self.lbl_zone_therblig.configure(text=f"Nivel de iluminación: {int(self.metrics['avg_lux'])} lx")
            self.lbl_zone_gender.configure(text="+20% fatiga miofascial trapecio femenino" if gender == "Femenino" else "Mayor carga discal axial en hombres")
        else:
            self.lbl_zone_angle.configure(text="Postura de trabajo estática sin apoyo dorsal")
            self.lbl_zone_therblig.configure(text=f"Nivel de ruido ambiental: {self.metrics['avg_db']:.1f} dB")
            self.lbl_zone_gender.configure(text="Sobrecarga estática sostenida en romboides y dorsal")

        stages = data["stages"]
        sorted_keys = sorted(stages.keys())
        active_key = sorted_keys[0]
        for k in sorted_keys:
            if months >= k:
                active_key = k
            else:
                break
                
        stage_info = stages[active_key]
        self.lbl_diag_cie.configure(text=stage_info["cie"], text_color=stage_info["color"])
        self.lbl_diag_desc.configure(text=stage_info["desc"])
        self.lbl_eva.configure(text=f"{stage_info['eva']} — Nivel {stage_info['risk']}", text_color=stage_info["color"])

        base_imp = self.zone_impacts.get(z_key, 0.5)
        time_mult = self._get_time_multiplier()
        calc_score = int(min(98, max(12, base_imp * time_mult * 80)))
        
        score_color = self._get_heat_color(calc_score / 100.0)
        risk_str = "Bajo Riesgo" if calc_score < 40 else "Riesgo Moderado" if calc_score < 65 else "Riesgo Alto" if calc_score < 85 else "Riesgo Crítico / Incapacitante"
        self.lbl_global_score.configure(text=f"{calc_score}% ({risk_str})", text_color=score_color)
        self.prog_bar.configure(progress_color=score_color)
        self.prog_bar.set(calc_score / 100.0)

        recoms = [
            f"1. Altura de mesa: regular la superficie para que los codos queden a 90°-105° sin elevar hombros.",
            f"2. Rotación de estación: limitar el plegado continuo a máximo 50 minutos con 10 minutos de tareas de empaque/inspección.",
            f"3. Pausas activas obligatorias: realizar extensiones pasivas de muñeca y rotaciones escapulares cada 60 minutos.",
            f"4. Ergonomía visual: mantener iluminación focalizada > 500 lux para reducir la flexión anterior del cuello.",
            f"5. Rediseño de pliegues: usar plegadores plásticos de hueso (bone folders) para evitar presión directa con la yema de los dedos."
        ]
        self.lbl_recom_text.configure(text="\n".join(recoms))

    def destroy(self):
        """Detiene cualquier hilo o ciclo de animación continua al salir."""
        if hasattr(self, 'anim_timer_id') and self.anim_timer_id:
            try:
                self.after_cancel(self.anim_timer_id)
            except Exception:
                pass
            self.anim_timer_id = None
        if hasattr(self, 'auto_rotate_id') and self.auto_rotate_id:
            try:
                self.after_cancel(self.auto_rotate_id)
            except Exception:
                pass
            self.auto_rotate_id = None
        self.is_animating = False
        super().destroy()
