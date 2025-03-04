from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import Optional, List, Dict, Any
import os
import json
from search import RelationshipSearch

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
csv_path = os.path.join(current_dir, 'data', 'vendor_client_relationships.csv')

# Initialize the search
search = RelationshipSearch(csv_path)

# Mount the static files directory
static_dir = os.path.join(current_dir, 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Cache for frequently accessed data
vendor_cache = {}
client_cache = {}

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
        clients = search.get_vendor_clients(vendor_name)
        if not clients:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        response = {
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
        vendors = search.get_client_vendors(client_name)
        if not vendors:
            raise HTTPException(status_code=404, detail="Client not found")
        
        response = {
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
