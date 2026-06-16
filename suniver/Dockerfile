FROM python:3.11-slim
RUN pip install --no-cache-dir flask
WORKDIR /app
COPY app.py .
EXPOSE 7000
CMD ["python", "app.py"]
