import math

pathologies = {
    "dedos_r": {
        "name": "Dedos Mano Derecha (Pulgar e Índice - Pinza Digital)",
        "tissue": "Poleas Flexoras A1-A2, Tendones Flexor Largo y Flexor Profundo",
        "subt": "Pinza digital de doblado y presión puntual repetitiva en dobleces",
        "stages": {
            1: {"cie": "M79.2 Neuralgia digital focal por compresión", "desc": "Sensación de entumecimiento y fatiga en yemas de dedos.", "risk": "LEVE", "eva": "2/10", "color": "#2ecc71"},
            3: {"cie": "M65.3 Dedo en resorte incipiente (Pulgar / Índice)", "desc": "Engrosamiento de la polea A1 con leve chasquido al extender.", "risk": "MODERADO", "eva": "4/10", "color": "#f1c40f"},
            6: {"cie": "M65.3 Tenosinovitis estenosante digital (Trigger Finger)", "desc": "Bloqueo mecánico doloroso que requiere desbloqueo pasivo.", "risk": "ALTO", "eva": "5.5/10", "color": "#e67e22"},
            12: {"cie": "M65.3 Nódulo tendinoso flexor con bloqueo crónico", "desc": "Incapacidad para pinza fina de precisión. Pérdida de destreza.", "risk": "ALTO / CRÍTICO", "eva": "7/10", "color": "#e74c3c"},
            36: {"cie": "M19.0 Artrosis interfalángica distal precoz", "desc": "Desgaste del cartílago articular y dolor continuo al presionar.", "risk": "MUY CRÍTICO", "eva": "8/10", "color": "#962d22"},
            60: {"cie": "M20.0 Deformidad articular fija y anquilosis interfalángica", "desc": "Pérdida irreversible de función motriz y pinza digital.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
        }
    },
    "mano_r": {
        "name": "Mano Derecha (Palma y Eminencia Tenar)",
        "tissue": "Músculos Tenares, Aponeurosis Palmar, Rama Motora Tenar",
        "subt": "Microtrauma y compresión palmar repetida contra mesa y papel",
        "stages": {
            1: {"cie": "M70.9 Fatiga muscular tenar aguda", "desc": "Pesadez en base del pulgar al final de turnos de plegado.", "risk": "LEVE", "eva": "2/10", "color": "#2ecc71"},
            3: {"cie": "M72.0 Fascitis palmar superficial incipiente", "desc": "Hipersensibilidad e inflamación de la fascia palmar media.", "risk": "MODERADO", "eva": "3.5/10", "color": "#f1c40f"},
            6: {"cie": "M70.0 Sinovitis crepitante palmar", "desc": "Crujido y dolor mecánico al cerrar la palma de la mano.", "risk": "ALTO", "eva": "5/10", "color": "#e67e22"},
            12: {"cie": "G56.0 Neuropatía motora de rama recurrente tenar", "desc": "Debilidad de abducción y oposición del pulgar.", "risk": "ALTO / CRÍTICO", "eva": "6.5/10", "color": "#e74c3c"},
            36: {"cie": "M72.0 Nódulos palmares fibróticos pre-Dupuytren", "desc": "Bandas tensas retráctiles en palma de la mano.", "risk": "MUY CRÍTICO", "eva": "8/10", "color": "#962d22"},
            60: {"cie": "M18.0 Rizartrosis severa con pérdida de pinza tenar", "desc": "Subluxación articular e incapacidad ocupacional.", "risk": "INCAPACITANTE", "eva": "9/10", "color": "#78281f"}
        }
    },
    "dedos_l": {
        "name": "Dedos Mano Izquierda (Pinza Estabilizadora)",
        "tissue": "Ligamentos Colaterales Interfalángicos, Tendones Flexores",
        "subt": "Fijación isométrica estática continua de las esquinas del papel",
        "stages": {
            1: {"cie": "M79.1 Mialgia de interóseos y lumbricales", "desc": "Dolor sordo por contracción mantenida.", "risk": "LEVE", "eva": "1.5/10", "color": "#2ecc71"},
            3: {"cie": "M65.8 Tenosinovitis interfalángica incipiente", "desc": "Edema digital leve matutino.", "risk": "MODERADO", "eva": "3/10", "color": "#f1c40f"},
            6: {"cie": "M65.9 Entesopatía digital subaguda", "desc": "Dolor al ejercer fuerza de contra-apoyo.", "risk": "MODERADO", "eva": "4.5/10", "color": "#f1c40f"},
            12: {"cie": "M65.3 Dedo en resorte digital medio e índice", "desc": "Resistencia elástica al estirar los dedos.", "risk": "ALTO", "eva": "6/10", "color": "#e67e22"},
            36: {"cie": "M19.0 Formación precoz de nódulos interfalángicos", "desc": "Engrosamiento articular óseo reactivo.", "risk": "CRÍTICO", "eva": "7.5/10", "color": "#e74c3c"},
            60: {"cie": "M20.1 Contractura en flexión y rigidez digital", "desc": "Limitación articular fija permanente.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
        }
    },
    "mano_l": {
        "name": "Mano Izquierda (Palma y Región Hipotenar)",
        "tissue": "Músculos Hipotenares, Canal de Guyón, Aponeurosis Palmar",
        "subt": "Apoyo estático prolongado y contra-fuerza de fijación",
        "stages": {
            1: {"cie": "M70.9 Tensión muscular hipotenar", "desc": "Tensión en borde externo de la mano.", "risk": "LEVE", "eva": "1/10", "color": "#2ecc71"},
            3: {"cie": "G56.2 Compresión cubital en Canal de Guyón Leve", "desc": "Hormigueo en borde palmar del 4to y 5to dedo.", "risk": "MODERADO", "eva": "3/10", "color": "#f1c40f"},
            6: {"cie": "M72.2 Fibromatosis palmar incipiente", "desc": "Endurecimiento de tejidos blandos de apoyo.", "risk": "MODERADO", "eva": "4.5/10", "color": "#f1c40f"},
            12: {"cie": "G56.2 Síndrome del Martillo Hipotenar Laboral", "desc": "Isquemia digital por microtraumatismo repetido.", "risk": "ALTO", "eva": "6/10", "color": "#e67e22"},
            36: {"cie": "G56.2 Neuropatía cubital axonal distal", "desc": "Pérdida de fuerza intrínseca y atrofia hipotenar.", "risk": "CRÍTICO", "eva": "7.5/10", "color": "#e74c3c"},
            60: {"cie": "M18.1 Artrosis carpo-metacarpiana bilateral", "desc": "Rigidez articular mecánica permanente.", "risk": "INCAPACITANTE", "eva": "8.5/10", "color": "#78281f"}
        }
    }
}
print("Pathologies test OK, keys:", list(pathologies.keys()))

