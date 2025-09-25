import pymysql
import streamlit as st
from typing import Optional, Dict, Any
import threading
import time
from functools import lru_cache
import pandas as pd

class DatabaseConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()
        
    def get_connection(self) -> Optional[pymysql.Connection]:
        """Get a database connection from the pool."""
        with self.lock:
            if self.connections:
                return self.connections.pop()
            
            try:
                conn = pymysql.connect(
                    host=st.secrets["db_host"],
                    port=int(st.secrets["db_port"]),
                    user=st.secrets["db_user"],
                    password=st.secrets["db_password"],
                    database=st.secrets["db_name"],
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                return conn
            except pymysql.MySQLError as err:
                st.error(f"❌ Erreur de connexion à la base de données : {err}")
                return None
    
    def return_connection(self, conn: pymysql.Connection):
        """Return a connection to the pool."""
        if conn and conn.open:
            with self.lock:
                if len(self.connections) < self.max_connections:
                    self.connections.append(conn)
                else:
                    conn.close()
    
    def close_all(self):
        """Close all connections in the pool."""
        with self.lock:
            for conn in self.connections:
                if conn.open:
                    conn.close()
            self.connections.clear()

db_pool = DatabaseConnectionPool()

class PerformanceOptimizer:
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutes
    
    @lru_cache(maxsize=1000)
    def cached_calculation(self, key: str, *args) -> Any:
        """Generic cached calculation method."""
        return None
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if still valid."""
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.cache_ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.cache_timestamps[key]
        return None
    
    def set_cached_data(self, key: str, data: Any):
        """Set cached data with timestamp."""
        self.cache[key] = data
        self.cache_timestamps[key] = time.time()
    
    def batch_process_stores(self, stores: pd.DataFrame, batch_size: int = 100) -> pd.DataFrame:
        """Process stores in batches for better performance."""
        if len(stores) <= batch_size:
            return stores
        
        processed_batches = []
        for i in range(0, len(stores), batch_size):
            batch = stores.iloc[i:i+batch_size].copy()
            processed_batches.append(batch)
        
        return pd.concat(processed_batches, ignore_index=True)
    
    def optimize_dataframe_operations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize common DataFrame operations."""
        for col in df.columns:
            if df[col].dtype == 'object':
                numeric_series = pd.to_numeric(df[col], errors='ignore')
                if not numeric_series.equals(df[col]):
                    df[col] = numeric_series
        
        return df
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.cache_timestamps.clear()

performance_optimizer = PerformanceOptimizer()

def load_managers_optimized() -> pd.DataFrame:
    """Optimized manager loading with caching."""
    cache_key = "managers_data"
    cached_data = performance_optimizer.get_cached_data(cache_key)
    
    if cached_data is not None:
        return cached_data
    
    conn = db_pool.get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rh")
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        df = performance_optimizer.optimize_dataframe_operations(df)
        
        performance_optimizer.set_cached_data(cache_key, df)
        
        return df
        
    except Exception as e:
        print(f"Erreur lors du chargement de la table RH : {e}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        db_pool.return_connection(conn)

def load_stores_optimized() -> pd.DataFrame:
    """Optimized store loading with caching."""
    cache_key = "stores_data"
    cached_data = performance_optimizer.get_cached_data(cache_key)
    
    if cached_data is not None:
        return cached_data
    
    conn = db_pool.get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pdv")
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        df = performance_optimizer.optimize_dataframe_operations(df)
        
        performance_optimizer.set_cached_data(cache_key, df)
        
        return df
        
    except Exception as e:
        print(f"Erreur lors du chargement de la table PDV : {e}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        db_pool.return_connection(conn)
