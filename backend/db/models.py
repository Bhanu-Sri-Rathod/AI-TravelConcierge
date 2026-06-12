from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from datetime import datetime
from typing import Optional, List
import uuid
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id:         Mapped[str]      = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email:      Mapped[str]      = mapped_column(String, unique=True, index=True)
    username:   Mapped[str]      = mapped_column(String)
    hashed_pw:  Mapped[str]      = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trips:      Mapped[List["Trip"]] = relationship(back_populates="user")

class Trip(Base):
    __tablename__ = "trips"
    id:          Mapped[str]      = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:     Mapped[str]      = mapped_column(ForeignKey("users.id"))
    title:       Mapped[str]      = mapped_column(String)
    destination: Mapped[str]      = mapped_column(String)
    start_date:  Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date:    Mapped[Optional[str]] = mapped_column(String, nullable=True)
    itinerary:   Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at:  Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user:        Mapped["User"]   = relationship(back_populates="trips")

class SearchHistory(Base):
    __tablename__ = "search_history"
    id:         Mapped[str]      = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:    Mapped[str]      = mapped_column(ForeignKey("users.id"))
    query:      Mapped[str]      = mapped_column(Text)
    results:    Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
