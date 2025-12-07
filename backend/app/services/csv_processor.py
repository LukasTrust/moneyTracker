"""
CSV Processor - Handle CSV file parsing and data extraction
Audit reference: 01_backend_action_plan.md - P0 Money precision
"""
import pandas as pd
import chardet
from typing import List, Dict, Any, Tuple, Optional
from io import BytesIO
from datetime import datetime
import re
from decimal import Decimal

from ..utils.money import normalize_amount as normalize_amount_to_decimal
from ..utils import get_logger

logger = get_logger(__name__)


class CsvProcessor:
    """
    Service for processing CSV files
    """
    
    @staticmethod
    def detect_encoding(file_content: bytes) -> str:
        """
        Detect the encoding of a CSV file
        
        Args:
            file_content: Raw file content as bytes
            
        Returns:
            Detected encoding (e.g., 'utf-8', 'iso-8859-1')
        """
        result = chardet.detect(file_content)
        return result['encoding'] or 'utf-8'
    
    @staticmethod
    def parse_csv(file_content: bytes, encoding: str = None) -> pd.DataFrame:
        """
        Parse CSV file to DataFrame
        
        Args:
            file_content: Raw file content as bytes
            encoding: File encoding (auto-detected if None)
            
        Returns:
            Pandas DataFrame
            
        Raises:
            ValueError: If CSV parsing fails
        """
        if encoding is None:
            encoding = CsvProcessor.detect_encoding(file_content)
        
        try:
            # Try different separators
            for sep in [',', ';', '\t']:
                try:
                    df = pd.read_csv(
                        BytesIO(file_content),
                        encoding=encoding,
                        sep=sep,
                        decimal=',',  # German format
                        thousands='.',
                        dtype=str,  # Read everything as string initially
                        keep_default_na=False
                    )
                    
                    # Valid if we have at least 2 columns
                    if len(df.columns) >= 2:
                        return df
                except Exception:
                    continue
            
            raise ValueError("Could not parse CSV with any common separator")
            
        except Exception as e:
            raise ValueError(f"CSV parsing failed: {str(e)}")
    
    @staticmethod
    def get_headers(df: pd.DataFrame) -> List[str]:
        """
        Get column headers from DataFrame
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            List of column names
        """
        return df.columns.tolist()
    
    @staticmethod
    def get_sample_rows(df: pd.DataFrame, n: int = 5) -> List[List[Any]]:
        """
        Get first n rows as list of lists
        
        Args:
            df: Pandas DataFrame
            n: Number of rows to return
            
        Returns:
            List of rows (each row is a list of values)
        """
        return df.head(n).values.tolist()
    
    @staticmethod
    def apply_mappings(
        df: pd.DataFrame,
        mappings: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Apply header mappings and convert DataFrame to list of dicts.
        Intelligently detects date format across entire dataset for consistent parsing.
        
        Args:
            df: Pandas DataFrame
            mappings: Dictionary mapping CSV headers to standard fields
                     Example: {"Buchungstag": "date", "Betrag": "amount"}
        
        Returns:
            List of dictionaries with standardized field names
            
        Example:
            >>> df = pd.DataFrame({
            ...     "Buchungstag": ["2024-11-15", "2024-11-14"],
            ...     "Betrag": ["-42.50", "100.00"]
            ... })
            >>> mappings = {"Buchungstag": "date", "Betrag": "amount"}
            >>> apply_mappings(df, mappings)
            [
                {"date": "2024-11-15", "amount": "-42.50"},
                {"date": "2024-11-14", "amount": "100.00"}
            ]
        """
        result = []
        
        # Detect date format if 'date' field is mapped
        detected_date_format = None
        date_column = None
        
        for csv_header, standard_field in mappings.items():
            if standard_field == 'date' and csv_header in df.columns:
                date_column = csv_header
                # Extract all date values for format detection
                date_values = df[csv_header].tolist()
                detected_date_format = CsvProcessor.detect_date_format(date_values)
                break
        
        # Store detected format for logging/debugging
        if detected_date_format:
            logger.info(f"Detected date format for column '{date_column}': {detected_date_format}")
        
        for _, row in df.iterrows():
            mapped_row = {}
            for csv_header, standard_field in mappings.items():
                if csv_header in df.columns:
                    value = row[csv_header]
                    # Clean empty values
                    if pd.isna(value) or value == '':
                        value = None
                    mapped_row[standard_field] = value
            
            # Store detected format for later use in normalization
            if detected_date_format:
                mapped_row['_detected_date_format'] = detected_date_format
            
            result.append(mapped_row)
        
        return result
    
    @staticmethod
    def normalize_amount(amount_str: str) -> Decimal:
        """
        Normalize amount string to Decimal for precise monetary calculations.
        DEPRECATED: Use utils.money.normalize_amount directly.
        
        Args:
            amount_str: Amount as string (e.g., "-1.234,56" or "1,234.56")
            
        Returns:
            Decimal value
            
        Raises:
            ValueError: If amount cannot be parsed
            
        Example:
            >>> normalize_amount("-1.234,56")
            Decimal('-1234.56')
            >>> normalize_amount("1,234.56")
            Decimal('1234.56')
        """
        if not amount_str or amount_str == '':
            raise ValueError("Amount string is empty")
        
        # Remove whitespace
        amount_str = str(amount_str).strip()
        
        # Detect format (German: 1.234,56 or English: 1,234.56)
        # Use the centralized money utility
        try:
            # Heuristic: if both separators present, determine which is decimal
            if ',' in amount_str and '.' in amount_str:
                # German format if comma comes after dot: 1.234,56
                german_format = amount_str.rindex(',') > amount_str.rindex('.')
            else:
                # Auto-detect based on last separator
                german_format = ',' in amount_str
                
            return normalize_amount_to_decimal(amount_str, german_format=german_format)
        except ValueError as e:
            raise ValueError(f"Invalid amount format: {amount_str}") from e
    
    @staticmethod
    def detect_delimiter(file_content: bytes, encoding: str = None) -> str:
        """
        Detect the delimiter used in CSV file
        
        Args:
            file_content: Raw file content as bytes
            encoding: File encoding (auto-detected if None)
            
        Returns:
            Detected delimiter (';', ',', or '\t')
        """
        if encoding is None:
            encoding = CsvProcessor.detect_encoding(file_content)
        
        # Read first few lines
        try:
            sample = file_content[:1024].decode(encoding)
            lines = sample.split('\n')[:3]
            
            # Count delimiter occurrences
            delimiters = {',': 0, ';': 0, '\t': 0}
            for line in lines:
                for delim in delimiters:
                    delimiters[delim] += line.count(delim)
            
            # Return most common
            return max(delimiters, key=delimiters.get)
        except Exception:
            return ','
    
    @staticmethod
    def parse_csv_advanced(
        file_content: bytes,
        encoding: str = None,
        delimiter: str = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Parse CSV file with auto-detection and return DataFrame and delimiter
        
        Args:
            file_content: Raw file content as bytes
            encoding: File encoding (auto-detected if None)
            delimiter: CSV delimiter (auto-detected if None)
            
        Returns:
            Tuple of (DataFrame, detected_delimiter)
            
        Raises:
            ValueError: If CSV parsing fails
        """
        # Try detected encoding first, then fallbacks
        encodings_to_try = []
        detected = None
        if encoding is None:
            detected = CsvProcessor.detect_encoding(file_content)
        else:
            detected = encoding

        # Build list of sensible fallbacks
        if detected:
            encodings_to_try.append(detected)
        for enc in ("utf-8", "iso-8859-1", "cp1252"):
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)

        if delimiter is None:
            # Use detected delimiter based on initial encoding guess
            try:
                delimiter = CsvProcessor.detect_delimiter(file_content, encodings_to_try[0])
            except Exception:
                delimiter = ','

        # Try combinations of encodings and common delimiters
        delimiters_to_try = [delimiter, ',', ';', '\t']

        last_exc = None
        for enc in encodings_to_try:
            for delim in delimiters_to_try:
                try:
                    df = pd.read_csv(
                        BytesIO(file_content),
                        encoding=enc,
                        sep=delim,
                        decimal=',',
                        thousands='.',
                        dtype=str,
                        keep_default_na=False,
                        engine='python',
                        skip_blank_lines=True,
                        on_bad_lines='warn'
                    )

                    # Strip column names
                    df.columns = [str(c).strip() for c in df.columns]
                    
                    # Remove BOM (Byte Order Mark) from column names
                    df.columns = [c.replace('\ufeff', '').replace('ï»¿', '') for c in df.columns]

                    # Trim whitespace from string values (using map instead of deprecated applymap)
                    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

                    # Check if we have valid data
                    if len(df.columns) < 2:
                        # Try next delimiter/encoding
                        continue

                    if len(df) == 0:
                        raise ValueError("CSV file is empty")

                    return df, delim

                except Exception as e:
                    last_exc = e
                    continue

        # If we reach here, parsing failed for all attempts
        raise ValueError(f"CSV parsing failed: {str(last_exc)}")
    
    @staticmethod
    def get_preview_rows(df: pd.DataFrame, n: int = 20) -> List[Dict[str, Any]]:
        """
        Get first n rows as list of dictionaries
        
        Args:
            df: Pandas DataFrame
            n: Number of rows to return
            
        Returns:
            List of row dictionaries with row_number included
        """
        result = []
        for idx, row in df.head(n).iterrows():
            row_dict = {
                'row_number': int(idx) + 1,
                'data': {col: (str(val) if pd.notna(val) and val != '' else None) 
                        for col, val in row.items()}
            }
            result.append(row_dict)
        return result
    
    @staticmethod
    def apply_mappings_advanced(
        df: pd.DataFrame,
        mapping: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Apply advanced mapping configuration to DataFrame
        
        Args:
            df: Pandas DataFrame
            mapping: Dictionary with field_name -> csv_header
                    Example: {"date": "Buchungstag", "amount": "Betrag", ...}
        
        Returns:
            List of dictionaries with standardized field names
        """
        result = []
        
        # Reverse mapping for easier lookup
        csv_to_field = {v: k for k, v in mapping.items() if v is not None}
        
        for idx, row in df.iterrows():
            mapped_row = {}
            
            for csv_header in df.columns:
                if csv_header in csv_to_field:
                    field_name = csv_to_field[csv_header]
                    value = row[csv_header]
                    
                    # Clean empty values
                    if pd.isna(value) or value == '':
                        value = None
                    
                    mapped_row[field_name] = value
            
            # Only add row if it has at least date and amount
            if mapped_row.get('date') and mapped_row.get('amount'):
                result.append(mapped_row)
        
        return result
    
    @staticmethod
    def detect_date_format(date_strings: List[str]) -> Optional[str]:
        """
        Intelligently detect the date format by analyzing all dates in the CSV.
        This ensures consistent parsing across the entire file.
        
        Args:
            date_strings: List of date strings from the CSV
            
        Returns:
            The detected format string or None if no format fits all dates
            
        Strategy:
            1. For ambiguous formats (e.g., 1/2/2025 could be DD/MM or MM/DD),
               we look at the entire dataset to find entries that disambiguate
            2. We test each format and only accept it if ALL dates can be parsed
            3. Priority is given to formats that make chronological sense
        """
        if not date_strings:
            return None
        
        # Clean and filter empty strings
        clean_dates = [d.strip() for d in date_strings if d and str(d).strip()]
        if not clean_dates:
            return None
        
        # Define candidate formats with priority
        # Order matters: more specific formats first
        candidate_formats = [
            '%d.%m.%Y',      # 31.12.2024 (German/European - unambiguous with dots)
            '%d.%m.%y',      # 31.12.24
            '%Y-%m-%d',      # 2024-12-31 (ISO - unambiguous with year first)
            '%d/%m/%Y',      # 31/12/2024 (European with slashes)
            '%d/%m/%y',      # 31/12/24
            '%m/%d/%Y',      # 12/31/2024 (US with slashes)
            '%m/%d/%y',      # 12/31/24
            '%d-%m-%Y',      # 31-12-2024 (European with dashes)
            '%d-%m-%y',      # 31-12-24
            '%m-%d-%Y',      # 12-31-2024 (US with dashes)
            '%m-%d-%y',      # 12-31-24
            '%Y/%m/%d',      # 2024/12/31 (ISO with slashes)
            '%Y.%m.%d',      # 2024.12.31 (ISO with dots)
            '%d.%m.%Y %H:%M',  # 31.12.2024 14:30
            '%Y-%m-%d %H:%M:%S',  # 2024-12-31 14:30:00
        ]
        
        # Test each format to see if it parses ALL dates consistently
        for fmt in candidate_formats:
            parsed_dates = []
            all_valid = True
            
            for date_str in clean_dates:
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    parsed_dates.append(parsed)
                except ValueError:
                    all_valid = False
                    break
            
            # If all dates parsed successfully with this format, it's our winner
            if all_valid and parsed_dates:
                # Additional validation: check if dates are reasonable
                # (e.g., not all in the far future or distant past)
                current_year = datetime.now().year
                reasonable = all(1950 <= d.year <= current_year + 10 for d in parsed_dates)
                
                if reasonable:
                    return fmt
        
        # Fallback: Try flexible manual parsing for formats like "1/2/2025"
        # We'll attempt to disambiguate DD/MM vs MM/DD by looking for values > 12
        if all('/' in d for d in clean_dates):
            # Check if any date has a part > 12, which tells us which part is day
            has_day_gt_12 = False
            position_of_day = None  # 0 for first position, 1 for second
            
            for date_str in clean_dates:
                parts = date_str.split('/')
                if len(parts) == 3:
                    try:
                        first = int(parts[0])
                        second = int(parts[1])
                        
                        # If first part > 12, it must be day (DD/MM format)
                        if first > 12:
                            has_day_gt_12 = True
                            position_of_day = 0
                            break
                        # If second part > 12, it must be day (MM/DD format)
                        elif second > 12:
                            has_day_gt_12 = True
                            position_of_day = 1
                            break
                    except ValueError:
                        continue
            
            # If we found a disambiguating date, use that format for all
            if has_day_gt_12:
                if position_of_day == 0:
                    return 'DD/MM'  # Custom marker for European format
                else:
                    return 'MM/DD'  # Custom marker for US format
        
        # Same for dash-separated dates
        if all('-' in d for d in clean_dates):
            # Skip if it looks like ISO format (YYYY-MM-DD)
            first_date = clean_dates[0].split('-')
            if len(first_date) == 3 and len(first_date[0]) == 4:
                return None  # Should have been caught by '%Y-%m-%d' above
            
            has_day_gt_12 = False
            position_of_day = None
            
            for date_str in clean_dates:
                parts = date_str.split('-')
                if len(parts) == 3:
                    try:
                        first = int(parts[0])
                        second = int(parts[1])
                        
                        if first > 12:
                            has_day_gt_12 = True
                            position_of_day = 0
                            break
                        elif second > 12:
                            has_day_gt_12 = True
                            position_of_day = 1
                            break
                    except ValueError:
                        continue
            
            if has_day_gt_12:
                if position_of_day == 0:
                    return 'DD-MM'  # Custom marker
                else:
                    return 'MM-DD'  # Custom marker
        
        return None
    
    @staticmethod
    def parse_date(date_str: str, date_format: Optional[str] = None) -> Optional[datetime]:
        """
        Parse date string with optional format hint for consistent parsing.
        
        Args:
            date_str: Date string in various formats
            date_format: Optional format hint from detect_date_format()
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_str or date_str == '':
            return None
        
        date_str_clean = date_str.strip()
        
        # If we have a specific format hint, use it
        if date_format:
            # Handle custom markers for ambiguous formats
            if date_format == 'DD/MM':
                parts = date_str_clean.split('/')
                if len(parts) == 3:
                    try:
                        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                        if year < 100:
                            year = 2000 + year if year <= 50 else 1900 + year
                        return datetime(year, month, day)
                    except (ValueError, IndexError):
                        pass
            
            elif date_format == 'MM/DD':
                parts = date_str_clean.split('/')
                if len(parts) == 3:
                    try:
                        month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                        if year < 100:
                            year = 2000 + year if year <= 50 else 1900 + year
                        return datetime(year, month, day)
                    except (ValueError, IndexError):
                        pass
            
            elif date_format == 'DD-MM':
                parts = date_str_clean.split('-')
                if len(parts) == 3:
                    try:
                        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                        if year < 100:
                            year = 2000 + year if year <= 50 else 1900 + year
                        return datetime(year, month, day)
                    except (ValueError, IndexError):
                        pass
            
            elif date_format == 'MM-DD':
                parts = date_str_clean.split('-')
                if len(parts) == 3:
                    try:
                        month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                        if year < 100:
                            year = 2000 + year if year <= 50 else 1900 + year
                        return datetime(year, month, day)
                    except (ValueError, IndexError):
                        pass
            
            else:
                # Standard format string
                try:
                    return datetime.strptime(date_str_clean, date_format)
                except ValueError:
                    pass
        
        # Fallback to old behavior if no format hint or parsing failed
        # Common date formats (ordered by likelihood)
        formats = [
            '%d.%m.%Y',      # 31.12.2024
            '%d.%m.%y',      # 31.12.24
            '%Y-%m-%d',      # 2024-12-31
            '%d/%m/%Y',      # 31/12/2024
            '%d-%m-%Y',      # 31-12-2024
            '%Y/%m/%d',      # 2024/12/31
            '%m/%d/%Y',      # 12/31/2024
            '%m/%d/%y',      # 12/31/24
            '%m-%d-%Y',      # 12-31-2024
            '%m-%d-%y',      # 12-31-24
            '%d.%m.%Y %H:%M',  # 31.12.2024 14:30
            '%Y-%m-%d %H:%M:%S',  # 2024-12-31 14:30:00
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str_clean, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def normalize_transaction_data(
        row: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize and validate transaction data (3 required + 2 optional fields)
        Uses Decimal for amount precision and respects detected date format.
        
        Args:
            row: Raw transaction data with mapped fields (date, amount, recipient, purpose?, saldo?)
                 May contain '_detected_date_format' key for consistent parsing
            
        Returns:
            Normalized transaction data with 3-5 fields (amount and saldo as Decimal)
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        normalized = {}
        
        # Extract detected date format if available
        detected_format = row.get('_detected_date_format')
        
        # Parse date with detected format for consistency
        date_str = row.get('date')
        if not date_str:
            raise ValueError("Date field is required")
        
        date_obj = CsvProcessor.parse_date(date_str, date_format=detected_format)
        if not date_obj:
            raise ValueError(f"Invalid date format: {date_str}")
        
        normalized['date'] = date_obj.isoformat()
        
        # Parse amount to Decimal
        amount_str = row.get('amount')
        if not amount_str:
            raise ValueError("Amount field is required")
        
        try:
            amount = CsvProcessor.normalize_amount(str(amount_str))
            normalized['amount'] = amount  # Keep as Decimal
        except Exception as e:
            raise ValueError(f"Invalid amount format: {amount_str}") from e
        
        # Recipient (required)
        recipient = str(row.get('recipient', '')).strip()
        if not recipient:
            raise ValueError("Recipient field is required")
        
        normalized['recipient'] = recipient
        
        # Purpose (optional)
        purpose = str(row.get('purpose', '')).strip() if row.get('purpose') else ''
        if purpose:
            normalized['purpose'] = purpose
        
        # Saldo (optional)
        saldo_str = row.get('saldo')
        if saldo_str:
            try:
                saldo = CsvProcessor.normalize_amount(str(saldo_str))
                normalized['saldo'] = saldo  # Keep as Decimal
            except Exception as e:
                # Log warning but don't fail import if saldo is invalid
                logger.warning(f"Invalid saldo format: {saldo_str}, skipping saldo for this row")
        
        return normalized

