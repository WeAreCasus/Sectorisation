#!/usr/bin/env python3
"""
Database verification script to confirm MySQL population
"""

from db_connection import get_connection
import pandas as pd

def verify_database():
    print('=== DATABASE CONNECTION TEST ===')
    conn = get_connection()
    if not conn:
        print('❌ Failed to connect to database')
        return False
    
    print('✅ Successfully connected to MySQL database')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT COUNT(*) FROM RH')
        rh_count = cursor.fetchone()[0]
        print(f'✅ RH table contains {rh_count} manager records')
        
        cursor.execute('SELECT COUNT(*) FROM PDV')
        pdv_count = cursor.fetchone()[0]
        print(f'✅ PDV table contains {pdv_count} store records')
        
        print('\n=== SAMPLE RH DATA ===')
        cursor.execute('SELECT Code_secteur, Nom, Prenom, Latitude, Longitude FROM RH LIMIT 3')
        for row in cursor.fetchall():
            print(f'Manager: {row[1]} {row[2]} | Sector: {row[0]} | Coords: ({row[3]}, {row[4]})')
        
        print('\n=== SAMPLE PDV DATA ===')
        cursor.execute('SELECT Code_secteur, lat, long, Temps, Frequence FROM PDV LIMIT 3')
        for row in cursor.fetchall():
            print(f'Store: Sector {row[0]} | Coords: ({row[1]}, {row[2]}) | Time: {row[3]}min | Freq: {row[4]}')
        
        print('\n✅ Database verification complete - all data populated successfully')
        return True
        
    except Exception as e:
        print(f'❌ Database verification failed: {e}')
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    verify_database()
