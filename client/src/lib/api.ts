import { Item } from '@/stores/itemStore'

const API_BASE_URL = 'http://localhost:8000'

export interface ItemCreate {
  name: string
  description?: string
  price: number
  is_active?: boolean
}

export interface ItemUpdate {
  name?: string
  description?: string
  price?: number
  is_active?: boolean
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async getItems(): Promise<Item[]> {
    return this.request<Item[]>('/items')
  }

  async getItem(id: number): Promise<Item> {
    return this.request<Item>(`/items/${id}`)
  }

  async createItem(item: ItemCreate): Promise<Item> {
    return this.request<Item>('/items', {
      method: 'POST',
      body: JSON.stringify(item),
    })
  }

  async updateItem(id: number, item: ItemUpdate): Promise<Item> {
    return this.request<Item>(`/items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(item),
    })
  }

  async deleteItem(id: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/items/${id}`, {
      method: 'DELETE',
    })
  }
}

export const apiClient = new ApiClient(API_BASE_URL)