FROM python:3.12-slim

WORKDIR /app

COPY app/HealthcareAgent/ ./

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "main.py"]
