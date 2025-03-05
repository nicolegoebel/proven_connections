from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import pandas as pd
import os

# Load environment variables
load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load data
vendor_client_df = pd.read_csv("data/vendor_client_relationships.csv")
vendor_details_df = pd.read_csv("data/vendor_details.csv")

# Normalize column names in vendor_details_df
vendor_details_df.columns = vendor_details_df.columns.str.lower()

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/config/map")
async def get_map_config():
    return {
        "accessToken": os.getenv("MAPBOX_ACCESS_TOKEN"),
        "style": "mapbox://styles/mapbox/light-v11",
        "center": [-95.7129, 37.0902],  # Center of USA
        "zoom": 3
    }

@app.get("/api/search/vendors")
async def search_vendors(q: str = ""):
    if not q:
        return {"results": []}
    
    try:
        # Get unique vendors and their details from relationships
        mask = vendor_client_df["vendor_name"].str.contains(q, case=False, na=False)
        vendor_details = vendor_client_df[mask].drop_duplicates("vendor_name")
        
        # Convert to list of dicts
        results = [
            {
                "name": row["vendor_name"],
                "domain": row["vendor_domain"],
                "latitude": float(row["vendor_lat"]) if pd.notna(row["vendor_lat"]) else None,
                "longitude": float(row["vendor_lng"]) if pd.notna(row["vendor_lng"]) else None
            }
            for _, row in vendor_details.iterrows()
        ]
        
        return {"results": results}
    except Exception as e:
        print(f"Error in search_vendors: {str(e)}")
        return {"results": []}

@app.get("/api/search/clients")
async def search_clients(q: str = ""):
    if not q:
        return {"results": []}
    
    try:
        # Get unique clients and their details from relationships
        mask = vendor_client_df["client_name"].str.contains(q, case=False, na=False)
        client_details = vendor_client_df[mask].drop_duplicates("client_name")
        
        # Convert to list of dicts
        results = [
            {
                "name": row["client_name"],
                "domain": row["client_domain"],
                "latitude": float(row["client_lat"]) if pd.notna(row["client_lat"]) else None,
                "longitude": float(row["client_lng"]) if pd.notna(row["client_lng"]) else None
            }
            for _, row in client_details.iterrows()
        ]
        
        return {"results": results}
    except Exception as e:
        print(f"Error in search_clients: {str(e)}")
        return {"results": []}

@app.get("/api/relationships/vendor/{vendor_name}")
async def get_vendor_relationships(vendor_name: str):
    try:
        # Get all clients for this vendor
        relationships = vendor_client_df[
            vendor_client_df["vendor_name"] == vendor_name
        ]
        
        if relationships.empty:
            return {"center": None, "related": []}
        
        # Get first relationship for vendor details
        vendor_row = relationships.iloc[0]
        
        # Create vendor object
        vendor = {
            "name": vendor_name,
            "domain": vendor_row["vendor_domain"],
            "latitude": float(vendor_row["vendor_lat"]) if pd.notna(vendor_row["vendor_lat"]) else None,
            "longitude": float(vendor_row["vendor_lng"]) if pd.notna(vendor_row["vendor_lng"]) else None
        }
        
        # Get all related clients
        clients = [
            {
                "name": row["client_name"],
                "domain": row["client_domain"],
                "latitude": float(row["client_lat"]) if pd.notna(row["client_lat"]) else None,
                "longitude": float(row["client_lng"]) if pd.notna(row["client_lng"]) else None
            }
            for _, row in relationships.iterrows()
        ]
        
        return {
            "center": vendor,
            "related": clients
        }
    except Exception as e:
        print(f"Error in get_vendor_relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/relationships/client/{client_name}")
async def get_client_relationships(client_name: str):
    try:
        # Get all vendors for this client
        relationships = vendor_client_df[
            vendor_client_df["client_name"] == client_name
        ]
        
        if relationships.empty:
            return {"center": None, "related": []}
        
        # Get first relationship for client details
        client_row = relationships.iloc[0]
        
        # Create client object
        client = {
            "name": client_name,
            "domain": client_row["client_domain"],
            "latitude": float(client_row["client_lat"]) if pd.notna(client_row["client_lat"]) else None,
            "longitude": float(client_row["client_lng"]) if pd.notna(client_row["client_lng"]) else None
        }
        
        # Get all related vendors
        vendors = []
        for _, row in relationships.iterrows():
            vendors.append({
                "name": row["vendor_name"],
                "domain": row["vendor_domain"],
                "latitude": float(row["vendor_lat"]) if pd.notna(row["vendor_lat"]) else None,
                "longitude": float(row["vendor_lng"]) if pd.notna(row["vendor_lng"]) else None
            })
        
        return {
            "center": client,
            "related": vendors
        }
    except Exception as e:
        print(f"Error in get_client_relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
