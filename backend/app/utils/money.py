"""
Money handling utilities for precise decimal operations.
Audit reference: 01_backend_action_plan.md - P0 Money precision
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Union, Optional
import json


# Standard quantization for currency (2 decimal places)
CURRENCY_QUANTIZE = Decimal('0.01')


def to_decimal(value: Union[str, int, float, Decimal, None]) -> Optional[Decimal]:
    """
    Convert various numeric types to Decimal safely.
    
    Args:
        value: Numeric value to convert (string, int, float, Decimal, or None)
        
    Returns:
        Decimal value or None if input is None
        
    Raises:
        ValueError: If value cannot be converted to Decimal
        
    Examples:
        >>> to_decimal("123.45")
        Decimal('123.45')
        >>> to_decimal(123.45)
        Decimal('123.45')
        >>> to_decimal(None)
        None
    """
    if value is None:
        return None
        
    if isinstance(value, Decimal):
        return value
        
    try:
        # Convert to string first to avoid float precision issues
        if isinstance(value, float):
            # Use string conversion to preserve precision
            return Decimal(str(value))
        return Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Cannot convert {value!r} to Decimal: {e}")


def quantize_amount(value: Union[str, int, float, Decimal, None], 
                   places: Decimal = CURRENCY_QUANTIZE) -> Optional[Decimal]:
    """
    Quantize a monetary amount to standard currency precision.
    
    Args:
        value: Numeric value to quantize
        places: Decimal precision template (default: 0.01 for 2 decimal places)
        
    Returns:
        Quantized Decimal or None if input is None
        
    Examples:
        >>> quantize_amount("123.456")
        Decimal('123.46')
        >>> quantize_amount(123.456)
        Decimal('123.46')
    """
    decimal_value = to_decimal(value)
    if decimal_value is None:
        return None
    return decimal_value.quantize(places, rounding=ROUND_HALF_UP)


def format_amount(value: Union[str, int, float, Decimal, None], 
                 currency_symbol: str = "€") -> str:
    """
    Format a monetary amount for display.
    
    Args:
        value: Numeric value to format
        currency_symbol: Currency symbol to append
        
    Returns:
        Formatted string (e.g., "123.45 €")
        
    Examples:
        >>> format_amount(123.456)
        '123.46 €'
        >>> format_amount(None)
        '0.00 €'
    """
    quantized = quantize_amount(value) or Decimal('0.00')
    return f"{quantized} {currency_symbol}"


def parse_german_amount(value: str) -> Decimal:
    """
    Parse German-formatted monetary amounts (comma as decimal separator).
    
    Args:
        value: String with German number format (e.g., "1.234,56" or "1234,56")
        
    Returns:
        Decimal value
        
    Examples:
        >>> parse_german_amount("1.234,56")
        Decimal('1234.56')
        >>> parse_german_amount("1234,56")
        Decimal('1234.56')
    """
    if not isinstance(value, str):
        return to_decimal(value)
        
    # Remove thousand separators (dots) and replace comma with dot
    cleaned = value.replace('.', '').replace(',', '.')
    return to_decimal(cleaned)


def normalize_amount(value: Union[str, int, float], german_format: bool = False) -> Decimal:
    """
    Normalize various amount formats to Decimal.
    Handles both English and German number formats.
    
    Args:
        value: Amount in various formats
        german_format: If True, treat commas as decimal separators
        
    Returns:
        Normalized Decimal value
        
    Raises:
        ValueError: If value cannot be parsed
        
    Examples:
        >>> normalize_amount("1,234.56")
        Decimal('1234.56')
        >>> normalize_amount("1.234,56", german_format=True)
        Decimal('1234.56')
    """
    if isinstance(value, (int, float, Decimal)):
        return to_decimal(value)
        
    value_str = str(value).strip()
    
    # Auto-detect German format (comma as decimal separator)
    if ',' in value_str and german_format:
        return parse_german_amount(value_str)
        
    # Handle English format (remove commas as thousand separators)
    if ',' in value_str and '.' in value_str:
        # English format: 1,234.56
        value_str = value_str.replace(',', '')
    elif ',' in value_str:
        # Could be German format without thousand separators: 1234,56
        # or large number with comma separators: 1,234
        # Heuristic: if comma is followed by exactly 2 digits at end, treat as decimal
        if value_str.count(',') == 1 and value_str.endswith(value_str.split(',')[1]) and len(value_str.split(',')[1]) == 2:
            return parse_german_amount(value_str)
        else:
            value_str = value_str.replace(',', '')
            
    return to_decimal(value_str)


class DecimalEncoder(json.JSONEncoder):
    """
    JSON encoder that safely serializes Decimal values as strings.
    Use with json.dumps(..., cls=DecimalEncoder) or configure globally.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Return as string to preserve precision
            return str(obj)
        return super().default(obj)


def decimal_to_json_safe(value: Union[Decimal, None]) -> Union[str, None]:
    """
    Convert Decimal to JSON-safe string representation.
    
    Args:
        value: Decimal value or None
        
    Returns:
        String representation or None
        
    Examples:
        >>> decimal_to_json_safe(Decimal('123.45'))
        '123.45'
        >>> decimal_to_json_safe(None)
        None
    """
    if value is None:
        return None
    return str(quantize_amount(value))
