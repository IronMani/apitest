from fastapi import FastAPI, Depends, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timedelta
import secrets
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from motor.motor_asyncio import AsyncIOMotorClient

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
verification_collection = db["verification_codes"]

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME = "jayakumarmanikandan27@gmail.com",
    MAIL_PASSWORD = "tfapirhjicxbkyau",
    MAIL_FROM = "jayakumarmanikandan27@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.example.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True
)

# Model for the verification request
class VerificationRequest(BaseModel):
    email: str

@app.post("/send_verification")
async def send_verification(request: VerificationRequest):
    # Generate a random verification code
    verification_code = secrets.token_hex(8)
    expiration_time = datetime.utcnow() + timedelta(minutes=5)

    # Store the code and expiration time in the database
    await verification_collection.insert_one({
        "email": request.email,
        "code": verification_code,
        "expires_at": expiration_time
    })

    # Send the verification code via email
    message = MessageSchema(
        subject="Your Verification Code",
        recipients=[request.email],
        body=f"Your verification code is {verification_code}. It expires in 5 minutes.",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message": "Verification code sent"}

@app.post("/verify_code")
async def verify_code(email: str, code: str):
    # Find the verification code in the database
    record = await verification_collection.find_one({"email": email, "code": code})

    if not record:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Check if the code has expired
    if datetime.utcnow() > record["expires_at"]:
        raise HTTPException(status_code=400, detail="Verification code has expired")

    # Mark the user as verified (you can update the user's document here)
    await verification_collection.delete_one({"_id": record["_id"]})  # Clean up

    return {"message": "User verified successfully"}
