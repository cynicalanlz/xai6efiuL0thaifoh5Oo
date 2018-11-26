FROM python:3.6
RUN apt-get update -y
RUN apt-get install -y python3-pip
COPY . /points_generator
WORKDIR /points_generator
RUN pip3 install -r reqs.txt
CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi"]