# Используем официальный Python образ
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем requirements
COPY backend/requirements.txt ./requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт
EXPOSE 10000

# Запуск приложения
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]