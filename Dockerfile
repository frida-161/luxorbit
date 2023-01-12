FROM python:3.9


COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY luxorbit /luxorbit

CMD ["gunicorn", "-b 0.0.0.0:4567", "luxorbit:app"]
