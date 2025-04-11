FROM public.ecr.aws/lambda/python:3.12

COPY . /app
RUN make -C /app install

# for lambda
CMD ["application.lambda_handler"]
