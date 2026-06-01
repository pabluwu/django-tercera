FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# CORREGIDO: Agregados pkg-config y default-libmysqlclient-dev para compilar mysqlclient con éxito
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# CORREGIDO: Todo en una sola línea con su espacio correspondiente
COPY . /app/

# Exponer el puerto por defecto de Gunicorn/Uvicorn
EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

