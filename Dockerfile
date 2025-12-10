FROM python:3.14.2-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Forward error logs to docker log collector
RUN ln -sf /dev/stderr /usr/src/app/livelaunch.log

CMD [ "python", "./main.py" ]
