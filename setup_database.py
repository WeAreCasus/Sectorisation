#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from db_connection import get_connection
from utils.csv_data_loader import load_managers_from_csv, load_stores_from_csv
import pandas as pd
import pymysql

def create_rh_table():
    """Create the RH table with proper schema."""
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS rh;")
        
        create_table_query = """
        CREATE TABLE rh (
            Code_secteur VARCHAR(50) PRIMARY KEY,
            Nom VARCHAR(100),
            Prenom VARCHAR(100),
            Adresse TEXT,
            Code_postal VARCHAR(10),
            Ville VARCHAR(100),
            Pays VARCHAR(50),
            Nb_heure_par_jour DECIMAL(5,2),
            Nb_jour_terrain_par_an INT,
            Nb_nuitees_max_par_an INT,
            Nb_jour_par_semaine INT,
            Coef_vitesse DECIMAL(5,2),
            Tolerance DECIMAL(5,2),
            Latitude DECIMAL(10,8),
            Longitude DECIMAL(11,8),
            Nb_visite_max_par_an INT,
            Code_DR VARCHAR(50),
            Code_DZ VARCHAR(50),
            Type VARCHAR(50),
            Temps_max_retour INT,
            Cout_KM DECIMAL(8,2),
            Cout_fixe DECIMAL(8,2),
            Cout_Nuitees DECIMAL(8,2)
        );
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        print("✅ RH table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating RH table: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def create_pdv_table():
    """Create the PDV table with proper schema."""
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS pdv;")
        
        create_table_query = """
        CREATE TABLE pdv (
            Code_mag VARCHAR(50) PRIMARY KEY,
            Code_client_PDV VARCHAR(50),
            Code_secteur VARCHAR(50),
            Temps INT,
            Frequence INT,
            `long` DECIMAL(11,8),
            `lat` DECIMAL(10,8),
            Enseigne_GMS VARCHAR(100),
            Nom_mag VARCHAR(100),
            Format_Magasin VARCHAR(50),
            Potentiel DECIMAL(12,2),
            Groupe VARCHAR(100),
            Code_postal VARCHAR(10),
            Adresse TEXT,
            Commune VARCHAR(100),
            Pays VARCHAR(50),
            Enseigne_GMS_Regroupees VARCHAR(100),
            Surface DECIMAL(10,2)
        );
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        print("✅ PDV table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating PDV table: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def populate_rh_table():
    """Populate RH table with manager data from CSV."""
    print("Loading manager data from CSV...")
    managers_df = load_managers_from_csv()
    
    if managers_df.empty:
        print("❌ No manager data found in CSV")
        return False
    
    print(f"📊 Loaded {len(managers_df)} managers from CSV")
    
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        column_mapping = {
            'Code_secteur': 'Code secteur',
            'Nom': 'Nom',
            'Prenom': 'Prenom',
            'Adresse': 'Adresse',
            'Code_postal': 'Code postal',
            'Ville': 'Ville',
            'Pays': 'Pays',
            'Nb_heure_par_jour': 'Nb heure par jour',
            'Nb_jour_terrain_par_an': 'Nb jour terrain par an',
            'Latitude': 'Latitude',
            'Longitude': 'Longitude',
            'Type': 'Type'
        }
        
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
        for _, row in managers_df.iterrows():
            data_tuple = (
                row.get('Code_secteur'),
                row.get('Nom'),
                row.get('Prenom'),
                row.get('Adresse'),
                row.get('Code_postal'),
                row.get('Ville'),
                row.get('Pays'),
                row.get('Nb_heure_par_jour', 8.0),
                row.get('Nb_jour_terrain_par_an', 200),
                100,  # Default Nb_nuitees_max_par_an
                5,    # Default Nb_jour_par_semaine
                1.0,  # Default Coef_vitesse
                0.1,  # Default Tolerance
                row.get('Latitude'),
                row.get('Longitude'),
                500,  # Default Nb_visite_max_par_an
                None, # Code_DR
                None, # Code_DZ
                row.get('Type'),
                480,  # Default Temps_max_retour (8 hours in minutes)
                0.5,  # Default Cout_KM
                100.0, # Default Cout_fixe
                50.0   # Default Cout_Nuitees
            )
            data_to_insert.append(data_tuple)
        
        cursor.executemany(query, data_to_insert)
        conn.commit()
        print(f"✅ Inserted {len(data_to_insert)} managers into RH table")
        return True
        
    except Exception as e:
        print(f"❌ Error populating RH table: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def populate_pdv_table():
    """Populate PDV table with store data from CSV."""
    print("Loading store data from CSV...")
    stores_df = load_stores_from_csv()
    
    if stores_df.empty:
        print("❌ No store data found in CSV")
        return False
    
    print(f"📊 Loaded {len(stores_df)} stores from CSV")
    
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        query = """
            INSERT INTO pdv (
                Code_mag, Code_client_PDV, Code_secteur, Temps, Frequence, `long`, `lat`,
                Enseigne_GMS, Nom_mag, Format_Magasin, Potentiel, Groupe, Code_postal,
                Adresse, Commune, Pays, Enseigne_GMS_Regroupees, Surface
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data_to_insert = []
        for _, row in stores_df.iterrows():
            data_tuple = (
                str(row.get('id')),  # Code_mag
                f"CLIENT_{row.get('id')}",  # Code_client_PDV
                row.get('Code_secteur'),
                row.get('Temps', 60),  # Temps
                row.get('Frequence', 2),
                row.get('long'),
                row.get('lat'),
                "GMS_DEFAULT",  # Enseigne_GMS
                row.get('Nom_magasin', f"Store_{row.get('id')}"),
                "SUPERMARCHE",  # Format_Magasin
                row.get('Potentiel', 25000),  # Potentiel
                "GROUPE_DEFAULT",  # Groupe
                "75000",  # Code_postal (default)
                f"Adresse {row.get('id')}",  # Adresse
                row.get('Ville', 'Paris'),  # Commune
                "France",  # Pays
                "GMS_REGROUPEES",  # Enseigne_GMS_Regroupees
                500.0   # Surface (default)
            )
            data_to_insert.append(data_tuple)
        
        cursor.executemany(query, data_to_insert)
        conn.commit()
        print(f"✅ Inserted {len(data_to_insert)} stores into PDV table")
        return True
        
    except Exception as e:
        print(f"❌ Error populating PDV table: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verify_tables():
    """Verify that tables were created and populated correctly."""
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM rh;")
        rh_count = cursor.fetchone()['count']
        print(f"📊 RH table contains {rh_count} records")
        
        cursor.execute("SELECT COUNT(*) as count FROM pdv;")
        pdv_count = cursor.fetchone()['count']
        print(f"📊 PDV table contains {pdv_count} records")
        
        cursor.execute("SELECT Code_secteur, Nom, Prenom, Ville FROM rh LIMIT 3;")
        rh_sample = cursor.fetchall()
        print("📋 Sample RH data:")
        for row in rh_sample:
            print(f"  - {row['Code_secteur']}: {row['Nom']} {row['Prenom']} ({row['Ville']})")
        
        cursor.execute("SELECT Code_mag, Code_secteur, Nom_mag FROM pdv LIMIT 3;")
        pdv_sample = cursor.fetchall()
        print("📋 Sample PDV data:")
        for row in pdv_sample:
            print(f"  - {row['Code_mag']}: {row['Nom_mag']} (Sector: {row['Code_secteur']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to set up the database."""
    print("🚀 Starting database setup...")
    
    conn = get_connection()
    if not conn:
        print("❌ Cannot connect to database. Check credentials.")
        return False
    conn.close()
    print("✅ Database connection successful")
    
    if not create_rh_table():
        return False
    
    if not create_pdv_table():
        return False
    
    if not populate_rh_table():
        return False
    
    if not populate_pdv_table():
        return False
    
    if not verify_tables():
        return False
    
    print("🎉 Database setup completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
