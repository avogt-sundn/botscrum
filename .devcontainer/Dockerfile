# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# install Node.js LTS
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get update && apt-get install -y nodejs unzip \
    && rm -rf /var/lib/apt/lists/*

# set workspace directory
WORKDIR /home/vscode

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install

# ensure the venv is activated by default for interactive sessions
ENV VIRTUAL_ENV=/workspaces/botscrum/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
