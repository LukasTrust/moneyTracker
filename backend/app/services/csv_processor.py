"""
CSV Processor - Handle CSV file parsing and data extraction
"""
import pandas as pd
import chardet
from typing import List, Dict, Any, Tuple, Optional
from io import BytesIO
from datetime import datetime
import re


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
        Apply header mappings and convert DataFrame to list of dicts
        
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
        
        for _, row in df.iterrows():
            mapped_row = {}
            for csv_header, standard_field in mappings.items():
                if csv_header in df.columns:
                    value = row[csv_header]
                    # Clean empty values
                    if pd.isna(value) or value == '':
                        value = None
                    mapped_row[standard_field] = value
            
            result.append(mapped_row)
        
        return result
    
    @staticmethod
    def normalize_amount(amount_str: str) -> float:
        """
        Normalize amount string to float
        
        Args:
            amount_str: Amount as string (e.g., "-1.234,56" or "1,234.56")
            
        Returns:
            Float value
            
        Example:
            >>> normalize_amount("-1.234,56")
            -1234.56
            >>> normalize_amount("1,234.56")
            1234.56
        """
        if not amount_str or amount_str == '':
            return 0.0
        
        # Remove whitespace
        amount_str = amount_str.strip()
        
        # Detect format (German: 1.234,56 or English: 1,234.56)
        if ',' in amount_str and '.' in amount_str:
            # Both present - determine which is decimal separator
            if amount_str.rindex(',') > amount_str.rindex('.'):
                # German format: 1.234,56
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                # English format: 1,234.56
                amount_str = amount_str.replace(',', '')
        elif ',' in amount_str:
            # Only comma - could be decimal or thousand separator
            # Assume decimal if only one comma and it's near the end
            parts = amount_str.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                amount_str = amount_str.replace(',', '.')
            else:
                amount_str = amount_str.replace(',', '')
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
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

                    # Trim whitespace from string values
                    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

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
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        Parse date string with multiple format support
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_str or date_str == '':
            return None
        
        # Common date formats
        formats = [
            '%d.%m.%Y',      # 31.12.2024
            '%d.%m.%y',      # 31.12.24
            '%Y-%m-%d',      # 2024-12-31
            '%d/%m/%Y',      # 31/12/2024
            '%d-%m-%Y',      # 31-12-2024
            '%Y/%m/%d',      # 2024/12/31
            '%d.%m.%Y %H:%M',  # 31.12.2024 14:30
            '%Y-%m-%d %H:%M:%S',  # 2024-12-31 14:30:00
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def normalize_transaction_data(
        row: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize and validate transaction data (3 required + 1 optional field)
        
        Args:
            row: Raw transaction data with mapped fields (date, amount, recipient, purpose?)
            
        Returns:
            Normalized transaction data with 3-4 fields
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        normalized = {}
        
        # Parse date
        date_str = row.get('date')
        if not date_str:
            raise ValueError("Date field is required")
        
        date_obj = CsvProcessor.parse_date(date_str)
        if not date_obj:
            raise ValueError(f"Invalid date format: {date_str}")
        
        normalized['date'] = date_obj.isoformat()
        
        # Parse amount
        amount_str = row.get('amount')
        if not amount_str:
            raise ValueError("Amount field is required")
        
        try:
            amount = CsvProcessor.normalize_amount(str(amount_str))
            normalized['amount'] = amount
        except Exception as e:
            raise ValueError(f"Invalid amount format: {amount_str}")
        
        # Recipient (required)
        recipient = str(row.get('recipient', '')).strip()
        if not recipient:
            raise ValueError("Recipient field is required")
        
        normalized['recipient'] = recipient
        
        # Purpose (optional)
        purpose = str(row.get('purpose', '')).strip() if row.get('purpose') else ''
        if purpose:
            normalized['purpose'] = purpose
        
        return normalized

