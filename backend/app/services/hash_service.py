"""
Hash Service - Generate unique hashes for transactions
"""
import hashlib
import json
from typing import Dict, Any


class HashService:
    """
    Service for generating SHA256 hashes for duplicate detection
    """
    
    @staticmethod
    def generate_hash(data: Dict[str, Any]) -> str:
        """
        Generate SHA256 hash from transaction data
        
        Args:
            data: Dictionary containing transaction data
            
        Returns:
            SHA256 hash as hex string
            
        Example:
            >>> data = {"date": "2024-11-15", "amount": "-42.50", "recipient": "REWE"}
            >>> hash_service.generate_hash(data)
            '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
        """
        # Sort keys to ensure consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        
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
