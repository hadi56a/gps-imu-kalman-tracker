import os
import numpy as np
import pandas as pd
from preprocessing.load_data import load_prepared_data
from preprocessing.conversion_capteurs import latlon_to_local_xy

def changement_repere(a_imu,theta):
    """
    Fonction qui permet de passer d'une accélération dans le repère de l'IMU à une
    accélération dans le repère du monde

    Arguments:
    """
    a_imu_x,a_imu_y = a_imu[0],a_imu[1]
    a_monde_x = a_imu_x*np.cos(theta)-a_imu_y*np.sin(theta)
    a_monde_y = a_imu_x*np.sin(theta)+a_imu_y*np.cos(theta)
    return (a_monde_x,a_monde_y)

def gps_to_cartesian(latitude, longitude, lat_init, long_init):
    """
    Projette un point GPS en coordonnées planes (x, y) en mètres autour du point
    de départ (projection équirectangulaire locale).
    On utilise le même rayon terrestre et la même latitude de référence que
    local_xy_to_latlon, pour que l'aller-retour GPS -> (x, y) -> GPS soit exact.

    Arguments:
    - latitude, longitude : point à convertir (en degrés)
    - lat_init, long_init : point de départ de la trajectoire (en degrés)
    Sortie : coordonnées (x, y) en mètres
    """
    x, y = latlon_to_local_xy(latitude, longitude, lat0=lat_init, lon0=long_init)
    return np.array([float(x), float(y)])


def jacobian_F(dt):
    """
    F = [x , y , vx , vy, ]
    """
    F = np.array([
        [1.0,0.0,dt,0.0,0.0],
        [0.0,1.0,0.0,dt,0.0],
        [0.0,0.0,1.0,0.0,0.0],
        [0.0,0.0,0.0,1.0,0.0],
        [0.0,0.0,0.0,0.0,1.0]
    ])
    return F


def magneto_to_angle(Mx,My):
    tetha= np.arctan2(Mx,My)
    tetha=normalisation_angle(tetha)
    return tetha

def normalisation_angle(angle):
    """
    Garde un angle dans l'intervalle [-pi, pi]
    """
    return (angle+np.pi)%(2*np.pi)-np.pi

def associer_gps_imu(data_imu, data_gps, tolerance=0.05):
    """
    Pour chaque point GPS, cherche le point IMU le plus proche dans le temps.
    Les timestamps IMU sont triés : une recherche dichotomique (np.searchsorted)
    suffit, au lieu de comparer chaque point GPS à tous les points IMU.
    Résultat : même nombre de lignes que le fichier GPS.
    """
    t_imu = data_imu["Timestamp"].to_numpy(dtype=float)
    t_gps = data_gps["Timestamp"].to_numpy(dtype=float)

    # indice du premier IMU >= t_gps, puis on compare avec son voisin de gauche
    droite = np.clip(np.searchsorted(t_imu, t_gps, side="left"), 0, len(t_imu) - 1)
    gauche = np.clip(droite - 1, 0, len(t_imu) - 1)
    delta_gauche = np.abs(t_imu[gauche] - t_gps)
    delta_droite = np.abs(t_imu[droite] - t_gps)
    # en cas d'égalité, on garde le plus petit indice (comme une recherche linéaire)
    meilleur = np.where(delta_gauche <= delta_droite, gauche, droite)
    meilleur_delta = np.minimum(delta_gauche, delta_droite)
    gps_trouve = meilleur_delta <= tolerance

    df_association = pd.DataFrame({
        "index_gps": np.arange(len(t_gps)),
        "index_imu": np.where(gps_trouve, meilleur, -1),
        "timestamp_gps": t_gps,
        "timestamp_imu": np.where(gps_trouve, t_imu[meilleur], np.nan),
        "difference": meilleur_delta,
        "gps_trouve": gps_trouve,
    })
    df_association["index_gps"] = df_association["index_gps"].astype("Int64")
    df_association["index_imu"] = df_association["index_imu"].astype("Int64").mask(~gps_trouve)

    return df_association

def filtre_kalman(file_path_imu, file_path_gps):
    os.makedirs("data", exist_ok=True)

    data_imu, data_gps, _, lat0, lon0 = load_prepared_data(file_path_gps, file_path_imu)

    # Association GPS -> meilleur IMU
    df_association = associer_gps_imu(data_imu, data_gps, tolerance=0.05)

    # On garde seulement les GPS qui ont trouvé un IMU
    df_association_utilisee = df_association[df_association["gps_trouve"]].copy()
    df_association_utilisee.to_csv("data/association_gps_imu.csv", index=False)

    # Table indice IMU -> indice GPS (le premier GPS associé à cet IMU),
    # pour ne pas parcourir toute l'association à chaque mesure IMU
    gps_par_imu = {}
    for index_imu, index_gps in zip(df_association_utilisee["index_imu"], df_association_utilisee["index_gps"]):
        gps_par_imu.setdefault(int(index_imu), int(index_gps))

    long_init = data_gps["Longitude"][0]
    lat_init = data_gps["Latitude"][0]

    n_imu, _ = data_imu.shape

    x = np.zeros((5, 1))
    P = np.eye(5)
    I = np.eye(5)

    sigma_Q = 0.1
    Q = np.diag([sigma_Q, sigma_Q, sigma_Q, sigma_Q, sigma_Q])

    sigma_r_gps = 5.0
    sigma_r_magneto = 0.1
    R = np.diag([sigma_r_gps, sigma_r_gps, sigma_r_magneto])

    H = np.array([
        [1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1]
    ])

    traj_estimee = []

    data_imu_time_stamp = data_imu["Timestamp"][0]

    for i in range(n_imu):
        t_imu = data_imu["Timestamp"][i]

        if i == 0:
            dt = 0.1
        else:
            dt = t_imu - data_imu_time_stamp
        if dt <= 0:
            dt = 0.1

        theta = magneto_to_angle(
            data_imu["Magneto_Z"][i],
            data_imu["Magneto_Y"][i]
        )

        a_imu = (
            data_imu["Accel_Z"][i],
            data_imu["Accel_Y"][i]
        )

        a_monde = changement_repere(a_imu, theta)
        w = data_imu["Gyro_X"][i]
        F = jacobian_F(dt)
        Bu = np.array([
            [0.5 * a_monde[0] * dt**2],
            [0.5 * a_monde[1] * dt**2],
            [a_monde[0] * dt],
            [a_monde[1] * dt],
            [w * dt]
        ])

        x_pred = F @ x + Bu
        x_pred[4, 0] = normalisation_angle(x_pred[4, 0])

        P_pred = F @ P @ F.T + Q

        # Cet IMU est-il le meilleur IMU d'un point GPS ?
        gps_index = gps_par_imu.get(i)

        if gps_index is not None:

            longitude = data_gps["Longitude"][gps_index]
            latitude = data_gps["Latitude"][gps_index]

            coord = gps_to_cartesian(latitude, longitude, lat_init, long_init)

            z = np.array([
                [coord[0]],
                [coord[1]],
                [theta]])

            innovation = z - H @ x_pred
            innovation[2, 0] = normalisation_angle(innovation[2, 0])

            S = H @ P_pred @ H.T + R
            K = P_pred @ H.T @ np.linalg.inv(S)

            x = x_pred + K @ innovation
            P = (I - K @ H) @ P_pred

            x[4, 0] = normalisation_angle(x[4, 0])

            traj_estimee.append({
                "Timestamp": data_gps["Timestamp"][gps_index],
                "x": x[0, 0],
                "y": x[1, 0],
            })

        else:

            x = x_pred
            P = P_pred
            x[4, 0] = normalisation_angle(x[4, 0])

        data_imu_time_stamp = t_imu

    df_traj = pd.DataFrame(traj_estimee)




    df_traj.to_csv("data/traj_estimee.csv", index=False)

    return traj_estimee

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Filtre de Kalman")

    parser.add_argument('fichier_imu',type=str,help="Chemin fichier CSV IMU")

    parser.add_argument('fichier_gps',type=str,help="Chemin fichier CSV GPS")

    args = parser.parse_args()

    if not os.path.exists(args.fichier_imu):
        print(f"Erreur : Le fichier IMU '{args.fichier_imu}' n'existe pas.")
        exit(1)

    if not os.path.exists(args.fichier_gps):
        print(f"Erreur : Le fichier GPS '{args.fichier_gps}' n'existe pas.")
        exit(1)

    if not os.path.exists("data"):
        os.makedirs("data")

    print(" fusion de données (Filtre de Kalman)")
    print(f" Fichier IMU : {args.fichier_imu}")
    print(f" Fichier GPS : {args.fichier_gps}")

    trajectoire = filtre_kalman(args.fichier_imu, args.fichier_gps)
    print(f" Filtre exécuté : {len(trajectoire)} points de trajectoire estimés.")