"""
Quick test to check what type DuckDB returns for timestamp queries.
"""
import os
import sys
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.persistence.duckdb.service import DuckDbPersistenceService


def main():
    test_db_path = "test_timestamp_check.duckdb"
    
    try:
        print("=== Testing DuckDB Timestamp Return Type ===\n")
        
        # Create service with test database
        db_service = DuckDbPersistenceService(db_path=test_db_path)
        
        # Create test dataframe with sample ticket
        test_df = pd.DataFrame({
            "Ref": ["TEST001", "TEST002"],
            "Service subcategory->Name": ["Test Category", "Test Category 2"],
            "Service->Name": ["Network", "Network"],
            "Request Type": ["Incident", "Request"],
            "Last team ID->Name": ["Team A", "Team B"],
            "Title_anon": ["Test title 1", "Test title 2"],
            "Description_anon": ["Test description 1", "Test description 2"],
            "Public_log_anon": ["Test log 1", "Test log 2"],
        })
        
        # Insert with timestamp
        print("Inserting test data with timestamp: '2026-01-24 10:30:45'")
        count = db_service.upsert_tickets_df(
            test_df, 
            split="train", 
            dataset_timestamp="2026-01-24 10:30:45"
        )
        print(f"Inserted {count} tickets\n")
        
        # Get the latest timestamp
        result = db_service.get_latest_dataset_timestamp()
        
        print("=== Results (with timestamp) ===")
        print(f"Returned value: {result}")
        print(f"Type: {type(result)}")
        print(f"Type name: {type(result).__name__}")
        print(f"Repr: {repr(result)}")
        
        if result:
            print(f"\nString conversion: {str(result)}")
            if hasattr(result, 'isoformat'):
                print(f"ISO format: {result.isoformat()}")
                print(f"strftime: {result.strftime('%Y%m%dT%H%M%S')}")
        
        # Test with NO timestamp
        print("\n=== Testing with NULL timestamp ===")
        test_df_no_timestamp = pd.DataFrame({
            "Ref": ["TEST003"],
            "Service subcategory->Name": ["No timestamp category"],
            "Service->Name": ["Network"],
            "Request Type": ["Incident"],
            "Last team ID->Name": ["Team C"],
            "Title_anon": ["No timestamp title"],
            "Description_anon": ["No timestamp desc"],
            "Public_log_anon": ["No timestamp log"],
        })
        
        print("Inserting test data with timestamp: None")
        count_no_ts = db_service.upsert_tickets_df(
            test_df_no_timestamp, 
            split="test", 
            dataset_timestamp=None
        )
        print(f"Inserted {count_no_ts} tickets\n")
        
        # This should still return the previous timestamp since MAX ignores NULLs
        result_after_null = db_service.get_latest_dataset_timestamp()
        print("=== Results (after adding NULL timestamp) ===")
        print(f"Returned value: {result_after_null}")
        print(f"Type: {type(result_after_null)}")
        print(f"Should still be the same as before: {result_after_null == result}")
        
        print("\n✓ Test completed successfully")
        
    finally:
        # Cleanup: remove test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print(f"\n🗑️  Cleaned up test database: {test_db_path}")


if __name__ == "__main__":
    main()
