from preprocessing.conversion_capteurs import local_xy_to_latlon
import argparse
import os
import pandas as pd

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Convertit un fichier de coordonnées (x, y) en coordonnées GPS (Lat, Long)."
    )

    parser.add_argument(
        'fichier_cartesian',
        type=str,
        help="Chemin vers le fichier CSV contenant les colonnes timestamp, x et y"
    )

    parser.add_argument(
        '--lat_init',
        type=float,
        required=True,
        help="Latitude de référence initiale"
    )

    parser.add_argument(
        '--long_init',
        type=float,
        required=True,
        help="Longitude de référence initiale"
    )

    args = parser.parse_args()

    if not os.path.exists(args.fichier_cartesian):
        print(f"Erreur : Le fichier '{args.fichier_cartesian}' n'existe pas.")
        exit(1)

    df = pd.read_csv(args.fichier_cartesian)

    if 'x' not in df.columns or 'y' not in df.columns:
        print("Erreur : Le fichier CSV doit contenir les colonnes 'x' et 'y'.")
        exit(1)

    if 'Timestamp' not in df.columns:
        print("Erreur : Le fichier CSV doit contenir une colonne 'Timestamp'.")
        exit(1)

    print("Conversion des coordonnées en Latitude/Longitude...")

    lats, longs = local_xy_to_latlon(
        df['x'].values,
        df['y'].values,
        args.lat_init,
        args.long_init
    )

    df_gps = pd.DataFrame({
        'Timestamp': df['Timestamp'],
        'Latitude': lats,
        'Longitude': longs
    })

    if not os.path.exists("data"):
        os.makedirs("data")

    output_path = "data/trajectoire_gps.csv"
    df_gps.to_csv(output_path, index=False)

    print(f"Conversion terminée avec succès ! ({len(df_gps)} points)")
    print(f"Fichier sauvegardé sous : '{output_path}'")