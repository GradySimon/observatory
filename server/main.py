from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Observatory API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    is_active: bool = True

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    is_active: bool = True

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None

items_db: List[Item] = [
    Item(id=1, name="Laptop", description="Gaming laptop", price=1299.99),
    Item(id=2, name="Mouse", description="Wireless mouse", price=59.99),
]

@app.get("/")
async def root():
    return {"message": "Observatory API"}

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    return {"error": "Item not found"}

@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    new_id = max([i.id for i in items_db]) + 1 if items_db else 1
    new_item = Item(id=new_id, **item.model_dump())
    items_db.append(new_item)
    return new_item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item_update: ItemUpdate):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            update_data = item_update.model_dump(exclude_unset=True)
            updated_item = item.model_copy(update=update_data)
            items_db[i] = updated_item
            return updated_item
    return {"error": "Item not found"}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            items_db.pop(i)
            return {"message": "Item deleted"}
    return {"error": "Item not found"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)