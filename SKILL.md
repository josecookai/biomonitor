name: biomonitor
description: "Personal health metrics tracking for CrossFit, walking, and Apple Watch data. Generate dashboards and shareable reports."
homepage: https://github.com/josecookai/biomonitor
version: 0.1.0
author: josecookai

metadata:
  emoji: 🏋️
  category: health
  tags: [fitness, crossfit, strava, apple-watch, dashboard]
  
  requires:
    bins:
      - python3
      - pip3
      - node
      - npm
    
  install:
    - id: pip-install
      kind: pip
      packages:
        - requests
        - pandas
        - sqlalchemy
        - fastapi
        - uvicorn
        - python-dateutil
        - pillow
        - playwright
      label: "Install Python dependencies"
    
    - id: npm-install
      kind: npm
      packages:
        - next
        - react
        - recharts
        - tailwindcss
      working-dir: "./dashboard/web"
      label: "Install dashboard dependencies"

config:
  strava:
    client_id: ""
    client_secret: ""
    access_token: ""
    refresh_token: ""
  
  apple_health:
    export_path: "~/HealthExport"
    auto_sync: true
    sync_interval_hours: 6
  
  crossfit:
    default_box: ""
    weekly_goal: 3
  
  dashboard:
    port: 3000
    host: "localhost"
    theme: "dark"
  
  sharing:
    default_template: "weekly_summary"
    watermark: true

commands:
  sync:
    description: "Sync data from all sources"
    usage: biomonitor sync [--source strava|apple|all]
  
  dashboard:
    description: "Launch web dashboard"
    usage: biomonitor dashboard [--port 3000]
  
  log:
    description: "Log a CrossFit workout"
    usage: biomonitor log --wod "Fran" --time "4:52" --rpe 8
  
  report:
    description: "Generate weekly report"
    usage: biomonitor report [--week 2026-W10] [--format png|pdf]
  
  share:
    description: "Generate shareable screenshot"
    usage: biomonitor share --type weekly --output ./share.png

examples:
  - biomonitor sync
  - biomonitor log --wod "Grace" --time "3:15" --notes "PR!"
  - biomonitor dashboard
  - biomonitor report --week 2026-W11 --format png
