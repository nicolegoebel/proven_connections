import pandas as pd
import os
import requests
import time
from typing import Optional, Dict, Any, List

# Load config
config_path = os.path.join(os.path.dirname(__file__), 'config.py')
with open(config_path) as f:
    exec(f.read())

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
                    'domain': domain,  # Use the exact domain we queried with
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

def search_company_domain(company_name: str) -> Optional[str]:
    """Search for a company's domain using Clearbit Autocomplete API."""
    if not CLEARBIT_API_KEY:
        print("  Warning: CLEARBIT_API_KEY not set, skipping domain search")
        return None
        
    try:
        # Use Clearbit's Autocomplete API to find the company
        url = 'https://autocomplete.clearbit.com/v1/companies/suggest'
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {CLEARBIT_API_KEY}'},
            params={'query': company_name}
        )
        
        if response.status_code == 401:
            print("  Warning: Invalid CLEARBIT_API_KEY, skipping domain search")
            return None
        elif response.status_code != 200:
            print(f"  Failed to search for {company_name}. Status Code: {response.status_code}")
            return None
            
        results = response.json()
        
        # Look for the most likely company match
        if not results:
            return None
            
        # The API returns results sorted by relevance
        # First result is usually the best match
        for result in results:
            domain = result.get('domain')
            if not domain:
                continue
                
            # Remove www. if present
            domain = domain.replace('www.', '')
            
            # Basic validation of domain
            if '.' not in domain or len(domain.split('.')) < 2:
                continue
                
            # If company name appears in domain, it's likely the right one
            company_words = company_name.lower().split()
            domain_words = domain.lower().split('.')
            if any(word in domain_words[0] for word in company_words if len(word) > 2):
                return domain
            
            # Otherwise, return first valid domain
            return domain
            
    except Exception as e:
        print(f"  Error searching for {company_name}: {str(e)}")
    
    return None

def update_company_info(df: pd.DataFrame) -> pd.DataFrame:
    """Update missing company information in the relationships DataFrame."""
    print("\n=== Starting Company Information Update ===")
    print("This may take a few minutes...\n")
    
    # Create a copy of the DataFrame
    updated_df = df.copy()
    
    # First, try to find domains for entries with only company names
    print("Looking up domains for companies without domains...")
    
    # Process vendors without domains
    vendors_no_domain = df[
        (df['vendor_domain'].isna()) & 
        (df['vendor_name'].notna())
    ][['vendor_name']].drop_duplicates()
    
    for _, row in vendors_no_domain.iterrows():
        vendor_name = row['vendor_name']
        print(f"\nSearching domain for vendor: {vendor_name}")
        domain = search_company_domain(vendor_name)
        if domain:
            print(f"✓ Found domain for {vendor_name}: {domain}")
            # Update all matching vendor names
            mask = updated_df['vendor_name'] == vendor_name
            updated_df.loc[mask, 'vendor_domain'] = domain
            # Get and update company info
            company_info = get_company_info_by_domain(domain)
            if company_info:
                updated_df.loc[mask, 'vendor_logo'] = company_info['logo']
                updated_df.loc[mask, 'vendor_lat'] = company_info['lat']
                updated_df.loc[mask, 'vendor_lng'] = company_info['lng']
        time.sleep(0.1)  # Rate limiting
    
    # Process clients without domains
    clients_no_domain = df[
        (df['client_domain'].isna()) & 
        (df['client_name'].notna())
    ][['client_name']].drop_duplicates()
    
    for _, row in clients_no_domain.iterrows():
        client_name = row['client_name']
        print(f"\nSearching domain for client: {client_name}")
        domain = search_company_domain(client_name)
        if domain:
            print(f"✓ Found domain for {client_name}: {domain}")
            # Update all matching client names
            mask = updated_df['client_name'] == client_name
            updated_df.loc[mask, 'client_domain'] = domain
            # Get and update company info
            company_info = get_company_info_by_domain(domain)
            if company_info:
                updated_df.loc[mask, 'client_logo'] = company_info['logo']
                updated_df.loc[mask, 'client_lat'] = company_info['lat']
                updated_df.loc[mask, 'client_lng'] = company_info['lng']
        time.sleep(0.1)  # Rate limiting
    
    # Now process remaining domains that need updating
    vendor_domains = updated_df[
        (updated_df['vendor_domain'].notna()) & 
        (
            updated_df['vendor_logo'].isna() | 
            updated_df['vendor_lat'].isna() | 
            updated_df['vendor_lng'].isna()
        )
    ]['vendor_domain'].unique()
    
    client_domains = updated_df[
        (updated_df['client_domain'].notna()) & 
        (
            updated_df['client_logo'].isna() | 
            updated_df['client_lat'].isna() | 
            updated_df['client_lng'].isna()
        )
    ]['client_domain'].unique()
    
    # Process vendor domains
    print(f"\nProcessing {len(vendor_domains)} vendors with missing information...")
    for domain in vendor_domains:
        print(f"\nFetching info for vendor: {domain}")
        company_info = get_company_info_by_domain(domain)
        if company_info:
            # Update all rows for this vendor
            mask = updated_df['vendor_domain'] == domain
            if pd.isna(updated_df.loc[mask, 'vendor_logo']).any():
                updated_df.loc[mask, 'vendor_logo'] = company_info['logo']
            if pd.isna(updated_df.loc[mask, 'vendor_lat']).any():
                updated_df.loc[mask, 'vendor_lat'] = company_info['lat']
            if pd.isna(updated_df.loc[mask, 'vendor_lng']).any():
                updated_df.loc[mask, 'vendor_lng'] = company_info['lng']
            print(f"✓ Updated vendor info for {domain}")
        time.sleep(0.1)  # Rate limiting
    
    # Process client domains
    print(f"\nProcessing {len(client_domains)} clients with missing information...")
    for domain in client_domains:
        print(f"\nFetching info for client: {domain}")
        company_info = get_company_info_by_domain(domain)
        if company_info:
            # Update all rows for this client
            mask = updated_df['client_domain'] == domain
            if pd.isna(updated_df.loc[mask, 'client_logo']).any():
                updated_df.loc[mask, 'client_logo'] = company_info['logo']
            if pd.isna(updated_df.loc[mask, 'client_lat']).any():
                updated_df.loc[mask, 'client_lat'] = company_info['lat']
            if pd.isna(updated_df.loc[mask, 'client_lng']).any():
                updated_df.loc[mask, 'client_lng'] = company_info['lng']
            print(f"✓ Updated client info for {domain}")
        time.sleep(0.1)  # Rate limiting
    
    # Calculate statistics
    vendor_info_complete = updated_df[['vendor_logo', 'vendor_lat', 'vendor_lng']].notna().all(axis=1).sum()
    client_info_complete = updated_df[['client_logo', 'client_lat', 'client_lng']].notna().all(axis=1).sum()
    total_relationships = len(updated_df)
    
    print("\n=== Update Complete! ===")
    print(f"\nTotal relationships: {total_relationships}")
    print(f"Relationships with complete vendor info: {vendor_info_complete}")
    print(f"Relationships with complete client info: {client_info_complete}")
    
    return updated_df

if __name__ == "__main__":
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    input_file = 'vendor_client_relationships_10Mar2025.csv'
    input_path = os.path.join(current_dir, 'data', input_file)
    
    # Read the relationships file
    df = pd.read_csv(input_path)
    print(f"Read {len(df)} relationships from {input_file}")
    
    # Update company information
    updated_df = update_company_info(df)
    
    # Save the updated data
    output_file = 'vendor_client_relationships_11Mar2025.csv'
    output_path = os.path.join(current_dir, 'data', output_file)
    updated_df.to_csv(output_path, index=False)
    print(f"\nSaved updated relationships to {output_file}")
