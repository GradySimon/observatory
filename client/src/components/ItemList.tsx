'use client'

import { useEffect } from 'react'
import { useItemStore } from '@/stores/itemStore'
import { apiClient } from '@/lib/api'

export default function ItemList() {
  const { items, loading, error, setItems, setLoading, setError, removeItem } = useItemStore()

  useEffect(() => {
    const fetchItems = async () => {
      setLoading(true)
      try {
        const fetchedItems = await apiClient.getItems()
        setItems(fetchedItems)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch items')
      } finally {
        setLoading(false)
      }
    }

    fetchItems()
  }, [setItems, setLoading, setError])

  const handleDelete = async (id: number) => {
    try {
      await apiClient.deleteItem(id)
      removeItem(id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete item')
    }
  }

  if (loading) return <div className="p-4">Loading...</div>
  if (error) return <div className="p-4 text-red-500">Error: {error}</div>

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Items</h1>
      <div className="grid gap-4">
        {items.map((item) => (
          <div key={item.id} className="border p-4 rounded-lg">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold">{item.name}</h3>
                {item.description && (
                  <p className="text-gray-600">{item.description}</p>
                )}
                <p className="text-xl font-bold text-green-600">${item.price}</p>
                <p className="text-sm text-gray-500">
                  Status: {item.is_active ? 'Active' : 'Inactive'}
                </p>
              </div>
              <button
                onClick={() => handleDelete(item.id)}
                className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}