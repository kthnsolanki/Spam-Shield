from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./spam_shield.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    username       = Column(String(50), unique=True, index=True, nullable=False)
    email          = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow)

    scans = relationship("ScanHistory", back_populates="user", cascade="all, delete")


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    scan_type     = Column(String(20), nullable=False)   # "message" | "url" | "batch"
    input_content = Column(Text, nullable=False)
    result        = Column(String(50), nullable=False)   # "spam" | "ham" | "HIGH RISK" | "SAFE" | etc.
    confidence    = Column(Float, nullable=True)         # % for messages, risk_score for URLs, None for batch
    extra_info    = Column(Text, nullable=True)          # JSON string for extra data if needed
    created_at    = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scans")


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
