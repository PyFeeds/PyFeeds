FROM python:3-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache openssl-dev libxml2-dev libxslt-dev

COPY . .

RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libffi-dev openssl-dev cargo \
 && pip install -e . \
 && apk del .build-deps

ENTRYPOINT [ "feeds" ]
