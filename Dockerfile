FROM python:3

ADD kafka_consumer.py /

RUN pip install kafka-python
RUN pip install psycopg2

CMD [ "python", "./kafka_consumer.py" ]

