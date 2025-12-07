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
    # Patterns are ordered by specificity - more specific patterns first
    FIELD_PATTERNS = {
        'date': [
            # Most specific first
            'buchungstag', 'buchungsdatum', 'transaktionsdatum',
            'valutadatum', 'wertstellungsdatum',
            'buchung', 'datum', 'date', 'valuta', 'wertstellung',
            'transaction.*date', 'booking.*date', 'value.*date'
        ],
        'amount': [
            # Most specific first
            'betrag', 'transaktionsbetrag', 'buchungsbetrag',
            'amount', 'umsatz', 'wert', 'value', 'summe',
            'sum', 'total'
        ],
        'recipient': [
            # Most specific first - prefer Empfänger/Auftraggeber over generic names
            'empfänger', 'empfaenger', 'auftraggeber', 
            'begünstigter', 'beguenstigter', 
            'sender', 'zahler', 'absender',
            'recipient', 'payee', 'payer', 'from', 'to',
            'kontoinhaber', 'account.*holder',
            'gegenpartei', 'counterparty', 'partei', 'party',
            'auftraggeber.*name', 'empfänger.*name',
            'name'  # Generic, lower priority
        ],
        'purpose': [
            # Most specific first
            'verwendungszweck', 'verwendungstext',
            'verwendung', 'zweck', 'purpose', 
            'buchungsdetails',
            'beschreibung', 'description', 'details',
            'notiz', 'note', 'memo', 'reference', 'ref',
            'buchungstext', 'transaktionstext',  # Lower priority - could be description or purpose
            'text'  # Generic, lowest priority
        ],
        'saldo': [
            # Most specific first
            'saldo', 'kontostand', 'balance', 'account.*balance',
            'stand', 'bestand', 'guthaben', 'kontosaldo',
            'balance.*after', 'saldo.*nach'
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
            Prioritizes exact/high-confidence matches first
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
        
        # Sort by score descending (highest confidence first)
        # This ensures best matches are prioritized in suggestions
        matches.sort(key=lambda x: (-x[1], x[0]))  # Sort by score desc, then name asc
        return matches
    
    @classmethod
    def _calculate_match_score(cls, header: str, patterns: List[str]) -> float:
        """
        Calculate match score between header and patterns
        Patterns are ordered by specificity - earlier patterns get higher scores
        
        Returns:
            Score between 0.0 and 1.0
        """
        header_lower = header.lower().strip()
        max_score = 0.0
        
        for idx, pattern in enumerate(patterns):
            # Specificity bonus: earlier patterns (more specific) get higher scores
            # This ensures "Verwendungszweck" beats "Text"
            specificity_bonus = 1.0 - (idx * 0.01)  # Small penalty for later patterns
            specificity_bonus = max(0.85, specificity_bonus)  # Min 0.85
            
            # Exact match
            if header_lower == pattern.lower():
                return 1.0 * specificity_bonus
            
            # Check if pattern is regex
            if '.*' in pattern or '\\' in pattern:
                if re.search(pattern, header_lower, re.IGNORECASE):
                    max_score = max(max_score, 0.95 * specificity_bonus)
                continue
            
            # Check if pattern is substring
            if pattern.lower() in header_lower:
                # Full word match is better than partial
                if re.search(r'\b' + re.escape(pattern.lower()) + r'\b', header_lower):
                    max_score = max(max_score, 0.90 * specificity_bonus)
                else:
                    max_score = max(max_score, 0.75 * specificity_bonus)
                continue
            
            # Fuzzy string matching
            similarity = SequenceMatcher(None, header_lower, pattern.lower()).ratio()
            if similarity > 0.6:
                max_score = max(max_score, similarity * 0.8 * specificity_bonus)
        
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
