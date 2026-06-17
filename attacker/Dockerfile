FROM kalilinux/kali-rolling
WORKDIR /app
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    curl bash python3 python3-pip \
    && pip3 install --no-cache-dir flask requests --break-system-packages \
    && rm -rf /var/lib/apt/lists/*
COPY app.py .
EXPOSE 9999
CMD ["python3", "app.py"]
