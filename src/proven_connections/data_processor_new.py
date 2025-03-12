import pandas as pd
import os
import requests
import time
from typing import Optional, Dict, Any, List
import json

from .config import CLEARBIT_API_KEY

def get_company_info_by_domain(domain: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Get company information from Clearbit API with retry logic for 202 responses."""
    url = f"https://company.clearbit.com/v2/companies/find?domain={domain}"
    
    headers = {
        'Authorization': f'Bearer {CLEARBIT_API_KEY}'
    }
    
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data.get('name'),
                    'domain': data.get('domain'),
                    'logo': data.get('logo'),
                    'lat': data.get('geo', {}).get('lat'),
                    'lng': data.get('geo', {}).get('lng')
                }
            elif response.status_code == 202:
                print(f"Request accepted for {domain}, waiting for processing (attempt {retries + 1}/{max_retries})")
                retries += 1
                if retries < max_retries:
                    time.sleep(2)  # Wait 2 seconds before retrying
                continue
            else:
                print(f"Failed to get data for {domain}. Status Code: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching data for {domain}: {str(e)}")
            return None
    
    print(f"Max retries reached for {domain}")
    return None

def parse_client_list(clients_str: str) -> List[str]:
    """Parse a string of client domains into a list of domains."""
    if not pd.notna(clients_str):
        return []

    # Split by comma and clean each domain
    domains = [domain.strip() for domain in clients_str.split(',')]
    # Filter out empty domains
    return [domain for domain in domains if domain]

def process_company_relationships(row: pd.Series) -> List[Dict[str, Any]]:
    """Process vendor and client relationships with full company information."""
    relationships = []
    
    # Get vendor information first
    vendor_info = None
    vendor_domain = row['Vendor Domain']
    if pd.notna(vendor_domain):
        print(f"Processing vendor: {row['Vendor Name']} ({vendor_domain})")
        vendor_info = get_company_info_by_domain(vendor_domain)
        if not vendor_info:
            vendor_info = {
                'name': row['Vendor Name'],
                'domain': vendor_domain,
                'logo': None,
                'lat': None,
                'lng': None
            }
    
    if not vendor_info:  # Skip if no vendor info
        return relationships
    
    # Process each client in the list
    client_domains = parse_client_list(row['Vendor clients domains'])
    for client_domain in client_domains:
        print(f"  Processing client domain: {client_domain}")
        time.sleep(0.5)  # Rate limiting
        client_info = get_company_info_by_domain(client_domain)
        
        if not client_info:
            client_info = {
                'name': client_domain.split('.')[0].title(),  # Use domain name as company name
                'domain': client_domain,
                'logo': None,
                'lat': None,
                'lng': None
            }
        
        # Create relationship record
        relationship = {
            'vendor_name': vendor_info['name'],
            'vendor_domain': vendor_info['domain'],
            'vendor_logo': vendor_info['logo'],
            'vendor_lat': vendor_info['lat'],
            'vendor_lng': vendor_info['lng'],
            'client_name': client_info['name'],
            'client_domain': client_info['domain'],
            'client_logo': client_info['logo'],
            'client_lat': client_info['lat'],
            'client_lng': client_info['lng']
        }
        relationships.append(relationship)
    
    return relationships

def process_vendor_data(csv_path: str):
    """Process vendor data from CSV file and create relationship records."""
    print("Starting vendor data processing...")
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    print(f"Read {len(df)} vendors from CSV")
    
    # Process each row and collect all relationships
    all_relationships = []
    for _, row in df.iterrows():
        relationships = process_company_relationships(row)
        all_relationships.extend(relationships)
    
    # Convert to DataFrame
    relationships_df = pd.DataFrame(all_relationships)
    
    # Remove any duplicate relationships
    relationships_df = relationships_df.drop_duplicates(subset=['vendor_name', 'client_name'])
    
    # Sort by vendor name and client name
    relationships_df = relationships_df.sort_values(['vendor_name', 'client_name'])
    
    # Calculate statistics
    total_relationships = len(relationships_df)
    unique_vendors = relationships_df['vendor_name'].nunique()
    unique_clients = relationships_df['client_name'].nunique()
    vendor_locations = relationships_df[['vendor_lat', 'vendor_lng']].notna().all(axis=1).sum()
    client_locations = relationships_df[['client_lat', 'client_lng']].notna().all(axis=1).sum()
    
    print("\nProcessed Data Statistics:")
    print(f"Total number of unique vendor-client relationships: {total_relationships}")
    print(f"Number of unique vendors: {unique_vendors}")
    print(f"Number of unique clients: {unique_clients}")
    print(f"Number of relationships with vendor location data: {vendor_locations}")
    print(f"Number of relationships with client location data: {client_locations}")
    
    print("\nSample of processed relationships:")
    # Group by vendor and show their clients
    for vendor in relationships_df['vendor_name'].unique()[:3]:
        vendor_clients = relationships_df[relationships_df['vendor_name'] == vendor]['client_name'].tolist()
        print(f"\n{vendor} has {len(vendor_clients)} clients:")
        for client in vendor_clients:
            print(f"  - {client}")
    
    # Save the processed data
    output_path = os.path.join(os.path.dirname(csv_path), 'vendor_client_relationships.csv')
    relationships_df.to_csv(output_path, index=False)
    print(f"\nProcessed data saved to: {output_path}")

if __name__ == "__main__":
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(current_dir, 'data', 'vendors_3Mar2025.csv')
    process_vendor_data(csv_path)
