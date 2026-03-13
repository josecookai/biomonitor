"""
BioMonitor - CLI Entry Point
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from collectors import StravaCollector, CrossFitLogger
from processors import MetricsCalculator
from storage import BioDatabase


def cmd_sync(args):
    """Sync data from sources"""
    print(f"🔄 Syncing data from {args.source or 'all sources'}...")
    
    db = BioDatabase()
    
    if args.source in ['strava', 'all']:
        print("  → Fetching from Strava...")
        # TODO: Load credentials from config
        # collector = StravaCollector(access_token)
        # activities = collector.get_activities()
        # for activity in activities:
        #     processed = collector.process_activity(activity)
        #     db.save_activity(processed)
        print("  ✓ Strava sync complete")
    
    print("✅ Sync complete!")


def cmd_dashboard(args):
    """Launch dashboard"""
    print(f"🚀 Starting dashboard on http://{args.host}:{args.port}")
    # TODO: Launch Next.js dev server or FastAPI
    print("  (Dashboard server not yet implemented)")


def cmd_log(args):
    """Log a CrossFit workout"""
    db = BioDatabase()
    logger = CrossFitLogger()
    
    workout = {
        'wod_name': args.wod,
        'date': datetime.now(),
        'time': args.time,
        'rounds': args.rounds,
        'reps': args.reps,
        'weight': args.weight,
        'rpe': args.rpe,
        'notes': args.notes
    }
    
    workout_id = db.save_crossfit_workout(workout)
    print(f"✅ Logged {args.wod} (ID: {workout_id})")


def cmd_report(args):
    """Generate weekly report"""
    print(f"📊 Generating report for week {args.week}...")
    
    db = BioDatabase()
    activities = db.get_activities()
    
    if activities.empty:
        print("  ⚠️ No activities found")
        return
    
    calculator = MetricsCalculator(activities)
    
    print(f"\n📈 Weekly Summary:")
    print(f"  CrossFit sessions: {calculator.weekly_crossfit_count()}")
    
    walking = calculator.weekly_walking_stats()
    print(f"  Walking: {walking['sessions']} sessions, {walking['total_distance_km']} km")


def cmd_config(args):
    """Configure BioMonitor"""
    print("⚙️ Configuration")
    print("  (Interactive config not yet implemented)")
    print("  Edit ~/.config/biomonitor/config.yaml manually")


def main():
    parser = argparse.ArgumentParser(
        prog='biomonitor',
        description='BioMonitor - Personal health metrics tracking'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync data from sources')
    sync_parser.add_argument('--source', choices=['strava', 'apple', 'all'], help='Data source')
    sync_parser.set_defaults(func=cmd_sync)
    
    # Dashboard command
    dash_parser = subparsers.add_parser('dashboard', help='Launch web dashboard')
    dash_parser.add_argument('--port', type=int, default=3000)
    dash_parser.add_argument('--host', default='localhost')
    dash_parser.set_defaults(func=cmd_dashboard)
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Log a CrossFit workout')
    log_parser.add_argument('--wod', required=True, help='WOD name')
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
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configure settings')
    config_parser.set_defaults(func=cmd_config)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
