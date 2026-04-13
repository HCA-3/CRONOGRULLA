import cv2
import sys

def test_cameras():
    print("--- DIAGNOSTICO DE CAMARA CRONOGRULLA ---")
    available_cams = []
    
    # Probar los primeros 5 indices
    for i in range(5):
        print(f"Probando camara {i}...")
        # Probamos con DirectShow que es lo mas estable en Windows
        cap = cv2.VideoCapture(i + cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"!!! LA CAMARA {i} FUNCIONA OK !!!")
                available_cams.append(i)
            else:
                print(f"--- LA CAMARA {i} ESTA ABIERTA PERO NO DA IMAGEN ---")
            cap.release()
        else:
            print(f"Camara {i} no disponible.")

    if not available_cams:
        print("\nNO SE DETECTARON CAMARAS ACTIVAS.")
        print("Sugerencias de configuracion en tu computador:")
        print("1. Ve a Inicio > Configuracion > Privacidad > Camara.")
        print("2. REVISA QUE 'Permitir que las aplicaciones de escritorio accedan a la camara' este en ON.")
    else:
        print(f"\nUsa el INDICE {available_cams[0]} en CronoGrulla.")

if __name__ == "__main__":
    test_cameras()
