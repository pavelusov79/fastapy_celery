FROM joyzoursky/python-chromedriver:3.9

ENV DISPLAY=:99

RUN mkdir /app

COPY requirements.txt /app

WORKDIR /app

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker_scripts/*.sh