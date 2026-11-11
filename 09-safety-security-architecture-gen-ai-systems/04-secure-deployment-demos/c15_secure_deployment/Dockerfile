FROM python:3.13-slim

# Public configuration only. Never put credentials in ENV, ARG or COPY.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --chmod=0444 app.py /app/app.py
USER 10001:10001
CMD ["python", "/app/app.py"]
