#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from db_connection import get_connection

def check_database_schema():
    print("Checking database schema...")
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            print("\n=== PDV table columns ===")
            cursor.execute("DESCRIBE pdv")
            pdv_columns = cursor.fetchall()
            for col in pdv_columns:
                print(f"  {col}")
            
            print("\n=== RH table columns ===")
            cursor.execute("DESCRIBE rh")
            rh_columns = cursor.fetchall()
            for col in rh_columns:
                print(f"  {col}")
            
            print("\n=== Sample PDV data ===")
            cursor.execute("SELECT * FROM pdv LIMIT 3")
            pdv_data = cursor.fetchall()
            for row in pdv_data:
                print(f"  {row}")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error checking schema: {e}")
            conn.close()
            return False
    else:
        print("❌ Database connection failed!")
        return False

if __name__ == "__main__":
    check_database_schema()
