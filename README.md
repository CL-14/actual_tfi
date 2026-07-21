# Dublin Bus GTFS-Realtime Vehicle Tracker

A Python tool that fetches real-time public transit vehicle data from the
National Transport Authority of Ireland (NTA), calculates the distance between
each active vehicle and one or more chosen bus stops using the Haversine
formula, and logs vehicles found within a given radius to a local SQLite
database for historical tracking.

## Features

- Fetches live GTFS-realtime vehicle positions from the NTA's public API
- Looks up real stop coordinates from the NTA's static GTFS feed (`stops.txt`)
- Calculates great-circle distance between each vehicle and a stop
- Supports checking multiple stops per run, reusing a single API fetch
- Persists timestamped results to SQLite (`TFI.db`) for building history over time
- Handles common API failure instances (rate limits, auth errors, malformed responses) instead of crashing
- Runs continuously on a configurable interval

## Requirements

- Python 3.x
- An API key from the [NTA Developer Portal](https://developer.nationaltransport.ie/) for the GTFS-Realtime Vehicles endpoint
- The static GTFS feed for the relevant operator, downloaded from the same portal (used for stop lookups, this repo expects it under `GTFS_Realtime/` but you can always change it)

## Installation

1. Install dependencies:

```bash
   pip install requests protobuf
```

2. Create a `.env` file (or otherwise set an environment variable) containing your API key:

2. Download the static GTFS feed from the NTA portal and place its contents (`stops.txt`, `routes.txt`, etc.) inside a `GTFS_Realtime/` folder in the project root.

## Usage

Edit the `stop_ids` list near the bottom of the script to the stop codes you want to monitor (the human-readable numbers on physical bus stop signs, e.g. `8269`), then run:

```bash
python fetch.py <radius_km>
```

Example — check all configured stops for vehicles within 5 km:

```bash
python fetch.py 5
```

The script runs continuously, checking every 60 seconds, and stops with `Ctrl+C`. Results are printed to the console and saved to `TFI.db`.

## Database

Results are stored in a local SQLite database (`TFI.db`), in a `bus_data` table:

| column | description |
|---|---|
| `id` | auto-incrementing row ID |
| `checked_at` | timestamp of the check |
| `stop_id` | stop code checked |
| `vehicle_id` | ID of the nearby vehicle |
| `distance_km` | distance from the stop, in km |

Every check is stored as a new row rather than overwriting previous ones, so the data accumulates into a history over time rather than only reflecting the current moment.

## Known limitations / roadmap

- Stop list is currently hardcoded rather than configurable via CLI or file
- No web interface yet, it is planned though, using [web.py](http://webpy.org/)
- API usage is bound by the NTA's daily rate limit (~3000 requests/day)
