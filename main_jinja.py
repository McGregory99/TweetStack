from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, field_validator
from typing import List, Optional, Union
from datetime import datetime, date, timedelta
from collections import defaultdict
import calendar
import json
import os

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tweetstack.db")

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
    user_id = Column(String, index=True)
    content = Column(Text)
    media_path = Column(String)
    media_type = Column(String)
    is_thread = Column(Boolean, default=False)
    thread_tweets_json = Column(Text)
    scheduled_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    collections = relationship("Collection", secondary=tweet_collections, back_populates="tweets")

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    user_id = Column(String, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    tweets = relationship("Tweet", secondary=tweet_collections, back_populates="collections")

# Modelos Pydantic para API
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
    scheduled_date: Optional[Union[datetime, str]] = None
    
    @field_validator('scheduled_date')
    @classmethod
    def validate_scheduled_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            if not v.strip():
                return None
            try:
                # Try to parse the string as datetime
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, return None instead of raising error
                return None
        return v

class TweetUpdate(BaseModel):
    content: Optional[str] = None
    media_path: Optional[str] = None
    media_type: Optional[str] = None
    is_thread: Optional[bool] = None
    thread_tweets: Optional[List[ThreadTweet]] = None
    collection_ids: Optional[List[int]] = None
    scheduled_date: Optional[Union[datetime, str]] = None
    
    @field_validator('scheduled_date')
    @classmethod
    def validate_scheduled_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            if not v.strip():
                return None
            try:
                # Try to parse the string as datetime
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, return None instead of raising error
                return None
        return v

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    user_id: str

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
    collections: List[dict] = []

class CollectionResponse(BaseModel):
    id: int
    name: str
    description: str
    user_id: str
    tweet_count: int
    created_at: datetime

# Crear la aplicación FastAPI
app = FastAPI(title="TweetStack - Jinja2 Version", version="2.0.0")

# Configurar archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS (mantenemos para API endpoints)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Funciones auxiliares
def format_tweet_response(tweet: Tweet, db: Session) -> dict:
    thread_tweets = []
    if tweet.thread_tweets_json:
        try:
            thread_data = json.loads(tweet.thread_tweets_json)
            thread_tweets = thread_data
        except:
            pass
    
    collections = [{"id": c.id, "name": c.name, "description": c.description or ""} for c in tweet.collections]
    
    return {
        "id": tweet.id,
        "user_id": tweet.user_id,
        "content": tweet.content or "",
        "media_path": tweet.media_path or "",
        "media_type": tweet.media_type or "",
        "is_thread": tweet.is_thread,
        "thread_tweets": thread_tweets,
        "scheduled_date": tweet.scheduled_date.isoformat() if tweet.scheduled_date else None,
        "created_at": tweet.created_at.isoformat(),
        "collections": collections
    }

def format_collection_response(collection: Collection, db: Session) -> dict:
    tweet_count = len(collection.tweets) if hasattr(collection, 'tweets') else 0
    
    return {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description or "",
        "user_id": collection.user_id,
        "tweet_count": tweet_count,
        "created_at": collection.created_at.isoformat()
    }

# RUTAS HTML (Jinja2 Templates)

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    """Página principal con todos los tweets"""
    user_id = "demo-user-123"  # En producción esto vendría de autenticación
    
    tweets = db.query(Tweet).filter(Tweet.user_id == user_id).order_by(Tweet.created_at.desc()).all()
    collections = db.query(Collection).filter(Collection.user_id == user_id).order_by(Collection.name).all()
    
    tweets_data = [format_tweet_response(tweet, db) for tweet in tweets]
    collections_data = [format_collection_response(collection, db) for collection in collections]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tweets": tweets_data,
        "collections": collections_data,
        "user_id": user_id
    })

@app.get("/editor", response_class=HTMLResponse)
def tweet_editor(request: Request, tweet_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Editor de tweets"""
    user_id = "demo-user-123"
    
    tweet_data = None
    if tweet_id:
        tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
        if tweet:
            tweet_data = format_tweet_response(tweet, db)
    
    collections = db.query(Collection).filter(Collection.user_id == user_id).order_by(Collection.name).all()
    collections_data = [format_collection_response(collection, db) for collection in collections]
    
    return templates.TemplateResponse("editor.html", {
        "request": request,
        "tweet": tweet_data,
        "collections": collections_data,
        "user_id": user_id
    })

@app.get("/collections", response_class=HTMLResponse)
def collections_page(request: Request, db: Session = Depends(get_db)):
    """Página de gestión de colecciones"""
    user_id = "demo-user-123"
    
    collections = db.query(Collection).filter(Collection.user_id == user_id).order_by(Collection.name).all()
    collections_data = [format_collection_response(collection, db) for collection in collections]
    
    return templates.TemplateResponse("collections.html", {
        "request": request,
        "collections": collections_data,
        "user_id": user_id
    })

@app.get("/calendar", response_class=HTMLResponse)
def calendar_view(request: Request, year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(get_db)):
    """Vista de calendario con tweets programados"""
    user_id = "demo-user-123"
    
    # Use current date if not specified
    now = datetime.now()
    target_year = year or now.year
    target_month = month or now.month
    
    # Get tweets with scheduled dates for the target month
    start_date = datetime(target_year, target_month, 1)
    if target_month == 12:
        end_date = datetime(target_year + 1, 1, 1)
    else:
        end_date = datetime(target_year, target_month + 1, 1)
    
    scheduled_tweets = db.query(Tweet).filter(
        Tweet.user_id == user_id,
        Tweet.scheduled_date >= start_date,
        Tweet.scheduled_date < end_date
    ).order_by(Tweet.scheduled_date).all()
    
    # Group tweets by date
    tweets_by_date = defaultdict(list)
    for tweet in scheduled_tweets:
        if tweet.scheduled_date:
            date_key = tweet.scheduled_date.date()
            tweets_by_date[date_key].append(format_tweet_response(tweet, db))
    
    # Generate calendar data
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    calendar_days = []
    
    for week in cal.monthdayscalendar(target_year, target_month):
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                day_date = date(target_year, target_month, day)
                day_tweets = tweets_by_date.get(day_date, [])
                week_data.append({
                    'day': day,
                    'date': day_date,
                    'tweets': day_tweets,
                    'tweet_count': len(day_tweets),
                    'has_threads': any(t['is_thread'] for t in day_tweets),
                    'collections': list(set([c['name'] for t in day_tweets for c in t['collections']]))
                })
        calendar_days.append(week_data)
    
    # Navigation dates
    if target_month == 1:
        prev_month = {'year': target_year - 1, 'month': 12}
    else:
        prev_month = {'year': target_year, 'month': target_month - 1}
    
    if target_month == 12:
        next_month = {'year': target_year + 1, 'month': 1}
    else:
        next_month = {'year': target_year, 'month': target_month + 1}
    
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "calendar_days": calendar_days,
        "current_year": target_year,
        "current_month": target_month,
        "month_name": calendar.month_name[target_month],
        "prev_month": prev_month,
        "next_month": next_month,
        "total_scheduled": len(scheduled_tweets),
        "user_id": user_id
    })

# RUTAS API (mantener funcionalidad AJAX)

@app.get("/api/tweets/day")
def get_tweets_by_day(date: str, user_id: str = "demo-user-123", db: Session = Depends(get_db)):
    """Get tweets for a specific day"""
    try:
        # Parse the date string
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Get start and end of day
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # Query tweets scheduled for that day
        tweets = db.query(Tweet).filter(
            Tweet.user_id == user_id,
            Tweet.scheduled_date >= start_datetime,
            Tweet.scheduled_date <= end_datetime
        ).order_by(Tweet.scheduled_date).all()
        
        tweets_data = [format_tweet_response(tweet, db) for tweet in tweets]
        
        return {"tweets": tweets_data, "count": len(tweets_data), "date": date}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tweets", response_model=TweetResponse)
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
    
    if tweet.collection_ids:
        collections = db.query(Collection).filter(Collection.id.in_(tweet.collection_ids)).all()
        db_tweet.collections = collections
        db.commit()
    
    return format_tweet_response(db_tweet, db)

@app.get("/api/tweets", response_model=List[TweetResponse])
def get_tweets(user_id: str, db: Session = Depends(get_db)):
    tweets = db.query(Tweet).filter(Tweet.user_id == user_id).order_by(Tweet.created_at.desc()).all()
    return [format_tweet_response(tweet, db) for tweet in tweets]

@app.put("/api/tweets/{tweet_id}", response_model=TweetResponse)
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

@app.delete("/api/tweets/{tweet_id}")
def delete_tweet(tweet_id: int, db: Session = Depends(get_db)):
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    db.delete(db_tweet)
    db.commit()
    return {"message": "Tweet deleted successfully"}

@app.post("/api/collections", response_model=CollectionResponse)
def create_collection(collection: CollectionCreate, db: Session = Depends(get_db)):
    existing = db.query(Collection).filter(
        Collection.name == collection.name,
        Collection.user_id == collection.user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Collection name already exists")
    
    db_collection = Collection(
        name=collection.name,
        description=collection.description,
        user_id=collection.user_id
    )
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    
    return format_collection_response(db_collection, db)

@app.get("/api/collections", response_model=List[CollectionResponse])
def get_collections(user_id: str, db: Session = Depends(get_db)):
    collections = db.query(Collection).filter(Collection.user_id == user_id).order_by(Collection.name).all()
    return [format_collection_response(collection, db) for collection in collections]

@app.delete("/api/collections/{collection_id}")
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    db_collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not db_collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    db.delete(db_collection)
    db.commit()
    return {"message": "Collection deleted successfully"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "TweetStack Jinja2 Version is running"}

# Crear tablas
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 