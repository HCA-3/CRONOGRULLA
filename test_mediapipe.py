"""
DIAGNOSTICO MEDIAPIPE - CronoGrulla
Corre este script para verificar si MediaPipe funciona correctamente.
Presiona 'q' para salir.
"""
import cv2
import mediapipe as mp
import numpy as np

print("=" * 50)
print("  DIAGNOSTICO MEDIAPIPE - CronoGrulla")
print("=" * 50)

# 1. Verificar importación
print("[1] MediaPipe importado OK")
print(f"    Version: {mp.__version__}")

# 2. Inicializar Holistic
try:
    mp_holistic = mp.solutions.holistic
    mp_drawing = mp.solutions.drawing_utils
    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=0,
        smooth_landmarks=True,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3
    )
    print("[2] Holistic inicializado OK")
except Exception as e:
    print(f"[2] ERROR al inicializar Holistic: {e}")
    input("Presiona ENTER para salir...")
    exit(1)

# 3. Abrir cámara
cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
if not cap.isOpened():
    print("[3] Camara 0 no disponible, probando camara 1...")
    cap = cv2.VideoCapture(1 + cv2.CAP_DSHOW)

if not cap.isOpened():
    print("[3] ERROR: No se encontró ninguna cámara")
    input("Presiona ENTER para salir...")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
print("[3] Camara abierta OK")
print()
print(">>> Abriendo ventana de camara...")
print(">>> Posicionate frente a la camara.")
print(">>> Si aparece el esqueleto verde = MediaPipe funciona OK")
print(">>> Presiona 'q' para salir.")
print()

pose_spec = mp_drawing.DrawingSpec(color=(0, 255, 80), thickness=4, circle_radius=6)
conn_spec  = mp_drawing.DrawingSpec(color=(50, 255, 50), thickness=3)
hand_spec  = mp_drawing.DrawingSpec(color=(0, 200, 255), thickness=3, circle_radius=5)
hand_conn  = mp_drawing.DrawingSpec(color=(0, 180, 255), thickness=2)

frames_detected = 0
frames_total = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: No se pudo leer frame de la camara")
        break

    frame = cv2.flip(frame, 1)
    frames_total += 1
    h, w = frame.shape[:2]

    # Procesar con MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb.flags.writeable = False
    results = holistic.process(frame_rgb)
    frame_rgb.flags.writeable = True

    person_detected = results.pose_landmarks is not None

    if person_detected:
        frames_detected += 1
        # Dibujar esqueleto
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=pose_spec,
            connection_drawing_spec=conn_spec)

    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=hand_spec, connection_drawing_spec=hand_conn)

    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=hand_spec, connection_drawing_spec=hand_conn)

    # Banner de estado
    overlay = frame.copy()
    if person_detected:
        cv2.rectangle(overlay, (0, 0), (w, 45), (0, 140, 40), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, "PERSONA DETECTADA - ESQUELETO ACTIVO",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 100), 2)
    else:
        cv2.rectangle(overlay, (0, 0), (w, 45), (160, 80, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, "BUSCANDO PERSONA... posicionate frente a la camara",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)

    # Stats en pantalla
    pct = (frames_detected / frames_total * 100) if frames_total > 0 else 0
    cv2.putText(frame, f"Detecciones: {frames_detected}/{frames_total} ({pct:.0f}%)",
                (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    cv2.imshow("TEST MediaPipe - CronoGrulla (presiona Q para salir)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
holistic.close()

print()
print("=" * 50)
print(f"RESULTADO: {frames_detected} detecciones en {frames_total} frames ({pct:.1f}%)")
if frames_detected > 0:
    print(">>> MediaPipe FUNCIONA correctamente.")
    print(">>> El problema esta en la integracion con tkinter.")
else:
    print(">>> MediaPipe NO detectó ninguna persona.")
    print(">>> Posibles causas:")
    print("    - Mala iluminacion")
    print("    - Persona muy lejos o fuera de cuadro")
    print("    - Version de MediaPipe incompatible")
print("=" * 50)
input("Presiona ENTER para cerrar...")
