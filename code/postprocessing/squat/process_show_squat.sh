#!/bin/bash
# Analyse d'une acquisition de squats : détection, normalisation, puis graphique.
# Usage : ./process_show_squat.sh <nom_du_dossier_dans_code/data>
set -e

if [[ $# -ne 1 ]]; then
  echo "Usage : $0 <dossier_acquisition>" >&2
  exit 1
fi

# On se place dans code/ pour que les imports (utils, ...) et les chemins data/ fonctionnent
CODE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$CODE_DIR"
export PYTHONPATH="$CODE_DIR${PYTHONPATH:+:$PYTHONPATH}"

python3 postprocessing/squat/analyse_squat.py "data/$1/timestamps_squat.csv"
python3 postprocessing/squat/process_squat.py "data/$1/timestamps_squat.csv" "data/$1/new_data.csv"
python3 postprocessing/plot/plot_squat.py "data/$1/timestamps_squat.csv"
