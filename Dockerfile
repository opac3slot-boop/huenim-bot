
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "echo '=== ПРОВЕРКА TELEGRAM API ==='; python -c \"import urllib.request; print(urllib.request.urlopen('https://api.telegram.org', timeout=15).status)\"; echo '=== ЗАПУСК БОТА ==='; python bot.py"]
