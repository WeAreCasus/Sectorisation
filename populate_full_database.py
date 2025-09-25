#!/usr/bin/env python3
"""
Comprehensive database population script using the complete Excel datasets
"""

import pandas as pd
import pymysql
import sys
import os

def get_connection():
    """Connect to MySQL database"""
    try:
        conn = pymysql.connect(
            host='51.158.59.186',
            port=17126,
            user='adv',
            password='4EBr_eUR_HnRZ0',
            database='advent-plus',
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def clear_tables():
    """Clear existing data from tables"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        print("🔄 Clearing existing data...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DELETE FROM pdv")
        cursor.execute("DELETE FROM rh")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        print("✅ Tables cleared successfully")
        return True
    except Exception as e:
        print(f"❌ Error clearing tables: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def import_managers_from_excel():
    """Import managers from CS Data.xlsx"""
    print("\n=== IMPORTING MANAGERS FROM CS DATA.XLSX ===")
    
    try:
        df = pd.read_excel('CS Data.xlsx')
        print(f"📊 Loaded {len(df)} manager records from Excel")
        
        df = df.dropna(subset=['Code secteur'])
        df = df[~df['Code secteur'].astype(str).str.contains('VACANT', na=False)]
        
        print(f"📊 After filtering: {len(df)} valid manager records")
        
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        query = """
            INSERT INTO rh (
                Code_secteur, Nom, Prenom, Adresse, Code_postal, Ville, Pays, 
                Nb_heure_par_jour, Nb_jour_terrain_par_an, Nb_nuitees_max_par_an, 
                Nb_jour_par_semaine, Coef_vitesse, Tolerance,
                Latitude, Longitude, Nb_visite_max_par_an, Code_DR, Code_DZ, 
                Type, Temps_max_retour, Cout_KM, Cout_fixe, Cout_Nuitees
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data_to_insert = []
        for _, row in df.iterrows():
            data_to_insert.append((
                None if pd.isna(row.get('Code secteur', None)) else row.get('Code secteur', None),
                None if pd.isna(row.get('Nom', None)) else row.get('Nom', None),
                None if pd.isna(row.get('Prenom', None)) else row.get('Prenom', None),
                None if pd.isna(row.get('Adresse', None)) else row.get('Adresse', None),
                None if pd.isna(row.get('Code postal', None)) else row.get('Code postal', None),
                None if pd.isna(row.get('Ville', None)) else row.get('Ville', None),
                None if pd.isna(row.get('Pays', None)) else row.get('Pays', None),
                None if pd.isna(row.get('Nb heure par jour', None)) else row.get('Nb heure par jour', None),
                None if pd.isna(row.get('Nb jour terrain par an', None)) else row.get('Nb jour terrain par an', None),
                None if pd.isna(row.get('Nb nuitées max par an', None)) else row.get('Nb nuitées max par an', None),
                None if pd.isna(row.get('Nb jour par semaine', None)) else row.get('Nb jour par semaine', None),
                None if pd.isna(row.get('Coef vitesse', None)) else row.get('Coef vitesse', None),
                None if pd.isna(row.get('Tolérance', None)) else row.get('Tolérance', None),
                None if pd.isna(row.get('Latitude', None)) else row.get('Latitude', None),
                None if pd.isna(row.get('Longitude', None)) else row.get('Longitude', None),
                None if pd.isna(row.get('Nb visite max par an', None)) else row.get('Nb visite max par an', None),
                None if pd.isna(row.get('Code DR', None)) else row.get('Code DR', None),
                None if pd.isna(row.get('Code DZ', None)) else row.get('Code DZ', None),
                None if pd.isna(row.get('Type', None)) else row.get('Type', None),
                None if pd.isna(row.get('Temps max retour', None)) else row.get('Temps max retour', None),
                None if pd.isna(row.get('Cout KM', None)) else row.get('Cout KM', None),
                None if pd.isna(row.get('Cout fixe', None)) else row.get('Cout fixe', None),
                None if pd.isna(row.get('Cout Nuités', None)) else row.get('Cout Nuités', None)
            ))
        
        cursor.executemany(query, data_to_insert)
        conn.commit()
        print(f"✅ Successfully imported {len(data_to_insert)} managers")
        return True
        
    except Exception as e:
        print(f"❌ Error importing managers: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def import_stores_from_datakiss():
    """Import stores from Datakiss Template 2024 REVILLARS.xlsx"""
    print("\n=== IMPORTING STORES FROM DATAKISS TEMPLATE ===")
    
    try:
        df = pd.read_excel('Datakiss Template 2024 REVILLARS.xlsx')
        print(f"📊 Loaded {len(df)} store records from Datakiss Template")
        
        df = df.dropna(subset=['Code secteur'])
        
        print(f"📊 After filtering: {len(df)} valid store records")
        
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        query = """
            INSERT INTO pdv (
                Code_mag, Code_client_PDV, Code_secteur, Temps, Frequence, `long`, `lat`,
                Enseigne_GMS, Nom_mag, Format_Magasin, Potentiel, Groupe, Code_postal,
                Adresse, Commune, Pays, Enseigne_GMS_Regroupees, Surface
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data_to_insert = []
        for _, row in df.iterrows():
            data_to_insert.append((
                None if pd.isna(row.get('Code mag', None)) else row.get('Code mag', None),
                None if pd.isna(row.get('Code client PDV', None)) else row.get('Code client PDV', None),
                None if pd.isna(row.get('Code secteur', None)) else row.get('Code secteur', None),
                None if pd.isna(row.get('Temps', None)) else row.get('Temps', None),
                None if pd.isna(row.get('Frequence', None)) else row.get('Frequence', None),
                None if pd.isna(row.get('long', None)) else row.get('long', None),
                None if pd.isna(row.get('lat', None)) else row.get('lat', None),
                None if pd.isna(row.get('Enseigne GMS', None)) else row.get('Enseigne GMS', None),
                None if pd.isna(row.get('Nom mag', None)) else row.get('Nom mag', None),
                None if pd.isna(row.get('Format Magasin', None)) else row.get('Format Magasin', None),
                None if pd.isna(row.get('Potentiel', None)) else row.get('Potentiel', None),
                None if pd.isna(row.get('Groupe', None)) else row.get('Groupe', None),
                None if pd.isna(row.get('CP', None)) else row.get('CP', None),  # Note: Excel has 'CP' but database expects 'Code_postal'
                None if pd.isna(row.get('Adresse', None)) else row.get('Adresse', None),
                None if pd.isna(row.get('Commune', None)) else row.get('Commune', None),
                None if pd.isna(row.get('Pays', None)) else row.get('Pays', None),
                None if pd.isna(row.get('Enseigne GMS Regroupées', None)) else row.get('Enseigne GMS Regroupées', None),
                None if pd.isna(row.get('Surface', None)) else row.get('Surface', None)
            ))
        
        cursor.executemany(query, data_to_insert)
        conn.commit()
        print(f"✅ Successfully imported {len(data_to_insert)} stores")
        return True
        
    except Exception as e:
        print(f"❌ Error importing stores: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def verify_population():
    """Verify the database population"""
    print("\n=== VERIFYING DATABASE POPULATION ===")
    
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) FROM rh')
        rh_count = cursor.fetchone()[0]
        print(f"👥 RH table: {rh_count} manager records")
        
        cursor.execute('SELECT COUNT(*) FROM pdv')
        pdv_count = cursor.fetchone()[0]
        print(f"🏪 PDV table: {pdv_count} store records")
        
        cursor.execute('SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS "Size_MB" FROM information_schema.tables WHERE table_schema = "advent-plus"')
        size_info = cursor.fetchall()
        total_size = sum(row[1] for row in size_info if row[1] is not None)
        
        print(f"💾 Database size: {total_size} MB")
        
        if rh_count > 0:
            cursor.execute('SELECT Code_secteur, Nom, Prenom, Latitude, Longitude FROM rh LIMIT 3')
            print("\n📋 Sample RH data:")
            for row in cursor.fetchall():
                print(f"   - Manager: {row[1]} {row[2]} | Sector: {row[0]} | Coords: ({row[3]}, {row[4]})")
        
        if pdv_count > 0:
            cursor.execute('SELECT Code_secteur, lat, `long`, Temps, Frequence FROM pdv LIMIT 3')
            print("\n📋 Sample PDV data:")
            for row in cursor.fetchall():
                print(f"   - Store: Sector {row[0]} | Coords: ({row[1]}, {row[2]}) | Time: {row[3]}min | Freq: {row[4]}")
        
        if rh_count > 25 and pdv_count > 2000:
            print("\n🎯 SUCCESS: Database populated with substantial dataset!")
            return True
        else:
            print(f"\n❌ WARNING: Database population appears insufficient (RH: {rh_count}, PDV: {pdv_count})")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying population: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    print("=== COMPREHENSIVE DATABASE POPULATION ===")
    print("This script will populate the MySQL database with the complete Excel datasets")
    
    required_files = ['CS Data.xlsx', 'Datakiss Template 2024 REVILLARS.xlsx']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file not found: {file}")
            return False
    
    if not clear_tables():
        print("❌ Failed to clear tables")
        return False
    
    if not import_managers_from_excel():
        print("❌ Failed to import managers")
        return False
    
    if not import_stores_from_datakiss():
        print("❌ Failed to import stores")
        return False
    
    if verify_population():
        print("\n🎉 DATABASE POPULATION COMPLETED SUCCESSFULLY!")
        return True
    else:
        print("\n❌ DATABASE POPULATION FAILED VERIFICATION")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
