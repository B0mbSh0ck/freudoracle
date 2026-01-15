# Используем легкий образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем директорию для данных (для монтирования диска)
RUN mkdir -p /app/data

# Устанавливаем системные зависимости (если нужны для компиляции)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY . .

# Команда запуска
CMD ["python", "main.py"]
