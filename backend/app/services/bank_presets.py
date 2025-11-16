"""
Bank Presets - Vorkonfigurierte CSV-Mappings für deutsche Banken

Dieses Modul enthält vordefinierte Mappings für die wichtigsten deutschen Banken,
um den CSV-Import zu vereinfachen.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class BankPreset:
    """
    Bank-Preset mit Mapping-Konfiguration
    """
    id: str
    name: str
    description: str
    mapping: Dict[str, str]  # standard_field -> csv_header
    header_patterns: List[str]  # Patterns zur Auto-Erkennung
    delimiter: str = ';'
    decimal: str = ','
    date_format: str = 'DD.MM.YYYY'


# Deutsche Bank-Presets
BANK_PRESETS: Dict[str, BankPreset] = {
    'sparkasse': BankPreset(
        id='sparkasse',
        name='Sparkasse',
        description='Sparkassen-Finanzgruppe (CSV-Export)',
        mapping={
            'date': 'Buchungstag',
            'amount': 'Betrag',
            'recipient': 'Empfänger/Zahlungspflichtiger',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Buchungstag',
            'Empfänger/Zahlungspflichtiger',
            'Kontonummer',
            'BLZ',
        ],
        delimiter=';',
        decimal=',',
    ),
    
    'dkb': BankPreset(
        id='dkb',
        name='DKB (Deutsche Kreditbank)',
        description='DKB Cash - Girokonto',
        mapping={
            'date': 'Wertstellung',
            'amount': 'Betrag (EUR)',
            'recipient': 'Auftraggeber / Begünstigter',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Wertstellung',
            'Betrag (EUR)',
            'Auftraggeber / Begünstigter',
            'Buchungstext',
        ],
        delimiter=';',
        decimal=',',
    ),
    
    'ing': BankPreset(
        id='ing',
        name='ING (ING-DiBa)',
        description='ING Girokonto',
        mapping={
            'date': 'Buchung',
            'amount': 'Betrag',
            'recipient': 'Empfänger/Auftraggeber',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Buchung',
            'Valuta',
            'Empfänger/Auftraggeber',
            'Verwendungszweck',
        ],
        delimiter=';',
        decimal=',',
    ),
    
    'commerzbank': BankPreset(
        id='commerzbank',
        name='Commerzbank',
        description='Commerzbank Girokonto',
        mapping={
            'date': 'Buchungstag',
            'amount': 'Umsatz in EUR',
            'recipient': 'Empfänger / Auftraggeber',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Buchungstag',
            'Wertstellung',
            'Umsatz in EUR',
            'Empfänger / Auftraggeber',
        ],
        delimiter=';',
        decimal=',',
    ),
    
    'volksbank': BankPreset(
        id='volksbank',
        name='Volksbank / Raiffeisenbank',
        description='Volksbanken Raiffeisenbanken',
        mapping={
            'date': 'Buchungstag',
            'amount': 'Betrag',
            'recipient': 'Empfänger/Auftraggeber',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Buchungstag',
            'Valuta',
            'Empfänger/Auftraggeber',
            'Verwendungszweck',
        ],
        delimiter=';',
        decimal=',',
    ),
    
    'postbank': BankPreset(
        id='postbank',
        name='Postbank',
        description='Postbank Girokonto',
        mapping={
            'date': 'Buchungstag',
            'amount': 'Betrag (EUR)',
            'recipient': 'Empfänger',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Buchungstag',
            'Wertstellung',
            'Betrag (EUR)',
            'Empfänger',
        ],
        delimiter=';',
        decimal=',',
    ),
    
    'n26': BankPreset(
        id='n26',
        name='N26',
        description='N26 Bank (CSV-Export)',
        mapping={
            'date': 'Date',
            'amount': 'Amount (EUR)',
            'recipient': 'Payee',
            'purpose': 'Payment reference',
        },
        header_patterns=[
            'Date',
            'Amount (EUR)',
            'Payee',
            'Payment reference',
            'Account number',
        ],
        delimiter=',',  # N26 uses comma
        decimal='.',    # N26 uses dot
        date_format='YYYY-MM-DD',
    ),
    
    'comdirect': BankPreset(
        id='comdirect',
        name='comdirect',
        description='comdirect Girokonto',
        mapping={
            'date': 'Buchungstag',
            'amount': 'Umsatz in EUR',
            'recipient': 'Empfänger / Zahlungspflichtiger',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Buchungstag',
            'Wertstellung (Valuta)',
            'Umsatz in EUR',
            'Empfänger / Zahlungspflichtiger',
        ],
        delimiter=';',
        decimal=',',
    ),
    
    'deutsche_bank': BankPreset(
        id='deutsche_bank',
        name='Deutsche Bank',
        description='Deutsche Bank Girokonto',
        mapping={
            'date': 'Buchungstag',
            'amount': 'Betrag (EUR)',
            'recipient': 'Begünstigter / Auftraggeber',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Buchungstag',
            'Wert',
            'Betrag (EUR)',
            'Begünstigter / Auftraggeber',
        ],
        delimiter=';',
        decimal=',',
    ),
    
    'santander': BankPreset(
        id='santander',
        name='Santander',
        description='Santander Consumer Bank',
        mapping={
            'date': 'Buchungsdatum',
            'amount': 'Betrag',
            'recipient': 'Empfänger/Auftraggeber',
            'purpose': 'Verwendungszweck',
        },
        header_patterns=[
            'Buchungsdatum',
            'Valutadatum',
            'Betrag',
            'Empfänger/Auftraggeber',
        ],
        delimiter=';',
        decimal=',',
    ),
}


class BankPresetMatcher:
    """
    Service zur Erkennung der Bank anhand CSV-Header
    """
    
    @staticmethod
    def detect_bank(csv_headers: List[str]) -> Optional[str]:
        """
        Erkenne Bank anhand der CSV-Header
        
        Args:
            csv_headers: Liste der CSV-Spalten-Namen
            
        Returns:
            Bank-ID wenn erkannt, sonst None
            
        Example:
            >>> headers = ['Buchungstag', 'Betrag', 'Empfänger/Zahlungspflichtiger']
            >>> detect_bank(headers)
            'sparkasse'
        """
        csv_headers_lower = [h.lower() for h in csv_headers]
        
        best_match = None
        best_score = 0
        
        for bank_id, preset in BANK_PRESETS.items():
            # Zähle wie viele Pattern-Header im CSV vorhanden sind
            matches = sum(
                1 for pattern in preset.header_patterns
                if any(pattern.lower() in header for header in csv_headers_lower)
            )
            
            # Score: Prozentsatz der gematchten Patterns
            score = matches / len(preset.header_patterns)
            
            # Minimum 60% Match erforderlich
            if score > best_score and score >= 0.6:
                best_score = score
                best_match = bank_id
        
        return best_match
    
    @staticmethod
    def get_preset(bank_id: str) -> Optional[BankPreset]:
        """
        Hole Preset für eine Bank
        
        Args:
            bank_id: Bank-ID (z.B. 'sparkasse', 'dkb')
            
        Returns:
            BankPreset wenn gefunden, sonst None
        """
        return BANK_PRESETS.get(bank_id)
    
    @staticmethod
    def get_all_presets() -> List[BankPreset]:
        """
        Hole alle verfügbaren Bank-Presets
        
        Returns:
            Liste aller BankPreset-Objekte
        """
        return list(BANK_PRESETS.values())
    
    @staticmethod
    def get_preset_names() -> Dict[str, str]:
        """
        Hole Namen aller Banken für Dropdown
        
        Returns:
            Dictionary mit bank_id -> bank_name
        """
        return {
            bank_id: preset.name
            for bank_id, preset in BANK_PRESETS.items()
        }
