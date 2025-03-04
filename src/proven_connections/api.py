from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from .database import Database

app = FastAPI(title="Proven Connections API")
db = Database()

class ClientResponse(BaseModel):
    id: int
    name: str
    email: str

class VendorResponse(BaseModel):
    id: int
    name: str
    email: str
    service_type: str

@app.get("/clients/{client_id}/vendors", response_model=List[VendorResponse])
async def get_client_vendors(client_id: int):
    """Get all vendors associated with a specific client."""
    vendors = db.get_client_vendors(client_id)
    if not vendors:
        raise HTTPException(status_code=404, detail="Client not found or has no vendors")
    return vendors

@app.get("/vendors/{vendor_id}/clients", response_model=List[ClientResponse])
async def get_vendor_clients(vendor_id: int):
    """Get all clients associated with a specific vendor."""
    clients = db.get_vendor_clients(vendor_id)
    if not clients:
        raise HTTPException(status_code=404, detail="Vendor not found or has no clients")
    return clients

@app.post("/relationships/client-vendor")
async def create_relationship(client_id: int, vendor_id: int):
    """Create a new relationship between a client and a vendor."""
    success = db.add_client_vendor_relationship(client_id, vendor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client or vendor not found")
    return {"message": "Relationship created successfully"}
