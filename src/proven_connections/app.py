from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import Optional, List, Dict, Any
import os
import json
import logging
from proven_connections.search import RelationshipSearch
from proven_connections.config import MAPBOX_ACCESS_TOKEN, DEFAULT_MAP_STYLE, DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Proven Connections Search")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your Webflow domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Get the absolute path to the data directory
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
csv_path = os.path.join(current_dir, 'data', 'vendor_client_relationships_11Mar2025.csv')

# Initialize the search
logging.info(f"Loading relationship data from: {csv_path}")
search = RelationshipSearch(csv_path)

# Mount the static files directory
static_dir = os.path.join(current_dir, 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Cache for frequently accessed data
vendor_cache = {}
client_cache = {}

@app.get("/api/config/map")
async def get_map_config():
    """Get Mapbox configuration settings."""
    return {
        "accessToken": MAPBOX_ACCESS_TOKEN,
        "style": DEFAULT_MAP_STYLE,
        "center": DEFAULT_MAP_CENTER,
        "zoom": DEFAULT_MAP_ZOOM
    }

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    with open(os.path.join(static_dir, 'index.html'), 'r') as f:
        return f.read()

@app.get("/api/search/vendors")
async def search_vendors(q: str, limit: Optional[int] = 10):
    """Search for vendors by name prefix with caching."""
    cache_key = f"vendor_search_{q}_{limit}"
    if cache_key in vendor_cache:
        return vendor_cache[cache_key]
    
    results = search.search_vendors(q, limit)
    vendor_cache[cache_key] = results
    return results

@app.get("/api/search/clients")
async def search_clients(q: str, limit: Optional[int] = 10):
    """Search for clients by name prefix with caching."""
    cache_key = f"client_search_{q}_{limit}"
    if cache_key in client_cache:
        return client_cache[cache_key]
    
    results = search.search_clients(q, limit)
    client_cache[cache_key] = results
    return results

@app.get("/api/vendor/{vendor_name}/clients")
async def get_vendor_clients(vendor_name: str, include_stats: bool = False):
    """Get all clients for a specific vendor with optional statistics."""
    try:
        # Get vendor details and clients
        vendor_details = search.get_vendor_details(vendor_name)
        if not vendor_details:
            raise HTTPException(status_code=404, detail="Vendor not found")
            
        clients = search.get_vendor_clients(vendor_name)
        
        response = {
            "vendor_name": vendor_name,
            "vendor_domain": vendor_details.get("domain"),
            "vendor_latitude": vendor_details.get("latitude"),
            "vendor_longitude": vendor_details.get("longitude"),
            "clients": clients,
            "total_count": len(clients)
        }
        
        if include_stats:
            response["stats"] = {
                "with_location": sum(1 for c in clients if c["latitude"] and c["longitude"]),
                "with_logo": sum(1 for c in clients if c["logo"])
            }
        
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/client/{client_name}/vendors")
async def get_client_vendors(client_name: str, include_stats: bool = False):
    """Get all vendors for a specific client with optional statistics."""
    try:
        # Get client details and vendors
        client_details = search.get_client_details(client_name)
        if not client_details:
            raise HTTPException(status_code=404, detail="Client not found")
            
        vendors = search.get_client_vendors(client_name)
        
        response = {
            "client_name": client_name,
            "client_domain": client_details.get("domain"),
            "client_latitude": client_details.get("latitude"),
            "client_longitude": client_details.get("longitude"),
            "vendors": vendors,
            "total_count": len(vendors)
        }
        
        if include_stats:
            response["stats"] = {
                "with_location": sum(1 for v in vendors if v["latitude"] and v["longitude"]),
                "with_logo": sum(1 for v in vendors if v["logo"])
            }
        
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get overall statistics about the dataset."""
    try:
        return {
            "total_vendors": len(search.vendors),
            "total_clients": len(search.clients),
            "total_relationships": len(search.df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
