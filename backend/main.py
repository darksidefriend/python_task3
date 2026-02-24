from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models
import database
from database import SessionLocal, engine
from pydantic import BaseModel

# Создание таблиц в базе данных (если их нет)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Разрешаем CORS для всех источников (в продакшене лучше указать конкретный домен)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зависимость для получения сессии БД в каждом запросе
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic-схемы для валидации и сериализации данных
class TermBase(BaseModel):
    term: str
    definition: str
    sources: List[str] = []
    related_terms: List[str] = []

class TermCreate(TermBase):
    pass

class TermUpdate(TermBase):
    pass

class TermOut(TermBase):
    id: int

    class Config:
        orm_mode = True

class TermSimpleOut(BaseModel):
    term: str
    definition: str

    class Config:
        orm_mode = True

# ----- Эндпоинты -----

@app.get("/terms", response_model=List[TermSimpleOut])
def read_terms(db: Session = Depends(get_db)):
    """Возвращает все термины в упрощённом виде (только термин и определение)"""
    terms = db.query(models.Term).all()
    return terms

@app.get("/terms/{term}", response_model=TermOut)
def read_term(term: str, db: Session = Depends(get_db)):
    """Возвращает полную информацию о конкретном термине"""
    db_term = db.query(models.Term).filter(models.Term.term == term).first()
    if db_term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    return db_term

@app.post("/terms", response_model=TermOut, status_code=201)
def create_term(term_data: TermCreate, db: Session = Depends(get_db)):
    """Создаёт новый термин"""
    # Проверка на существование термина с таким же ключевым словом
    existing = db.query(models.Term).filter(models.Term.term == term_data.term).first()
    if existing:
        raise HTTPException(status_code=400, detail="Term already exists")
    db_term = models.Term(**term_data.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term

@app.put("/terms/{term}", response_model=TermOut)
def update_term(term: str, term_data: TermUpdate, db: Session = Depends(get_db)):
    """Полностью обновляет существующий термин"""
    db_term = db.query(models.Term).filter(models.Term.term == term).first()
    if db_term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    # Если изменяется ключевое слово, проверяем, что новое значение уникально
    if term != term_data.term:
        existing = db.query(models.Term).filter(models.Term.term == term_data.term).first()
        if existing:
            raise HTTPException(status_code=400, detail="New term already exists")
    # Обновляем поля
    for key, value in term_data.dict().items():
        setattr(db_term, key, value)
    db.commit()
    db.refresh(db_term)
    return db_term

@app.delete("/terms/{term}", status_code=204)
def delete_term(term: str, db: Session = Depends(get_db)):
    """Удаляет термин"""
    db_term = db.query(models.Term).filter(models.Term.term == term).first()
    if db_term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    db.delete(db_term)
    db.commit()
    return None

# ----- Инициализация тестовыми данными при старте приложения -----
@app.on_event("startup")
def startup_event():
    """При первом запуске, если база пуста, добавляем несколько терминов"""
    db = SessionLocal()
    if db.query(models.Term).count() == 0:
        initial_terms = [
            models.Term(
                term="FastAPI",
                definition="Современный веб-фреймворк для создания API на Python",
                sources=["https://fastapi.tiangolo.com/"],
                related_terms=["Python", "API"]
            ),
            models.Term(
                term="Docker",
                definition="Платформа для контейнеризации приложений",
                sources=["https://docker.com/"],
                related_terms=["Контейнер", "DevOps"]
            ),
            models.Term(
                term="Python",
                definition="Язык программирования",
                sources=["https://python.org/"],
                related_terms=["FastAPI", "Docker"]
            ),
            models.Term(
                term="API",
                definition="Интерфейс для взаимодействия программ",
                sources=["https://ru.wikipedia.org/wiki/API"],
                related_terms=["FastAPI"]
            ),
            models.Term(
                term="Контейнер",
                definition="Изолированная среда для запуска приложений",
                sources=["https://ru.wikipedia.org/wiki/Контейнеризация"],
                related_terms=["Docker"]
            ),
        ]
        db.add_all(initial_terms)
        db.commit()
    db.close()