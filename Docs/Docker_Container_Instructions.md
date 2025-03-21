# Docker Container Instructions

This document details instructions and guidelines for containerizing the agents.

## Overview
- Detailed steps for building and running Docker containers for each service.
- Tips for troubleshooting Docker-related issues, particularly with driver versions and compatibility.

## Recommended Pipeline
- Use Quark in place of the deprecated Vitis AI stack.
- Verify against the latest AMD driver versions.

## Example Dockerfile Snippet
```
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y python3 python3-pip
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
CMD ["python3", "run_app.py"]
```

## References
- Official Docker documentation
