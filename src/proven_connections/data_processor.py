import pandas as pd
import os
import requests
import time
from typing import Optional, Dict, Any, List
import json

CLEARBIT_API_KEY = 'sk_5b6d6a22d28f21aad880ce891449f1d9'

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

def extract_domain_from_email(client_info: str) -> Optional[str]:
    """Extract domain from client information string."""
    try:
        # Extract the email part between parentheses
        email_start = client_info.find('(')
        email_end = client_info.find(')')
        if email_start != -1 and email_end != -1:
            email = client_info[email_start + 1:email_end]
            # Some entries might just be empty parentheses
            if email and email != 'nan':
                return email.strip()
    except Exception as e:
        print(f"Error processing client info {client_info}: {str(e)}")
    return None

def parse_client_list(clients_str: str) -> List[Dict[str, str]]:
    """Parse a string of clients into a list of client dictionaries with name and domain."""
    if not pd.notna(clients_str):
        return []

    clients = []
    # Split by comma and handle each client separately
    parts = [p.strip() for p in clients_str.split(',')]
    
    for part in parts:
        # Extract name and domain from format: 'Name (domain.com)'
        name = domain = None
        if '(' in part and ')' in part:
            name = part[:part.find('(')].strip()
            domain = part[part.find('(')+1:part.find(')')].strip()
        else:
            name = part.strip()
        
        if name:  # Only add if we at least have a name
            clients.append({
                'name': name,
                'domain': domain
            })
    
    return clients

def process_company_relationships(row: pd.Series) -> List[Dict[str, Any]]:
    """Process vendor and client relationships with full company information."""
    relationships = []
    
    # Get vendor information first
    vendor_info = None
    if pd.notna(row['DOMAIN']):
        print(f"Processing vendor: {row['NAME']} ({row['DOMAIN']})")
        vendor_info = get_company_info_by_domain(row['DOMAIN'])
        if not vendor_info:
            vendor_info = {
                'name': row['NAME'],
                'domain': row['DOMAIN'],
                'logo': None,
                'lat': None,
                'lng': None
            }
    
    if not vendor_info:  # Skip if no vendor info
        return relationships
    
    # Process each client in the list
    clients = parse_client_list(row['CLIENTS'])
    for client in clients:
        if client['domain']:
            print(f"  Processing client: {client['name']} ({client['domain']})")
            time.sleep(0.5)  # Rate limiting
            client_info = get_company_info_by_domain(client['domain'])
            
            if not client_info:
                client_info = {
                    'name': client['name'],
                    'domain': client['domain'],
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

def process_vendor_data(csv_path: str) -> pd.DataFrame:
    """Process vendor data from CSV file and create relationship records."""
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Select specific columns
    columns_needed = ["NAME", "DOMAIN", "ADDRESS", "CLIENTS"]
    df = df[columns_needed]
    
    # Drop rows where CLIENTS column is empty
    df = df.dropna(subset=['CLIENTS'])
    
    # Drop duplicates
    df = df.drop_duplicates()
    
    # Process relationships and create new records
    print("Fetching company information from Clearbit...")
    all_relationships = []
    for _, row in df.iterrows():
        relationships = process_company_relationships(row)
        all_relationships.extend(relationships)
    
    # Create new DataFrame with relationship records
    relationships_df = pd.DataFrame(all_relationships)
    
    return relationships_df

if __name__ == "__main__":
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(current_dir, 'data', 'vendor_details.csv')
    
    # Process the data
    processed_df = process_vendor_data(csv_path)
    
    # Save the processed data
    output_path = os.path.join(current_dir, 'data', 'vendor_client_relationships.csv')
    processed_df.to_csv(output_path, index=False)
    
    # Print some basic statistics
    print("\nProcessed Data Statistics:")
    print(f"Total number of vendor-client relationships: {len(processed_df)}")
    print(f"Number of relationships with vendor location data: {processed_df['vendor_lat'].notna().sum()}")
    print(f"Number of relationships with client location data: {processed_df['client_lat'].notna().sum()}")
    
    # Display sample of the data
    print("\nSample of processed relationships (first 3 rows):")
    display_columns = [
        'vendor_name', 'vendor_domain', 'vendor_lat', 'vendor_lng',
        'client_name', 'client_domain', 'client_lat', 'client_lng'
    ]
    print(processed_df[display_columns].head(3).to_string())
    print(f"\nProcessed data saved to: {output_path}")
