# Запуск локальной LLM
## установка Docker Engine
https://docs.docker.com/engine/install/ubuntu
```
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
# Install Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## Запуск локальной LLM
Создать файл `entrypoint.sh`
```
#!/bin/bash

/bin/ollama serve &
pid=$!
sleep 5
ollama pull llama3
wait $pid
```
Создать файл Docker Compose манифеста `docker-compose.yaml`
```
---
version: '3.8'
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ./ollama:/root/.ollama
      - ./entrypoint.sh:/entrypoint.sh
    environment:
      - OLLAMA_DEVICE=cpu
    restart: always
    tty: true
    pull_policy: always
    container_name: ollama
    entrypoint: ["/usr/bin/bash", "/entrypoint.sh"]

  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "80:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
    restart: always
    container_name: openwebui
...
```
Запустить
```
docker compose up -d
```

## Запуск первого API запроса
```
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3:latest",
    base_url="http://<VM_IP>:11434",
)

response = llm.invoke([("human", "What is LLM?")])

print(response.content)
```