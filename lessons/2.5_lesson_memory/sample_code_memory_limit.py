#!/usr/bin/env python

import warnings

from langchain_core._api.deprecation import LangChainDeprecationWarning

warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationTokenBufferMemory

from tools.ping import ping


# ---------------------------- TOOLS ----------------------------

@tool
def ping_tool(host: str) -> bool:
    """Ping a host to check if it's reachable. Returns True or False."""
    return ping(host)


# ---------------------------- SETUP ----------------------------

tools = [ping_tool]

# Инициализация модели
llm = init_chat_model("gpt-4o-mini", model_provider="openai")

# Создание памяти с ограничением по токенам
memory = ConversationTokenBufferMemory(
    llm=llm,
    max_token_limit=40,
    memory_key="chat_history",
    input_key="input",
    return_messages=True,
)

# Системное сообщение — как себя вести
memory.chat_memory.add_message(SystemMessage(content=(
    "Ты — ассистент сетевого инженера. "
    "Ты умеешь использовать команду ping()."
)))

# Инициализация агента с памятью
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    handle_parsing_errors=True
)


# ---------------------------- DIALOG ----------------------------

inputs = [
    "Проверь, доступен ли 8.8.8.8 по ping",
    "ещё раз",
    "а теперь проверь 8.8.4.4",
    "ещё раз",
    "ещё раз",
    "ещё раз",
    "ещё раз",
]

for prompt in inputs:
    print(f"==> вопрос: {prompt}")
    response = agent.invoke({"input": prompt})
    print(f"==> ответ: {response['output']}\n")