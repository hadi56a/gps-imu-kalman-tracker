import argparse
import pandas as pd
import numpy as np

MIN_DATA_VALIDATION = 3
MAX_DISTANCE_THRESHOLD = 1000  # mètres
RAYON_TERRE = 6_371_000  # mètres
REQUIRED_COLUMNS = ["Timestamp", "Latitude", "Longitude"]

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcule la distance en mètres entre deux points GPS."""
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return RAYON_TERRE * c


def project_df(df):
    """Ne garde que les colonnes Latitude et Longitude."""
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {missing_columns}")
    return df[REQUIRED_COLUMNS].copy()


def get_point(df, index):
    """Retourne la latitude et la longitude d'une ligne."""
    row = df.iloc[index]
    return row["Latitude"], row["Longitude"]


def points_valides(df, index1, index2, max_distance=MAX_DISTANCE_THRESHOLD):
    """Vérifie si deux points consécutifs sont proches."""
    lat1, lon1 = get_point(df, index1)
    lat2, lon2 = get_point(df, index2)
    return haversine_distance(lat1, lon1, lat2, lon2) <= max_distance


def fenetre_valide(df, start_index, window_size, max_distance=MAX_DISTANCE_THRESHOLD):
    """Vérifie qu'une fenêtre contient des points consécutifs proches."""
    end_index = start_index + window_size
    return all(points_valides(df, i - 1, i, max_distance=max_distance) for i in range(start_index + 1, end_index))


def premier_index_valide(df, max_distance=MAX_DISTANCE_THRESHOLD):
    """Trouve le premier index d'une fenêtre valide."""
    max_start_index = len(df) - MIN_DATA_VALIDATION + 1
    for start_index in range(max_start_index):
        if fenetre_valide(df, start_index, MIN_DATA_VALIDATION, max_distance=max_distance):
            return start_index
    raise ValueError(f"Aucune fenêtre de {MIN_DATA_VALIDATION} points consécutifs ne respecte le seuil de distance {MAX_DISTANCE_THRESHOLD} m.")


def filter_gps_data(df, max_distance):
    """Supprime les points GPS trop éloignés du point précédent valide."""
    if len(df) < MIN_DATA_VALIDATION:
        raise ValueError(f"Le DataFrame doit contenir au moins {MIN_DATA_VALIDATION} points.")

    df = df.reset_index(drop=True) # Réinitialise les index pour faciliter l'accès par position
    premier_index = premier_index_valide(df)
    print(f"Premier index valide trouvé : {premier_index}")

    points_valides = [df.iloc[premier_index]]
    for i in range(premier_index + 1, len(df)):
        point_pred = points_valides[-1]
        point_courant = df.iloc[i]

        dist = haversine_distance(
            point_pred["Latitude"], point_pred["Longitude"],
            point_courant["Latitude"], point_courant["Longitude"]
        )

        if dist <= max_distance:
            points_valides.append(point_courant)
        else:
            print(f"Point à l'index {i} supprimé : distance de {dist:.2f} m avec le dernier point valide.")

    return pd.DataFrame(points_valides).reset_index(drop=True)


def filter_gps(input_csv, output_csv, max_distance):
    """Lit un CSV, filtre les points GPS, puis écrit le résultat."""
    df = pd.read_csv(input_csv)

    projected_df = project_df(df)
    filtered_df = filter_gps_data(projected_df, max_distance)

    filtered_df.to_csv(output_csv, index=False)
    print(f"Filtrage terminé. Fichier enregistré : {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filtre un fichier CSV GPS pour ne conserver que les points valides.")
    parser.add_argument("input_csv", type=str, help="Chemin du fichier CSV d'entrée.")
    parser.add_argument("output_csv", type=str, help="Chemin du fichier CSV de sortie.")
    parser.add_argument("--max_distance", type=float, default=MAX_DISTANCE_THRESHOLD, help="Distance maximale en mètres entre points consécutifs (par défaut : 1000 m).")
    args = parser.parse_args()

    filter_gps(args.input_csv, args.output_csv, max_distance=args.max_distance)