from utils import CSVHandler
from datetime import datetime, timedelta
import argparse
import numpy as np
from math import radians, sin, cos, sqrt, atan2
import folium

def utc_to_timestamp(ts_str):
    dt = datetime.strptime(ts_str.strip(), "%Y/%m/%d - %H:%M:%S")
    dt = dt + timedelta(hours=2)
    return dt.timestamp()

def load_strava(rows):
    return [
        {
            "t": utc_to_timestamp(r["UTC"]),
            "lat": float(r["Latitude"]),
            "lon": float(r["Longitude"])
        }
        for r in rows
    ]

def load_modele(rows):
    return [
        {
            "t": float(r["Timestamp"]),
            "lat": float(r["Latitude"]),
            "lon": float(r["Longitude"])
        }
        for r in rows
    ]

def match_by_timestamp(strava, modele):
    pairs = []
    used_modele = set()

    for s in strava:
        ts_s = s["t"]

        closest = None
        best_dist = float("inf")

        for m in modele:
            dt = abs(ts_s - m["t"])
            if dt < best_dist:
                best_dist = dt
                closest = m

        if closest is None:
            continue

        if closest["t"] in used_modele:
            continue

        used_modele.add(closest["t"])

        pairs.append((s, closest))

    return pairs

def distance_gps(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def compute_score(pairs):
    distances = []
    for s, m in pairs:
        distances.append(
            distance_gps(
                s["lat"], s["lon"],
                m["lat"], m["lon"]
            )
        )

    distances = np.array(distances)
    print("Nb pairs :", len(distances))
    print("Médiane :", np.median(distances))
    print("Moyenne :", np.mean(distances))
    return distances

def creer_carte(pairs, strava_points, modele_points):
    lat_center = np.mean([p["lat"] for p in strava_points])
    lon_center = np.mean([p["lon"] for p in strava_points])

    m = folium.Map(location=[lat_center, lon_center], zoom_start=18)

    strava_coords = [(p["lat"], p["lon"]) for p in strava_points]
    modele_coords = [(p["lat"], p["lon"]) for p in modele_points]

    folium.PolyLine(
        strava_coords,
        color="blue",
        weight=4,
        opacity=0.8,
        popup="Strava"
    ).add_to(m)

    folium.PolyLine(
        modele_coords,
        color="red",
        weight=4,
        opacity=0.8,
        popup="Modele"
    ).add_to(m)

    for s, mpt in pairs[::5]:
        folium.PolyLine(
            [(s["lat"], s["lon"]), (mpt["lat"], mpt["lon"])],
            color="gray",
            weight=1,
            opacity=0.5
        ).add_to(m)

        folium.CircleMarker(
            location=(s["lat"], s["lon"]),
            radius=2,
            color="blue",
            fill=True
        ).add_to(m)

    m.save("comparison_gps.html")
    print("Carte générée : comparison_gps.html")

def main(strava_csv, modele_csv):
    rowsS = CSVHandler(strava_csv).read_dict_rows()
    rowsM = CSVHandler(modele_csv).read_dict_rows()

    strava = load_strava(rowsS)
    modele = load_modele(rowsM)

    pairs = match_by_timestamp(strava, modele)

    compute_score(pairs)
    creer_carte(pairs, strava, modele)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("strava_csv")
    parser.add_argument("modele_csv")
    args = parser.parse_args()

    main(args.strava_csv, args.modele_csv)