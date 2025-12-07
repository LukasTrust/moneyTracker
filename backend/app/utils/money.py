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
    Handles both English and German number formats, including malformed formats.
    
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
        >>> normalize_amount("146,0,47")  # Malformed: should be 146,47
        Decimal('146.47')
    """
    if isinstance(value, (int, float, Decimal)):
        return to_decimal(value)
        
    value_str = str(value).strip()
    
    # Remove currency symbols
    value_str = value_str.replace('EUR', '').replace('€', '').replace('$', '').replace('USD', '').strip()
    
    # Handle malformed formats with mixed separators
    # Pattern 1: "146,0,47" or "146.0,47" (should be "146,47" or "146.47")
    # Pattern 2: "0.0,62" or "22.0,83" (should be "0.62" or "22.83")
    # Pattern 3: "0.000001" or "64.000008" (should be "0.01" or "64.08")
    # This appears when thousand separators are incorrectly replaced or when decimals have too many zeros
    
    import re
    
    # First, handle cases with extraneous zeros in decimal part: X.00000Y → X.0Y
    # e.g., "0.000001" → "0.01", "-64.000008" → "-64.08"
    match_zeros = re.match(r'^(-?\d+)\.0+(\d+)$', value_str)
    if match_zeros:
        integer_part = match_zeros.group(1)
        decimal_part = match_zeros.group(2)
        # Take the significant digits (last 2 non-zero or all if less than 2)
        # "000001" → "01", "000008" → "08"
        if len(decimal_part) >= 2:
            decimal_part = decimal_part[-2:]  # Last 2 digits
        else:
            decimal_part = decimal_part.zfill(2)  # Pad if only 1 digit
        value_str = f"{integer_part}.{decimal_part}"
    
    # Check for pattern X.0,Y or X,0,Y where Y is 1-2 digits
    # e.g., "146.0,47" → "146.47", "0.0,62" → "0.62"
    elif '.0,' in value_str or ',0,' in value_str:
        # Match: digits, then (.0, or ,0,), then 1-2 digits
        match = re.match(r'^(-?\d+)[.,]0[.,](\d{1,2})$', value_str)
        if match:
            integer_part = match.group(1)
            decimal_part = match.group(2).zfill(2)  # Pad to 2 digits
            value_str = f"{integer_part}.{decimal_part}"
    
    # Handle multiple commas (fallback if not caught by above)
    elif value_str.count(',') > 1:
        parts = value_str.split(',')
        if len(parts) >= 2:
            # Assume last comma is decimal separator if followed by 1-2 digits
            if len(parts[-1]) in [1, 2]:
                # Last part is likely decimal: rejoin all but last with empty string
                decimal_part = parts[-1].zfill(2)  # Pad to 2 digits
                value_str = ''.join(parts[:-1]) + '.' + decimal_part
            else:
                # Remove all commas as thousand separators
                value_str = value_str.replace(',', '')
    
    # Auto-detect format: German (1.234,56) vs English (1,234.56)
    if ',' in value_str and '.' in value_str:
        # Both separators present - determine which is decimal
        comma_pos = value_str.rindex(',')
        dot_pos = value_str.rindex('.')
        
        if comma_pos > dot_pos:
            # German format: 1.234,56 (comma is decimal separator)
            german_format = True
        else:
            # English format: 1,234.56 (dot is decimal separator)
            german_format = False
    
    # Process based on detected/specified format
    if german_format or (value_str.count(',') == 1 and '.' not in value_str):
        # German format or ambiguous single comma
        if ',' in value_str:
            parts = value_str.split(',')
            if len(parts) == 2 and len(parts[1]) in [1, 2]:
                # Likely German decimal: 1234,56 or 1.234,56
                return parse_german_amount(value_str)
        # Check if it has dots before comma (German thousands)
        if '.' in value_str and ',' in value_str:
            return parse_german_amount(value_str)
        
    # Handle English format (remove commas as thousand separators)
    if ',' in value_str and '.' in value_str:
        # English format confirmed: 1,234.56
        value_str = value_str.replace(',', '')
    elif ',' in value_str:
        # Single comma - could be thousands or decimal
        parts = value_str.split(',')
        if len(parts) == 2 and len(parts[1]) in [1, 2]:
            # Treat as German decimal
            value_str = value_str.replace(',', '.')
        else:
            # Treat as thousand separator
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
