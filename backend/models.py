from sqlalchemy import Column, Integer, String, JSON
from .database import Base

class Term(Base):
    __tablename__ = "terms"

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String, unique=True, index=True, nullable=False)
    definition = Column(String, nullable=False)
    sources = Column(JSON, default=list)          # список ссылок
    related_terms = Column(JSON, default=list)    # список связанных терминов