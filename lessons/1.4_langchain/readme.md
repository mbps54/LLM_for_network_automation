# Основы работы с LangChain
## Запуск первого API запроса
```
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai"
)

response = llm.invoke("What is LLM?")
```

## System prompt
```
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

model_name = "gpt-4o-mini"

# Инициализация чата через универсальный интерфейс LangChain
chat = init_chat_model(
    model_name,
    model_provider="openai",
    temperature=0.7,
)

# Создание сообщений
system_prompt = SystemMessage(
    content="Ты — умный помощник сетевого инженера. Отвечай кратко, технически и по делу."
)
human_message = HumanMessage(
    content="Объясни, что такое VLAN trunk"
)

# Отправка запроса
response = chat.invoke([system_prompt, human_message])

# Вывод результата
print(response.content)
```

## Streamlit

app.py
```
#!/usr/bin/env python

import streamlit as st
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

# Название модели и системный промпт
model_name = "gpt-4o-mini"
system_prompt = "Ты — ассистент сетевого инженера. Отвечай кратко и по делу."

# Инициализация модели
chat = init_chat_model(
    model_name,
    model_provider="openai",
    temperature=0.7,
)

# Заголовок страницы
st.title("Network LLM Assistant")

# Инициализация истории сообщений в сессии
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Добавим системный промпт как объект LangChain только при инициализации
    st.session_state.messages.append(SystemMessage(content=system_prompt))

# Отображение истории (все кроме system message)
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    elif hasattr(msg, "name") and msg.name == "assistant":  # для совместимости
        st.chat_message("assistant").write(msg.content)

# Ввод пользователя
if prompt := st.chat_input("Введите ваш вопрос..."):
    # Добавление вопроса в историю
    user_msg = HumanMessage(content=prompt)
    st.chat_message("user").write(user_msg.content)
    st.session_state.messages.append(user_msg)

    # Вызов модели
    response = chat.invoke(st.session_state.messages)

    # Отображение и сохранение ответа
    st.chat_message("assistant").write(response.content)
    st.session_state.messages.append(response)
```
run
```
streamlit run app.py
```
