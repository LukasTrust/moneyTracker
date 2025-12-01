"""
Category Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class CategoryMappings(BaseModel):
    """Schema for category mappings - simplified to pattern list"""
    patterns: List[str] = Field(default_factory=list, description="List of patterns for matching (words/phrases)")


class CategoryBase(BaseModel):
    """Base schema for Category"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    icon: Optional[str] = Field(None, max_length=10, description="Emoji or icon identifier")
    mappings: CategoryMappings = Field(default_factory=lambda: CategoryMappings(), description="Mapping rules")


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = Field(None, max_length=10)
    mappings: Optional[CategoryMappings] = None


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
