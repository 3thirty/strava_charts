FROM public.ecr.aws/lambda/python:3.12
RUN dnf install -y make

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# /var/task is $LAMBDA_TASK_ROOT in AWS
COPY app /var/task

# for lambda
CMD ["application.lambda_handler"]
