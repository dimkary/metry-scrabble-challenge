# dockerfile, Image, Container
FROM python:3.9

WORKDIR /app
# Use COPY if ADD functionality is not needed
COPY ["requirements.txt", "/app/"]

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ["*.py", "*.json", "/app/"]

ADD ["templates/", "/app/templates/"]

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]