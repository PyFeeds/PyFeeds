FROM python:3-alpine

WORKDIR /usr/src/app

COPY . .

RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libffi-dev libxml2-dev libxslt-dev openssl-dev cargo \
 && pip install --no-cache-dir -e . \
 && apk del .build-deps gcc musl-dev python3-dev libffi-dev libxml2-dev openssl-dev libxslt-dev cargo

ENTRYPOINT [ "feeds" ]
