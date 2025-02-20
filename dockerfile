FROM python:3.10-slim-bullseye

RUN apt-get update \ 
&& apt-get install -y --no-install-recommends --no-install-suggests postgresql postgresql-contrib \
&& pip install --no-cache-dir --upgrade pip

WORKDIR /myApp
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000

CMD [ "python3","main.py" ]