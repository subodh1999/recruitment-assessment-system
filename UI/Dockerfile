# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# This is a placeholder file. The actual user code will be mounted here at runtime.
# We copy a file to ensure the WORKDIR is created and the base image is functional.
COPY test.py .

# The command that will be executed when the container runs.
# It runs the python interpreter on the file named "test.py".
CMD [ "python", "./test.py" ]