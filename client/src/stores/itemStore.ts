import { create } from 'zustand'

export interface Item {
  id: number
  name: string
  description?: string
  price: number
  is_active: boolean
}

interface ItemState {
  items: Item[]
  loading: boolean
  error: string | null
  setItems: (items: Item[]) => void
  addItem: (item: Item) => void
  updateItem: (id: number, item: Partial<Item>) => void
  removeItem: (id: number) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useItemStore = create<ItemState>((set) => ({
  items: [],
  loading: false,
  error: null,
  setItems: (items) => set({ items }),
  addItem: (item) => set((state) => ({ items: [...state.items, item] })),
  updateItem: (id, updatedItem) =>
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, ...updatedItem } : item
      ),
    })),
  removeItem: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
    })),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))