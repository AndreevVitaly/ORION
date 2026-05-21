# 1. Базовый образ (Операционная система + Python)
FROM python:3.11-slim

# 2. Рабочая папка внутри контейнера
WORKDIR /app

# 3. Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем весь код проекта в контейнер
COPY . .

# 5. Команда, которая запускает приложение
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]