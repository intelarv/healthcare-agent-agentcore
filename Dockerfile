FROM python:3.12-slim

WORKDIR /app

ARG AGENT_DIR=app/HealthcareAgent
COPY ${AGENT_DIR}/ ./

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "main.py"]
