from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os

# Configuración de la base de datos Neon
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tabla de asociación para la relación many-to-many entre tweets y colecciones
tweet_collections = Table(
    'tweet_collections',
    Base.metadata,
    Column('tweet_id', Integer, ForeignKey('tweets.id')),
    Column('collection_id', Integer, ForeignKey('collections.id'))
)

# Modelos de base de datos
class Tweet(Base):
    __tablename__ = "tweets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('neon_auth.users_sync.id'))
    content = Column(Text)
    media_path = Column(String)
    media_type = Column(String)  # 'image' or 'video'
    is_thread = Column(Boolean, default=False)
    thread_tweets_json = Column(Text)  # JSON string para tweets del hilo
    scheduled_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    collections = relationship("Collection", secondary=tweet_collections, back_populates="tweets")

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    user_id = Column(String, ForeignKey('neon_auth.users_sync.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    tweets = relationship("Tweet", secondary=tweet_collections, back_populates="collections")

# Modelos Pydantic
class ThreadTweet(BaseModel):
    content: str
    media_path: Optional[str] = ""
    media_type: Optional[str] = ""

class TweetCreate(BaseModel):
    user_id: str
    content: Optional[str] = ""
    media_path: Optional[str] = ""
    media_type: Optional[str] = ""
    is_thread: bool = False
    thread_tweets: Optional[List[ThreadTweet]] = []
    collection_ids: Optional[List[int]] = []
    scheduled_date: Optional[datetime] = None

class TweetUpdate(BaseModel):
    content: Optional[str] = None
    media_path: Optional[str] = None
    media_type: Optional[str] = None
    is_thread: Optional[bool] = None
    thread_tweets: Optional[List[ThreadTweet]] = None
    collection_ids: Optional[List[int]] = None
    scheduled_date: Optional[datetime] = None

class TweetScheduleUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    user_id: str

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CollectionResponse(BaseModel):
    id: int
    name: str
    description: str
    user_id: str
    tweet_count: int
    created_at: datetime

class TweetResponse(BaseModel):
    id: int
    user_id: str
    content: str
    media_path: str
    media_type: str
    is_thread: bool
    thread_tweets: Optional[List[ThreadTweet]] = []
    scheduled_date: Optional[datetime] = None
    created_at: datetime
    collections: List[CollectionResponse] = []

# Crear la aplicación FastAPI
app = FastAPI(title="Twitter Organizer API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints de Tweets
@app.post("/tweets", response_model=TweetResponse)
def create_tweet(tweet: TweetCreate, db: Session = Depends(get_db)):
    db_tweet = Tweet(
        user_id=tweet.user_id,
        content=tweet.content,
        media_path=tweet.media_path,
        media_type=tweet.media_type,
        is_thread=tweet.is_thread,
        thread_tweets_json=json.dumps([t.dict() for t in tweet.thread_tweets]) if tweet.thread_tweets else "[]",
        scheduled_date=tweet.scheduled_date
    )
    
    db.add(db_tweet)
    db.commit()
    db.refresh(db_tweet)
    
    # Agregar colecciones
    if tweet.collection_ids:
        collections = db.query(Collection).filter(Collection.id.in_(tweet.collection_ids)).all()
        db_tweet.collections = collections
        db.commit()
    
    return format_tweet_response(db_tweet, db)

@app.get("/tweets", response_model=List[TweetResponse])
def get_tweets(user_id: str, db: Session = Depends(get_db)):
    tweets = db.query(Tweet).filter(Tweet.user_id == user_id).order_by(Tweet.created_at.desc()).all()
    return [format_tweet_response(tweet, db) for tweet in tweets]

@app.get("/tweets/{tweet_id}", response_model=TweetResponse)
def get_tweet(tweet_id: int, db: Session = Depends(get_db)):
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    return format_tweet_response(tweet, db)

@app.put("/tweets/{tweet_id}", response_model=TweetResponse)
def update_tweet(tweet_id: int, tweet_update: TweetUpdate, db: Session = Depends(get_db)):
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    update_data = tweet_update.dict(exclude_unset=True)
    
    if 'thread_tweets' in update_data:
        update_data['thread_tweets_json'] = json.dumps([t.dict() for t in tweet_update.thread_tweets])
        del update_data['thread_tweets']
    
    if 'collection_ids' in update_data:
        collections = db.query(Collection).filter(Collection.id.in_(tweet_update.collection_ids)).all()
        db_tweet.collections = collections
        del update_data['collection_ids']
    
    for field, value in update_data.items():
        setattr(db_tweet, field, value)
    
    db.commit()
    db.refresh(db_tweet)
    
    return format_tweet_response(db_tweet, db)

@app.put("/tweets/{tweet_id}/schedule")
def update_tweet_schedule(tweet_id: int, schedule_update: TweetScheduleUpdate, db: Session = Depends(get_db)):
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    db_tweet.scheduled_date = schedule_update.scheduled_date
    db.commit()
    
    return {"message": "Schedule updated successfully"}

@app.delete("/tweets/{tweet_id}")
def delete_tweet(tweet_id: int, db: Session = Depends(get_db)):
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    db.delete(db_tweet)
    db.commit()
    
    return {"message": "Tweet deleted successfully"}

# Endpoints de Colecciones
@app.post("/collections", response_model=CollectionResponse)
def create_collection(collection: CollectionCreate, db: Session = Depends(get_db)):
    # Verificar si ya existe una colección con ese nombre para el usuario
    existing = db.query(Collection).filter(
        Collection.name == collection.name,
        Collection.user_id == collection.user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Collection name already exists for this user")
    
    db_collection = Collection(
        name=collection.name,
        description=collection.description,
        user_id=collection.user_id
    )
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    
    return format_collection_response(db_collection, db)

@app.get("/collections", response_model=List[CollectionResponse])
def get_collections(user_id: str, db: Session = Depends(get_db)):
    collections = db.query(Collection).filter(Collection.user_id == user_id).order_by(Collection.name).all()
    return [format_collection_response(collection, db) for collection in collections]

@app.get("/collections/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: int, db: Session = Depends(get_db)):
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return format_collection_response(collection, db)

@app.put("/collections/{collection_id}", response_model=CollectionResponse)
def update_collection(collection_id: int, collection_update: CollectionUpdate, db: Session = Depends(get_db)):
    db_collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not db_collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    update_data = collection_update.dict(exclude_unset=True)
    
    # Verificar nombre único si se está actualizando
    if 'name' in update_data:
        existing = db.query(Collection).filter(
            Collection.name == update_data['name'],
            Collection.user_id == db_collection.user_id,
            Collection.id != collection_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Collection name already exists for this user")
    
    for field, value in update_data.items():
        setattr(db_collection, field, value)
    
    db.commit()
    db.refresh(db_collection)
    
    return format_collection_response(db_collection, db)

@app.delete("/collections/{collection_id}")
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    db_collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not db_collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    db.delete(db_collection)
    db.commit()
    
    return {"message": "Collection deleted successfully"}

# Funciones auxiliares
def format_tweet_response(tweet: Tweet, db: Session) -> TweetResponse:
    thread_tweets = []
    if tweet.thread_tweets_json:
        try:
            thread_data = json.loads(tweet.thread_tweets_json)
            thread_tweets = [ThreadTweet(**t) for t in thread_data]
        except:
            pass
    
    collections = [format_collection_response(c, db) for c in tweet.collections]
    
    return TweetResponse(
        id=tweet.id,
        user_id=tweet.user_id,
        content=tweet.content or "",
        media_path=tweet.media_path or "",
        media_type=tweet.media_type or "",
        is_thread=tweet.is_thread,
        thread_tweets=thread_tweets,
        scheduled_date=tweet.scheduled_date,
        created_at=tweet.created_at,
        collections=collections
    )

def format_collection_response(collection: Collection, db: Session) -> CollectionResponse:
    tweet_count = 0
    if db:
        tweet_count = db.query(Tweet).join(tweet_collections).filter(
            tweet_collections.c.collection_id == collection.id
        ).count()
    else:
        tweet_count = len(collection.tweets) if hasattr(collection, 'tweets') else 0
    
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description or "",
        user_id=collection.user_id,
        tweet_count=tweet_count,
        created_at=collection.created_at
    )

# Endpoint de salud
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Twitter Organizer API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)