#!/usr/bin/env python3
"""
Comprehensive database population script to import ALL available Excel datasets
This will replace the inadequate current dataset with the complete comprehensive data
"""

import pandas as pd
import pymysql
import os
import sys
from pathlib import Path

def get_database_connection():
    """Connect to MySQL database using the configured credentials"""
    try:
        conn = pymysql.connect(
            host='51.158.59.186',
            port=17126,
            user='adv',
            password='4EBr_eUR_HnRZ0',
            database='advent-plus',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def clear_existing_data():
    """Clear existing inadequate data from RH and PDV tables"""
    print("🗑️ Clearing existing inadequate data...")
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM rh")
        cursor.execute("DELETE FROM pdv")
        
        try:
            cursor.execute("ALTER TABLE rh AUTO_INCREMENT = 1")
            cursor.execute("ALTER TABLE pdv AUTO_INCREMENT = 1")
        except:
            pass  # Tables might not have auto-increment
        
        conn.commit()
        print("✅ Existing data cleared successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def create_clients_table():
    """Create clients table for the Calibrage France Direct data"""
    print("📋 Creating clients table for comprehensive client data...")
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS clients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Code_client INT,
            Code_client_ADV VARCHAR(50),
            Nom_client VARCHAR(200),
            Nom_pays VARCHAR(100),
            Rue VARCHAR(200),
            Code_postal VARCHAR(10),
            Ville VARCHAR(100),
            Adresse TEXT,
            Longitude DECIMAL(11,8),
            Latitude DECIMAL(10,8),
            Activite VARCHAR(100),
            Sous_activite VARCHAR(100),
            Directeur_commercial VARCHAR(100),
            Directeur_des_ventes VARCHAR(100),
            Chef_de_zone VARCHAR(100),
            Chef_de_marche VARCHAR(100),
            Commercial VARCHAR(100),
            Matricule_commercial INT,
            Commerciale_sedentaire VARCHAR(100),
            Affectation_TLV VARCHAR(50),
            Departement_client VARCHAR(100),
            N_Dep INT,
            Region_administrative VARCHAR(100),
            Region_Nielsen VARCHAR(50),
            Typo_SalesForce VARCHAR(50),
            Typo_retenu VARCHAR(50),
            Fidelisation VARCHAR(50),
            CA_2023 DECIMAL(12,2),
            Volume_2024 DECIMAL(12,2),
            CANF_2024 DECIMAL(12,2),
            CANF_2025 DECIMAL(12,2),
            Volume_2025 DECIMAL(12,2),
            Circuit_distribution VARCHAR(100),
            CC_CA VARCHAR(100),
            Regle_prod VARCHAR(100),
            SC_Client_Gold_Platinium DECIMAL(5,2),
            Nbre_visite_annuel INT,
            Nb_visite INT,
            Nbre_appel_theorique INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ Clients table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating clients table: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def import_managers_data():
    """Import complete manager data from CS Data.xlsx"""
    print("👥 Importing complete manager dataset from CS Data.xlsx...")
    
    try:
        df = pd.read_excel('/home/ubuntu/repos/Sectorisation/CS Data.xlsx', sheet_name='Liste des CS')
        print(f"📊 Loaded {len(df)} manager records from Excel")
        
        df_filtered = df[df['Nom'].str.upper() != 'VACANT'].copy()
        print(f"📊 After filtering VACANT entries: {len(df_filtered)} managers")
        
        if df_filtered.empty:
            print("⚠️ No valid manager data to import")
            return 0
        
        conn = get_database_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        imported_count = 0
        
        for _, row in df_filtered.iterrows():
            try:
                def safe_value(val):
                    return None if pd.isna(val) else val
                
                insert_sql = """
                INSERT INTO rh (
                    Code_secteur, Nom, Prenom, Adresse, Code_postal, Ville, Pays,
                    Nb_heure_par_jour, Nb_jour_terrain_par_an, Nb_nuitees_max_par_an,
                    Nb_jour_par_semaine, Coef_vitesse, Tolerance, Latitude, Longitude,
                    Nb_visite_max_par_an, Code_DR, Code_DZ, Type, Temps_max_retour,
                    Cout_KM, Cout_fixe, Cout_Nuitees
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                values = (
                    safe_value(row.get('Code secteur')),
                    safe_value(row.get('Nom')),
                    safe_value(row.get('Prenom')),
                    safe_value(row.get('Adresse')),
                    safe_value(row.get('Code postal')),
                    safe_value(row.get('Ville')),
                    safe_value(row.get('Pays')),
                    safe_value(row.get('Nb heure par jour')),
                    safe_value(row.get('Nb jour terrain par an')),
                    safe_value(row.get('Nb nuitées max par an')),
                    safe_value(row.get('Nb jour par semaine')),
                    safe_value(row.get('Coef vitesse')),
                    safe_value(row.get('Tolérance')),
                    safe_value(row.get('Latitude')),
                    safe_value(row.get('Longitude')),
                    safe_value(row.get('Nb visite max par an')),
                    safe_value(row.get('Code DR')),
                    safe_value(row.get('Code DZ')),
                    safe_value(row.get('Type')),
                    safe_value(row.get('Temps max retour')),
                    safe_value(row.get('Cout KM')),
                    safe_value(row.get('Cout fixe')),
                    safe_value(row.get('Cout Nuités'))
                )
                
                cursor.execute(insert_sql, values)
                imported_count += 1
                
            except Exception as e:
                print(f"⚠️ Error importing manager {row.get('Nom', 'Unknown')}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Successfully imported {imported_count} managers")
        return imported_count
        
    except Exception as e:
        print(f"❌ Error importing managers: {e}")
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def import_stores_data():
    """Import complete store data from Datakiss Template 2024 REVILLARS.xlsx"""
    print("🏪 Importing complete store dataset from Datakiss Template...")
    
    try:
        df_main = pd.read_excel('/home/ubuntu/repos/Sectorisation/Datakiss Template 2024 REVILLARS.xlsx', 
                               sheet_name='Liste des PDV')
        print(f"📊 Loaded {len(df_main)} stores from main sheet")
        
        try:
            df_non_geocoded = pd.read_excel('/home/ubuntu/repos/Sectorisation/Datakiss Template 2024 REVILLARS.xlsx', 
                                          sheet_name='Mag Non Geocoded')
            print(f"📊 Loaded {len(df_non_geocoded)} stores from non-geocoded sheet")
            
            df = pd.concat([df_main, df_non_geocoded], ignore_index=True)
        except:
            print("⚠️ Could not load non-geocoded sheet, using main sheet only")
            df = df_main
        
        print(f"📊 Total stores to import: {len(df)}")
        
        if df.empty:
            print("⚠️ No store data to import")
            return 0
        
        conn = get_database_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                def safe_value(val):
                    return None if pd.isna(val) else val
                
                code_postal = safe_value(row.get('CP', row.get('Code postal')))
                
                insert_sql = """
                INSERT INTO pdv (
                    Code_mag, Code_client_PDV, Code_secteur, Temps, Frequence,
                    `long`, lat, Enseigne_GMS, Nom_mag, Format_Magasin,
                    Potentiel, Groupe, Code_postal, Adresse, Commune,
                    Pays, Enseigne_GMS_Regroupees, Surface
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                values = (
                    safe_value(row.get('Code mag')),
                    safe_value(row.get('Code client PDV')),
                    safe_value(row.get('Code secteur', row.get('Code Secteur'))),
                    safe_value(row.get('Temps')),
                    safe_value(row.get('Frequence')),
                    safe_value(row.get('long')),
                    safe_value(row.get('lat')),
                    safe_value(row.get('Enseigne GMS')),
                    safe_value(row.get('Nom mag')),
                    safe_value(row.get('Format Magasin')),
                    safe_value(row.get('Potentiel')),
                    safe_value(row.get('Groupe')),
                    code_postal,
                    safe_value(row.get('Adresse')),
                    safe_value(row.get('Commune')),
                    safe_value(row.get('Pays')),
                    safe_value(row.get('Enseigne GMS Regroupées')),
                    safe_value(row.get('Surface'))
                )
                
                cursor.execute(insert_sql, values)
                imported_count += 1
                
            except Exception as e:
                print(f"⚠️ Error importing store {row.get('Code mag', 'Unknown')}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Successfully imported {imported_count} stores")
        return imported_count
        
    except Exception as e:
        print(f"❌ Error importing stores: {e}")
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def import_clients_data():
    """Import comprehensive client data from Calibrage France Direct Test.xlsx"""
    print("👤 Importing comprehensive client dataset from Calibrage France Direct Test...")
    
    try:
        df_main = pd.read_excel('/home/ubuntu/repos/Sectorisation/Calibrage France Direct Test (1).xlsx', 
                               sheet_name='Calibrage France Direct Test')
        print(f"📊 Loaded {len(df_main)} clients from main sheet")
        
        try:
            df_second = pd.read_excel('/home/ubuntu/repos/Sectorisation/Calibrage France Direct Test (1).xlsx', 
                                    sheet_name='Calibrage France Direct Tes (2)')
            print(f"📊 Loaded {len(df_second)} clients from second sheet")
            
            df = pd.concat([df_main, df_second], ignore_index=True)
        except:
            print("⚠️ Could not load second sheet, using main sheet only")
            df = df_main
        
        print(f"📊 Total clients to import: {len(df)}")
        
        if df.empty:
            print("⚠️ No client data to import")
            return 0
        
        conn = get_database_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                def safe_value(val):
                    return None if pd.isna(val) else val
                
                insert_sql = """
                INSERT INTO clients (
                    Code_client, Code_client_ADV, Nom_client, Nom_pays, Rue,
                    Code_postal, Ville, Adresse, Longitude, Latitude,
                    Activite, Sous_activite, Directeur_commercial, Directeur_des_ventes,
                    Chef_de_zone, Chef_de_marche, Commercial, Matricule_commercial,
                    Commerciale_sedentaire, Affectation_TLV, Departement_client,
                    N_Dep, Region_administrative, Region_Nielsen, Typo_SalesForce,
                    Typo_retenu, Fidelisation, CA_2023, Volume_2024, CANF_2024,
                    CANF_2025, Volume_2025, Circuit_distribution, CC_CA,
                    Regle_prod, SC_Client_Gold_Platinium, Nbre_visite_annuel,
                    Nb_visite, Nbre_appel_theorique
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                values = (
                    safe_value(row.get('Code du client')),
                    safe_value(row.get('Code client ADV+')),
                    safe_value(row.get('Nom du client')),
                    safe_value(row.get('Nom_pays')),
                    safe_value(row.get('Rue')),
                    safe_value(row.get('Code Postal', row.get('Code postal'))),
                    safe_value(row.get('Ville')),
                    safe_value(row.get('Adresse')),
                    safe_value(row.get('long')),
                    safe_value(row.get('lat')),
                    safe_value(row.get('Activité')),
                    safe_value(row.get('Sous_activité')),
                    safe_value(row.get('Directeur_commercial')),
                    safe_value(row.get('Directeur_des_ventes')),
                    safe_value(row.get('Chef_de_zone')),
                    safe_value(row.get('Chef_de_marché')),
                    safe_value(row.get('Commercial')),
                    safe_value(row.get('N° Matricule')),
                    safe_value(row.get('Commerciale Sedentaire')),
                    safe_value(row.get('Affectation TLV')),
                    safe_value(row.get('Département Client')),
                    safe_value(row.get('N°Dep')),
                    safe_value(row.get('Région admnistrative')),
                    safe_value(row.get('Region Nielsen')),
                    safe_value(row.get('Typo (SalesForce)')),
                    safe_value(row.get('Typo retenu')),
                    safe_value(row.get('Fidélisation')),
                    safe_value(row.get('CA 2023')),
                    safe_value(row.get('Volume 2024')),
                    safe_value(row.get('CANF 2024')),
                    safe_value(row.get('CANF 2025 [26/05]')),
                    safe_value(row.get('Volume 2025 [26/05]')),
                    safe_value(row.get('Circuit_de_distribution')),
                    safe_value(row.get('CC CA')),
                    safe_value(row.get('régle prod')),
                    safe_value(row.get('SC\xa0: Client GOLD ou Platinium + 2 visites uniquement sur les CC50 et CC80 ART ET CHR')),
                    safe_value(row.get('Nbre de Visite Annuel')),
                    safe_value(row.get('Nb Visite', row.get('Nbre de Visite Annuel 2'))),
                    safe_value(row.get("Nbre d'appel théorique"))
                )
                
                cursor.execute(insert_sql, values)
                imported_count += 1
                
                if imported_count % 1000 == 0:
                    print(f"📊 Imported {imported_count} clients...")
                
            except Exception as e:
                print(f"⚠️ Error importing client {row.get('Code du client', 'Unknown')}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Successfully imported {imported_count} clients")
        return imported_count
        
    except Exception as e:
        print(f"❌ Error importing clients: {e}")
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def verify_comprehensive_population():
    """Verify the comprehensive database population was successful"""
    print("\n🔍 VERIFYING COMPREHENSIVE DATABASE POPULATION")
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        table_names = [table[list(table.keys())[0]] for table in tables]
        print(f"📋 Available tables: {table_names}")
        
        total_records = 0
        
        cursor.execute('SELECT COUNT(*) as count FROM rh')
        rh_count = cursor.fetchone()['count']
        total_records += rh_count
        print(f"👥 RH table: {rh_count} managers")
        
        if rh_count > 0:
            cursor.execute('SELECT Code_secteur, Nom, Prenom FROM rh LIMIT 3')
            samples = cursor.fetchall()
            for sample in samples:
                print(f"   - {sample['Nom']} {sample['Prenom']} (Sector: {sample['Code_secteur']})")
        
        cursor.execute('SELECT COUNT(*) as count FROM pdv')
        pdv_count = cursor.fetchone()['count']
        total_records += pdv_count
        print(f"🏪 PDV table: {pdv_count} stores")
        
        if pdv_count > 0:
            cursor.execute('SELECT Code_secteur, Nom_mag, Commune FROM pdv LIMIT 3')
            samples = cursor.fetchall()
            for sample in samples:
                print(f"   - {sample['Nom_mag']} in {sample['Commune']} (Sector: {sample['Code_secteur']})")
        
        if 'clients' in table_names:
            cursor.execute('SELECT COUNT(*) as count FROM clients')
            clients_count = cursor.fetchone()['count']
            total_records += clients_count
            print(f"👤 Clients table: {clients_count} clients")
            
            if clients_count > 0:
                cursor.execute('SELECT Nom_client, Ville, Commercial FROM clients LIMIT 3')
                samples = cursor.fetchall()
                for sample in samples:
                    print(f"   - {sample['Nom_client']} in {sample['Ville']} (Commercial: {sample['Commercial']})")
        
        cursor.execute("""
            SELECT table_name, 
                   ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb 
            FROM information_schema.tables 
            WHERE table_schema = 'advent-plus'
        """)
        size_info = cursor.fetchall()
        total_size = sum(row['size_mb'] for row in size_info if row['size_mb'] is not None)
        
        print(f"\n💾 DATABASE SIZE ANALYSIS:")
        for row in size_info:
            if row['size_mb'] is not None:
                print(f"   - {row['table_name']}: {row['size_mb']} MB")
        print(f"   Total database size: {total_size} MB")
        
        print(f"\n🎯 COMPREHENSIVE POPULATION SUMMARY:")
        print(f"   - Total records: {total_records:,}")
        print(f"   - Database size: {total_size} MB")
        print(f"   - Tables populated: {len([t for t in table_names if t in ['rh', 'pdv', 'clients']])}")
        
        success = (
            rh_count >= 25 and  # At least 25 managers
            pdv_count >= 2000 and  # At least 2000 stores
            total_size >= 2.0  # At least 2 MB
        )
        
        if success:
            print("✅ COMPREHENSIVE DATABASE POPULATION SUCCESSFUL!")
            print(f"   Database now contains {total_records:,} records ({total_size} MB)")
        else:
            print("❌ Database population may be incomplete:")
            print(f"   - Managers: {rh_count} (expected: 25+)")
            print(f"   - Stores: {pdv_count} (expected: 2000+)")
            print(f"   - Size: {total_size} MB (expected: 2+ MB)")
        
        return success
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to execute comprehensive database population"""
    print("🚀 STARTING COMPREHENSIVE DATABASE POPULATION")
    print("=" * 60)
    
    if not clear_existing_data():
        print("❌ Failed to clear existing data")
        return False
    
    if not create_clients_table():
        print("❌ Failed to create clients table")
        return False
    
    managers_imported = import_managers_data()
    if managers_imported == 0:
        print("❌ Failed to import manager data")
        return False
    
    stores_imported = import_stores_data()
    if stores_imported == 0:
        print("❌ Failed to import store data")
        return False
    
    clients_imported = import_clients_data()
    print(f"📊 Imported {clients_imported} clients (may be 0 if file not accessible)")
    
    success = verify_comprehensive_population()
    
    if success:
        print("\n🎉 COMPREHENSIVE DATABASE POPULATION COMPLETED SUCCESSFULLY!")
        print(f"   - Managers: {managers_imported}")
        print(f"   - Stores: {stores_imported}")
        print(f"   - Clients: {clients_imported}")
        print("   - Database size significantly increased")
        print("   - Ready for territorial sectorization system")
    else:
        print("\n⚠️ Database population completed with warnings")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
