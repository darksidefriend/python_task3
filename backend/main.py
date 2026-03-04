from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from . import models
import . database
from database import SessionLocal, engine
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import random
from pathlib import Path
from fastapi import Request
from fastapi.responses import Response

AB_PERCENTAGE_A = 50  # можно менять (например 90)

# Создание таблиц в базе данных (если их нет)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Путь к frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Раздача статики (css, js)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

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

@app.get("/", response_class=HTMLResponse)
def ab_test(request: Request):
    ab_cookie = request.cookies.get("ab_version")

    if ab_cookie in ["A", "B"]:
        version = ab_cookie
    else:
        # случайное распределение
        version = "A" if random.randint(1, 100) <= AB_PERCENTAGE_A else "B"

    file_name = "index_a.html" if version == "A" else "index_b.html"
    file_path = FRONTEND_DIR / file_name

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.set_cookie(
        key="ab_version",
        value=version,
        max_age=60 * 60 * 24 * 30  # 30 дней
    )

    return response

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
                term="Когнитивная нагрузка",
                definition="мера умственных усилий, затрачиваемых человеком на выполнение конкретной задачи. В контексте обучения – объем рабочей памяти человека, необходимый для усвоения нового материала.",
                sources=["https://doi.org/10.1207/S15516709COG1202_4"],
                related_terms=[]
            ),
            models.Term(
                term="Теория когнитивной нагрузки",
                definition="теория, выдвинутая Джоном Свеллером, которая описывает обучение как процесс обработки информации в рабочей памяти с последующей архивацией в долговременную память. Основной принцип заключается в том, что рабочая память человека ограничена, а долговременная – почти не имеет ограничений.",
                sources=["https://doi.org/10.1023/A:1022193728205"],
                related_terms=["Когнитивная нагрузка"]
            ),
            models.Term(
                term="LMS",
                definition="система управления обучением, программное приложение для администрирования, документирования, отслеживания и предоставления учебных курсов.",
                sources=["https://doi.org/10.1007/s44217-024-00138-5"],
                related_terms=["Moodle"]
            ),
            models.Term(
                term="Moodle",
                definition="модульная объектно-ориентированная динамическая обучающая среда, бесплатная система управления обучением с открытым кодом.",
                sources=["https://doi.org/10.1186/s40594-022-00342-9"],
                related_terms=["LMS", "Moodle Web Services"]
            ),
            models.Term(
                term="API",
                definition="Интерфейс для взаимодействия программ",
                sources=["https://ru.wikipedia.org/wiki/API"],
                related_terms=["REST API", "Moodle Web Services", "Endpoint"]
            ),
            models.Term(
                term="REST API",
                definition="архитектурный стиль взаимодействия различных компонентов распределенного приложения в сети.",
                sources=["https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm"],
                related_terms=["API", "JSON", "Endpoint"]
            ),
            models.Term(
                term="Node.js",
                definition="кроссплатформенная среда выполнения языка Javascript на стороне сервера, построенная на движке Chrome V8.",
                sources=["https://nodejs.org/en/learn/getting-started/introduction-to-nodejs"],
                related_terms=["Express.js"]
            ),
            models.Term(
                term="Express.js",
                definition="веб-фреймворк для Node.js, используемый для построения серверов и создания маршрутизации API-запросов.",
                sources=["https://expressjs.com/en/starter/installing.html"],
                related_terms=["Node.js", "REST API"]
            ),
            models.Term(
                term="Endpoint",
                definition="конкретный URL-адрес (конечная точка) в API, по которому клиентское приложение обращается к серверу для обмена данными, выполнения действий или получения доступа к ресурсу.",
                sources=["https://developer.mozilla.org/en-US/docs/Glossary/Endpoint"],
                related_terms=["API", "REST API"]
            ),
            models.Term(
                term="JSON",
                definition="независимый от языков программирования формат обмена данными, основанный на синтаксе объектов Javascript. Он используется для хранения и передачи структурированной информации между сервером и веб-приложениями, являясь стандартом для современных API.",
                sources=["https://www.rfc-editor.org/rfc/rfc8259"],
                related_terms=["REST API"]
            ),
            models.Term(
                term="Moodle Web Services",
                definition="программный интерфейс (API), позволяющий внешним приложениям, системам обмениваться данными с платформой Moodle в реальном времени.",
                sources=["https://docs.moodle.org/dev/Web_services"],
                related_terms=["Moodle", "API"]
            ),
            models.Term(
                term="Парсинг",
                definition="автоматизированный процесс сбора данных с сайтов или других источников с помощью специальных программ-парсеров.",
                sources=["https://www.ijresm.com/Vol.3_2020/Vol3_Iss4_April20/IJRESM_V3_I4_53.pdf"],
                related_terms=[]
            ),
        ]
        db.add_all(initial_terms)
        db.commit()
    db.close()