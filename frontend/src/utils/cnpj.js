/**
 * CNPJ utility functions
 * Formatting, cleaning, and validation with check digit algorithm
 */

/**
 * Format a digits-only string as XX.XXX.XXX/XXXX-XX
 * @param {string} value - raw input (may contain non-digits)
 * @returns {string} formatted CNPJ
 */
export function formatCnpj(value) {
  const digits = (value || '').replace(/\D/g, '').slice(0, 14)
  const len = digits.length

  if (len <= 2) return digits
  if (len <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`
  if (len <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`
  if (len <= 12) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`
}

/**
 * Strip all non-digit characters
 * @param {string} value
 * @returns {string} digits only
 */
export function cleanCnpj(value) {
  return (value || '').replace(/\D/g, '')
}

/**
 * Validate CNPJ check digits using the standard modulo-11 algorithm
 * @param {string} value - CNPJ (formatted or raw digits)
 * @returns {boolean} true if valid
 */
export function validateCnpj(value) {
  const digits = cleanCnpj(value)

  if (digits.length !== 14) return false

  // Reject all-same-digit CNPJs (e.g., 00000000000000)
  if (/^(\d)\1{13}$/.test(digits)) return false

  const numbers = digits.split('').map(Number)

  // First check digit
  const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  let sum1 = 0
  for (let i = 0; i < 12; i++) {
    sum1 += numbers[i] * weights1[i]
  }
  const remainder1 = sum1 % 11
  const check1 = remainder1 < 2 ? 0 : 11 - remainder1

  if (numbers[12] !== check1) return false

  // Second check digit
  const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  let sum2 = 0
  for (let i = 0; i < 13; i++) {
    sum2 += numbers[i] * weights2[i]
  }
  const remainder2 = sum2 % 11
  const check2 = remainder2 < 2 ? 0 : 11 - remainder2

  if (numbers[13] !== check2) return false

  return true
}

/**
 * Check if value has exactly 14 digits after cleaning
 * @param {string} value
 * @returns {boolean}
 */
export function isCnpj(value) {
  const digits = cleanCnpj(value)
  return digits.length === 14
}

/**
 * Compute the two CNPJ check digits for a 12-digit base.
 * @param {string} base12
 * @returns {string} two-digit string
 */
function cnpjCheckDigits(base12) {
  const calc = (nums) => {
    let sum = 0
    for (let i = 0; i < nums.length; i++) {
      const weight = ((nums.length - 1 - i) % 8) + 2
      sum += Number(nums[i]) * weight
    }
    const remainder = sum % 11
    return remainder < 2 ? '0' : String(11 - remainder)
  }
  const d1 = calc(base12)
  const d2 = calc(base12 + d1)
  return d1 + d2
}

/**
 * Complete an 8-digit CNPJ root into the full matriz CNPJ (/0001 + check digits).
 * BrasilAPI returns only the root for PJ partners.
 * @param {string} base - 8-digit root (may contain non-digits)
 * @returns {string|null} 14-digit CNPJ, or null if base is not 8 digits
 */
export function completeCnpjBase(base) {
  const digits = cleanCnpj(base)
  if (digits.length !== 8) return null
  const base12 = `${digits}0001`
  return base12 + cnpjCheckDigits(base12)
}
