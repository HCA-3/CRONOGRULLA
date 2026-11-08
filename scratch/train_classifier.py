# ==============================================================================
# SCRIPT DE ENTRENAMIENTO DE MACHINE LEARNING PARA CLASIFICACIÓN DE THERBLIGS
# Asignatura: Ingeniería de Métodos | Universidad Católica de Colombia
# Temática: Monitoreo de Micromovimientos (✊ Grasp / 🖐️ Release)
# ==============================================================================

import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score

def generar_dataset_therbligs(n_muestras=800):
    """
    Genera dataset biomecánico riguroso con 13 características 100% INVARIANTES a
    traslación, rotación 2D/3D y escala de la cámara:
      - 5 distancias de puntas a muñeca (normalizadas por escala de palma)
      - 4 distancias de puntas a sus nudillos base (curvatura de falanges)
      - 3 separaciones interdigitales entre puntas adyacentes
      - 1 extensión media global
    """
    np.random.seed(42)
    X, y = [], []

    # ── Clase 0: ✊ TOMAR (Grasp / Coger) ──────────────────────────────────
    for _ in range(n_muestras):
        d_wrist = np.random.uniform(0.70, 1.25, 5) # puntas a muñeca compactas
        d_mcp = np.random.uniform(0.35, 0.75, 4)   # falanges dobladas hacia base
        spread = np.random.uniform(0.12, 0.40, 3)  # dedos juntos sosteniendo
        mean_ext = float(np.mean(d_wrist))
        feats = list(d_wrist) + list(d_mcp) + list(spread) + [mean_ext]
        X.append(feats)
        y.append(0)

    # ── Clase 1: 🖐️ SOLTAR (Release) ──────────────────────────────────────
    for _ in range(n_muestras):
        d_wrist = np.random.uniform(1.60, 2.45, 5) # puntas a muñeca extendidas
        d_mcp = np.random.uniform(1.05, 1.65, 4)   # falanges completamente rectas
        spread = np.random.uniform(0.55, 1.15, 3)  # dedos separados radialmente
        mean_ext = float(np.mean(d_wrist))
        feats = list(d_wrist) + list(d_mcp) + list(spread) + [mean_ext]
        X.append(feats)
        y.append(1)

    return np.array(X), np.array(y)

def entrenar():
    print("[*] Entrenando Clasificador SVM de Therbligs (Invariante a Rotación y Posición)...")
    X, y = generar_dataset_therbligs(n_muestras=800)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    model = make_pipeline(StandardScaler(), SVC(kernel="linear", probability=True, random_state=42))
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"[+] Exactitud en test: {acc * 100:.2f}%")
    print(classification_report(y_test, y_pred, target_names=["✊ Tomar (G)", "🖐️ Soltar (RL)"]))

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "therblig_svm_model.pkl")
    with open(out_path, "wb") as f:
        pickle.dump(model, f)
    print(f"[+] Modelo exportado correctamente en: {out_path}")

if __name__ == "__main__":
    entrenar()
