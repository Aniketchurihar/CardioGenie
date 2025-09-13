#!/usr/bin/env python3
"""
CardioGenie Database Cleanup Script
Use this script to clean up and reinitialize the database for fresh start
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from database.models import DatabaseManager
from backend.config import Config

def cleanup_database(reinitialize=True):
    """Clean up database and optionally reinitialize"""
    
    print("🧹 CardioGenie Database Cleanup Script")
    print("=" * 50)
    
    # Initialize database manager
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    
    # Get current stats before cleanup
    try:
        stats = db_manager.get_database_stats()
        print(f"📊 Current Database Stats:")
        print(f"   • Symptoms: {stats['symptoms']}")
        print(f"   • Patients: {stats['patients']}")
        print(f"   • Completed Consultations: {stats['completed_consultations']}")
        print()
    except Exception as e:
        print(f"⚠️  Could not get current stats: {e}")
    
    # Confirm cleanup
    if not args.force:
        confirm = input("⚠️  This will delete ALL patient data and symptom rules. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Cleanup cancelled")
            return False
    
    try:
        # Clean up database
        print("🗑️  Cleaning up database...")
        db_manager.cleanup_database()
        
        if reinitialize:
            print("🔄 Reinitializing database with medical dataset...")
            db_manager.initialize_database(Config.MEDICAL_DATASET_PATH)
            
            # Get new stats
            new_stats = db_manager.get_database_stats()
            print(f"✅ Database reinitialized successfully!")
            print(f"📊 New Database Stats:")
            print(f"   • Symptoms: {new_stats['symptoms']}")
            print(f"   • Patients: {new_stats['patients']}")
            print(f"   • Completed Consultations: {new_stats['completed_consultations']}")
        else:
            print("✅ Database cleaned up successfully!")
            print("ℹ️  Database is now empty. Run with --reinitialize to load medical dataset.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

def main():
    """Main function"""
    global args
    
    parser = argparse.ArgumentParser(description='CardioGenie Database Cleanup Script')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Force cleanup without confirmation')
    parser.add_argument('--no-reinit', action='store_true',
                       help='Clean up without reinitializing (empty database)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Show database statistics only')
    
    args = parser.parse_args()
    
    # Show stats only
    if args.stats_only:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        try:
            stats = db_manager.get_database_stats()
            print("📊 CardioGenie Database Statistics")
            print("=" * 40)
            print(f"Symptoms: {stats['symptoms']}")
            print(f"Patients: {stats['patients']}")
            print(f"Completed Consultations: {stats['completed_consultations']}")
            print(f"Database Path: {Config.DATABASE_PATH}")
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
        return
    
    # Perform cleanup
    reinitialize = not args.no_reinit
    success = cleanup_database(reinitialize)
    
    if success:
        print("\n🎉 Database cleanup completed successfully!")
        print("💡 You can now restart the CardioGenie application.")
    else:
        print("\n❌ Database cleanup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 