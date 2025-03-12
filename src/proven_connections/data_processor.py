import pandas as pd
import os
from typing import Optional, Dict, Any, List

from . import data_processor_sync as sync
from . import data_processor_async as async_processor

def process_vendor_data(csv_path: str, use_async: bool = True) -> pd.DataFrame:
    """Process vendor data from CSV file and create relationship records.
    
    Args:
        csv_path: Path to the CSV file containing vendor data
        use_async: If True, use async version for faster processing (requires aiohttp)
                  If False, use synchronous version
    
    Returns:
        DataFrame containing vendor-client relationships
    """
    if use_async:
        try:
            import asyncio
            return asyncio.run(async_processor.process_vendor_data(csv_path))
        except ImportError:
            print("Warning: aiohttp not installed. Falling back to synchronous version.")
            return sync.process_vendor_data(csv_path)
    else:
        return sync.process_vendor_data(csv_path)

if __name__ == "__main__":
    print("\n=== Starting Proven Connections Data Processor ===")
    print("This may take a few minutes...\n")

    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(current_dir, 'data', 'vendors_ireland_10Mar2025.csv')
    
    # Process the data (using async by default)
    processed_df = process_vendor_data(csv_path, use_async=True)
    
    # Save the processed data with date suffix from input file
    input_filename = os.path.basename(csv_path)
    date_suffix = input_filename.split('_')[-1]  # Get '3Mar2025.csv'
    output_filename = f'vendor_client_relationships_{date_suffix}'
    output_path = os.path.join(current_dir, 'data', output_filename)
    processed_df.to_csv(output_path, index=False)
    
    # Calculate statistics
    total_relationships = len(processed_df)
    unique_vendors = processed_df['vendor_name'].nunique()
    unique_clients = processed_df['client_name'].nunique()
    
    # Location statistics
    vendor_has_location = processed_df[['vendor_lat', 'vendor_lng']].notna().all(axis=1)
    client_has_location = processed_df[['client_lat', 'client_lng']].notna().all(axis=1)
    
    vendor_locations = vendor_has_location.sum()
    client_locations = client_has_location.sum()
    
    # Count unique vendors/clients without locations
    unique_vendors_no_location = processed_df[~vendor_has_location]['vendor_name'].nunique()
    unique_clients_no_location = processed_df[~client_has_location]['client_name'].nunique()
    
    print("\nProcessed Data Statistics:")
    print(f"Total number of unique vendor-client relationships: {total_relationships}")
    print(f"Number of unique vendors: {unique_vendors}")
    print(f"Number of unique clients: {unique_clients}")
    print("\nLocation Data:")
    print(f"Vendors with location data: {vendor_locations} relationships")
    print(f"Vendors missing location data: {unique_vendors_no_location} unique vendors")
    print(f"Clients with location data: {client_locations} relationships")
    print(f"Clients missing location data: {unique_clients_no_location} unique clients")
    
    print("\nSample of processed relationships:")
    # Group by vendor and show their clients
    for vendor in processed_df['vendor_name'].unique()[:3]:
        vendor_clients = processed_df[processed_df['vendor_name'] == vendor]['client_name'].tolist()
        print(f"\n{vendor} has {len(vendor_clients)} clients:")
        for client in vendor_clients:
            print(f"  - {client}")
    
    print(f"\nProcessed data saved to: {output_path}")
    print("\n=== Data Processing Complete! ===\n")
