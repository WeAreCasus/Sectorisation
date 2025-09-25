#!/usr/bin/env python3
"""
Efficient Excel data import script that avoids database timeouts
"""

import pandas as pd
import pymysql
import sys

def get_connection():
    """Get database connection with timeout settings"""
    try:
        conn = pymysql.connect(
            host='51.158.59.186',
            port=17126,
            user='adv',
            password='4EBr_eUR_HnRZ0',
            database='advent-plus',
            charset='utf8mb4',
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30
        )
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def import_managers():
    """Import managers from CS Data.xlsx"""
    print("👥 Importing managers from CS Data.xlsx...")
    
    try:
        df = pd.read_excel('/home/ubuntu/repos/Sectorisation/CS Data.xlsx', sheet_name='Liste des CS')
        df_filtered = df[df['Nom'].str.upper() != 'VACANT'].copy()
        print(f"📊 Found {len(df_filtered)} managers to import")
        
        conn = get_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        imported = 0
        
        for _, row in df_filtered.iterrows():
            try:
                def safe_val(val):
                    return None if pd.isna(val) else val
                
                sql = """
                INSERT INTO rh (
                    Code_secteur, Nom, Prenom, Adresse, Code_postal, Ville, Pays,
                    Nb_heure_par_jour, Nb_jour_terrain_par_an, Latitude, Longitude
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    safe_val(row.get('Code secteur')),
                    safe_val(row.get('Nom')),
                    safe_val(row.get('Prenom')),
                    safe_val(row.get('Adresse')),
                    safe_val(row.get('Code postal')),
                    safe_val(row.get('Ville')),
                    safe_val(row.get('Pays')),
                    safe_val(row.get('Nb heure par jour')),
                    safe_val(row.get('Nb jour terrain par an')),
                    safe_val(row.get('Latitude')),
                    safe_val(row.get('Longitude'))
                )
                
                cursor.execute(sql, values)
                imported += 1
                
            except Exception as e:
                print(f"⚠️ Error importing manager {row.get('Nom', 'Unknown')}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Imported {imported} managers")
        return imported
        
    except Exception as e:
        print(f"❌ Manager import failed: {e}")
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def import_stores():
    """Import stores from Datakiss Template"""
    print("🏪 Importing stores from Datakiss Template...")
    
    try:
        df = pd.read_excel('/home/ubuntu/repos/Sectorisation/Datakiss Template 2024 REVILLARS.xlsx', 
                          sheet_name='Liste des PDV')
        print(f"📊 Found {len(df)} stores to import")
        
        conn = get_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        imported = 0
        
        batch_size = 100
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
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
                    
                    cursor.execute(sql, values)
                    imported += 1
                    
                except Exception as e:
                    print(f"⚠️ Error importing store {row.get('Code mag', 'Unknown')}: {e}")
                    continue
            
            conn.commit()
            print(f"📊 Imported batch {i//batch_size + 1}: {imported} stores so far")
        
        print(f"✅ Imported {imported} stores total")
        return imported
        
    except Exception as e:
        print(f"❌ Store import failed: {e}")
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def verify_import():
    """Verify the import was successful"""
    print("\n🔍 Verifying import...")
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM rh")
        rh_count = cursor.fetchone()['count']
        print(f"👥 RH table: {rh_count} managers")
        
        cursor.execute("SELECT COUNT(*) as count FROM pdv")
        pdv_count = cursor.fetchone()['count']
        print(f"🏪 PDV table: {pdv_count} stores")
        
        cursor.execute("""
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
            FROM information_schema.tables 
            WHERE table_schema = 'advent-plus'
        """)
        size_result = cursor.fetchone()
        size_mb = size_result['size_mb'] if size_result['size_mb'] else 0
        print(f"💾 Database size: {size_mb} MB")
        
        success = rh_count >= 25 and pdv_count >= 2000
        if success:
            print("✅ Import successful!")
        else:
            print(f"⚠️ Import may be incomplete (expected: 25+ managers, 2000+ stores)")
        
        return success
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    print("🚀 STARTING EFFICIENT EXCEL DATA IMPORT")
    print("=" * 50)
    
    managers_imported = import_managers()
    if managers_imported == 0:
        print("❌ Manager import failed")
        return False
    
    stores_imported = import_stores()
    if stores_imported == 0:
        print("❌ Store import failed")
        return False
    
    success = verify_import()
    
    if success:
        print(f"\n🎉 IMPORT COMPLETED SUCCESSFULLY!")
        print(f"   - Managers: {managers_imported}")
        print(f"   - Stores: {stores_imported}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
