FROM python:3
COPY . /app
WORKDIR /app
ENV PYTHONPATH "${PYTHONPATH}:/app"
RUN pip install -r requirements_sub.txt
CMD python src/conduct_classification.py

# Commands:
# docker build --tag my-app .
# docker run --name app my-app

# For interactive processes (like a shell), you must use -i -t together in order to allocate a tty for the container
# process.
# docker run -it --name ricardo_luiz_app my-app

# Sharing data between the docker container and the host
# Bind-mounting a volume
# Optional: ADD the dir to mount into the Dockerfile for creation
# docker run -it --name <container_name> -v "$(pwd)"/logs:/app/logs <image_tag>
# Bind volume: -v
# <dir_on_host_machine>:<dir_in_container>
# * Local dir to mount in the container [bind created]
# * Writing to mount in container will make it accessible to the local machine
# * Write to the dir in source code: logs/<filename>

# Remove docker image:
# docker images
# docker rmi <IMAGE ID>

# Remove docker container:
# docker ps -a
# docker rm <CONTAINER ID>

# Running linux screen:
# screen -S <SCREEN NAME>
# Detach: Ctrl-a Ctrl-d
# Re-attach: screen -r <SCREEN NAME>