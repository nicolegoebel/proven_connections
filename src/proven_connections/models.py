from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Association table for the many-to-many relationship between clients and vendors
client_vendor_association = Table(
    'client_vendor_association',
    Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id')),
    Column('vendor_id', Integer, ForeignKey('vendors.id'))
)

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    
    # Relationship to vendors
    vendors = relationship(
        "Vendor",
        secondary=client_vendor_association,
        back_populates="clients"
    )

class Vendor(Base):
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    service_type = Column(String)
    
    # Relationship to clients
    clients = relationship(
        "Client",
        secondary=client_vendor_association,
        back_populates="vendors"
    )
