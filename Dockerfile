FROM python:3
RUN mkdir /app
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

COPY . /app/
CMD ["python3", "main.py", "nocmd"]
