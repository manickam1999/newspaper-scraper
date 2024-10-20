
FROM selenium/standalone-chrome

USER root

RUN apt-get update && apt-get install -y python3-venv python3-pip

WORKDIR /usr/src/app

RUN python3 -m venv venv
COPY requirements.txt .
RUN ./venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

ENV CHROME_BIN=/opt/google/chrome/chrome
ENV CHROME_DRIVER=/usr/bin/chromedriver

ENV PATH="/usr/src/app/venv/bin:$PATH"

CMD ["python", "main.py"]