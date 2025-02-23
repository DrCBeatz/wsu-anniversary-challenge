# Dockerfile

FROM public.ecr.aws/lambda/python:3.9

# Install your dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir

# Copy your application code
COPY app.py .

# Set the CMD to your handler
CMD ["app.handler"]

