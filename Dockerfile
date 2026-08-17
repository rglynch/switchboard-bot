FROM python:3.12-slim

ENV MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libfreetype6 libpng16-16 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ bot/

RUN useradd --create-home appuser
USER appuser

CMD ["python", "-m", "bot.main"]
