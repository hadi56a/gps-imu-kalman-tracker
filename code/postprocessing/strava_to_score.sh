#!/usr/bin/env bash
# Compare une trace Strava (.gpx) à l'acquisition GPS du boîtier et calcule un score.
# Usage : ./strava_to_score.sh <dossier_contenant_le_gpx_et_timestamps_coords.csv>
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage : $0 <dossier>" >&2
  exit 1
fi

dir="$(cd "$1" 2>/dev/null && pwd)" || { echo "Dossier introuvable : $1" >&2; exit 1; }

# On se place dans code/ pour que les imports (utils, ...) fonctionnent
CODE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CODE_DIR"
export PYTHONPATH="$CODE_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "Traitement du dossier : $dir"
python3 postprocessing/conversion_gpx.py "$dir"/*.gpx "$dir/donnees_strava.csv"
python3 postprocessing/score.py "$dir/donnees_strava.csv" "$dir/timestamps_coords.csv"
mkdir -p "$dir/cartes"
mv comparison_gps.html "$dir/cartes/comparison_gps.html"
echo "Carte enregistrée dans : $dir/cartes/comparison_gps.html"
