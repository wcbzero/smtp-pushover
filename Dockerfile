FROM python:3-alpine
ADD requirements.txt /tmp/
RUN pip install -r "/tmp/requirements.txt" && rm -f "/tmp/requirements.txt"
ADD main.py /app/main.py
RUN chmod +x /app/main.py
CMD ["python", "/app/main.py"]
