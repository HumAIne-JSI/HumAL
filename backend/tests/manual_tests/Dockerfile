FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Only dependency required by xai_rabbitmq_simulator.py
RUN pip install --no-cache-dir aio-pika

# Copy only the simulator script into the image
COPY xai_rabbitmq_simulator.py /app/xai_rabbitmq_simulator.py

CMD ["python", "/app/xai_rabbitmq_simulator.py"]
