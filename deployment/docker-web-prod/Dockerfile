FROM dschien/web-bare:latest

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y nginx gunicorn

ADD req_prod.txt /app/
WORKDIR /app/
RUN pip install -r req_prod.txt

ENV C_FORCE_ROOT "true"

# Directory in container for all project files
#RUN mkdir /ep_site
#VOLUME ["/ep_site/log/"]

#COPY ./entrypoint.sh /
#WORKDIR /
#ENTRYPOINT ["/entrypoint.sh"]