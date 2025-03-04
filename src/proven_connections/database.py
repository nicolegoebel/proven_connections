from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import List
from .models import Base, Client, Vendor

class Database:
    def __init__(self, db_url: str = "sqlite:///./proven_connections.db"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        
    def get_client_vendors(self, client_id: int) -> List[Vendor]:
        """Get all vendors associated with a specific client."""
        with self.SessionLocal() as session:
            client = session.query(Client).filter(Client.id == client_id).first()
            return client.vendors if client else []
            
    def get_vendor_clients(self, vendor_id: int) -> List[Client]:
        """Get all clients associated with a specific vendor."""
        with self.SessionLocal() as session:
            vendor = session.query(Vendor).filter(Vendor.id == vendor_id).first()
            return vendor.clients if vendor else []
            
    def add_client_vendor_relationship(self, client_id: int, vendor_id: int) -> bool:
        """Add a relationship between a client and a vendor."""
        with self.SessionLocal() as session:
            client = session.query(Client).filter(Client.id == client_id).first()
            vendor = session.query(Vendor).filter(Vendor.id == vendor_id).first()
            
            if client and vendor:
                client.vendors.append(vendor)
                session.commit()
                return True
            return False
