#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from utils.csv_data_loader import is_csv_mode_available, load_managers_from_csv, load_stores_from_csv

def test_csv_loader():
    print("Testing CSV data loader...")
    
    csv_available = is_csv_mode_available()
    print(f"CSV mode available: {csv_available}")
    
    if csv_available:
        managers = load_managers_from_csv()
        print(f"Managers loaded: {len(managers)} rows")
        if not managers.empty:
            print(f"Manager columns: {list(managers.columns)}")
            print(f"Sample manager data:")
            print(managers.head(2))
        
        stores = load_stores_from_csv()
        print(f"Stores generated: {len(stores)} rows")
        if not stores.empty:
            print(f"Store columns: {list(stores.columns)}")
            print(f"Sample store data:")
            print(stores.head(2))
    else:
        print("CSV file not found - checking path...")
        csv_path = os.path.join(os.path.dirname(__file__), "CS Data.csv")
        print(f"Looking for CSV at: {csv_path}")
        print(f"File exists: {os.path.exists(csv_path)}")

if __name__ == "__main__":
    test_csv_loader()
