import { request } from './request'

const getHealth = () => {
  request('/health')  
}

export { getHealth }