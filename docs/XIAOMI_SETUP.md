# Xiaomi Mi Band Setup Guide for Zelda

This guide covers two methods to get your Mi Band data into BioMonitor.
Method A (Gadgetbridge) is recommended because it is free, open-source, and
supports real-time syncing. Method B (Mi Fitness CSV) is a simpler one-time
import path.

---

## Data Flow

```
Method A — Gadgetbridge (real-time + historical)
------------------------------------------------
Mi Band  <--BLE-->  Gadgetbridge (Android)
                          |
                    HTTP server plugin
                          |
                  POST /api/xiaomi/webhook      (real-time, every 5 min)
                          |
                    BioMonitor API
                          |
                    SQLite health_metrics
                          |
                    Dashboard charts


Method B — Mi Fitness CSV (historical only)
-------------------------------------------
Mi Band  <--BLE-->  Mi Fitness (Android/iOS)
                          |
                    Export data  (CSV file)
                          |
               POST /api/xiaomi/upload          (one-time or periodic)
                          |
                    BioMonitor API
                          |
                    SQLite health_metrics
```

---

## Method A: Gadgetbridge (Recommended)

### Step 1: Install Gadgetbridge on Android

<!-- SCREENSHOT: Gadgetbridge on F-Droid -->

Download Gadgetbridge from **F-Droid** (preferred — unmodified open-source build):

```
https://f-droid.org/packages/nodomain.freeyourgadget.gadgetbridge/
```

Or search "Gadgetbridge" on the Google Play Store (community-maintained build).

> Gadgetbridge is free and open source. It does NOT require a Xiaomi account
> or any cloud service.

### Step 2: Pair your Mi Band in Gadgetbridge

<!-- SCREENSHOT: Gadgetbridge device pairing screen -->

1. Open Gadgetbridge.
2. Tap the **+** button (bottom right).
3. Tap **Scan** — your Mi Band should appear as "Mi Band X" or "Xiaomi Smart Band".
4. Tap the device name, then **Pair**.
5. Confirm pairing on the band itself (tap/press when prompted).
6. You should see the band listed with a green connection indicator.

> If the band does not appear, make sure Bluetooth is on and that Mi Fitness /
> Zepp is **not** running in the background (two apps cannot hold a BLE
> connection simultaneously).

### Step 3: Enable the HTTP Server Plugin

<!-- SCREENSHOT: Gadgetbridge settings -> HTTP server -->

1. In Gadgetbridge, open the **hamburger menu** (top-left) -> **Settings**.
2. Scroll to **HTTP server** (or search for it).
3. Toggle **Enable HTTP server** ON.
4. Set **Server URL** to:

   ```
   http://YOUR_SERVER_IP:8000/api/xiaomi/webhook
   ```

   Replace `YOUR_SERVER_IP` with the local IP of the machine running
   BioMonitor (e.g. `192.168.1.42`).

5. Set **Sync interval** to `5` minutes (or shorter for more real-time data).
6. (Optional) If you have `BIOMONITOR_API_KEY` set, add a header:
   - Header name: `X-API-Key`
   - Header value: your key

> The HTTP server plugin sends a JSON payload each time the band syncs.
> BioMonitor receives it at `POST /api/xiaomi/webhook` and stores it in the
> database immediately.

### Step 4: Export Historical Data

<!-- SCREENSHOT: Gadgetbridge -> long-press device -> Export data -->

To import past data that predates the webhook setup:

1. In Gadgetbridge, **long-press** your device entry.
2. Tap **Export data** -> choose **JSON** format.
3. Transfer the `.json` file to the BioMonitor server (e.g. via `scp` or a
   file-sharing app).
4. Upload via the API:

```bash
# Upload a Gadgetbridge JSON export
curl -X POST http://localhost:8000/api/xiaomi/upload \
  -H "Content-Type: application/json" \
  -d '{
    "format": "gadgetbridge",
    "data": '"$(cat /path/to/gadgetbridge_export.json)"'
  }'
```

---

## Method B: Mi Fitness App CSV Export

### Step 1: Export from Mi Fitness

1. Open **Mi Fitness** (or Zepp) on your phone.
2. Tap your profile picture -> **Settings** -> **Personal info** -> **Export data**.
3. Tap **Export** and wait for the file to be generated.
4. Share / transfer the CSV file to your computer or server.

### Step 2: Upload the CSV

```bash
# Convert CSV to the JSON upload format (simple helper script)
python3 - <<'EOF'
import csv, json, sys

filepath = "mi_fitness_export.csv"
records = []
with open(filepath, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        records.append(row)

print(json.dumps({"format": "mi_fitness", "data": records}))
EOF > /tmp/mi_upload.json

curl -X POST http://localhost:8000/api/xiaomi/upload \
  -H "Content-Type: application/json" \
  -d @/tmp/mi_upload.json
```

Expected CSV columns (Mi Fitness export):

| Column         | Description                          | Unit    |
|----------------|--------------------------------------|---------|
| date           | Date of the record (YYYY-MM-DD)      |         |
| steps          | Total steps for the day              | count   |
| distance       | Distance walked                      | metres  |
| calories       | Active calories burned               | kcal    |
| heart_rate     | Average heart rate                   | bpm     |
| sleep_start    | Sleep start time (ISO 8601)          |         |
| sleep_end      | Sleep end time (ISO 8601)            |         |
| sleep_duration | Total sleep duration                 | minutes |

---

## API Reference

### Upload export file

```
POST /api/xiaomi/upload
Content-Type: application/json

{
  "format": "gadgetbridge",   // or "mi_fitness"
  "data": [ ... ]             // array of record objects
}
```

Response:

```json
{
  "success": true,
  "format": "gadgetbridge",
  "records_saved": 720,
  "breakdown": {
    "heart_rate": 480,
    "steps": 180,
    "sleep": 30,
    "calories": 30
  }
}
```

### Gadgetbridge real-time webhook

```
POST /api/xiaomi/webhook
Content-Type: application/json

{
  "timestamp": 1710000000,
  "heart_rate": 72,
  "steps": 8432,
  "battery": 85,
  "activity": "walking"
}
```

Response:

```json
{
  "success": true,
  "records_saved": 2,
  "battery": 85
}
```

### Query stored metrics

```
GET /api/xiaomi/stats?days=7
```

Response includes arrays for `StepCount`, `HeartRate`, `SleepAnalysis`, and
`ActiveEnergyBurned` for the requested window.

---

## Metrics Collected

| Metric            | DB type             | Unit       | Source(s)                  |
|-------------------|---------------------|------------|----------------------------|
| Step count        | StepCount           | count      | Both methods               |
| Heart rate        | HeartRate           | bpm        | Both methods               |
| Sleep duration    | SleepAnalysis       | minutes    | Both methods               |
| Active calories   | ActiveEnergyBurned  | kcal       | Both methods               |
| Battery level     | (webhook only)      | %          | Gadgetbridge webhook       |

---

## Troubleshooting

### Band not syncing to Gadgetbridge

- Ensure Mi Fitness / Zepp is **force-stopped** — two BLE connections cannot
  coexist.
- Toggle Bluetooth off and on, then reopen Gadgetbridge.
- Try "Reconnect" by long-pressing the device entry.

### Webhook not reaching BioMonitor

- Verify your phone and server are on the **same Wi-Fi network**.
- Check the server IP in the Gadgetbridge HTTP server settings.
- Test connectivity: `curl http://YOUR_SERVER_IP:8000/api/health`
- If `BIOMONITOR_API_KEY` is set, make sure the `X-API-Key` header is
  configured in Gadgetbridge.

### Wrong data format on upload

- Gadgetbridge exports can be SQLite (`.db`) or JSON. The collector
  auto-detects by file extension — rename to `.json` or `.db` as appropriate.
- Mi Fitness CSV must use UTF-8 or UTF-8-BOM encoding. Open in a text editor
  to verify the first line contains the expected column headers.
- Use `GET /api/apple-health/formats` for reference on how metric type strings
  map to HealthKit identifiers (the Xiaomi types follow the same conventions).

### Steps are zero / missing

- Gadgetbridge aggregates steps per minute in the `MI_BAND_ACTIVITY_SAMPLE`
  table. Rows with `STEPS = 0` are normal (resting periods) and are filtered
  out automatically.
- In the JSON export format, ensure the `steps` field is present and numeric.

### Duplicate records

- `db.save_health_metric()` uses upsert logic on `(date, metric_type, source)`.
  Re-uploading the same export file is safe — it will not create duplicates.
