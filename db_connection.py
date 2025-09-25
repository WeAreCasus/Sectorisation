
import streamlit as st
import pymysql


def get_connection():
    try:
        conn = pymysql.connect(
            host=st.secrets["connections"]["mysql"]["host"],
            port=int(st.secrets["connections"]["mysql"]["port"]),
            user=st.secrets["connections"]["mysql"]["username"],
            password=st.secrets["connections"]["mysql"]["password"],
            database=st.secrets["connections"]["mysql"]["database"],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as err:
        st.error(f"❌ Erreur de connexion à la base de données : {err}")
        return None
    
# def get_connection():
#     try:
#         conn = pymysql.connect(
#             host=st.secrets["db_host"],
#             port=int(st.secrets["db_port"]),
#             user=st.secrets["db_user"],
#             password=st.secrets["db_password"],
#             database=st.secrets["db_name"],
#             charset='utf8mb4',
#             cursorclass=pymysql.cursors.DictCursor
#         )
#         return conn
#     except pymysql.MySQLError as err:
#         st.error(f"❌ Erreur de connexion à la base de données : {err}")
#         return None

# def get_connection():
#     try:
#         print("Tentative de connexion à MySQL...")  # DEBUG
#         conn = pymysql.connect(
#             host="localhost",
#             user="root",
#             password="",  # XAMPP n'a pas de mot de passe par défaut
#             database="secto",
#             port=3306
#         )
#         print("✅ Connexion réussie !")  # DEBUG
#         return conn
#     except pymysql.Error as err:
#         print(f"❌ ERREUR MYSQL : {err}")  # DEBUG
#         st.error(f"❌ Erreur de connexion MySQL : {err}")
#         return None
#     except Exception as e:
#         print(f"❌ ERREUR INATTENDUE : {e}")  # DEBUG
#         st.error(f"❌ Erreur inattendue : {e}")
#         return None
   
def clear_table_RH():
    """Vide la table 'rh' en supprimant toutes les données."""
    conn = get_connection()
    if not conn:
        st.error("❌ Impossible de se connecter à la base de données.")
        return
    
    st.write("📌 Connexion MySQL établie :", conn)  # DEBUG

    cursor = conn.cursor()

    with conn.cursor() as cursor: 
        try:
            st.write("🔴 Désactivation des clés étrangères...")  # DEBUG
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            st.write("🔴 Suppression des données...")  # DEBUG
            cursor.execute("DELETE FROM rh;")
            conn.commit()
            
            st.write(f"✅ Suppression effectuée. {cursor.rowcount} lignes supprimées.")
            
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")  # Réactiver les clés
            st.success("✅ La table 'rh' a été vidée avec succès !")

        except Exception as e:
            if conn.open:  # ✅ Vérifie si la connexion est encore ouverte avant d'exécuter rollback
                conn.rollback()
            st.error(f"❌ Erreur lors de la suppression des données : {e}")
    
        finally:
            cursor.close()

# if st.button("🗑️ Vider la table RH"):
#     clear_table()
def clear_table_PDV():
    """Vide la table 'rh' en supprimant toutes les données."""
    conn = get_connection()
    if not conn:
        st.error("❌ Impossible de se connecter à la base de données.")
        return
    
    st.write("📌 Connexion MySQL établie :", conn)  # DEBUG

    cursor = conn.cursor()

    with conn.cursor() as cursor: 
        try:
            st.write("🔴 Désactivation des clés étrangères...")  # DEBUG
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            st.write("🔴 Suppression des données...")  # DEBUG
            cursor.execute("DELETE FROM pdv;")
            conn.commit()
            
            st.write(f"✅ Suppression effectuée. {cursor.rowcount} lignes supprimées.")
            
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")  # Réactiver les clés
            st.success("✅ La table 'pdv' a été vidée avec succès !")

        except Exception as e:
            if conn.open:  # ✅ Vérifie si la connexion est encore ouverte avant d'exécuter rollback
                conn.rollback()
            st.error(f"❌ Erreur lors de la suppression des données : {e}")
    
        finally:
            cursor.close()

def check_table_empty(table_name="rh"):
    """Vérifie si la table spécifiée contient des données."""
    conn = get_connection()
    if not conn:
        st.error("❌ Impossible de se connecter à la base de données.")
        return None

    cursor = conn.cursor()
    
    try:
        query = f"SELECT COUNT(*) FROM {table_name};"
        cursor.execute(query)
        row_count = cursor.fetchone()["COUNT(*)"]
        # row_count = cursor.fetchone()[0] 
        return row_count
    except Exception as e:
        st.error(f"❌ Erreur lors de la vérification de la table '{table_name}' : {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def update_database(df_selected):
    """Met à jour les lignes modifiées dans MySQL."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            for _, row in df_selected.iterrows():
                query = """
                    UPDATE rh SET 
                        Nom = %s, Prenom = %s, Adresse = %s, Code_postal = %s, Ville = %s, Pays = %s,
                        Nb_heure_par_jour = %s, Nb_jour_terrain_par_an = %s, Nb_nuitees_max_par_an = %s,
                        Nb_jour_par_semaine = %s, Coef_vitesse = %s, Tolerance = %s,
                        Latitude = %s, Longitude = %s, Nb_visite_max_par_an = %s, 
                        Code_DR = %s, Code_DZ = %s, Type = %s, Temps_max_retour = %s, 
                        Cout_KM = %s, Cout_fixe = %s, Cout_Nuitees = %s
                    WHERE Code_secteur = %s
                """
                cursor.execute(query, (
                    row["Nom"], row["Prenom"], row["Adresse"], row["Code_postal"], row["Ville"], row["Pays"],
                    row["Nb_heure_par_jour"], row["Nb_jour_terrain_par_an"], row["Nb_nuitees_max_par_an"],
                    row["Nb_jour_par_semaine"], row["Coef_vitesse"], row["Tolerance"],
                    row["Latitude"], row["Longitude"], row["Nb_visite_max_par_an"],
                    row["Code_DR"], row["Code_DZ"], row["Type"], row["Temps_max_retour"],
                    row["Cout_KM"], row["Cout_fixe"], row["Cout_Nuitees"], row["Code_secteur"]
                ))
            conn.commit()
            st.success("✅ Données mises à jour avec succès !")
        except Exception as e:
            conn.rollback()
            st.error(f"❌ Erreur lors de la mise à jour : {e}")
        finally:
            cursor.close()
            conn.close()

