#!/usr/bin/env python3
"""
Analyze all Excel files to determine their structure and data volume
"""

import pandas as pd
import os
from pathlib import Path

def analyze_excel_file(file_path):
    """Analyze an Excel file and return its structure information"""
    try:
        print(f"\n=== ANALYZING: {file_path} ===")
        
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        print(f"File size: {file_size:.2f} MB")
        
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"Sheets: {sheet_names}")
        
        total_rows = 0
        for sheet_name in sheet_names:
            try:
                df_sample = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5)
                df_full = pd.read_excel(file_path, sheet_name=sheet_name)
                
                rows, cols = df_full.shape
                total_rows += rows
                
                print(f"  Sheet '{sheet_name}': {rows} rows, {cols} columns")
                print(f"  Columns: {list(df_full.columns)}")
                
                if not df_sample.empty:
                    print(f"  Sample data:")
                    for i, row in df_sample.iterrows():
                        print(f"    Row {i+1}: {dict(row)}")
                        if i >= 2:  # Show max 3 sample rows
                            break
                
            except Exception as e:
                print(f"  Error reading sheet '{sheet_name}': {e}")
        
        print(f"Total rows across all sheets: {total_rows}")
        return total_rows, file_size
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return 0, 0

def main():
    print("=== EXCEL FILES ANALYSIS ===")
    
    excel_files = [
        "Calibrage France Direct Test (1).xlsx",
        "CS Data.xlsx", 
        "Datakiss Template 2024 REVILLARS.xlsx",
        "PDV_Data_Template.xlsx",
        "CS_Data_Template.xlsx"
    ]
    
    total_data_rows = 0
    total_file_size = 0
    
    for file_name in excel_files:
        file_path = f"/home/ubuntu/repos/Sectorisation/{file_name}"
        if os.path.exists(file_path):
            rows, size = analyze_excel_file(file_path)
            total_data_rows += rows
            total_file_size += size
        else:
            print(f"\n❌ File not found: {file_path}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total data rows available: {total_data_rows:,}")
    print(f"Total file size: {total_file_size:.2f} MB")
    print(f"Current database has only ~87 records (29 managers + 58 stores)")
    print(f"Potential data increase: {total_data_rows/87:.1f}x more data available!")

if __name__ == "__main__":
    main()
