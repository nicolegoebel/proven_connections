import pandas as pd
import os
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
import json

import os
config_path = os.path.join(os.path.dirname(__file__), 'config.py')
with open(config_path) as f:
    exec(f.read())

async def get_company_info_by_domain_async(session: aiohttp.ClientSession, domain: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Get company information from Clearbit API with retry logic for 202 responses."""
    url = f"https://company.clearbit.com/v2/companies/find?domain={domain}"
    
    headers = {
        'Authorization': f'Bearer {CLEARBIT_API_KEY}'
    }
    
    retries = 0
    while retries < max_retries:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'name': data.get('name'),
                        'domain': domain,  # Use the exact domain we queried with
                        'logo': data.get('logo'),
                        'lat': data.get('geo', {}).get('lat'),
                        'lng': data.get('geo', {}).get('lng')
                    }
                elif response.status == 202:
                    print(f"Request accepted for {domain}, waiting for processing (attempt {retries + 1}/{max_retries})")
                    retries += 1
                    if retries < max_retries:
                        await asyncio.sleep(2)  # Wait 2 seconds before retrying
                    continue
                else:
                    print(f"Failed to get data for {domain}. Status Code: {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching data for {domain}: {str(e)}")
            return None
    
    print(f"Max retries reached for {domain}")
    return None

async def fetch_company_info_batch(domains: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch company information for multiple domains in parallel."""
    async with aiohttp.ClientSession() as session:
        tasks = [get_company_info_by_domain_async(session, domain) for domain in domains]
        results = await asyncio.gather(*tasks)
        return {domain: result for domain, result in zip(domains, results) if result is not None}

async def search_company_domain_async(session: aiohttp.ClientSession, company_name: str) -> Optional[str]:
    """Search for a company's domain using Clearbit's Name to Domain API."""
    try:
        url = f"https://company.clearbit.com/v1/domains/find?name={company_name}"
        headers = {
            'Authorization': f'Bearer {CLEARBIT_API_KEY}'
        }
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('domain')
            elif response.status == 404:
                print(f"  No domain found for {company_name}")
            else:
                print(f"  Failed to get domain for {company_name}. Status Code: {response.status}")
    except Exception as e:
        print(f"  Error searching for {company_name}: {str(e)}")
    
    return None

def parse_client_list(clients_str: str) -> List[Dict[str, str]]:
    """Parse a string of client domains into a list of client info dicts."""
    if not pd.notna(clients_str):
        return []

    # Split by comma and clean each entry
    entries = [entry.strip() for entry in clients_str.split(',')]
    
    # Process each entry to determine if it's a domain or company name
    clients = []
    for entry in entries:
        if not entry:
            continue
            
        # Check if entry looks like a domain (contains a dot)
        if '.' in entry:
            clients.append({'domain': entry, 'name': None})
        else:
            # Entry is likely a company name
            clients.append({'domain': None, 'name': entry})
    
    return clients

async def process_company_relationships(row: pd.Series, company_info_cache: Dict[str, Dict[str, Any]], session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Process vendor and client relationships with full company information."""
    relationships = []
    
    # Get vendor information from cache
    vendor_info = None
    vendor_domain = row['Vendor Domain']
    if pd.notna(vendor_domain):
        print(f"Processing vendor: {row['Vendor Name']} ({vendor_domain})")
        vendor_clearbit = company_info_cache.get(vendor_domain)
        if vendor_clearbit:
            vendor_info = vendor_clearbit
        else:
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
    clients = parse_client_list(row['Vendor clients domains'])
    for client in clients:
        client_domain = client['domain']
        client_name = client['name']
        
        # If we have a name but no domain, try to find the domain
        if client_name and not client_domain:
            print(f"  Searching for domain of {client_name}...")
            client_domain = await search_company_domain_async(session, client_name)
            if not client_domain:
                print(f"  Could not find domain for {client_name}")
                continue
            print(f"  Found domain for {client_name}: {client_domain}")
            await asyncio.sleep(0.1)  # Rate limiting for web search
        
        print(f"  Processing client: {client_name or client_domain}")
        await asyncio.sleep(0.1)  # Rate limiting for Clearbit
        client_clearbit = company_info_cache.get(client_domain)
        
        if client_clearbit:
            client_info = client_clearbit
        else:
            # Try to get a more readable name from the domain or use provided name
            if client_name:
                name = client_name
            else:
                domain_parts = client_domain.split('.')
                if len(domain_parts) >= 2:
                    name = domain_parts[0].replace('-', ' ').title()
                else:
                    name = client_domain
                
            client_info = {
                'name': name,
                'domain': client_domain,
                'logo': None,
                'lat': None,
                'lng': None
            }
        
        # Create relationship record
        relationship = {
            'vendor_name': vendor_info['name'],  # Use Clearbit name if available
            'vendor_domain': vendor_info['domain'],
            'vendor_proven_url': row.get('Vendor Proven URL', vendor_domain),
            'vendor_logo': vendor_info['logo'],
            'vendor_lat': vendor_info['lat'],
            'vendor_lng': vendor_info['lng'],
            'client_name': client_info['name'],  # Use Clearbit name if available
            'client_domain': client_info['domain'],
            'client_logo': client_info['logo'],
            'client_lat': client_info['lat'],
            'client_lng': client_info['lng']
        }
        relationships.append(relationship)
    
    return relationships

async def process_vendor_data(csv_path: str) -> pd.DataFrame:
    """Process vendor data from CSV file and create relationship records."""
    print("\n=== Starting Proven Connections Data Processor (Async Version) ===")
    print("This may take a few minutes...\n")

    # Read the CSV file
    df = pd.read_csv(csv_path)
    print(f"Read {len(df)} vendors from CSV")
    
    # Drop rows where client domains column is empty
    df = df.dropna(subset=['Vendor clients domains'])
    
    # Drop duplicates
    df = df.drop_duplicates()
    
    # Collect all unique domains (vendors and clients)
    all_domains = set()
    all_domains.update(df['Vendor Domain'].dropna())
    for clients in df['Vendor clients domains'].dropna():
        # Only add known domains to the batch lookup
        client_entries = parse_client_list(clients)
        all_domains.update(client['domain'] for client in client_entries if client['domain'])
    
    # Fetch company information for all domains in parallel
    print("Fetching company information from Clearbit...")
    company_info_cache = await fetch_company_info_batch(list(all_domains))
    
    # Process relationships and create new records
    all_relationships = []
    async with aiohttp.ClientSession() as session:
        for _, row in df.iterrows():
            relationships = await process_company_relationships(row, company_info_cache, session)
            all_relationships.extend(relationships)
    
    # Create new DataFrame with relationship records
    relationships_df = pd.DataFrame(all_relationships)
    
    print("\n=== Data Processing Complete! ===\n")
    return relationships_df

if __name__ == "__main__":
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(current_dir, 'data', 'vendors_ireland_10Mar2025.csv')
    
    # Process the data
    processed_df = asyncio.run(process_vendor_data(csv_path))
    
    # Save the processed data with date suffix from input file
    input_filename = os.path.basename(csv_path)
    date_suffix = input_filename.split('_')[-1]  # Get '10Mar2025.csv'
    output_filename = f'vendor_client_relationships_{date_suffix}'
    output_path = os.path.join(current_dir, 'data', output_filename)
    processed_df.to_csv(output_path, index=False)
    
    # Calculate statistics
    total_relationships = len(processed_df)
    unique_vendors = processed_df['vendor_name'].nunique()
    unique_clients = processed_df['client_name'].nunique()
    vendor_locations = processed_df[['vendor_lat', 'vendor_lng']].notna().all(axis=1).sum()
    client_locations = processed_df[['client_lat', 'client_lng']].notna().all(axis=1).sum()
    
    print("\nProcessed Data Statistics:")
    print(f"Total number of unique vendor-client relationships: {total_relationships}")
    print(f"Number of unique vendors: {unique_vendors}")
    print(f"Number of unique clients: {unique_clients}")
    print(f"Number of relationships with vendor location data: {vendor_locations}")
    print(f"Number of relationships with client location data: {client_locations}")
    
    print("\nSample of processed relationships:")
    # Group by vendor and show their clients
    for vendor in processed_df['vendor_name'].unique()[:3]:
        vendor_clients = processed_df[processed_df['vendor_name'] == vendor]['client_name'].tolist()
        print(f"\n{vendor} has {len(vendor_clients)} clients:")
        for client in vendor_clients:
            print(f"  - {client}")
    
    print(f"\nProcessed data saved to: {output_path}")
