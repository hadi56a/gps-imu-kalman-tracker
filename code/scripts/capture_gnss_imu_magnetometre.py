import time
import shutil
import smbus
import argparse
import traceback
import threading
from pathlib import Path
from sensors import GNSS, IMU
from utils import Button, LED, create_acquisition_directory, CSVHandler, LCD
from config import (
    PORT_BUTTON,
    PORT_LED,
    ACQUISITION_ROOT,
    GNSS_DEVICE_ADDR,
    LSM6DSO_ADDR,
    GNSS_MODES,
    MODE_GNSS,
    ACCEL_RANGE,
    ACCEL_FREQ,
    GYRO_RANGE,
    GYRO_FREQ,
    MAGNETO_FREQ,
    MAGNETO_RANGE,
    LCD_DEVICE_ADDR
)

ACQUISITION_PATH = Path(ACQUISITION_ROOT)

def start_acquisition(state, led):
    """
    Lance une acquisition multisenseur :
    - création du dossier session
    - création des sous-dossiers images / scans
    - création des CSV de timestamps
    """
    session_dir, subdirs = create_acquisition_directory(
        root_dir=ACQUISITION_ROOT,
        prefix="acquisition"
    )

    state["is_acquiring"] = True
    state["session_dir"] = session_dir
    state["coord_index"] = 0
    state["imu_index"] = 0

    # Copie du fichier config/parameters.py dans le dossier d'acquisition
    shutil.copyfile("./config/parameters.py", f"{session_dir}/parameters.py")

    # Création des fichiers CSV timestamps/frames et timestamps/scans
    # Ajout des CSVHandlers créés dans state (pour y accéder en dehors de la fonction)
    state["csv_coords"] = CSVHandler(f"{session_dir}/timestamps_coords.csv")
    state["csv_coords"].create_csv_with_header(["Index", "Timestamp", "Latitude", "Longitude", "Altitude", "PDOP", "HDOP", "VDOP", "COG_MAGNETIC"])

    state["csv_imu"] = CSVHandler(f"{session_dir}/timestamps_imu.csv")
    state["csv_imu"].create_csv_with_header([
        "Index",
        "Timestamp",
        "Accel_X",
        "Accel_Y",
        "Accel_Z",
        "Gyro_X",
        "Gyro_Y",
        "Gyro_Z",
        "Magneto_X",
        "Magneto_Y",
        "Magneto_Z"
    ])

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
    state["coords_dir"] = None
    state["imu_dir"] = None
    state["coord_index"] = 0
    state["imu_index"] = 0
    state["csv_coords"] = None
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

def gnss_worker(gnss, state, lock, stop_event, extension="csv", lcd_display=None):
    """
    Thread d'acquisition GNSS.
    """
    if lcd_display is not None:
        lcd_display.afficher("Recherche de    signal GNSS...")
    while not stop_event.is_set():
        try:
            # Lecture d'une acquisition GNSS
            data = None
            while data is None:
                data = gnss.read_donnee_acquisition()
                time.sleep(0.01)
            
            timestamp, date_acquiring = data
            index = state["coord_index"]
            
            with lock:
                if state["is_acquiring"]:
                    # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
                    # state["csv_scans"].append_row([timestamp, file_path])
                    state["csv_coords"].append_row([
                        index,
                        timestamp,
                        date_acquiring[0],
                        date_acquiring[1],
                        date_acquiring[2],
                        date_acquiring[3],
                        date_acquiring[4],
                        date_acquiring[5],
                        date_acquiring[6],
                    ])
                    state["coord_index"] += 1
                    if lcd_display is not None:
                        lcd_display.afficher(f"{date_acquiring[0]:.11f}  {date_acquiring[1]:.11f}")
                else:
                    if lcd_display is not None:
                        lcd_display.afficher("Acquisition     arretee")

        except Exception:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["coord_index"] = 0
                state["imu_index"] = 0
                state["csv_coords"] = None
                state["csv_imu"] = None
            time.sleep(0.1)

        time.sleep(0.01)

def imu_worker(imu, state, lock, stop_event, extension="csv"):
    """
    Thread d'acquisition IMU.
    """
    while not stop_event.is_set():
        try:
            # Lecture d'une acquisition IMU
            timestamp, imu_data = imu.read_IMU()
            magneto_data = imu.read_magnetometer()
            index = state["imu_index"]

            with lock:
                if state["is_acquiring"]:
                    # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
                    # state["csv_scans"].append_row([timestamp, file_path])
                    state["csv_imu"].append_row([
                        index,
                        timestamp,
                        *imu_data,
                        *magneto_data,
                    ])
                    state["imu_index"] += 1

        except Exception:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["coord_index"] = 0
                state["imu_index"] = 0
                state["csv_coords"] = None
                state["csv_imu"] = None
            time.sleep(0.1)

        time.sleep(0.01)

def main(args):
    print("Initialisation du GNSS...")
    bus = smbus.SMBus(1)
    # Initialisation du GNSS
    gnss = GNSS.GNSS(bus, GNSS_DEVICE_ADDR)

    # Configuration du GNSS
    gnss.initialisation(GNSS_MODES[MODE_GNSS])
    
    print("Initialisation du IMU...")
    # Initialisation du IMU
    imu = IMU.IMU(bus, LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ, MAGNETO_RANGE, MAGNETO_FREQ)

    # Démarrage du IMU
    imu.initialize_sensors()
    
    print("Initialisation du bouton...")
    
    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)
    
    lcd_display = LCD(LCD_DEVICE_ADDR) if args.display_lcd else None

    ACQUISITION_PATH.mkdir(parents=True, exist_ok=True)

    state = {
        "is_acquiring": False,
        "session_dir": None,
        "coord_index": 0,
        "imu_index": 0,
        "csv_coords": None,
        "csv_imu": None,
    }

    lock = threading.Lock()
    stop_event = threading.Event()

    gnss_thread = threading.Thread(
        target=gnss_worker,
        args=(gnss, state, lock, stop_event, "csv", lcd_display),
        daemon=True
    )

    imu_thread = threading.Thread(
        target=imu_worker,
        args=(imu, state, lock, stop_event),
        daemon=True
    )

    print("Appuyer sur le bouton pour démarrer / arrêter l'acquisition multisenseur.")
    print("Ctrl+C pour quitter.")

    try:
        gnss_thread.start()
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

        gnss_thread.join(timeout=1.0)
        imu_thread.join(timeout=1.0)

        led.off()
        button.cleanup()
        led.cleanup()

        if lcd_display is not None:
            lcd_display.effacer()

        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Acquisition multisenseur GNSS + IMU"
    )
    parser.add_argument("--display_lcd", action="store_true", help="Afficher les données sur l'écran LCD.")
    args = parser.parse_args()
    main(args)