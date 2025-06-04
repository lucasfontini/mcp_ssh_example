MCP Server SSH
==============

This project provides a Dockerized server that runs an SSH-compatible service, accessible via port 8000.

Getting Started
---------------

Follow these steps to build and run the Docker container.

1. Build the Docker Image

    docker build -t mcp-server_ssh .

    This command builds the Docker image using the current directory's Dockerfile and tags it as 'mcp-server_ssh'.

2. Run the Docker Container

    docker run -p 8000:8000 mcp-server_ssh

    This command runs the container and maps port 8000 from the container to port 8000 on your host machine.
3. Now you can config with claude or vscode mcp client 
```

        "mcp-server_ssh": {
          "url": "http://localhost:8000/sse"
        }
```