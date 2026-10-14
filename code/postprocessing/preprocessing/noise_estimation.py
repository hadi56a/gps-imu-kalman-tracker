import numpy as np
from .constants import G

def _estimate_mag_heading_noise(df_mag):
    """
    Estime le bruit du cap magnétique
    """
    heading = df_mag["Heading_rad"].to_numpy(dtype=float)

    if len(heading) < 2:
        return np.deg2rad(30.0)

    # Évite les sauts artificiels entre 359° et 0°
    heading = np.unwrap(heading)
    sigma_heading = np.std(heading, ddof=1)
    return sigma_heading

def _estimate_imu_noise(df_accel, df_gyro, df_mag=None):
    """
    Estime simplement le bruit des capteurs à partir de données immobiles
    """
    acc = df_accel[["Accel_X", "Accel_Y", "Accel_Z"]].to_numpy(dtype=float)
    gyro = df_gyro[["Gyro_X", "Gyro_Y", "Gyro_Z"]].to_numpy(dtype=float)

    acc = acc * G
    gyro = np.deg2rad(gyro)

    acc_mean = np.mean(acc, axis=0)
    acc_std = np.std(acc, axis=0, ddof=1)

    gyro_bias = np.mean(gyro, axis=0)
    gyro_std = np.std(gyro, axis=0, ddof=1)

    result = {
        "acc_mean": acc_mean,
        "acc_std": acc_std,
        "gyro_bias_rads": gyro_bias,
        "gyro_std_rads": gyro_std,
    }

    if df_mag is not None:
        result["mag_heading_std_rad"] = _estimate_mag_heading_noise(df_mag)
        result["mag_heading_std_deg"] = np.rad2deg(result["mag_heading_std_rad"])

    return result

def _estimate_gps_R_static(df_gps):
    """
    Estime R_gps à partir d'une acquisition GPS immobile
    """
    xy = df_gps[["GPS_X", "GPS_Y"]].to_numpy(dtype=float)

    sigma_x = np.std(xy[:, 0], ddof=1)
    sigma_y = np.std(xy[:, 1], ddof=1)

    return np.diag([sigma_x**2, sigma_y**2])

def estimate_all_noises(df_accel, df_gyro ,df_mag, df_gps=None):
    """
    Fonction qui estime les variables pour R et Q
    """
    result = _estimate_imu_noise(df_accel, df_gyro, df_mag)

    if df_gps is not None:
        result["R_gps_static"] = _estimate_gps_R_static(df_gps)
    return result