# Dockerfile
FROM python:3.9-slim
WORKDIR /project
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN groupadd -r preppy && useradd -r -g preppy preppy
RUN chown -R preppy:preppy /project
USER preppy
RUN python init_db.py
EXPOSE 5000
ENV FLASK_APP=app:app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:5000/ || exit 1
