from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import pandas as pd
import os
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load data
csv_path = "data/vendor_client_relationships_11Mar2025.csv"
print(f"Loading relationship data from: {csv_path}")
vendor_client_df = pd.read_csv(csv_path)

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/config/map")
async def get_map_config():
    token = os.environ.get("MAPBOX_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Mapbox access token not found")
    print(f"Token length: {len(token)}")  # Debug print
    return {
        "accessToken": token,
        "style": "mapbox://styles/mapbox/light-v11",
        "center": [-95.7129, 37.0902],  # Center of USA
        "zoom": 3
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8004, reload=True)

@app.get("/api/search/companies")
async def search_companies(q: str = ""):
    if not q:
        return {"results": []}
    
    try:
        # Search in both name and domain, removing spaces and special characters
        search_term = q.lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '')
        
        # Search for vendors
        vendor_name_mask = vendor_client_df["vendor_name"].str.lower().str.replace(' ', '').str.replace('-', '').str.replace('_', '').str.contains(search_term, na=False)
        vendor_domains = vendor_client_df["vendor_domain"].str.lower()
        vendor_domains = vendor_domains.str.replace(r'\.com|\.org|\.net|\.co\.\w+|\.\w+$', '', regex=True)
        vendor_domains = vendor_domains.str.replace('.', '').str.replace('-', '').str.replace('_', '')
        vendor_domain_mask = vendor_domains.str.contains(search_term, na=False)
        vendor_mask = vendor_name_mask | vendor_domain_mask
        vendor_details = vendor_client_df[vendor_mask].drop_duplicates("vendor_name")
        
        # Search for clients
        client_name_mask = vendor_client_df["client_name"].str.lower().str.replace(' ', '').str.replace('-', '').str.replace('_', '').str.contains(search_term, na=False)
        client_domains = vendor_client_df["client_domain"].str.lower()
        client_domains = client_domains.str.replace(r'\.com|\.org|\.net|\.co\.\w+|\.\w+$', '', regex=True)
        client_domains = client_domains.str.replace('.', '').str.replace('-', '').str.replace('_', '')
        client_domain_mask = client_domains.str.contains(search_term, na=False)
        client_mask = client_name_mask | client_domain_mask
        client_details = vendor_client_df[client_mask].drop_duplicates("client_name")
        
        # Convert vendors to list of dicts
        vendor_results = [
            {
                "name": row["vendor_name"],
                "domain": row["vendor_domain"],
                "logo": row["vendor_logo"],
                "latitude": float(row["vendor_lat"]) if pd.notna(row["vendor_lat"]) else None,
                "longitude": float(row["vendor_lng"]) if pd.notna(row["vendor_lng"]) else None,
                "type": "service_provider"
            }
            for _, row in vendor_details.iterrows()
        ]
        
        # Convert clients to list of dicts
        client_results = [
            {
                "name": row["client_name"],
                "domain": row["client_domain"],
                "logo": row["client_logo"],
                "latitude": float(row["client_lat"]) if pd.notna(row["client_lat"]) else None,
                "longitude": float(row["client_lng"]) if pd.notna(row["client_lng"]) else None,
                "type": "client"
            }
            for _, row in client_details.iterrows()
        ]
        
        # Combine and sort results
        all_results = vendor_results + client_results
        all_results.sort(key=lambda x: len(x["name"]))  # Sort by name length to prioritize shorter matches
        
        return {"results": all_results}
    except Exception as e:
        print(f"Error in search_companies: {str(e)}")
        return {"results": []}

@app.get("/api/vendor/{vendor_name}/clients")
async def get_vendor_clients(vendor_name: str, include_stats: bool = False):
    """Get all clients for a specific vendor with optional statistics."""
    try:
        # Get all clients for this vendor
        relationships = vendor_client_df[
            vendor_client_df["vendor_name"] == vendor_name
        ]
        
        if relationships.empty:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # Get first relationship for vendor details
        vendor_row = relationships.iloc[0]
        
        # Create vendor object
        vendor = {
            "name": vendor_name,
            "domain": vendor_row["vendor_domain"],
            "logo": vendor_row["vendor_logo"],
            "latitude": float(vendor_row["vendor_lat"]) if pd.notna(vendor_row["vendor_lat"]) else None,
            "longitude": float(vendor_row["vendor_lng"]) if pd.notna(vendor_row["vendor_lng"]) else None,
            "type": "service_provider"
        }
        
        # Get all related clients
        clients = [
            {
                "name": row["client_name"],
                "domain": row["client_domain"],
                "logo": row["client_logo"],
                "latitude": float(row["client_lat"]) if pd.notna(row["client_lat"]) else None,
                "longitude": float(row["client_lng"]) if pd.notna(row["client_lng"]) else None,
                "type": "client"
            }
            for _, row in relationships.iterrows()
        ]
        
        response = {
            "center": vendor,
            "related": clients,
            "total_count": len(clients)
        }
        
        if include_stats:
            response["stats"] = {
                "with_location": sum(1 for c in clients if c["latitude"] and c["longitude"]),
                "with_logo": sum(1 for c in clients if c["logo"])
            }
        
        return response
    except Exception as e:
        print(f"Error in get_vendor_relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/client/{client_name}/vendors")
async def get_client_vendors(client_name: str, include_stats: bool = False):
    """Get all vendors for a specific client with optional statistics."""
    try:
        # Get all vendors for this client
        relationships = vendor_client_df[
            vendor_client_df["client_name"] == client_name
        ]
        
        if relationships.empty:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get first relationship for client details
        client_row = relationships.iloc[0]
        
        # Create client object
        client = {
            "name": client_name,
            "domain": client_row["client_domain"],
            "logo": client_row["client_logo"],
            "latitude": float(client_row["client_lat"]) if pd.notna(client_row["client_lat"]) else None,
            "longitude": float(client_row["client_lng"]) if pd.notna(client_row["client_lng"]) else None,
            "type": "client"
        }
        
        # Get all related vendors
        vendors = [
            {
                "name": row["vendor_name"],
                "domain": row["vendor_domain"],
                "logo": row["vendor_logo"],
                "latitude": float(row["vendor_lat"]) if pd.notna(row["vendor_lat"]) else None,
                "longitude": float(row["vendor_lng"]) if pd.notna(row["vendor_lng"]) else None,
                "type": "service_provider"
            }
            for _, row in relationships.iterrows()
        ]
        
        response = {
            "center": client,
            "related": vendors,
            "total_count": len(vendors)
        }
        
        if include_stats:
            response["stats"] = {
                "with_location": sum(1 for v in vendors if v["latitude"] and v["longitude"]),
                "with_logo": sum(1 for v in vendors if v["logo"])
            }
        
        return response
    except Exception as e:
        print(f"Error in get_client_relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
