# ==============================================================================
# SCRIPT DE ENTRENAMIENTO DE MACHINE LEARNING PARA CLASIFICACIÓN DE THERBLIGS
# Asignatura: Ingeniería de Métodos | Universidad Católica de Colombia
# Temática: Monitoreo de Micromovimientos (✊ Grasp / 🖐️ Release)
# ==============================================================================
# Este script demuestra formalmente cómo recolectar, estructurar, entrenar y 
# evaluar un modelo de Machine Learning (Random Forest y SVM) utilizando las 
# coordenadas tridimensionales de los 21 landmarks de la mano de MediaPipe.
#
# Para ejecutar este script y entrenar tu propio modelo, necesitas instalar:
#   pip install scikit-learn pandas numpy
# ==============================================================================

import numpy as np
import pandas as pd
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score

def generar_datos_sinteticos_mediapipe(n_muestras=500):
    """
    Simula la recolección de landmarks de MediaPipe para entrenar el modelo.
    Genera coordenadas (x, y, z) realistas para 21 puntos de la mano.
    - Clase 0 (✊ Coger/Grasp): Dedos doblados, puntas cerca de la muñeca (coordenadas compactas).
    - Clase 1 (🖐️ Soltar/Release): Dedos extendidos, puntas lejos de la muñeca.
    """
    np.random.seed(42)
    datos = []
    
    for _ in range(n_muestras):
        # --- Clase 0: PUÑO / COGER (Grasp) ---
        # Landmark 0 es la muñeca (origen aprox en 0.5, 0.8)
        wrist = np.array([0.5, 0.8, 0.0])
        # Puntos clave de los 21 landmarks simulando puño cerrado (distancias cortas)
        hand_fist = []
        for i in range(21):
            if i == 0:
                pt = wrist + np.random.normal(0, 0.01, 3)
            else:
                # Simular puntos plegados hacia la palma
                pt = wrist + np.random.normal(0, 0.08, 3)
            hand_fist.extend(pt)
        datos.append(hand_fist + [0]) # Etiqueta 0 = Grasp
        
        # --- Clase 1: MANO ABIERTA / SOLTAR (Release) ---
        hand_open = []
        for i in range(21):
            if i == 0:
                pt = wrist + np.random.normal(0, 0.01, 3)
            else:
                # Simular puntos extendidos radialmente hacia arriba y los lados
                pt = wrist + np.random.normal(0, 0.25, 3)
            hand_open.extend(pt)
        datos.append(hand_open + [1]) # Etiqueta 1 = Release

    # Columnas: 21 landmarks * 3 coord (x,y,z) = 63 columnas + 1 etiqueta (target)
    columnas = []
    for l_idx in range(21):
        columnas.extend([f"lm_{l_idx}_x", f"lm_{l_idx}_y", f"lm_{l_idx}_z"])
    columnas.append("target")
    
    df = pd.DataFrame(datos, columns=columnas)
    return df

def entrenar_clasificadores():
    print("======================================================================")
    print("[*] INICIANDO ENTRENAMIENTO DE MACHINE LEARNING (THERBLIG CLASSIFIER)")
    print("======================================================================")
    
    # 1. Cargar/Generar Dataset de landmarks
    print("\n[Paso 1/4] Cargando dataset de landmarks de MediaPipe...")
    df = generar_datos_sinteticos_mediapipe(n_muestras=400)
    print(f"-> Dataset generado con exito: {df.shape[0]} muestras y {df.shape[1] - 1} caracteristicas de landmarks.")
    
    # Dividir en Caracteristicas (X) y Etiquetas (y)
    X = df.drop(columns=["target"])
    y = df["target"]
    
    # Separar en conjunto de Entrenamiento (Train) y Prueba (Test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    
    # 2. Entrenar clasificador Random Forest (Bosque Aleatorio)
    print("\n[Paso 2/4] Entrenando Clasificador Random Forest...")
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    rf_model.fit(X_train, y_train)
    
    # Predecir y Evaluar Random Forest
    y_pred_rf = rf_model.predict(X_test)
    acc_rf = accuracy_score(y_test, y_pred_rf)
    print(f"-> Random Forest Entrenado! Precision (Accuracy): {acc_rf * 100:.2f}%")
    
    # 3. Entrenar clasificador SVM (Maquina de Vectores de Soporte)
    print("\n[Paso 3/4] Entrenando Clasificador SVM (Maquina de Vectores de Soporte)...")
    svm_model = SVC(kernel="linear", probability=True, random_state=42)
    svm_model.fit(X_train, y_train)
    
    # Predecir y Evaluar SVM
    y_pred_svm = svm_model.predict(X_test)
    acc_svm = accuracy_score(y_test, y_pred_svm)
    print(f"-> SVM Entrenado! Precision (Accuracy): {acc_svm * 100:.2f}%")
    
    # Mostrar reporte formal de metricas
    print("\n-------------------------------------------------------------")
    print("[Reporte] REPORTE DE RENDIMIENTO DEL MODELO (SVM CLASSIFIER):")
    print("-------------------------------------------------------------")
    print(classification_report(y_test, y_pred_svm, target_names=["Coger (Grasp)", "Soltar (Release)"]))
    
    # 4. Exportar el modelo entrenado
    print("\n[Paso 4/4] Exportando el modelo serializado...")
    output_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(output_dir, "therblig_svm_model.pkl")
    
    with open(model_path, "wb") as f:
        pickle.dump(svm_model, f)
        
    print(f"-> Exito! El modelo SVM entrenado ha sido exportado en: {model_path}")
    print("\n==============================================================")
    print("[Info] COMO SE INTEGRA ESTE MODELO A CRONOGRULLA?")
    print("==============================================================")
    print("En tu script principal, cargas el archivo .pkl entrenado:")
    print("  with open('therblig_svm_model.pkl', 'rb') as f:")
    print("      model = pickle.load(f)")
    print("\nY en el bucle de la camara, extraes las coordenadas de MediaPipe")
    print("como un vector unidimensional de 63 elementos [x0, y0, z0, ..., x20, y20, z20]")
    print("y realizas la clasificacion en tiempo real:")
    print("  prediccion = model.predict([vector_63_elementos])")
    print("  if prediccion[0] == 0: estado = 'Coger (Grasp)'")
    print("  else: estado = 'Soltar (Release)'")
    print("==============================================================")

if __name__ == "__main__":
    entrenar_clasificadores()
