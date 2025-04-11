FROM public.ecr.aws/lambda/python:3.12
RUN dnf install -y make

COPY . /app
RUN make -C /app install

# for lambda
WORKDIR /app
CMD ["application.lambda_handler"]
