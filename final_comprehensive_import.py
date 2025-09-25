#!/usr/bin/env python3
"""
Final comprehensive database import script with robust timeout handling
"""

import pandas as pd
import pymysql
import sys
import time
from pathlib import Path

def get_robust_connection():
    """Get database connection with optimized timeout settings"""
    try:
        conn = pymysql.connect(
            host='51.158.59.186',
            port=17126,
            user='adv',
            password='4EBr_eUR_HnRZ0',
            database='advent-plus',
            charset='utf8mb4',
            connect_timeout=15,
            read_timeout=60,
            write_timeout=60,
            autocommit=False
        )
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def safe_execute(cursor, query, params=None, description="query"):
    """Execute query with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return True
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed for {description}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return False
    return False

def import_stores_comprehensive():
    """Import all stores from Datakiss Template with robust error handling"""
    print("🏪 Starting comprehensive store import...")
    
    try:
        excel_path = '/home/ubuntu/repos/Sectorisation/Datakiss Template 2024 REVILLARS.xlsx'
        if not Path(excel_path).exists():
            print(f"❌ File not found: {excel_path}")
            return 0
            
        df = pd.read_excel(excel_path, sheet_name='Liste des PDV')
        print(f"📊 Found {len(df)} stores to import")
        
        conn = get_robust_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        imported = 0
        failed = 0
        
        print("🧹 Clearing existing PDV data...")
        if safe_execute(cursor, "DELETE FROM pdv", description="clear PDV table"):
            conn.commit()
            print("✅ PDV table cleared")
        else:
            print("⚠️ Could not clear PDV table, continuing with insert...")
        
        batch_size = 50
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(df))
            batch = df.iloc[start_idx:end_idx]
            
            print(f"📦 Processing batch {batch_num + 1}/{total_batches} (rows {start_idx}-{end_idx})")
            
            batch_imported = 0
            for _, row in batch.iterrows():
                try:
                    def safe_val(val):
                        return None if pd.isna(val) else val
                    
                    sql = """
                    INSERT INTO pdv (
                        Code_mag, Code_secteur, Temps, Frequence, `long`, lat,
                        Nom_mag, Code_postal, Adresse, Commune, Pays, Potentiel
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    values = (
                        safe_val(row.get('Code mag')),
                        safe_val(row.get('Code secteur')),
                        safe_val(row.get('Temps')),
                        safe_val(row.get('Frequence')),
                        safe_val(row.get('long')),
                        safe_val(row.get('lat')),
                        safe_val(row.get('Nom mag')),
                        safe_val(row.get('CP')),  # Excel uses 'CP' for postal code
                        safe_val(row.get('Adresse')),
                        safe_val(row.get('Commune')),
                        safe_val(row.get('Pays')),
                        safe_val(row.get('Potentiel'))
                    )
                    
                    if safe_execute(cursor, sql, values, f"store {row.get('Code mag', 'Unknown')}"):
                        batch_imported += 1
                        imported += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    print(f"⚠️ Error processing store {row.get('Code mag', 'Unknown')}: {e}")
                    failed += 1
                    continue
            
            try:
                conn.commit()
                print(f"✅ Batch {batch_num + 1} committed: {batch_imported} stores")
            except Exception as e:
                print(f"❌ Failed to commit batch {batch_num + 1}: {e}")
                conn.rollback()
            
            time.sleep(0.5)
        
        print(f"🎯 Store import completed: {imported} imported, {failed} failed")
        return imported
        
    except Exception as e:
        print(f"❌ Store import failed: {e}")
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_clients_table():
    """Create clients table for the Calibrage France Direct data"""
    print("🏗️ Creating clients table...")
    
    conn = get_robust_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        safe_execute(cursor, "DROP TABLE IF EXISTS clients", description="drop clients table")
        
        create_sql = """
        CREATE TABLE clients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Code_client VARCHAR(50),
            Nom_client VARCHAR(255),
            Adresse VARCHAR(500),
            Code_postal VARCHAR(10),
            Ville VARCHAR(100),
            Pays VARCHAR(50),
            Latitude DECIMAL(10, 8),
            Longitude DECIMAL(11, 8),
            Secteur VARCHAR(50),
            CA_potentiel DECIMAL(15, 2),
            Type_client VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        if safe_execute(cursor, create_sql, description="create clients table"):
            conn.commit()
            print("✅ Clients table created successfully")
            return True
        else:
            print("❌ Failed to create clients table")
            return False
            
    except Exception as e:
        print(f"❌ Error creating clients table: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def import_clients_comprehensive():
    """Import client data from Calibrage France Direct Test"""
    print("👥 Starting comprehensive client import...")
    
    try:
        excel_path = '/home/ubuntu/repos/Sectorisation/Calibrage France Direct Test (1).xlsx'
        if not Path(excel_path).exists():
            print(f"❌ File not found: {excel_path}")
            return 0
        
        excel_file = pd.ExcelFile(excel_path)
        sheet_names = excel_file.sheet_names
        print(f"📋 Available sheets: {sheet_names}")
        
        main_sheet = sheet_names[0]
        df = pd.read_excel(excel_path, sheet_name=main_sheet)
        print(f"📊 Found {len(df)} client records to import")
        
        if not create_clients_table():
            return 0
        
        conn = get_robust_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        imported = 0
        failed = 0
        
        batch_size = 25  # Even smaller for client data
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(df))
            batch = df.iloc[start_idx:end_idx]
            
            print(f"📦 Processing client batch {batch_num + 1}/{total_batches} (rows {start_idx}-{end_idx})")
            
            batch_imported = 0
            for _, row in batch.iterrows():
                try:
                    def safe_val(val):
                        return None if pd.isna(val) else val
                    
                    columns = df.columns.tolist()
                    
                    sql = """
                    INSERT INTO clients (
                        Code_client, Nom_client, Adresse, Code_postal, Ville, Pays,
                        Latitude, Longitude, Secteur, CA_potentiel, Type_client
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    code_client = safe_val(row.get('Code client', row.get('Code_client', row.get(columns[0] if columns else None))))
                    nom_client = safe_val(row.get('Nom client', row.get('Nom_client', row.get('Nom', row.get(columns[1] if len(columns) > 1 else None)))))
                    adresse = safe_val(row.get('Adresse', row.get('Address', row.get(columns[2] if len(columns) > 2 else None))))
                    code_postal = safe_val(row.get('Code postal', row.get('CP', row.get('Code_postal'))))
                    ville = safe_val(row.get('Ville', row.get('City', row.get('Commune'))))
                    pays = safe_val(row.get('Pays', row.get('Country', 'France')))
                    latitude = safe_val(row.get('Latitude', row.get('lat')))
                    longitude = safe_val(row.get('Longitude', row.get('long', row.get('lng'))))
                    secteur = safe_val(row.get('Secteur', row.get('Code secteur')))
                    ca_potentiel = safe_val(row.get('CA potentiel', row.get('Potentiel', row.get('CA'))))
                    type_client = safe_val(row.get('Type client', row.get('Type', row.get('Categorie'))))
                    
                    values = (
                        code_client, nom_client, adresse, code_postal, ville, pays,
                        latitude, longitude, secteur, ca_potentiel, type_client
                    )
                    
                    if safe_execute(cursor, sql, values, f"client {code_client}"):
                        batch_imported += 1
                        imported += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    print(f"⚠️ Error processing client row {start_idx + batch_imported}: {e}")
                    failed += 1
                    continue
            
            try:
                conn.commit()
                print(f"✅ Client batch {batch_num + 1} committed: {batch_imported} clients")
            except Exception as e:
                print(f"❌ Failed to commit client batch {batch_num + 1}: {e}")
                conn.rollback()
            
            time.sleep(0.5)
        
        print(f"🎯 Client import completed: {imported} imported, {failed} failed")
        return imported
        
    except Exception as e:
        print(f"❌ Client import failed: {e}")
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def verify_comprehensive_import():
    """Verify the comprehensive import was successful"""
    print("\n🔍 Verifying comprehensive import...")
    
    conn = get_robust_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        tables_info = []
        
        if safe_execute(cursor, "SELECT COUNT(*) FROM rh", description="count RH"):
            rh_count = cursor.fetchone()[0]
            tables_info.append(("RH (Managers)", rh_count))
        
        if safe_execute(cursor, "SELECT COUNT(*) FROM pdv", description="count PDV"):
            pdv_count = cursor.fetchone()[0]
            tables_info.append(("PDV (Stores)", pdv_count))
        
        if safe_execute(cursor, "SELECT COUNT(*) FROM clients", description="count clients"):
            clients_count = cursor.fetchone()[0]
            tables_info.append(("Clients", clients_count))
        else:
            clients_count = 0
            tables_info.append(("Clients", "Table not found"))
        
        size_query = """
            SELECT table_name, 
                   ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
            FROM information_schema.tables 
            WHERE table_schema = 'advent-plus'
        """
        
        if safe_execute(cursor, size_query, description="get database size"):
            size_results = cursor.fetchall()
            total_size = sum(row[1] for row in size_results if row[1] is not None)
        else:
            total_size = "Unknown"
        
        print(f"\n📊 COMPREHENSIVE DATABASE VERIFICATION RESULTS:")
        print(f"=" * 50)
        for table_name, count in tables_info:
            print(f"   {table_name}: {count:,} records" if isinstance(count, int) else f"   {table_name}: {count}")
        
        if isinstance(total_size, (int, float)):
            print(f"   Total database size: {total_size:.2f} MB")
        else:
            print(f"   Total database size: {total_size}")
        
        total_records = sum(count for _, count in tables_info if isinstance(count, int))
        print(f"   Total records across all tables: {total_records:,}")
        
        success = (
            isinstance(rh_count, int) and rh_count >= 30 and
            isinstance(pdv_count, int) and pdv_count >= 2000 and
            total_records >= 16000  # Should have 35 + 2487 + 14135+ = 16,657+
        )
        
        if success:
            print(f"\n🎉 COMPREHENSIVE IMPORT SUCCESSFUL!")
            print(f"   Database now contains {total_records:,} records")
            print(f"   Size increased to {total_size:.2f} MB" if isinstance(total_size, (int, float)) else f"   Size: {total_size}")
        else:
            print(f"\n⚠️ Import may be incomplete:")
            print(f"   Expected: 30+ managers, 2000+ stores, 16000+ total records")
            print(f"   Actual: {rh_count} managers, {pdv_count} stores, {total_records} total")
        
        return success
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    print("🚀 STARTING FINAL COMPREHENSIVE DATABASE IMPORT")
    print("=" * 60)
    print("This script will import ALL available Excel datasets:")
    print("- CS Data.xlsx (35 managers) - already imported")
    print("- Datakiss Template 2024 REVILLARS.xlsx (2,487 stores)")
    print("- Calibrage France Direct Test (1).xlsx (14,135+ clients)")
    print("=" * 60)
    
    stores_imported = import_stores_comprehensive()
    if stores_imported == 0:
        print("❌ Store import failed completely")
        return False
    
    clients_imported = import_clients_comprehensive()
    if clients_imported == 0:
        print("⚠️ Client import failed, but continuing...")
    
    success = verify_comprehensive_import()
    
    if success:
        print(f"\n🎉 FINAL COMPREHENSIVE IMPORT COMPLETED!")
        print(f"   - Managers: Already imported (35)")
        print(f"   - Stores: {stores_imported:,}")
        print(f"   - Clients: {clients_imported:,}")
        print(f"   - Database now contains comprehensive territorial sectorization data!")
    else:
        print(f"\n⚠️ Import completed with some issues")
        print(f"   - Stores: {stores_imported:,}")
        print(f"   - Clients: {clients_imported:,}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
