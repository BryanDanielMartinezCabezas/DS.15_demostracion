FROM python:3.11-slim
WORKDIR /app
RUN apt-get update -qq && apt-get install -y --no-install-recommends curl bash \
    && pip install --no-cache-dir flask requests \
    && rm -rf /var/lib/apt/lists/*
COPY app.py .
EXPOSE 9999
CMD ["python", "app.py"]
