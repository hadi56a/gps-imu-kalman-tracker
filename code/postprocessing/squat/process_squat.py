import numpy as np
from scipy.signal import butter, filtfilt
import argparse
from utils import CSVHandler

def filter_signal(raw_data: np.ndarray, fs: float = 50.0, cutoff: float = 2.0, order: int = 4) -> np.ndarray:
    """
    Méthode permettant de filtrer les données avec un filtre de Butterworth (passe bas)
    
    :params raw_data: données brutes à filtrer
    :params fs: fréquence d'échantillonnage en Hz (défaut: 50.0)
    :params cutoff: fréquence de coupure en Hz (défaut: 2.0)
    :params order: ordre du filtre (défaut: 4)
    """

    nyq = fs / 2.0
    b, a = butter(order, cutoff / nyq, btype='low', analog=False)
    return filtfilt(b, a, raw_data)


def normalize(acc_x: np.ndarray, acc_y: np.ndarray, acc_z: np.ndarray, 
              gyr_x: np.ndarray, gyr_y: np.ndarray, gyr_z: np.ndarray):
    """
    Normalise les données de l'accéléromètre et du gyroscope en calculant leur norme.
    
    Retourne:
        tuple: (accel_norm, gyro_norm) sous forme de tableaux numpy.
    """
    accel_norm = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
    gyro_norm = np.sqrt(gyr_x**2 + gyr_y**2 + gyr_z**2)
    
    return accel_norm, gyro_norm


def process_squat(csv_src: str, csv_out: str):
    """
    Lit l'acquisition, applique le filtre, normalise les données et génère le fichier de sortie.
    """
    csv_reader = CSVHandler(csv_src)
    raw_rows = csv_reader.read_dict_rows()

    if not raw_rows:
        print(f"Erreur : Le fichier {csv_src} est vide ou introuvable.")
        return

    print(f"Traitement de {len(raw_rows)} lignes en cours...")

    try:
        indices = [int(r['Index']) for r in raw_rows]
        timestamps = [float(r['Timestamp']) for r in raw_rows]
        
        acc_x = np.array([float(r['Accel_X']) for r in raw_rows])
        acc_y = np.array([float(r['Accel_Y']) for r in raw_rows])
        acc_z = np.array([float(r['Accel_Z']) for r in raw_rows])
        
        gyr_x = np.array([float(r['Gyro_X']) for r in raw_rows])
        gyr_y = np.array([float(r['Gyro_Y']) for r in raw_rows])
        gyr_z = np.array([float(r['Gyro_Z']) for r in raw_rows])
    except KeyError as e:
        print(f"Erreur : Colonne manquante dans le fichier source : {e}")
        return

    acc_x_f = filter_signal(acc_x)
    acc_y_f = filter_signal(acc_y)
    acc_z_f = filter_signal(acc_z)
    
    gyr_x_f = filter_signal(gyr_x)
    gyr_y_f = filter_signal(gyr_y)
    gyr_z_f = filter_signal(gyr_z)

    accel_norm, gyro_norm = normalize(acc_x_f, acc_y_f, acc_z_f, gyr_x_f, gyr_y_f, gyr_z_f)

    csv_writer = CSVHandler(csv_out)
    csv_writer.create_csv_with_header(["Index", "Timestamp", "Accel_Norm", "Gyro_Norm"])

    for i in range(len(raw_rows)):
        csv_writer.append_row([
            indices[i], 
            timestamps[i], 
            round(accel_norm[i], 6), 
            round(gyro_norm[i], 6)
        ])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filtre et normalise les données d'acquisition squat.")
    parser.add_argument("input_csv", type=str, help="Chemin du fichier CSV d'entrée.")
    parser.add_argument("output_csv", type=str, help="Chemin du fichier CSV de sortie.")
    args = parser.parse_args()

    process_squat(args.input_csv, args.output_csv)