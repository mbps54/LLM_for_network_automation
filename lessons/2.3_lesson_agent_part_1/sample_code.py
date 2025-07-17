#!/usr/bin/env python

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain.agents import initialize_agent
from tools.ping import ping

# 1. Инструмент ping
@tool
def ping_tool(host: str) -> bool:
    """Проверяет доступность IP-адреса через ping."""
    return ping(host)

# 2. Задаем список инструментов
tools = [ping_tool]

# 3. Инициализируем модель
llm = init_chat_model("gpt-4o-mini", model_provider="openai")

# 4. Инициализируем агента
agent = initialize_agent(
    tools=tools,
    llm=llm,
    verbose=True
)

# 5. Запуск агента
response = agent.invoke({"input": "Проверь, доступен ли 8.8.8.8 по ping"})
print(f"==> ответ: {response['output']}\n")
print("\n---\n")
response = agent.invoke({"input": "Проверь, доступен ли 192.168.8.1 по ping"})
print(f"==> ответ: {response['output']}\n")
