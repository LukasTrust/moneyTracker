/**
 * Money/Amount Utilities
 * Handles conversion and formatting of monetary values
 * 
 * Backend uses Decimal and serializes as strings ("123.45")
 * Frontend must parse strings and format for display
 * 
 * Audit reference: 09_frontend_action_plan.md - P0 Money handling
 */

/**
 * Parse amount from various formats to number
 * Handles: strings, numbers, German format (1.234,56), English format (1,234.56)
 * 
 * @param {string|number} value - Amount to parse
 * @returns {number} Parsed amount as float
 * @throws {Error} If value cannot be parsed
 */
export function parseAmount(value) {
  if (value === null || value === undefined || value === '') {
    return 0;
  }

  // Already a number
  if (typeof value === 'number') {
    return value;
  }

  // Convert to string and trim
  const str = String(value).trim();
  
  if (str === '') {
    return 0;
  }

  // Detect German format (comma as decimal separator)
  // Examples: "1.234,56" or "1234,56"
  const isGermanFormat = /^\d{1,3}(\.\d{3})*(,\d{1,2})?$/.test(str);
  
  if (isGermanFormat) {
    // Remove thousands separators (.) and replace comma with dot
    const normalized = str.replace(/\./g, '').replace(',', '.');
    const parsed = parseFloat(normalized);
    
    if (isNaN(parsed)) {
      throw new Error(`Invalid amount: ${value}`);
    }
    
    return parsed;
  }

  // Detect English format (dot as decimal separator)
  // Examples: "1,234.56" or "1234.56"
  const isEnglishFormat = /^\d{1,3}(,\d{3})*(\.\d{1,2})?$/.test(str);
  
  if (isEnglishFormat) {
    // Remove thousands separators (,)
    const normalized = str.replace(/,/g, '');
    const parsed = parseFloat(normalized);
    
    if (isNaN(parsed)) {
      throw new Error(`Invalid amount: ${value}`);
    }
    
    return parsed;
  }

  // Try simple parsing for other formats
  const parsed = parseFloat(str);
  
  if (isNaN(parsed)) {
    throw new Error(`Invalid amount: ${value}`);
  }
  
  return parsed;
}

/**
 * Format amount for display with currency symbol
 * 
 * @param {string|number} value - Amount to format
 * @param {string} currency - Currency symbol (default: '€')
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted amount with currency
 */
export function formatAmount(value, currency = '€', decimals = 2) {
  try {
    const amount = parseAmount(value);
    
    // Use German locale for formatting (1.234,56 €)
    const formatted = new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(amount);
    
    return `${formatted} ${currency}`;
  } catch (error) {
    console.warn('Failed to format amount:', value, error);
    return `${value} ${currency}`;
  }
}

/**
 * Format amount without currency symbol
 * Useful for input fields
 * 
 * @param {string|number} value - Amount to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted amount
 */
export function formatAmountPlain(value, decimals = 2) {
  try {
    const amount = parseAmount(value);
    
    return new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(amount);
  } catch (error) {
    console.warn('Failed to format amount:', value, error);
    return String(value);
  }
}

/**
 * Round amount to specified decimal places
 * 
 * @param {string|number} value - Amount to round
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {number} Rounded amount
 */
export function roundAmount(value, decimals = 2) {
  const amount = parseAmount(value);
  const multiplier = Math.pow(10, decimals);
  return Math.round(amount * multiplier) / multiplier;
}

/**
 * Convert amount to API format (string with 2 decimals)
 * Backend expects Decimal as string: "123.45"
 * 
 * @param {string|number} value - Amount to convert
 * @returns {string} Amount as string with 2 decimals
 */
export function toApiAmount(value) {
  const amount = parseAmount(value);
  return amount.toFixed(2);
}

/**
 * Check if amount is positive
 * 
 * @param {string|number} value - Amount to check
 * @returns {boolean} True if amount > 0
 */
export function isPositiveAmount(value) {
  try {
    return parseAmount(value) > 0;
  } catch {
    return false;
  }
}

/**
 * Check if amount is negative
 * 
 * @param {string|number} value - Amount to check
 * @returns {boolean} True if amount < 0
 */
export function isNegativeAmount(value) {
  try {
    return parseAmount(value) < 0;
  } catch {
    return false;
  }
}

/**
 * Calculate sum of amounts
 * 
 * @param {Array<string|number>} amounts - Amounts to sum
 * @returns {number} Sum of all amounts
 */
export function sumAmounts(amounts) {
  return amounts.reduce((sum, amount) => {
    try {
      return sum + parseAmount(amount);
    } catch {
      console.warn('Skipping invalid amount in sum:', amount);
      return sum;
    }
  }, 0);
}

/**
 * Format amount with color based on positive/negative
 * Returns object with formatted text and color class
 * 
 * @param {string|number} value - Amount to format
 * @param {string} currency - Currency symbol (default: '€')
 * @returns {{text: string, color: string}} Formatted amount and color class
 */
export function formatAmountWithColor(value, currency = '€') {
  const amount = parseAmount(value);
  const formatted = formatAmount(value, currency);
  
  return {
    text: formatted,
    color: amount > 0 ? 'text-green-600' : amount < 0 ? 'text-red-600' : 'text-gray-600'
  };
}

/**
 * Validate amount input
 * 
 * @param {string} value - Input value to validate
 * @returns {{valid: boolean, error?: string}} Validation result
 */
export function validateAmount(value) {
  if (!value || value.trim() === '') {
    return { valid: false, error: 'Amount is required' };
  }
  
  try {
    const amount = parseAmount(value);
    
    if (!isFinite(amount)) {
      return { valid: false, error: 'Amount must be a finite number' };
    }
    
    return { valid: true };
  } catch (error) {
    return { valid: false, error: error.message };
  }
}
