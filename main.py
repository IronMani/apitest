from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId

# MongoDB connection string
connection_string = "mongodb+srv://jayakumarmanikandan27:sNJHldRA14jB0iXd@cluster0.ggasj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(connection_string)
db = client['college']
collection = db['attendence']

app = FastAPI()

# Helper function to convert ObjectId to string
def item_helper(item) -> dict:
    return {
        "id": str(item["_id"]),
        "name": item["name"],
        "age": item["age"],
        "city": item["city"]
    }

# Pydantic model for the data
class Item(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    age: int
    city: str

#Home page
@app.get("/")
def read_root():
    return{"Hello":"World"}


# CREATE: Add a new item
@app.post("/items/", response_model=Item)
def create_item(item: Item):
    result = collection.insert_one(item.dict(by_alias=True, exclude={"id"}))
    item.id = str(result.inserted_id)
    return item

# READ: Get all items
@app.get("/items/", response_model=List[Item])
def read_items():
    items = list(collection.find())
    return [item_helper(item) for item in items]

# READ: Get an item by name
@app.get("/items/{name}", response_model=Item)
def read_item(name: str):
    item = collection.find_one({"name": name})
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_helper(item)

# UPDATE: Update an item
@app.put("/items/{name}", response_model=Item)
def update_item(name: str, item: Item):
    result = collection.update_one({"name": name}, {"$set": item.dict(by_alias=True, exclude={"id"})})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# DELETE: Delete an item
@app.delete("/items/{name}", response_model=dict)
def delete_item(name: str):
    result = collection.delete_one({"name": name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": "Item deleted"}

# Run the server with: uvicorn main:app --reload
