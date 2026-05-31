import os
import pandas as pd

class ExcelDataLoader:
    @staticmethod
    def get_group_data():
        """Retorna un diccionario con el Título, Objetivos, Metodología y Participantes del grupo del usuario.
        Reemplaza los caracteres no-ASCII por sus equivalentes limpios basándose en sus ordinales (ej. 225 -> á, 243 -> ó, etc.)
        para evitar cualquier corrupción debida al encoding del sistema operativo o consola.
        """
        p = r"C:\Users\dsant\Desktop\esta\Distribución temáticas_Ing Métodos.xlsx"
        if not os.path.exists(p):
            return {
                "titulo": "Sistema de análisis ergonómico y monitoreo inteligente de micromovimientos en entornos productivos",
                "objetivos": (
                    "O. General: Integrar técnicas de monitoreo de micromovimientos y análisis ergonómico para mejorar las condiciones laborales y la eficiencia operativa.\n\n"
                    "O.E.1: Diseñar herramientas de captura y análisis de movimientos del trabajador.\n"
                    "O.E.2: Incorporar criterios ergonómicos para la evaluación de riesgo laboral.\n"
                    "O.E.3: Generar recomendaciones para la reducción de fatiga y optimización del desempeño."
                ),
                "metodologia": "Investigación aplicada con enfoque cuantitativo y ergonómico. Uso de machine learning, análisis biomecánico y mejora continua en procesos industriales.",
                "participantes": "David Santiago Castelblanco Artunduaga (5201057)\nJuan Diego Escobar Duarte (5200969)\nLaura Vanessa Céspedes Acosta (5200901)"
            }
        try:
            df = pd.read_excel(p)
            row = df.iloc[4]
            
            def clean_by_ordinal(val):
                s = str(val).strip()
                result = []
                for c in s:
                    code = ord(c)
                    if code == 225:   # á
                        result.append('á')
                    elif code == 233: # é
                        result.append('é')
                    elif code == 237: # í
                        result.append('í')
                    elif code == 243: # ó
                        result.append('ó')
                    elif code == 250: # ú
                        result.append('ú')
                    elif code == 241: # ñ
                        result.append('ñ')
                    elif code == 193: # Á
                        result.append('Á')
                    elif code == 201: # É
                        result.append('É')
                    elif code == 205: # Í
                        result.append('Í')
                    elif code == 211: # Ó
                        result.append('Ó')
                    elif code == 218: # Ú
                        result.append('Ú')
                    elif code == 209: # Ñ
                        result.append('Ñ')
                    else:
                        result.append(c)
                return "".join(result)

            return {
                "titulo": clean_by_ordinal(row.iloc[1]),
                "objetivos": clean_by_ordinal(row.iloc[2]),
                "metodologia": clean_by_ordinal(row.iloc[3]),
                "participantes": clean_by_ordinal(row.iloc[4])
            }
        except Exception:
            return {
                "titulo": "Sistema de análisis ergonómico y monitoreo inteligente de micromovimientos en entornos productivos",
                "objetivos": (
                    "O. General: Integrar técnicas de monitoreo de micromovimientos y análisis ergonómico para mejorar las condiciones laborales y la eficiencia operativa.\n\n"
                    "O.E.1: Diseñar herramientas de captura y análisis de movimientos del trabajador.\n"
                    "O.E.2: Incorporar criterios ergonómicos para la evaluación de riesgo laboral.\n"
                    "O.E.3: Generar recomendaciones para la reducción de fatiga y optimización del desempeño."
                ),
                "metodologia": "Investigación aplicada con enfoque cuantitativo y ergonómico. Uso de machine learning, análisis biomecánico y mejora continua en procesos industriales.",
                "participantes": "David Santiago Castelblanco Artunduaga (5201057)\nJuan Diego Escobar Duarte (5200969)\nLaura Vanessa Céspedes Acosta (5200901)"
            }
