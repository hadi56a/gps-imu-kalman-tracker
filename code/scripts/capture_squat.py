import time
import shutil
import smbus
import argparse
import traceback
import threading
from pathlib import Path
from sensors import IMU
from utils import Button, LED, create_acquisition_directory, CSVHandler
from config import (
    PORT_BUTTON,
    PORT_LED,
    ACQUISITION_ROOT,
    LSM6DSO_ADDR,
    ACCEL_RANGE,
    ACCEL_FREQ,
    GYRO_RANGE,
    GYRO_FREQ,
    MAGNETO_RANGE,
    MAGNETO_FREQ
)

ACQUISITION_PATH = Path(ACQUISITION_ROOT)

def start_acquisition(state, led):
    """
    Lance une acquisition multisenseur :
    - création du dossier session
    - création des CSV de timestamps
    """
    session_dir, _ = create_acquisition_directory(
        root_dir=ACQUISITION_ROOT,
        prefix="squat"
    )

    state["is_acquiring"] = True
    state["session_dir"] = session_dir
    state["imu_index"] = 0

    # Copie du fichier config/parameters.py dans le dossier d'acquisition
    shutil.copyfile("./config/parameters.py", f"{session_dir}/parameters.py")

    # Création du fichier CSV timestamp/accel_gyro
    # Ajout des CSVHandlers créés dans state (pour y accéder en dehors de la fonction)
    state["csv_imu"] = CSVHandler(f"{session_dir}/timestamps_squat.csv")
    state["csv_imu"].create_csv_with_header(["Index", "Timestamp", "Accel_X", "Accel_Y", "Accel_Z", "Gyro_X", "Gyro_Y", "Gyro_Z"])

    led.on()
    print(f"Acquisition démarrée : {session_dir}")

def stop_acquisition(state, led, reason=None):
    """
    Arrête l'acquisition en cours et remet l'état session à zéro.
    """
    if reason is not None:
        print(f"Acquisition interrompue : {reason}")
    elif state["session_dir"] is not None:
        print(f"Acquisition arrêtée : {state['session_dir']}")

    state["is_acquiring"] = False
    state["session_dir"] = None
    state["imu_dir"] = None
    state["imu_index"] = 0
    state["csv_imu"] = None

    led.off()

def toggle_acquisition(state, led, lock):
    """
    Démarre ou arrête une acquisition.
    """
    with lock:
        if not state["is_acquiring"]:
            start_acquisition(state, led)
        else:
            stop_acquisition(state, led)

def imu_worker(imu, state, lock, stop_event, extension="csv"):
    """
    Thread d'acquisition IMU.
    """
    while not stop_event.is_set():
        try:
            # Lecture d'une acquisition IMU
            timestamp, imu_data = imu.read_IMU()
            index = state["imu_index"]

            with lock:
                if state["is_acquiring"]:
                    # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
                    # state["csv_scans"].append_row([timestamp, file_path])
                    state["csv_imu"].append_row([
                        index,
                        timestamp,
                        *imu_data
                    ])
                    state["imu_index"] += 1

        except Exception:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["imu_index"] = 0
                state["csv_imu"] = None
            time.sleep(0.1)

        time.sleep(0.01)

def main():
    bus = smbus.SMBus(1)

    print("Initialisation du IMU...")
    # Initialisation du IMU
    imu = IMU.IMU(bus, LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ, MAGNETO_RANGE, MAGNETO_FREQ)

    # Démarrage du IMU
    imu.initialize_sensors()
    
    print("Initialisation du bouton...")
    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    ACQUISITION_PATH.mkdir(parents=True, exist_ok=True)

    state = {
        "is_acquiring": False,
        "session_dir": None,
        "imu_index": 0,
        "csv_imu": None,
    }

    lock = threading.Lock()
    stop_event = threading.Event()

    imu_thread = threading.Thread(
        target=imu_worker,
        args=(imu, state, lock, stop_event),
        daemon=True
    )

    print("Appuyer sur le bouton pour démarrer / arrêter l'acquisition multisenseur.")
    print("Ctrl+C pour quitter.")

    try:
        imu_thread.start()

        while True:
            if button.is_pressed():
                toggle_acquisition(state, led, lock)
                button.wait_for_release()
                time.sleep(0.05)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nArrêt du programme demandé par l'utilisateur.")

    finally:
        stop_event.set()

        imu_thread.join(timeout=1.0)

        led.off()
        button.cleanup()
        led.cleanup()

        print("Ressources libérées.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Acquisition Squat (IMU)"
    )
    args = parser.parse_args()
    main()