#!/bin/bash
# Fusion GPS + IMU par filtre de Kalman.
# Usage : ./kalman.sh <dossier_acquisition> <fichier_imu.csv> <fichier_gps.csv>
set -e

if [[ $# -ne 3 ]]; then
  echo "Usage : $0 <dossier_acquisition> <fichier_imu.csv> <fichier_gps.csv>" >&2
  exit 1
fi

DOSSIER_ACQUISITION="$1"
FICHIER_IMU="$2"
FICHIER_GPS="$3"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

IMU_PATH="$DOSSIER_ACQUISITION/$FICHIER_IMU"
GPS_PATH="$DOSSIER_ACQUISITION/$FICHIER_GPS"

RESULT_DIR="$DOSSIER_ACQUISITION/resultats_kalman"
mkdir -p "$RESULT_DIR"

echo "IMU : $IMU_PATH"
echo "GPS : $GPS_PATH"
echo "Dossier résultats : $RESULT_DIR"

LAT_INIT=$(python3 -c "import pandas as pd; df=pd.read_csv(r'$GPS_PATH'); print(df['Latitude'].iloc[0])")
LONG_INIT=$(python3 -c "import pandas as pd; df=pd.read_csv(r'$GPS_PATH'); print(df['Longitude'].iloc[0])")

python3 filtre_kalman.py "$IMU_PATH" "$GPS_PATH"

python3 cartesian_to_coord.py "data/traj_estimee.csv" --lat_init "$LAT_INIT" --long_init "$LONG_INIT"

cp "data/traj_estimee.csv" "$RESULT_DIR/traj_estimee.csv"
cp "data/trajectoire_gps.csv" "$RESULT_DIR/trajectoire_gps.csv"
cp "data/association_gps_imu.csv" "$RESULT_DIR/association_gps_imu.csv"

echo "Résultats Kalman enregistrés dans : $RESULT_DIR"
echo " - $RESULT_DIR/traj_estimee.csv"
echo " - $RESULT_DIR/trajectoire_gps.csv"
echo " - $RESULT_DIR/association_gps_imu.csv"