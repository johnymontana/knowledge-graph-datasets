#!/usr/bin/env python3
"""
GTFS Data Validation Script

This script validates and provides an overview of GTFS data files
before importing them into Neo4j.
"""

import os
from dotenv import load_dotenv

import csv
import os
from pathlib import Path
from typing import Dict, List, Any

def analyze_gtfs_data(data_dir: str = "gtfs/data") -> Dict[str, Any]:
    """Analyze GTFS data files and return summary statistics"""
    data_dir = Path(data_dir)
    results = {}
    
    # Expected GTFS files
    expected_files = [
        "agency.txt", "routes.txt", "stops.txt", "trips.txt", 
        "stop_times.txt", "calendar.txt", "calendar_dates.txt",
        "fare_attributes.txt", "fare_rules.txt", "transfers.txt",
        "shapes.txt", "feed_info.txt"
    ]
    
    for filename in expected_files:
        filepath = data_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                    results[filename] = {
                        'row_count': len(rows),
                        'columns': list(reader.fieldnames) if reader.fieldnames else [],
                        'sample_data': rows[:3] if rows else []
                    }
                    
                    # Special analysis for specific files
                    if filename == "stops.txt" and rows:
                        lat_values = [float(row.get('stop_lat', 0)) for row in rows if row.get('stop_lat')]
                        lon_values = [float(row.get('stop_lon', 0)) for row in rows if row.get('stop_lon')]
                        if lat_values and lon_values:
                            results[filename]['bounds'] = {
                                'min_lat': min(lat_values),
                                'max_lat': max(lat_values),
                                'min_lon': min(lon_values),
                                'max_lon': max(lon_values)
                            }
                            results[filename]['geo_info'] = {
                                'total_stops': len(rows),
                                'stops_with_coords': len([r for r in rows if r.get('stop_lat') and r.get('stop_lon')]),
                                'coordinate_format': 'Will be converted to geo type during import'
                            }
                    
                    elif filename == "routes.txt" and rows:
                        route_types = {}
                        for row in rows:
                            route_type = row.get('route_type', 'unknown')
                            route_types[route_type] = route_types.get(route_type, 0) + 1
                        results[filename]['route_types'] = route_types
                        
                print(f"✓ {filename}: {len(rows):,} rows")
                
            except Exception as e:
                print(f"✗ {filename}: Error reading file - {e}")
                results[filename] = {'error': str(e)}
        else:
            print(f"✗ {filename}: File not found")
            results[filename] = {'error': 'File not found'}
    
    return results

def print_summary(results: Dict[str, Any]):
    """Print a summary of the GTFS data analysis"""
    print("\n" + "="*60)
    print("GTFS DATA SUMMARY")
    print("="*60)
    
    total_rows = 0
    successful_files = 0
    
    for filename, data in results.items():
        if 'error' not in data:
            successful_files += 1
            row_count = data['row_count']
            total_rows += row_count
            
            print(f"\n{filename.upper()}")
            print(f"  Rows: {row_count:,}")
            print(f"  Columns: {len(data['columns'])}")
            
            if 'bounds' in data:
                bounds = data['bounds']
                print(f"  Geographic Bounds:")
                print(f"    Latitude: {bounds['min_lat']:.6f} to {bounds['max_lat']:.6f}")
                print(f"    Longitude: {bounds['min_lon']:.6f} to {bounds['max_lon']:.6f}")
            
            if 'geo_info' in data:
                geo_info = data['geo_info']
                print(f"  Geo Information:")
                print(f"    Total stops: {geo_info['total_stops']:,}")
                print(f"    Stops with coordinates: {geo_info['stops_with_coords']:,}")
                print(f"    Coordinate format: {geo_info['coordinate_format']}")
            
            if 'route_types' in data:
                print(f"  Route Types:")
                for route_type, count in data['route_types'].items():
                    route_type_name = {
                        '0': 'Tram/Streetcar',
                        '1': 'Subway/Metro',
                        '2': 'Rail',
                        '3': 'Bus',
                        '4': 'Ferry',
                        '5': 'Cable Car',
                        '6': 'Gondola',
                        '7': 'Funicular'
                    }.get(route_type, f'Unknown ({route_type})')
                    print(f"    {route_type_name}: {count}")
            
            if data['sample_data']:
                print(f"  Sample Data:")
                for i, row in enumerate(data['sample_data'][:2]):
                    print(f"    Row {i+1}: {dict(list(row.items())[:3])}")
    
    print("\n" + "="*60)
    print(f"SUMMARY STATISTICS")
    print("="*60)
    print(f"Total files processed: {len(results)}")
    print(f"Successful files: {successful_files}")
    print(f"Failed files: {len(results) - successful_files}")
    print(f"Total data rows: {total_rows:,}")
    
    if successful_files == len(results):
        print("\n✅ All GTFS files are ready for import!")
    else:
        print(f"\n⚠️  {len(results) - successful_files} files have issues that need to be resolved.")

def main():
    """Main function"""
    print("GTFS Data Validation Script")
    print("="*40)
    
    # Load configuration
    load_dotenv('config.env')
    
    # Check if data directory exists
    data_dir = os.getenv('DATA_DIR', 'data')
    if not Path(data_dir).exists():
        print(f"Error: Data directory '{data_dir}' not found!")
        print("Please ensure you have GTFS data files in the correct location.")
        return
    
    # Analyze the data
    results = analyze_gtfs_data(data_dir)
    
    # Print summary
    print_summary(results)

if __name__ == "__main__":
    main()
