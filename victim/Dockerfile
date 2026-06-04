FROM python:3.11-slim
RUN pip install --no-cache-dir flask requests
WORKDIR /app
COPY edr_agent.py .
EXPOSE 8000
CMD ["python", "edr_agent.py"]
