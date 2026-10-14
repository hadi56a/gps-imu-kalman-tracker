import numpy as np
from process_squat import normalize, filter_signal
import argparse
from utils import CSVHandler

def valider_rotation_gyro(gyro_window: np.ndarray, seuil_rotation: float) -> bool:
    """
    Vérifie si la vitesse angulaire (rotation) a été suffisante pendant le mouvement.
    :param gyro_window: Les données du gyroscope enregistrées PENDANT la durée du squat.
    :param seuil_rotation: Le pic de rotation minimum exigé (en degrés par seconde).
    """
    if len(gyro_window) == 0:
        return False

    pic_rotation = np.max(gyro_window)
    return pic_rotation >= seuil_rotation

def detect_complete_squats(csv_src: str, use_gyro: bool = True):
    """
    Détecte les squats complets via une Machine à États, avec vérification du temps
    et validation optionnelle par le gyroscope.
    """
    csv_reader = CSVHandler(csv_src)
    raw_rows = csv_reader.read_dict_rows()

    if not raw_rows:
        print("Erreur : Le fichier est vide.")
        return

    timestamps = np.array([float(r['Timestamp']) for r in raw_rows])
    
    acc_x = np.array([float(r['Accel_X']) for r in raw_rows])
    acc_y = np.array([float(r['Accel_Y']) for r in raw_rows])
    acc_z = np.array([float(r['Accel_Z']) for r in raw_rows])
    
    gyr_x = np.array([float(r['Gyro_X']) for r in raw_rows])
    gyr_y = np.array([float(r['Gyro_Y']) for r in raw_rows])
    gyr_z = np.array([float(r['Gyro_Z']) for r in raw_rows])

    dt_moyen = np.mean(np.diff(timestamps))
    fs_estime = 1.0 / dt_moyen
    
    accel_norm, gyro_norm = normalize(acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z)
    
    accel_norm_filt = filter_signal(accel_norm, fs=fs_estime, cutoff=2.0)
    gyro_norm_filt = filter_signal(gyro_norm, fs=fs_estime, cutoff=2.0)

    SEUIL_DESCENTE = 0.90    # Force d'allègement (en g)
    SEUIL_POUSSEE = 1.05     # Force de poussée (en g)
    SEUIL_REPOS = 1.05       # Retour à la stabilité (en g) 
    TEMPS_MIN_SQUAT = 1.25    # Le squat doit durer au moins 1 seconde
    TEMPS_MAX_SQUAT = 4.0    # Le squat doit durer au maximum 4 secondes
    SEUIL_ROTATION = 40.0    # Vitesse de rotation minimale exigée (en deg/s)

    etat = 0
    squats_detectes = []
    
    idx_debut_descente = 0
    temps_debut_descente = 0

    for i in range(len(accel_norm_filt)):
        val_accel = accel_norm_filt[i]
        temps_actuel = timestamps[i]

        if etat == 0:
            if val_accel < SEUIL_DESCENTE:
                etat = 1
                idx_debut_descente = i
                temps_debut_descente = temps_actuel

        elif etat == 1:
            if val_accel > SEUIL_POUSSEE:
                etat = 2
            elif (temps_actuel - temps_debut_descente) > TEMPS_MAX_SQUAT:
                etat = 0 

        elif etat == 2:
            if val_accel < SEUIL_REPOS:
                temps_fin = temps_actuel
                duree_squat = temps_fin - temps_debut_descente
                
                if duree_squat >= TEMPS_MIN_SQUAT:
                    squat_est_valide = True
                    
                    if use_gyro:
                        fenetre_gyro = gyro_norm_filt[idx_debut_descente:i]
                        
                        if not valider_rotation_gyro(fenetre_gyro, SEUIL_ROTATION):
                            squat_est_valide = False
                            print(f"[Refusé] Mouvement à {temps_fin - timestamps[0]:.1f}s rejeté : Manque de rotation (Flexion insuffisante).")
                            
                    if squat_est_valide:
                        squats_detectes.append(i)
                else:
                    print(f"[Refusé] Mouvement à {temps_fin - timestamps[0]:.1f}s rejeté : Trop rapide ({duree_squat:.2f}s).")
                etat = 0


    print("\n" + "="*45)
    mode_gyro = "ACTIVÉ" if use_gyro else "DÉSACTIVÉ"
    print(f"BILAN : {len(squats_detectes)} SQUATS VALIDES (Gyroscope : {mode_gyro})")
    print("="*45)
    
    for i, idx in enumerate(squats_detectes):
        t_relatif = timestamps[idx] - timestamps[0]
        print(f"Squat #{i+1:02d} | Validé à la seconde : {t_relatif:.2f}s")

    return squats_detectes, timestamps - timestamps[0], accel_norm_filt, gyro_norm_filt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", type=str)
    parser.add_argument("--no-gyro", action="store_true", help="Désactive la vérification du gyroscope")
    args = parser.parse_args()
    detect_complete_squats(args.input_csv, use_gyro=not args.no_gyro)