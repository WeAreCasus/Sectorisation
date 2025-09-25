#!/usr/bin/env python3
"""
OSRM Setup Script for Sectorisation Application
This script sets up a local OSRM instance using Docker with France OSM data.
"""

import os
import subprocess
import requests
import time
import sys

def run_command(command, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error output: {result.stderr}")
        sys.exit(1)
    return result

def download_france_osm_data():
    """Download France OSM data if not already present."""
    osm_file = "france-latest.osm.pbf"
    
    if os.path.exists(osm_file):
        print(f"{osm_file} already exists, skipping download.")
        return osm_file
    
    print("Downloading France OSM data (this may take a while)...")
    url = "https://download.geofabrik.de/europe/france-latest.osm.pbf"
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(osm_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded {osm_file}")
        return osm_file
    except Exception as e:
        print(f"Error downloading OSM data: {e}")
        sys.exit(1)

def setup_osrm_docker():
    """Set up OSRM using Docker."""
    osm_file = download_france_osm_data()
    
    print("Stopping any existing OSRM container...")
    run_command("docker stop osrm-backend || true", check=False)
    run_command("docker rm osrm-backend || true", check=False)
    
    data_dir = os.path.abspath("osrm-data")
    os.makedirs(data_dir, exist_ok=True)
    
    osm_path = os.path.join(data_dir, osm_file)
    if not os.path.exists(osm_path):
        run_command(f"cp {osm_file} {osm_path}")
    
    print("Preprocessing OSM data for OSRM (this will take several minutes)...")
    
    run_command(f"docker run -t -v {data_dir}:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/{osm_file}")
    
    base_name = osm_file.replace('.osm.pbf', '')
    run_command(f"docker run -t -v {data_dir}:/data osrm/osrm-backend osrm-partition /data/{base_name}.osrm")
    
    run_command(f"docker run -t -v {data_dir}:/data osrm/osrm-backend osrm-customize /data/{base_name}.osrm")
    
    print("Starting OSRM backend server...")
    
    run_command(f"docker run -d --name osrm-backend -p 5000:5000 -v {data_dir}:/data osrm/osrm-backend osrm-routed --algorithm mld /data/{base_name}.osrm")
    
    print("Waiting for OSRM to be ready...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            if response.status_code == 200:
                print("OSRM is ready!")
                return True
        except:
            pass
        time.sleep(2)
    
    print("OSRM failed to start properly")
    return False

def test_osrm():
    """Test OSRM with a sample route."""
    print("Testing OSRM with a sample route...")
    
    paris_coords = "2.3522,48.8566"  # lon, lat
    lyon_coords = "4.8357,45.7640"
    
    url = f"http://localhost:5000/route/v1/driving/{paris_coords};{lyon_coords}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('code') == 'Ok':
            route = data['routes'][0]
            duration_hours = route['duration'] / 3600
            distance_km = route['distance'] / 1000
            
            print(f"✅ OSRM test successful!")
            print(f"   Route: Paris → Lyon")
            print(f"   Distance: {distance_km:.1f} km")
            print(f"   Duration: {duration_hours:.1f} hours")
            return True
        else:
            print(f"❌ OSRM returned error: {data.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ OSRM test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up OSRM for Sectorisation Application")
    print("=" * 50)
    
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print("❌ Docker is not available. Please install Docker first.")
        sys.exit(1)
    
    print("✅ Docker is available")
    
    if setup_osrm_docker():
        if test_osrm():
            print("\n🎉 OSRM setup completed successfully!")
            print("The OSRM backend is running on http://localhost:5000")
            print("You can now run the Sectorisation application with realistic travel times.")
        else:
            print("\n❌ OSRM setup completed but testing failed.")
    else:
        print("\n❌ OSRM setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
