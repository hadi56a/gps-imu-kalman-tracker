#!/bin/bash
# Cartes interactives de la trace GPS avant et après le filtre de Kalman.
# Usage : ./plot_gnss.sh <dossier_acquisition>   (à lancer après kalman.sh)
set -e

if [[ $# -ne 1 ]]; then
  echo "Usage : $0 <dossier_acquisition>" >&2
  exit 1
fi

DOSSIER_ACQUISITION="$1"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

GPS_AVANT="$DOSSIER_ACQUISITION/timestamps_coords.csv"
GPS_APRES="$DOSSIER_ACQUISITION/resultats_kalman/trajectoire_gps.csv"
RESULT_DIR="$DOSSIER_ACQUISITION/cartes_gnss"

mkdir -p "$RESULT_DIR"

echo "GPS avant Kalman : $GPS_AVANT"
python3 plot/plot_gnss.py "$GPS_AVANT"

echo "GPS après Kalman : $GPS_APRES"
python3 plot/plot_gnss.py "$GPS_APRES"

mv "${GPS_AVANT%.csv}.html" "$RESULT_DIR/carte_avant_kalman.html"
mv "${GPS_APRES%.csv}.html" "$RESULT_DIR/carte_apres_kalman.html"

echo ""
echo "Cartes enregistrées dans : $RESULT_DIR"