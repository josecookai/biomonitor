# Strava Integration for BioMonitor

This guide explains how to connect your Strava data to the BioMonitor Railway deployment.

## Quick Setup

### Step 1: Get Strava API Credentials

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create an application if you haven't already
3. Note down:
   - **Client ID**
   - **Client Secret**

### Step 2: Generate Access Token

Run the token generator:

```bash
python get_strava_token.py
```

This will:
1. Open a browser for Strava authorization
2. Generate `access_token` and `refresh_token`
3. Save tokens to `strava_tokens.json`

### Step 3: Configure Railway Environment Variables

In your [Railway Dashboard](https://railway.app/dashboard), go to your project → **Variables** and add:

```
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_ACCESS_TOKEN=your_access_token
STRAVA_REFRESH_TOKEN=your_refresh_token
```

### Step 4: Deploy

Railway will automatically restart the service with the new environment variables.

---

## Usage

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strava/sync?days=30` | POST | Sync recent activities |
| `/api/strava/stats` | GET | Check connection status |
| `/api/activities` | GET | List all activities |
| `/api/stats/current-week` | GET | Current week stats |

### Manual Sync

```bash
# Trigger sync via API
curl -X POST "https://biomonitor-api-production.up.railway.app/api/strava/sync?days=30"

# Or use the Python script
python sync_strava_to_railway.py
```

### Automatic Sync (Recommended)

Set up a cron job to sync daily:

```bash
# Add to crontab (crontab -e)
0 6 * * * curl -X POST "https://biomonitor-api-production.up.railway.app/api/strava/sync?days=7"
```

---

## Data Flow

```
Strava API → BioMonitor API → SQLite Database → Web Dashboard
     ↑                                              ↓
     └───────── Token Refresh (auto) ←──────────────┘
```

### What Gets Synced

- **Activities**: Running, cycling, CrossFit, walking, etc.
- **Metrics**: Distance, duration, heart rate, calories
- **Auto-detection**: CrossFit workouts (based on name/HR patterns), walking

---

## Troubleshooting

### "Not connected" status
- Check environment variables are set correctly
- Verify tokens haven't expired (re-run `get_strava_token.py`)

### Sync fails
- Check logs: `railway logs`
- Ensure `STRAVA_ACCESS_TOKEN` is valid
- Token auto-refresh should handle expiration

### Missing activities
- Increase `days` parameter
- Check activity visibility on Strava (must be public or "Followers")

---

## Token Refresh

The system automatically refreshes expired access tokens using the refresh token. No manual action needed unless refresh token expires (rare - only happens if you revoke access in Strava settings).