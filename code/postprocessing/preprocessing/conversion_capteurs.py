import numpy as np
from .constants import EARTH_RADIUS_M

def latlon_to_local_xy(lat, lon, lat0=None, lon0=None):
    """
    Convertit latitude/longitude en coordonnées locales x/y en mètres
    """
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    if lat0 is not None and lon0 is not None:
        lat0 = float(lat0)
        lon0 = float(lon0)
    lat_rad = np.deg2rad(lat)
    lon_rad = np.deg2rad(lon)

    x = EARTH_RADIUS_M * (lon_rad - np.deg2rad(lon0)) * np.cos(np.deg2rad(lat0))
    y = EARTH_RADIUS_M * (lat_rad - np.deg2rad(lat0))

    return x, y

def local_xy_to_latlon(x, y, lat0, lon0):
    """
    Convertit coordonnées locales x/y en mètres en latitude/longitude
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    lat0_rad = np.deg2rad(lat0)
    lon0_rad = np.deg2rad(lon0)

    lat_rad = y / EARTH_RADIUS_M + lat0_rad
    lon_rad = x / (EARTH_RADIUS_M * np.cos(lat0_rad)) + lon0_rad

    lat = np.rad2deg(lat_rad)
    lon = np.rad2deg(lon_rad)

    return lat, lon

def add_gps_xy(df_gps):
    """
    Ajoute GPS_X et GPS_Y en mètres à un dataframe GPS
    """
    df = df_gps.copy()

    lat0 = df["Latitude"].iloc[0]
    lon0 = df["Longitude"].iloc[0]

    x, y = latlon_to_local_xy(
        df["Latitude"].to_numpy(),
        df["Longitude"].to_numpy(),
        lat0=lat0,
        lon0=lon0
    )

    df["GPS_X"] = x
    df["GPS_Y"] = y
    return df, lat0, lon0

def magnetometer_to_heading(mx, my):
    """
    Convertit Magneto_X / Magneto_Y en cap
    """
    heading = np.arctan2(my, mx)
    heading = heading % (2 * np.pi)

    return heading

def add_magnetic_heading(df_mag):
    """
    Ajoute un cap magnétique au dataframe magnétomètre
    """

    df = df_mag.copy()

    mx = df["Magneto_X"].to_numpy(dtype=float)
    my = df["Magneto_Y"].to_numpy(dtype=float)

    heading = magnetometer_to_heading(
        mx,
        my
    )

    df["Heading_rad"] = heading
    df["Heading_deg"] = np.rad2deg(heading)

    return df