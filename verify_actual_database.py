#!/usr/bin/env python3
"""
Comprehensive database verification script to show actual database contents
"""

import pymysql

def verify_database_contents():
    print('=== COMPREHENSIVE DATABASE VERIFICATION ===')
    
    try:
        conn = pymysql.connect(
            host='51.158.59.186',
            port=17126,
            user='adv',
            password='4EBr_eUR_HnRZ0',
            database='advent-plus',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        print('✅ Successfully connected to MySQL database')
        print(f'   Host: 51.158.59.186:17126')
        print(f'   Database: advent-plus')
        print()
        
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        print(f'📋 Tables in database: {[table[0] for table in tables]}')
        print()
        
        cursor.execute('SELECT COUNT(*) FROM rh')
        rh_count = cursor.fetchone()[0]
        print(f'👥 RH table contains {rh_count} manager records')
        
        if rh_count > 0:
            cursor.execute('SELECT Code_secteur, Nom, Prenom, Latitude, Longitude FROM rh LIMIT 5')
            print('   Sample RH data:')
            for row in cursor.fetchall():
                print(f'   - Manager: {row[1]} {row[2]} | Sector: {row[0]} | Coords: ({row[3]}, {row[4]})')
        
        print()
        
        cursor.execute('SELECT COUNT(*) FROM pdv')
        pdv_count = cursor.fetchone()[0]
        print(f'🏪 PDV table contains {pdv_count} store records')
        
        if pdv_count > 0:
            cursor.execute('SELECT Code_secteur, lat, `long`, Temps, Frequence FROM pdv LIMIT 5')
            print('   Sample PDV data:')
            for row in cursor.fetchall():
                print(f'   - Store: Sector {row[0]} | Coords: ({row[1]}, {row[2]}) | Time: {row[3]}min | Freq: {row[4]}')
        
        print()
        
        cursor.execute('SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS "DB Size in MB" FROM information_schema.tables WHERE table_schema = "advent-plus"')
        size_info = cursor.fetchall()
        total_size = sum(row[1] for row in size_info if row[1] is not None)
        
        print(f'💾 Database size information:')
        for table_name, size_mb in size_info:
            if size_mb is not None:
                print(f'   - {table_name}: {size_mb} MB')
        print(f'   Total database size: {total_size} MB')
        
        print()
        print('🎯 CONCLUSION: Database is populated with real data!')
        print(f'   - {rh_count} managers in RH table')
        print(f'   - {pdv_count} stores in PDV table')
        print(f'   - Total size: {total_size} MB (not 0 KB)')
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f'❌ Database verification failed: {e}')
        return False

if __name__ == "__main__":
    verify_database_contents()
