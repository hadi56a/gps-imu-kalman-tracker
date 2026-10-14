import numpy as np
from .conversion_capteurs import add_gps_xy, add_magnetic_heading
from .constants import G

def prepare_gps(df_gps, t0):
    """
    Applique les corrections simples aux données GPS
    """
    df = df_gps.copy()
    df, lat0, lon0 = add_gps_xy(df)
    df["t_s"] = df["Timestamp"] - t0
    return df, lat0, lon0

def prepare_imu(df_imu, noises, t0):
    """
    Applique les corrections simples aux données IMU
    """
    df = df_imu.copy()
    df = add_magnetic_heading(df)
    df["t_s"] = df["Timestamp"] - t0

    accel_cols = ["Accel_X", "Accel_Y", "Accel_Z"]
    df[accel_cols] = df[accel_cols] * G

    gyro_cols = ["Gyro_X", "Gyro_Y", "Gyro_Z"]
    df[gyro_cols] = np.deg2rad(df[gyro_cols])

    gyro_bias = noises.get("gyro_bias_rads", np.zeros(3))
    df[gyro_cols] = df[gyro_cols] - gyro_bias

    return df