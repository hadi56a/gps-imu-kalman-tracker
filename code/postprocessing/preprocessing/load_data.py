import pandas as pd
import numpy as np
from .prepare_data import prepare_gps, prepare_imu
from .noise_estimation import estimate_all_noises

def _load_data_imu(file_path):
    """Charge les données IMU depuis un fichier CSV."""
    try:
        df_imu = pd.read_csv(file_path)
        print(f"Données IMU chargées depuis {file_path} : {len(df_imu)} lignes.")
        return df_imu
    except Exception as e:
        print(f"Erreur lors du chargement des données IMU : {e}")
        raise

def _load_data_gps(file_path):
    """Charge les données GPS depuis un fichier CSV."""
    try:
        df_gps = pd.read_csv(file_path)
        print(f"Données GPS chargées depuis {file_path} : {len(df_gps)} lignes.")
        return df_gps
    except Exception as e:
        print(f"Erreur lors du chargement des données GPS : {e}")
        raise

def _keep_changed_rows(df, cols, keep_cols=None, name=None):
    """
    Garde uniquement les lignes où les colonnes données changent
    par rapport à la dernière valeur gardée.
    """
    df = df.copy()
    df = df.drop(columns=["Index"], errors="ignore")
    df = df.sort_values("Timestamp").reset_index(drop=True)

    values = df[list(cols)].to_numpy(dtype=float)

    keep = [False] * len(df)
    last_value = None

    for i, v in enumerate(values):
        if not np.all(np.isfinite(v)):
            continue

        if last_value is None or not np.array_equal(v, last_value):
            keep[i] = True
            last_value = v.copy()

    if name is not None:
        print(f"Filtrage de {len(df) - np.sum(keep)} lignes pour {name}")
    if keep_cols is not None:
        return df.loc[keep, ["Timestamp", *cols, *keep_cols]].reset_index(drop=True)
    else:
        return df.loc[keep, ["Timestamp", *cols]].reset_index(drop=True)

def _filter_imu_streams(df_imu):
    df_imu = _keep_changed_rows(
        df_imu,
        cols=("Accel_X", "Accel_Y", "Accel_Z", "Gyro_X", "Gyro_Y", "Gyro_Z", "Magneto_X", "Magneto_Y", "Magneto_Z"),
        name="accel_gyro_mag"
    )

    """df_mag = _keep_changed_rows(
        df_imu,
        cols=("Magneto_X", "Magneto_Y", "Magneto_Z"),
        name="mag"
    )"""

    return df_imu

def _load_data(gps_path, imu_path):
    """Charge les données depuis un fichier CSV.
    Renvoie un tuple (df_imu, df_gps) contenant les DataFrames correspondants.
    """
    try:
        df_imu = _load_data_imu(imu_path)
        df_gps = _load_data_gps(gps_path)
        return df_imu, df_gps
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        raise

def _load_filtered_data(gps_path, imu_path):
    """Charge les données depuis un fichier CSV.
    Renvoie un tuple (df_imu, df_gps) contenant les DataFrames correspondants.
    """
    df_imu, df_gps = _load_data(gps_path, imu_path)
    df_imu = _filter_imu_streams(df_imu)
    return df_imu, df_gps

def _get_static_noises(gps_path, imu_path):
    df_imu, df_gps = _load_filtered_data(gps_path, imu_path)
    t0 = min(df_imu["Timestamp"].min(), df_gps["Timestamp"].min())

    df_gps, _, _ = prepare_gps(df_gps, t0)
    df_imu = prepare_imu(df_imu, {}, t0)

    df_accel = df_imu[["Timestamp", "Accel_X", "Accel_Y", "Accel_Z"]]
    df_gyro = df_imu[["Timestamp", "Gyro_X", "Gyro_Y", "Gyro_Z"]]
    df_mag = df_imu[["Timestamp", "Magneto_X", "Magneto_Y", "Magneto_Z", "Heading_rad"]]

    return estimate_all_noises(df_accel, df_gyro, df_mag, df_gps)

def load_prepared_data(gps_path, imu_path):
    noises = _get_static_noises(gps_path, imu_path)
    df_imu, df_gps = _load_filtered_data(gps_path, imu_path)

    t0 = min(df_imu["Timestamp"].min(), df_gps["Timestamp"].min())
    df_gps, lat0, lon0 = prepare_gps(df_gps, t0)
    df_imu = prepare_imu(df_imu, noises, t0)

    return df_imu, df_gps, noises, lat0, lon0

if __name__ == "__main__":
    folder_path = "data/acquisition_20260519_080544"
    gps_path = folder_path + "/timestamps_coords.csv"
    imu_path = folder_path + "/timestamps_imu.csv"
    df_imu, df_gps, noises, lat0, lon0 = load_prepared_data(gps_path, imu_path)
    print(df_imu.head())