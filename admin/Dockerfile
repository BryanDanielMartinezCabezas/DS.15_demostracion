FROM python:3.11-slim
RUN pip install --no-cache-dir flask pyotp requests
WORKDIR /app
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
