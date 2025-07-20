from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from chat import chat_with_law_agent
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from auth import (
    User, UserCreate, UserResponse, Token,
    get_db, get_password_hash, verify_password,
    create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
import logging

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    text: str

class ChatResponse(BaseModel):
    id: str
    text: str
    isUser: bool
    timestamp: datetime

@app.post("/api/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email exists
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Check if username exists
        if db.query(User).filter(User.username == user.username).first():
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Create new user
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=get_password_hash(user.password)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/signin", response_model=Token)
async def signin(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Find user by username
        user = db.query(User).filter(User.email == username).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        if not message.text:
            raise HTTPException(status_code=400, detail="Message text cannot be empty")
            
        logger.info(f"Processing chat message: {message.text[:100]}...")  # Log only first 100 chars
        response_text = await chat_with_law_agent(message.text)
        
        if not response_text:
            raise HTTPException(status_code=500, detail="Received empty response from law agent")
            
        return ChatResponse(
            id=str(int(datetime.now().timestamp() * 1000)),
            text=response_text,
            isUser=False,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
