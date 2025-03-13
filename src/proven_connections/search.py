import pandas as pd
from typing import List, Dict, Any
import os

class RelationshipSearch:
    def __init__(self, csv_path: str):
        """Initialize the search with the relationship CSV data."""
        self.df = pd.read_csv(csv_path)
        # Remove any NaN values and convert to list of strings
        self.vendors = sorted([str(x) for x in self.df['vendor_name'].dropna().unique()])
        self.clients = sorted([str(x) for x in self.df['client_name'].dropna().unique()])
        
    def search_vendors(self, query: str, limit: int = 10) -> List[str]:
        """Search for vendors containing the query string."""
        if not query:
            return []
        query = query.lower()
        matches = [v for v in self.vendors if v and query in str(v).lower()]
        return sorted(matches)[:limit]
    
    def search_clients(self, query: str, limit: int = 10) -> List[str]:
        """Search for clients containing the query string."""
        if not query:
            return []
        query = query.lower()
        matches = [c for c in self.clients if c and query in str(c).lower()]
        return sorted(matches)[:limit]
    
    def get_vendor_clients(self, vendor_name: str) -> List[Dict[str, Any]]:
        """Get all unique clients for a specific vendor with their details."""
        # Case-insensitive match for vendor name, handling NaN values
        vendor_rows = self.df[self.df['vendor_name'].fillna('').str.lower() == vendor_name.lower()]
        if vendor_rows.empty:
            return []
            
        # Group by client name to get unique clients
        unique_clients = vendor_rows.groupby('client_name').first().reset_index()
        clients = []
        for _, row in unique_clients.iterrows():
            # Only include non-NaN values
            client_data = {
                'name': row['client_name'] if pd.notna(row['client_name']) else None,
                'domain': row['client_domain'] if pd.notna(row['client_domain']) else None,
                'logo': row['client_logo'] if pd.notna(row['client_logo']) else None,
                'latitude': row['client_lat'] if pd.notna(row['client_lat']) else None,
                'longitude': row['client_lng'] if pd.notna(row['client_lng']) else None,
                'type': 'client'
            }
            # Remove None values
            client_data = {k: v for k, v in client_data.items() if v is not None}
            clients.append(client_data)
        return sorted(clients, key=lambda x: x['name'])
    
    def get_vendor_details(self, vendor_name: str) -> Dict[str, Any]:
        """Get details for a specific vendor."""
        # Case-insensitive match for vendor name, handling NaN values
        vendor_row = self.df[self.df['vendor_name'].fillna('').str.lower() == vendor_name.lower()].iloc[0] if not self.df[self.df['vendor_name'].fillna('').str.lower() == vendor_name.lower()].empty else None
        
        if vendor_row is None:
            return None
            
        # Only include non-NaN values
        vendor_data = {
            'name': vendor_row['vendor_name'] if pd.notna(vendor_row['vendor_name']) else None,
            'domain': vendor_row['vendor_domain'] if pd.notna(vendor_row['vendor_domain']) else None,
            'logo': vendor_row['vendor_logo'] if pd.notna(vendor_row['vendor_logo']) else None,
            'latitude': vendor_row['vendor_lat'] if pd.notna(vendor_row['vendor_lat']) else None,
            'longitude': vendor_row['vendor_lng'] if pd.notna(vendor_row['vendor_lng']) else None,
            'proven_url': vendor_row['vendor_proven_url'] if pd.notna(vendor_row['vendor_proven_url']) else None
        }
        # Remove None values
        return {k: v for k, v in vendor_data.items() if v is not None}

    def get_client_details(self, client_name: str) -> Dict[str, Any]:
        """Get details for a specific client."""
        # Case-insensitive match for client name, handling NaN values
        client_row = self.df[self.df['client_name'].fillna('').str.lower() == client_name.lower()].iloc[0] if not self.df[self.df['client_name'].fillna('').str.lower() == client_name.lower()].empty else None
        
        if client_row is None:
            return None
            
        # Only include non-NaN values
        client_data = {
            'name': client_row['client_name'] if pd.notna(client_row['client_name']) else None,
            'domain': client_row['client_domain'] if pd.notna(client_row['client_domain']) else None,
            'logo': client_row['client_logo'] if pd.notna(client_row['client_logo']) else None,
            'latitude': client_row['client_lat'] if pd.notna(client_row['client_lat']) else None,
            'longitude': client_row['client_lng'] if pd.notna(client_row['client_lng']) else None
        }
        # Remove None values
        return {k: v for k, v in client_data.items() if v is not None}

    def get_client_vendors(self, client_name: str) -> List[Dict[str, Any]]:
        """Get all unique vendors for a specific client with their details."""
        # Case-insensitive match for client name, handling NaN values
        client_rows = self.df[self.df['client_name'].fillna('').str.lower() == client_name.lower()]
        if client_rows.empty:
            return []
            
        # Group by vendor name to get unique vendors
        unique_vendors = client_rows.groupby('vendor_name').first().reset_index()
        vendors = []
        for _, row in unique_vendors.iterrows():
            # Only include non-NaN values
            vendor_data = {
                'name': row['vendor_name'] if pd.notna(row['vendor_name']) else None,
                'domain': row['vendor_domain'] if pd.notna(row['vendor_domain']) else None,
                'logo': row['vendor_logo'] if pd.notna(row['vendor_logo']) else None,
                'latitude': row['vendor_lat'] if pd.notna(row['vendor_lat']) else None,
                'longitude': row['vendor_lng'] if pd.notna(row['vendor_lng']) else None,
                'proven_url': row['vendor_proven_url'] if pd.notna(row['vendor_proven_url']) else None
            }
            # Remove None values
            vendor_data = {k: v for k, v in vendor_data.items() if v is not None}
            vendors.append(vendor_data)
        return sorted(vendors, key=lambda x: x['name'])

    def search_all(self, query: str) -> List[Dict[str, Any]]:
        """Search for both vendors and clients with unified results."""
        if not query:
            return []

        # Search in both name and domain, removing spaces and special characters
        search_term = query.lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '')
        
        # Search for vendors
        vendor_name_mask = self.df['vendor_name'].str.lower().str.replace(' ', '').str.replace('-', '').str.replace('_', '').str.contains(search_term, na=False)
        vendor_domains = self.df['vendor_domain'].str.lower()
        vendor_domains = vendor_domains.str.replace(r'\.com|\.org|\.net|\.co\.\w+|\.\w+$', '', regex=True)
        vendor_domains = vendor_domains.str.replace('.', '').str.replace('-', '').str.replace('_', '')
        vendor_domain_mask = vendor_domains.str.contains(search_term, na=False)
        vendor_mask = vendor_name_mask | vendor_domain_mask
        vendor_details = self.df[vendor_mask].drop_duplicates('vendor_name')
        
        # Search for clients
        client_name_mask = self.df['client_name'].str.lower().str.replace(' ', '').str.replace('-', '').str.replace('_', '').str.contains(search_term, na=False)
        client_domains = self.df['client_domain'].str.lower()
        client_domains = client_domains.str.replace(r'\.com|\.org|\.net|\.co\.\w+|\.\w+$', '', regex=True)
        client_domains = client_domains.str.replace('.', '').str.replace('-', '').str.replace('_', '')
        client_domain_mask = client_domains.str.contains(search_term, na=False)
        client_mask = client_name_mask | client_domain_mask
        client_details = self.df[client_mask].drop_duplicates('client_name')
        
        # Convert vendors to list of dicts
        vendor_results = [
            {
                'name': row['vendor_name'],
                'domain': row['vendor_domain'],
                'logo': row['vendor_logo'],
                'latitude': float(row['vendor_lat']) if pd.notna(row['vendor_lat']) else None,
                'longitude': float(row['vendor_lng']) if pd.notna(row['vendor_lng']) else None,
                'type': 'vendor',
                'proven_url': row['vendor_proven_url'] if pd.notna(row['vendor_proven_url']) else None
            }
            for _, row in vendor_details.iterrows()
            if pd.notna(row['vendor_name'])
        ]
        
        # Convert clients to list of dicts
        client_results = [
            {
                'name': row['client_name'],
                'domain': row['client_domain'],
                'logo': row['client_logo'],
                'latitude': float(row['client_lat']) if pd.notna(row['client_lat']) else None,
                'longitude': float(row['client_lng']) if pd.notna(row['client_lng']) else None,
                'type': 'client'
            }
            for _, row in client_details.iterrows()
            if pd.notna(row['client_name'])
        ]
        
        # Combine and sort results by name length to prioritize shorter matches
        all_results = vendor_results + client_results
        all_results.sort(key=lambda x: len(x['name']))
        return all_results
