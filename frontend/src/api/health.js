import { request } from './request'

const getHealth = () => {
  return request('/health')
}

export { getHealth }
