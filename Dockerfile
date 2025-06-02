FROM ubuntu:latest
LABEL authors="pikro"

ENTRYPOINT ["top", "-b"]