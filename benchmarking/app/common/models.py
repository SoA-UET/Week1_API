"""
Shared models for all API benchmarking implementations
"""
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class User:
    """User data model"""
    id: int
    name: str
    email: str
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"]
        )

@dataclass
class UserCreate:
    """User creation model"""
    name: str
    email: str
    
    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email
        }

@dataclass
class UserUpdate:
    """User update model"""
    name: Optional[str] = None
    email: Optional[str] = None
    
    def to_dict(self):
        data = {}
        if self.name is not None:
            data["name"] = self.name
        if self.email is not None:
            data["email"] = self.email
        return data