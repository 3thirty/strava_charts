FROM public.ecr.aws/lambda/python:3.12
RUN dnf install -y make

# can use LAMBDA_TASK_ROOT in AWS
COPY . /var/task
RUN make -C /var/task install

# for lambda
CMD ["application.lambda_handler"]
