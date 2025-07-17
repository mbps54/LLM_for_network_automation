import os
import ipaddress

import streamlit as st
from pydantic import BaseModel, Field

import warnings
from langchain_core._api.deprecation import LangChainDeprecationWarning

# Подавляем предупреждение об устаревании AgentExecutor
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import ToolException, tool

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools.ping import ping
from tools.cmdb import cmdb
from tools.show_vlan_port import show_vlan_port
from tools.show_vlan_ports_all import show_vlan_ports_all
from tools.change_vlan import change_vlan


# ---------------------------- TOOLS ----------------------------

@tool
def lookup_docs(query: str) -> str:
    """
    lookup_docs(query: str) -> str

    Ищет информацию по внутренней документации: IP-адреса, hostname, описания и т.д.
    Используй, если cmdb() не дал IP.

    Аргумент:
    - query: IP, hostname или ключевое слово. Например, "BI" или "asw1"
    """
    if retriever is None:
        raise ToolException("База знаний не загружена.")
    docs = retriever.invoke(query)
    if not docs:
        raise ToolException("Ничего не найдено в документации.")
    return "\n\n".join(doc.page_content for doc in docs)


class PingInput(BaseModel):
    ip: str = Field(..., description="IPv4-адрес устройства")

@tool(args_schema=PingInput)
def ping_tool(ip: str) -> str: # TSHOOT
    """
    Проверяет доступность IP-адреса через ping.
    Используется только при наличии корректного IP-адреса.
    """
    ipaddress.IPv4Address(ip)
    result = str(ping(ip)) # TSHOOT
    return result

class CmdbInput(BaseModel):
    name: str = Field(..., description="Имя устройства (hostname)")

@tool(args_schema=CmdbInput)
def cmdb_tool(name: str) -> str:
    """
    Получает IP-адрес по имени устройства из CMDB.
    Если IP не найден — используй lookup_docs(). # TUNING
    """
    ip = cmdb(name)
    if not ip:
        raise ToolException(f"IP-адрес для {name} не найден в CMDB.")
    return ip

class ShowVlanPortInput(BaseModel):
    ip: str = Field(..., description="IP-адрес устройства")
    port: str = Field(..., description="Имя порта (например, Gi0/1)")

@tool(args_schema=ShowVlanPortInput)
def show_vlan_port_tool(ip: str, port: str) -> str:
    """
    Показывает VLAN, настроенный на конкретном порту сетевого устройства.
    Требуются IP-адрес и имя порта.
    """
    ipaddress.IPv4Address(ip)
    return show_vlan_port(ip, port)

class ShowAllPortsInput(BaseModel):
    ip: str = Field(..., description="IP-адрес устройства")

@tool(args_schema=ShowAllPortsInput)
def show_vlan_ports_all_tool(ip: str) -> str:
    """
    Показывает список всех портов устройства с соответствующими VLAN.
    Требуется IP-адрес устройства.
    """
    ipaddress.IPv4Address(ip)
    return show_vlan_ports_all(ip)

class ChangeVlanInput(BaseModel):
    ip: str = Field(..., description="IP-адрес устройства")
    port: str = Field(..., description="Имя порта (например, Gi0/1)")
    vlan: int = Field(..., description="Номер VLAN (например, 10)")

@tool(args_schema=ChangeVlanInput)
def change_vlan_tool(ip: str, port: str, vlan: int) -> str:
    """
    Изменяет VLAN на заданном порту устройства.
    Требуются IP-адрес, имя порта и номер VLAN.
    """
    ipaddress.IPv4Address(ip)
    return change_vlan(ip, port, vlan)


# ---------------------------- SETUP ----------------------------

retriever = None


def build_prompt_from_history(messages, system_prompt: str) -> str:
    """
    Формирует текст запроса для агента из истории сообщений и текущего ввода.
    """
    lines = [f"[Системное сообщение]: {system_prompt}"]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            lines.append(f"Пользователь: {msg.content}")
        elif hasattr(msg, "name") and msg.name == "assistant":
            lines.append(f"Ассистент: {msg.content}")
    #lines.append(f"Пользователь: {new_user_input}\n")
    return "\n".join(lines)


# ---------------------------- MAIN ----------------------------

def chat_rag_multitools_memory_main():
    global retriever

    st.title("AI Assistant — Chat & RAG & Multitools & Memory")

    model_name = st.sidebar.selectbox(
        "Выберите модель:",
        ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"]
    )

    llm = init_chat_model(model_name, model_provider="openai", temperature=0.3)

    system_prompt = (
        "Ты — ассистент в корпоративной IT-инфраструктуре.\n"
        "Если в запросе указано имя устройства (например, 'asw1'), но не указан IP, то:\n"
        "1. Сначала вызови cmdb_tool(), чтобы получить IP по имени.\n"
        "2. Если cmdb_too() не дал результата — вызови lookup_docs().\n"
        "Никогда не придумывай IP-адрес — только через cmdb_tool() или lookup_docs().\n"
        "RAG c корпоративными документами и справочной информацией доступен по lookup_docs().\n"
        "Отвечай строго на основе данных из внутренней документации\n"
        "Отвечай кратко и по делу.\n"
        "Не отвечай в формате Markdown, отвечай удобно читаемым текстом.\n" # TUNING
        "Если пишешь список команд, то пиши каждую команду с новой строки."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

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
                        chunk_size=500, # TUNING
                        chunk_overlap=100 # TUNING
                    )
                    splits = splitter.split_documents(documents)
                    embeddings = OpenAIEmbeddings()
                    vectorstore = FAISS.from_documents(splits, embeddings)
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 2}) # TUNING
                    st.session_state.retriever = retriever
                    st.success("✅ Загружено и проиндексировано")
            else:
                st.warning("Директория ./docs пуста")

    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
        elif hasattr(msg, "name") and msg.name == "assistant":
            st.chat_message("assistant").write(msg.content)

    if prompt := st.chat_input("Введите вопрос..."):
        user_msg = HumanMessage(content=prompt)
        st.chat_message("user").write(user_msg.content)
        st.session_state.messages.append(user_msg)

        tools = [
            lookup_docs,
            ping_tool,
            show_vlan_port_tool,
            show_vlan_ports_all_tool,
            change_vlan_tool,
            cmdb_tool
        ]

        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True, # TSHOOT
            handle_parsing_errors=True, # TUNING
            max_iterations=10, # TUNING
            max_execution_time=90, # TUNING
        )

        try:
            full_prompt = build_prompt_from_history(
                messages=st.session_state.messages,
                system_prompt=system_prompt
            )
            print(f"==> full prompt:\n{full_prompt}")
            result = agent.invoke({"input": full_prompt})
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