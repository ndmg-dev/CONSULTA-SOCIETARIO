import axios from 'axios'
import { cleanCnpj } from './cnpj'

/**
 * Axios instance — base URL empty so Vite proxy handles /api routes
 */
const api = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Lookup CNPJ company data + partners
 * @param {string} cnpj - raw or formatted CNPJ
 * @returns {Promise} API response data
 */
export async function lookupCnpj(cnpj) {
  const cleaned = cleanCnpj(cnpj)
  const response = await api.get(`/api/cnpj/${cleaned}`)
  return response.data
}

/**
 * Get ownership tree for a CNPJ
 * @param {string} cnpj - raw or formatted CNPJ
 * @returns {Promise} API response data
 */
export async function getOwnershipTree(cnpj) {
  const cleaned = cleanCnpj(cnpj)
  const response = await api.get(`/api/cnpj/${cleaned}/ownership`)
  return response.data
}

export default api
