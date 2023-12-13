#docker pull python:3.8-slim
FROM python:3.8-slim

# устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в рабочую директорию
COPY . .

# устанавилваем зависимости для libGL
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
# устанавливаем зависимости и делаем python файл исполняемым
RUN  pip install  --use-deprecated=legacy-resolver --no-cache-dir -r ./requirements.txt \
     && chmod +x ./*.py

# открываем порт на котором будет работать наше приложение
EXPOSE 5000
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["gunicorn --bind 0.0.0.0:5000 main:app"]
