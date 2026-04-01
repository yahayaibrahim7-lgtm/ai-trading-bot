from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    is_vip = Column(Boolean, default=False)
    vip = Column(Boolean, default=False)
    chat_id = Column(String, nullable=True)