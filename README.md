# Dublin Bus GTFS-Realtime Vehicle Tracker

A Python tool that fetches real-time public transit vehicle data from the
National Transport Authority of Ireland (NTA), calculates the distance
between active vehicles and one or more chosen bus stops using the
Haversine formula, and makes the results available both as a persistent
history (SQLite) and through a small live web interface built with web.py.

## Features

- Fetches live GTFS-realtime vehicle positions from the NTA's public API
- Looks up real stop coordinates from the NTA's static GTFS feed (`stops.txt`)
- Calculates great-circle distance (Haversine) between each vehicle and a stop
- Supports checking multiple stops per run, reusing a single API fetch
- Persists timestamped results to SQLite (`TFI.db`) for building history over time
- Handles common API failure modes gracefully (rate limits, auth errors, malformed responses) instead of crashing
- Web interface (web.py) with a simple form, search any stop code and radius from the browser, no CLI required

## Project structure

- `bus_core.py` — shared, reusable logic
- `fetch.py` — command-line entry point. Runs continuously, checks configured stops on an interval, and persists results to SQLite.
- `hello.py` — web.py entry point. Serves a form for searching a stop/radius and displays live results in the browser.

## Requirements

- Python 3.x
- `pip install requests protobuf web.py`
- An API key from the [NTA Developer Portal](https://developer.nationaltransport.ie/) for the GTFS-Realtime Vehicles endpoint
- The static GTFS feed for the relevant operator, downloaded from the same portal, placed under `GTFS_Realtime/` in the project root

## Setup

1. Install dependencies:

```bash
   pip install requests protobuf web.py
```

2. Create a `.env` file (or otherwise set an environment variable) with your API key

3. Download the static GTFS feed and place its contents (`stops.txt`, `routes.txt`, etc.) inside `GTFS_Realtime/`.

## Usage

### Command-line / persistence mode

Edit the `stop_ids` list in `fetch.py` to the stop codes you want to monitor, then run:

```bash
python fetch.py <radius_km>
```

Runs continuously, checking every 60 seconds, saving results to `TFI.db`. Stop with `Ctrl+C`.

### Web interface

```bash
python hello.py
```

Then open `http://localhost:8080`, enter a stop code and radius, and submit.

## Database

Results from `fetch.py` are stored in `TFI.db`, table `bus_data`:

| column | description |
|---|---|
| `id` | auto-incrementing row ID |
| `checked_at` | timestamp of the check |
| `stop_id` | stop code checked |
| `vehicle_id` | ID of the nearby vehicle |
| `distance_km` | distance from the stop, in km |

Every check is stored as a new row rather than overwriting previous ones, building genuine history over time.

## Known limitations

- Stop list is hardcoded rather than user-configurable via the web interface yet
- Web output is currently plain text, not styled HTML
- API usage is bound by the NTA's daily rate limit (~3000 requests/day)
