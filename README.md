
# Dublin Bus GTFS-Realtime Vehicle Tracker

A Python script that fetches real-time public transit vehicle data from the National Transport Authority of Ireland (TFI), calculates the distance between each active vehicle and a specified coordinate using the Haversine formula, and filters for vehicles within a 5 km radius.

## Installation

1. **Required dependency** using pip:

   ```bash
   pip install requests protobuf
