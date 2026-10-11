# Cognifyz Machine Learning Internship — Task 4

## Location-Based Restaurant Analysis

Task 4 explores where restaurants are located, how they cluster by city and locality, and how ratings, cuisines, and price ranges vary across those areas. This task has its own analysis script and reports, separate from the other internship tasks.

## Project files

```text
src/analyze_locations.py                 Reproducible location analysis
reports/key_insights.json                Dataset-wide headline findings
reports/city_summary.csv                 Counts, ratings, prices, cuisines by city
reports/locality_summary.csv             Counts and attributes by city/locality
reports/cuisine_counts.csv               Frequency of listed cuisines
visualizations/coordinate_distribution.png  Coordinate scatter coloured by rating
visualizations/top_cities.png            Restaurants in the most represented cities
visualizations/top_localities.png        Restaurants in the most represented areas
visualizations/restaurant_locations.html Interactive restaurant density map
requirements.txt                         Python dependencies
```

## Technology

- Python 3.10 or newer
- pandas and NumPy for data preparation and aggregation
- Matplotlib and Seaborn for static visualizations
- Leaflet for the interactive coordinate density map (map assets and OpenStreetMap tiles load online)

## Dataset

The source dataset is the Cognifyz restaurant CSV supplied for the internship. To keep this repository focused on Task 4 and avoid redistributing a dataset without its license terms, place the supplied file at `data/Dataset.csv`. The script accepts a different path with `--data`.

Required fields are restaurant name, city, locality, longitude, latitude, cuisines, price range, and aggregate rating. Rows with missing or out-of-range coordinates are excluded from coordinate plots and the map; they remain in city and locality summaries. Missing city, locality, and cuisine values are grouped as `Unknown`.

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python src/analyze_locations.py --data data/Dataset.csv
```

The run writes fresh tables to `reports/`, plots and the interactive map to `visualizations/`, and prints a JSON summary. Set `--top` to choose how many cities and localities appear in the ranked charts (15 by default).

## Method and interpretation

Restaurant coordinates are checked against valid longitude and latitude ranges. The static coordinate plot colours valid locations by aggregate rating, while the HTML map aggregates coordinates to one decimal place and scales circles by restaurant count to show spatial density. City and city/locality groupings report restaurant count, average rating, median and mean price range, and distinct cuisine strings. Cuisine mentions are split on commas and counted once per restaurant row.

Average ratings omit unrated rows. City-level rating comparisons are more stable for places with enough restaurants, so the headline high-rating city is limited to cities with at least 30 records. Dataset coverage and location concentration describe this dataset only; they do not represent all restaurants in a city or prove that location causes rating or price differences. Price range is an ordinal field, not a currency amount.

## Task checklist

- [x] Inspect latitude/longitude and visualize restaurant distribution on a map.
- [x] Group restaurants by city and locality and compare concentration.
- [x] Summarize ratings, cuisine variety, and price range by city/locality.
- [x] Record location-related findings from the supplied dataset.

## Results from the supplied dataset

The reproducible run covered **9,551 restaurants across 141 cities** and 1,265 city/locality groups. All 9,551 rows had valid coordinates. **New Delhi** contained 5,473 restaurants (57.3% of the dataset), followed by Gurgaon (1,118) and Noida (1,080). Connaught Place in New Delhi was the largest locality group with 122 restaurants.

The overall average rating was **2.666**. Among cities with at least 30 restaurants, Gurgaon had the highest mean rating at **2.651** (1,118 restaurants); New Delhi averaged 2.439 and Noida 2.036. North Indian was the most frequently listed cuisine (3,960 restaurant mentions). Median price range was 1 in New Delhi, Noida, and Faridabad, and 2 in Gurgaon. The city's concentration reflects the dataset's coverage and should not be read as a complete census of those markets.

The exact metrics and full city/locality tables are saved in `reports/`; the charts and interactive map are saved in `visualizations/`.

