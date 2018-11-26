FROM python:3.6
RUN apt-get update -y
RUN apt-get install -y python3-pip supervisor
COPY . /web
WORKDIR /web
RUN pip3 install -r reqs.txt
CMD ["./run_web.sh"]