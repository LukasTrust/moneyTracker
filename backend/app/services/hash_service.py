"""
Hash Service - Generate unique hashes for transactions
Audit reference: 05_backend_services.md - Stable hash generation with Decimal normalization
"""
import hashlib
import json
from typing import Dict, Any
from decimal import Decimal


class HashService:
    """
    Service for generating SHA256 hashes for duplicate detection.
    Normalizes Decimal values to ensure consistent hashing.
    """
    
    @staticmethod
    def _normalize_for_hash(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize data values for consistent hashing.
        Converts Decimal to normalized string representation.
        
        Args:
            data: Dictionary containing transaction data
            
        Returns:
            Normalized dictionary safe for JSON serialization
        """
        normalized = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                # Normalize Decimal and convert to string
                normalized[key] = str(value.normalize())
            elif isinstance(value, float):
                # Format floats consistently (legacy support)
                normalized[key] = f"{value:.2f}"
            else:
                normalized[key] = value
        return normalized
    
    @staticmethod
    def generate_hash(data: Dict[str, Any]) -> str:
        """
        Generate SHA256 hash from transaction data with proper normalization.
        
        Args:
            data: Dictionary containing transaction data
            
        Returns:
            SHA256 hash as hex string
            
        Example:
            >>> data = {"date": "2024-11-15", "amount": Decimal("-42.50"), "recipient": "REWE"}
            >>> hash_service.generate_hash(data)
            '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
        """
        # Normalize values (especially Decimal) before hashing
        normalized = HashService._normalize_for_hash(data)
        
        # Sort keys to ensure consistent hashing
        sorted_data = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
        
        # Generate SHA256 hash
        hash_object = hashlib.sha256(sorted_data.encode('utf-8'))
        return hash_object.hexdigest()
    
    @staticmethod
    def is_duplicate(hash_value: str, existing_hashes: set) -> bool:
        """
        Check if a hash already exists
        
        Args:
            hash_value: Hash to check
            existing_hashes: Set of existing hashes
            
        Returns:
            True if duplicate, False otherwise
        """
        return hash_value in existing_hashes
