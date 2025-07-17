import os
import ipaddress

import streamlit as st

import warnings
from langchain_core._api.deprecation import LangChainDeprecationWarning

# Подавляем предупреждение об устаревании AgentExecutor
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain.agents import initialize_agent, AgentType

from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools.ping import ping


# ---------------------------- TOOLS ----------------------------

@tool
def ping_tool(ip: str) -> bool:
    """
    Проверяет доступность IP-адреса через ping.
    Используется только при наличии корректного IP-адреса.
    """
    try:
        # Проверка корректности IPv4
        ipaddress.IPv4Address(ip)
    except ValueError:
        raise ValueError("ping() принимает только корректный IPv4-адрес.")
    return ping(ip)


# Определяем lookup-инструмент
@tool
def lookup_docs(query: str) -> str:
    """
    Ищет информацию по внутренней документации.
    Может помочь найти IP адрес устройства.
    """
    if retriever is None:
        return "База знаний не загружена."

    docs = retriever.invoke(query)
    if not docs:
        return "Ничего не найдено."

    return "\n\n".join(doc.page_content for doc in docs)

# ---------------------------- SETUP ----------------------------

retriever = None

# ---------------------------- MAIN ----------------------------

def chat_rag_tools_main():
    global retriever

    st.title("AI Assistant — Chat & RAG & Tools")

    # Выбор модели
    model_name = st.sidebar.selectbox(
        "Выберите модель:",
        ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"]
    )

    llm = init_chat_model(model_name, model_provider="openai", temperature=0.3)

    # История сообщений
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Загрузка документов в retriever
    with st.expander("Загрузка документов для RAG"):
        if st.button("Индексировать ./docs"):
            docs_path = "./docs"
            if os.path.exists(docs_path) and os.listdir(docs_path):
                with st.spinner("Индексируем документы..."):
                    loader = DirectoryLoader(
                        docs_path,
                        loader_cls=TextLoader,
                        show_progress=True
                    )
                    documents = loader.load()
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=200
                    )
                    splits = splitter.split_documents(documents)
                    embeddings = OpenAIEmbeddings()
                    vectorstore = FAISS.from_documents(splits, embeddings)
                    st.session_state.retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
                    retriever = st.session_state.retriever
                    st.success("✅ Загружено и проиндексировано")
            else:
                st.warning("Директория ./docs пуста")

    # Показываем историю сообщений
    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
        elif hasattr(msg, "name") and msg.name == "assistant":
            st.chat_message("assistant").write(msg.content)

    # Обработка ввода пользователя
    if prompt := st.chat_input("Введите вопрос..."):
        user_msg = HumanMessage(content=prompt)
        st.chat_message("user").write(user_msg.content)
        st.session_state.messages.append(user_msg)

        # Если retriever есть — инициализируем агента
        if "retriever" in st.session_state:
            tools = [lookup_docs, ping_tool]

            agent = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True
            )

            try:
                result = agent.invoke({"input": prompt})
                answer = result.get("output", "(нет ответа)")
                st.chat_message("assistant").write(answer)
                st.session_state.messages.append(
                    SystemMessage(name="assistant", content=answer)
                )
            except Exception as e:
                error_msg = f"Ошибка агента: {e}"
                st.chat_message("assistant").write(error_msg)
                st.session_state.messages.append(
                    SystemMessage(name="assistant", content=error_msg)
                )
        else:
            st.warning("Сначала загрузите документы в базу знаний.")
