"""Explore restaurant locations and city/locality patterns.

Run from the repository root:
    python src/analyze_locations.py --data data/Dataset.csv

The script writes tabular summaries, static plots, and an interactive map under
reports/ and visualizations/. Rows with missing or invalid coordinates remain
available to the city and locality analysis but are excluded from the map.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


REQUIRED_COLUMNS = {
    "Restaurant Name", "City", "Locality", "Longitude", "Latitude",
    "Cuisines", "Price range", "Aggregate rating",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/Dataset.csv"))
    parser.add_argument("--top", type=int, default=15, help="Number of areas in summary charts")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top < 1:
        raise SystemExit("--top must be at least 1")
    root = Path.cwd()
    reports = root / "reports"
    visuals = root / "visualizations"
    reports.mkdir(parents=True, exist_ok=True)
    visuals.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(args.data, encoding="utf-8-sig", low_memory=False)
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise SystemExit(f"Dataset is missing required columns: {', '.join(missing)}")

    for column in ("Longitude", "Latitude", "Price range", "Aggregate rating"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    # A zero aggregate rating is the dataset's "Not rated" sentinel.
    data["rating_for_analysis"] = data["Aggregate rating"].where(data["Aggregate rating"] > 0)
    for column in ("City", "Locality", "Cuisines"):
        data[column] = data[column].fillna("Unknown").astype(str).str.strip()
        data.loc[data[column].eq(""), column] = "Unknown"

    valid_coords = (
        data["Longitude"].between(-180, 180)
        & data["Latitude"].between(-90, 90)
        & data["Longitude"].notna()
        & data["Latitude"].notna()
    )
    geo = data.loc[valid_coords].copy()

    city = data.groupby("City", dropna=False).agg(
        restaurant_count=("Restaurant Name", "size"),
        average_rating=("rating_for_analysis", "mean"),
        median_price_range=("Price range", "median"),
        average_price_range=("Price range", "mean"),
        unique_cuisines=("Cuisines", "nunique"),
    ).sort_values("restaurant_count", ascending=False)
    city["top_cuisine"] = data.groupby("City")["Cuisines"].agg(
        lambda values: values.str.split(r"\s*,\s*").explode().replace("", np.nan).dropna().value_counts().index[0]
        if values.str.split(r"\s*,\s*").explode().replace("", np.nan).dropna().size else "Unknown"
    )
    city.to_csv(reports / "city_summary.csv", float_format="%.3f")

    locality = data.groupby(["City", "Locality"], dropna=False).agg(
        restaurant_count=("Restaurant Name", "size"),
        average_rating=("rating_for_analysis", "mean"),
        median_price_range=("Price range", "median"),
        unique_cuisines=("Cuisines", "nunique"),
    ).sort_values("restaurant_count", ascending=False)
    locality.to_csv(reports / "locality_summary.csv", float_format="%.3f")

    cuisine_counts = (
        data.assign(Cuisine=data["Cuisines"].str.split(r"\s*,\s*"))
        .explode("Cuisine").query("Cuisine != 'Unknown'")
        .groupby("Cuisine").size().sort_values(ascending=False)
    )
    cuisine_counts.rename("restaurant_mentions").to_csv(reports / "cuisine_counts.csv")

    top_cities = city.head(args.top).sort_values("restaurant_count")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, max(5, len(top_cities) * 0.34)))
    sns.barplot(data=top_cities.reset_index(), x="restaurant_count", y="City", color="#2878B5", ax=ax)
    ax.set(title=f"Top {len(top_cities)} cities by restaurant count", xlabel="Restaurants", ylabel="")
    fig.tight_layout()
    fig.savefig(visuals / "top_cities.png", dpi=180)
    plt.close(fig)

    top_areas = locality.head(args.top).reset_index().sort_values("restaurant_count")
    fig, ax = plt.subplots(figsize=(11, max(5, len(top_areas) * 0.36)))
    labels = top_areas["Locality"] + " — " + top_areas["City"]
    sns.barplot(x=top_areas["restaurant_count"], y=labels, color="#36A17B", ax=ax)
    ax.set(title=f"Top {len(top_areas)} city/locality clusters", xlabel="Restaurants", ylabel="")
    fig.tight_layout()
    fig.savefig(visuals / "top_localities.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 7))
    rated_geo = geo.loc[geo["rating_for_analysis"].notna()]
    sample = rated_geo.sample(min(len(rated_geo), 12000), random_state=42) if len(rated_geo) else rated_geo
    points = ax.scatter(sample["Longitude"], sample["Latitude"], c=sample["Aggregate rating"],
                        cmap="viridis", s=10, alpha=0.55, linewidths=0)
    fig.colorbar(points, ax=ax, label="Aggregate rating")
    ax.set(title="Restaurant coordinate distribution", xlabel="Longitude", ylabel="Latitude")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(visuals / "coordinate_distribution.png", dpi=180)
    plt.close(fig)

    if len(geo):
        center = [float(geo["Latitude"].median()), float(geo["Longitude"].median())]
        map_data = geo.assign(
            lat=geo["Latitude"].round(1), lon=geo["Longitude"].round(1)
        ).groupby(["lat", "lon"], as_index=False).agg(
            restaurants=("Restaurant Name", "size"), average_rating=("rating_for_analysis", "mean"),
            city=("City", lambda values: values.mode().iat[0]),
        )
        points_json = map_data.to_json(orient="records", double_precision=2)
        map_html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Restaurant locations</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>html,body,#map{height:100%;margin:0} .note{position:absolute;z-index:1000;top:10px;left:50px;background:white;padding:8px 12px;border-radius:4px;font:14px Arial;box-shadow:0 1px 5px #777}</style></head>
<body><div id="map"></div><div class="note">Restaurant density by rounded coordinate cell — larger circles indicate more restaurants</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>const points=__POINTS__;const map=L.map('map').setView(__CENTER__,2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
points.forEach(p=>{const radius=Math.min(18,5+Math.sqrt(p.restaurants)*2);const marker=L.circleMarker([p.lat,p.lon],{radius,fillColor:'#2878B5',color:'#fff',weight:1,fillOpacity:.72});
marker.bindPopup('<b>'+String(p.city).replace(/[&<>]/g,'')+'</b><br>Restaurants in coordinate cell: '+p.restaurants+'<br>Average rating: '+(p.average_rating??'Not rated'));marker.addTo(map)});</script></body></html>""".replace(
            "__POINTS__", points_json
        ).replace("__CENTER__", json.dumps(center))
        (visuals / "restaurant_locations.html").write_text(map_html, encoding="utf-8")

    top_city_name = str(city.index[0]) if len(city) else None
    top_locality = locality.iloc[0] if len(locality) else None
    insights = {
        "dataset_rows": int(len(data)),
        "cities": int(data["City"].nunique()),
        "city_locality_groups": int(len(locality)),
        "valid_coordinate_rows": int(valid_coords.sum()),
        "invalid_or_missing_coordinate_rows": int((~valid_coords).sum()),
        "coordinate_coverage_percent": round(float(valid_coords.mean() * 100), 2),
        "overall_average_rating": round(float(data["Aggregate rating"].mean()), 3),
        "average_rating_among_rated_restaurants": round(float(data["rating_for_analysis"].mean()), 3),
        "not_rated_restaurants": int(data["rating_for_analysis"].isna().sum()),
        "most_represented_city": top_city_name,
        "most_represented_city_restaurants": int(city.iloc[0]["restaurant_count"]) if len(city) else 0,
        "most_represented_locality": {
            "city": str(top_locality.name[0]), "locality": str(top_locality.name[1]),
            "restaurants": int(top_locality["restaurant_count"]),
        } if top_locality is not None else None,
        "most_common_cuisine": str(cuisine_counts.index[0]) if len(cuisine_counts) else None,
        "most_common_cuisine_mentions": int(cuisine_counts.iloc[0]) if len(cuisine_counts) else 0,
        "city_with_highest_average_rating_min_30_restaurants": (
            str(city.loc[city["restaurant_count"] >= 30, "average_rating"].idxmax())
            if (city["restaurant_count"] >= 30).any() else None
        ),
        "note": "Zero aggregate ratings are treated as unrated and excluded from rating averages. Cuisine counts count each listed cuisine once per restaurant row.",
    }
    (reports / "key_insights.json").write_text(json.dumps(insights, indent=2), encoding="utf-8")
    print(json.dumps(insights, indent=2))


if __name__ == "__main__":
    main()

