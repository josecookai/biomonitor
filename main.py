#!/usr/bin/env python3
"""
BioMonitor CLI
Command line interface for BioMonitor
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from collectors import StravaCollector, CrossFitLogger, load_config
from processors import MetricsCalculator
from storage import BioDatabase


def cmd_sync(args):
    """Sync data from sources"""
    print(f"🔄 Syncing data from {args.source or 'all sources'}...")
    
    db = BioDatabase()
    
    if args.source in ['strava', 'all']:
        print("  → Fetching from Strava...")
        collector = StravaCollector()
        
        if not collector.access_token:
            print("  ❌ Strava not configured. Please check config.yaml")
            return
        
        try:
            count = collector.sync_to_database(db, days=args.days)
            print(f"  ✓ Synced {count} activities from Strava")
        except Exception as e:
            print(f"  ❌ Strava sync failed: {e}")
    
    if args.source in ['apple', 'all']:
        print("  → Checking Apple Health exports...")
        # TODO: Process Health Auto Export files
        print("  ℹ️ Apple Health data is received via webhook")
    
    print("\n✅ Sync complete!")
    
    # Show stats
    stats = db.get_activities()
    if not stats.empty:
        print(f"\n📊 Total activities in database: {len(stats)}")


def cmd_dashboard(args):
    """Launch dashboard"""
    print(f"🚀 Starting dashboard...")
    print(f"  API: http://localhost:8000")
    print(f"  Dashboard: http://localhost:3000")
    print()
    print("  Run these commands in separate terminals:")
    print("  1. python api_server.py")
    print("  2. cd dashboard/web && npm run dev")


def cmd_log(args):
    """Log a CrossFit workout"""
    db = BioDatabase()
    
    workout = {
        'wod_name': args.wod,
        'date': datetime.now().isoformat() if not args.date else f"{args.date}T00:00:00",
        'time': args.time,
        'rounds': args.rounds,
        'reps': args.reps,
        'weight': args.weight,
        'rpe': args.rpe,
        'notes': args.notes
    }
    
    workout_id = db.save_crossfit_workout(workout)
    print(f"✅ Logged {args.wod} (ID: {workout_id})")
    
    if args.time:
        print(f"   Time: {args.time}")
    if args.rpe:
        print(f"   RPE: {args.rpe}/10")


def cmd_report(args):
    """Generate weekly report"""
    print(f"📊 Generating report...")
    
    db = BioDatabase()
    activities = db.get_activities()
    
    if activities.empty:
        print("  ⚠️ No activities found. Run 'biomonitor sync' first.")
        return
    
    calculator = MetricsCalculator(activities)
    
    print(f"\n📈 Weekly Summary:")
    print(f"  CrossFit sessions: {calculator.weekly_crossfit_count()}")
    
    walking = calculator.weekly_walking_stats()
    print(f"  Walking: {walking['sessions']} sessions, {walking['total_distance_km']} km")


def cmd_strava(args):
    """Strava management commands"""
    if args.action == 'status':
        config = load_config()
        strava_config = config.get('strava', {})
        
        print("🔗 Strava Configuration:")
        print(f"  Client ID: {strava_config.get('client_id', 'Not set')}")
        print(f"  Access Token: {'✓ Configured' if strava_config.get('access_token') else '✗ Not set'}")
        print(f"  Refresh Token: {'✓ Configured' if strava_config.get('refresh_token') else '✗ Not set'}")
    
    elif args.action == 'sync':
        cmd_sync(argparse.Namespace(source='strava', days=args.days))


def cmd_config(args):
    """Show configuration"""
    config = load_config()
    
    print("⚙️ BioMonitor Configuration:")
    print()
    
    if 'strava' in config:
        print("Strava:")
        print(f"  Client ID: {config['strava'].get('client_id', 'Not set')}")
        print(f"  Connected: {'✓' if config['strava'].get('access_token') else '✗'}")
    
    if 'apple_health' in config:
        print("\nApple Health:")
        print(f"  Webhook: {'✓ Enabled' if config['apple_health'].get('webhook_enabled') else '✗'}")
    
    print(f"\nConfig file: {Path(__file__).parent / 'config.yaml'}")


def main():
    parser = argparse.ArgumentParser(
        prog='biomonitor',
        description='BioMonitor - Personal health metrics tracking'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync data from sources')
    sync_parser.add_argument('--source', choices=['strava', 'apple', 'all'], default='all', help='Data source')
    sync_parser.add_argument('--days', type=int, default=30, help='Number of days to sync')
    sync_parser.set_defaults(func=cmd_sync)
    
    # Dashboard command
    dash_parser = subparsers.add_parser('dashboard', help='Launch web dashboard')
    dash_parser.add_argument('--port', type=int, default=3000)
    dash_parser.add_argument('--host', default='localhost')
    dash_parser.set_defaults(func=cmd_dashboard)
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Log a CrossFit workout')
    log_parser.add_argument('--wod', required=True, help='WOD name')
    log_parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    log_parser.add_argument('--time', help='Completion time')
    log_parser.add_argument('--rounds', type=int, help='Number of rounds')
    log_parser.add_argument('--reps', type=int, help='Total reps')
    log_parser.add_argument('--weight', type=float, help='Weight used (kg)')
    log_parser.add_argument('--rpe', type=int, choices=range(1, 11), help='RPE score (1-10)')
    log_parser.add_argument('--notes', help='Additional notes')
    log_parser.set_defaults(func=cmd_log)
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate weekly report')
    report_parser.add_argument('--week', help='Week identifier (e.g., 2026-W10)')
    report_parser.add_argument('--format', choices=['text', 'png', 'pdf'], default='text')
    report_parser.set_defaults(func=cmd_report)
    
    # Strava command
    strava_parser = subparsers.add_parser('strava', help='Strava management')
    strava_parser.add_argument('action', choices=['status', 'sync'], help='Action')
    strava_parser.add_argument('--days', type=int, default=30, help='Days to sync')
    strava_parser.set_defaults(func=cmd_strava)
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show configuration')
    config_parser.set_defaults(func=cmd_config)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
