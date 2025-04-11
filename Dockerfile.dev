FROM python:3.9.22-alpine3.21
RUN apk add --update make openssl

COPY . /app
RUN make -C /app install

CMD make -C /app dev
