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
                'longitude': row['client_lng'] if pd.notna(row['client_lng']) else None
            }
            # Remove None values
            client_data = {k: v for k, v in client_data.items() if v is not None}
            clients.append(client_data)
        return sorted(clients, key=lambda x: x['name'])
    
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
                'longitude': row['vendor_lng'] if pd.notna(row['vendor_lng']) else None
            }
            # Remove None values
            vendor_data = {k: v for k, v in vendor_data.items() if v is not None}
            vendors.append(vendor_data)
        return sorted(vendors, key=lambda x: x['name'])
