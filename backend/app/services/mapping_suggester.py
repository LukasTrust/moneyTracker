"""
Mapping Suggester Service - Intelligente Vorschläge für CSV-Header-Mapping
"""
from typing import Dict, List, Tuple, Optional
import re
from difflib import SequenceMatcher


class MappingSuggester:
    """
    Service to suggest CSV header mappings based on common patterns
    
    Uses fuzzy string matching and keyword detection to suggest
    which CSV headers should map to which standard fields.
    """
    
    # Keyword patterns for field detection (lowercase)
    FIELD_PATTERNS = {
        'date': [
            'datum', 'date', 'buchung', 'valuta', 'wertstellung',
            'transaction.*date', 'booking.*date', 'value.*date'
        ],
        'amount': [
            'betrag', 'amount', 'umsatz', 'wert', 'value', 'summe',
            'sum', 'total', 'saldo', 'balance'
        ],
        'recipient': [
            # Patterns for sender/recipient name
            'empfänger', 'empfaenger', 'recipient',
            'beguenstigter', 'payee', 'to',
            'sender', 'auftraggeber', 'zahler', 'payer', 'from',
            'absender', 'kontoinhaber', 'account.*holder',
            'gegenpartei', 'counterparty', 'partei', 'party',
            'name', 'auftraggeber.*name', 'empfänger.*name'
        ],
        'purpose': [
            # Patterns for purpose/description/usage
            'verwendungszweck', 'verwendung', 'zweck',
            'purpose', 'beschreibung', 'description', 'text',
            'buchungstext', 'transaktionstext', 'details',
            'notiz', 'note', 'memo', 'reference', 'ref',
            'verwendungstext', 'buchungsdetails'
        ]
    }
    
    @classmethod
    def suggest_mappings(
        cls,
        csv_headers: List[str],
        required_fields: List[str] = None
    ) -> Dict[str, Tuple[Optional[str], float, List[str]]]:
        """
        Suggest mappings for CSV headers to standard fields
        
        Args:
            csv_headers: List of CSV column headers
            required_fields: List of required field names to map (default: date, amount, recipient, purpose)
            
        Returns:
            Dict with field_name as key and tuple of:
            - suggested_header (or None if no good match)
            - confidence score (0.0 - 1.0)
            - list of alternative suggestions
        """
        if required_fields is None:
            required_fields = ['date', 'amount', 'recipient', 'purpose']
        
        suggestions = {}
        used_headers = set()
        
        # Sort fields by priority (required first)
        all_fields = required_fields + [
            f for f in cls.FIELD_PATTERNS.keys() 
            if f not in required_fields
        ]
        
        for field_name in all_fields:
            matches = cls._find_matches_for_field(
                field_name,
                csv_headers,
                used_headers
            )
            
            if matches:
                best_match = matches[0]
                alternatives = [m[0] for m in matches[1:4]]  # Top 3 alternatives
                
                suggestions[field_name] = (
                    best_match[0],  # header name
                    best_match[1],  # confidence
                    alternatives
                )
                
                # Mark best match as used (to avoid duplicate assignments)
                if best_match[1] > 0.7:  # Only mark if confidence is high
                    used_headers.add(best_match[0])
            else:
                suggestions[field_name] = (None, 0.0, [])
        
        return suggestions
    
    @classmethod
    def _find_matches_for_field(
        cls,
        field_name: str,
        csv_headers: List[str],
        exclude_headers: set = None
    ) -> List[Tuple[str, float]]:
        """
        Find best matching CSV headers for a given field
        
        Returns:
            List of tuples (header_name, confidence_score) sorted by score
        """
        if exclude_headers is None:
            exclude_headers = set()
        
        patterns = cls.FIELD_PATTERNS.get(field_name, [])
        matches = []
        
        for header in csv_headers:
            if header in exclude_headers:
                continue
            
            score = cls._calculate_match_score(header, patterns)
            if score > 0.0:
                matches.append((header, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    @classmethod
    def _calculate_match_score(cls, header: str, patterns: List[str]) -> float:
        """
        Calculate match score between header and patterns
        
        Returns:
            Score between 0.0 and 1.0
        """
        header_lower = header.lower().strip()
        max_score = 0.0
        
        for pattern in patterns:
            # Exact match
            if header_lower == pattern.lower():
                return 1.0
            
            # Check if pattern is regex
            if '.*' in pattern or '\\' in pattern:
                if re.search(pattern, header_lower, re.IGNORECASE):
                    max_score = max(max_score, 0.9)
                continue
            
            # Check if pattern is substring
            if pattern.lower() in header_lower:
                # Full word match is better than partial
                if re.search(r'\b' + re.escape(pattern.lower()) + r'\b', header_lower):
                    max_score = max(max_score, 0.85)
                else:
                    max_score = max(max_score, 0.7)
                continue
            
            # Fuzzy string matching
            similarity = SequenceMatcher(None, header_lower, pattern.lower()).ratio()
            if similarity > 0.6:
                max_score = max(max_score, similarity * 0.8)
        
        return max_score
    
    @classmethod
    def validate_mapping(
        cls,
        mapping: Dict[str, str],
        csv_headers: List[str],
        required_fields: List[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate that mapping is complete and correct
        
        Args:
            mapping: Dict mapping field_name -> csv_header
            csv_headers: Available CSV headers
            required_fields: Required field names
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if required_fields is None:
            required_fields = ['date', 'amount', 'recipient']
        
        errors = []
        
        # Check required fields are present
        for field in required_fields:
            if field not in mapping or not mapping[field]:
                errors.append(f"Required field '{field}' is not mapped")
        
        # Check all mapped headers exist in CSV
        for field_name, csv_header in mapping.items():
            if csv_header and csv_header not in csv_headers:
                errors.append(
                    f"Mapped header '{csv_header}' for field '{field_name}' "
                    f"not found in CSV headers"
                )
        
        # Check for duplicate mappings
        used_headers = {}
        for field_name, csv_header in mapping.items():
            if not csv_header:
                continue
            if csv_header in used_headers:
                errors.append(
                    f"CSV header '{csv_header}' is mapped to both "
                    f"'{used_headers[csv_header]}' and '{field_name}'"
                )
            else:
                used_headers[csv_header] = field_name
        
        return len(errors) == 0, errors
