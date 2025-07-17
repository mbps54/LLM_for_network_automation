import os
from datetime import datetime

import streamlit as st

import warnings
from langchain_core._api.deprecation import LangChainDeprecationWarning

# Подавляем предупреждение об устаревании AgentExecutor
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage

from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------------

def log_interaction(question: str, answer: str):
    """Сохраняет вопрос и ответ в файл ./history.log."""
    with open("./history.log", "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now().isoformat()} ---\n")
        f.write(f"Пользователь: {question}\n")
        f.write(f"Ассистент: {answer}\n")


# ---------------------------- MAIN ----------------------------

def chat_rag_main():
    st.title("AI Assistant — Chat & RAG")

    # Выбор модели
    model_name = st.sidebar.selectbox(
        "Выберите модель:",
        ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"]
    )

    # Инициализация модели
    llm = init_chat_model(
        model_name,
        model_provider="openai",
        temperature=0.3,
    )

    # История сообщений
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ---------------------- ЗАГРУЗКА ДОКУМЕНТОВ ----------------------

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
                        chunk_size=500,
                        chunk_overlap=100
                    )
                    splits = splitter.split_documents(documents)
                    embeddings = OpenAIEmbeddings()
                    vectorstore = FAISS.from_documents(splits, embeddings)
                    st.session_state.retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
                    st.success("✅ Документы загружены.")
            else:
                st.warning("./docs пуста. Поместите туда .txt или .md файлы.")

    # ---------------------- ОТОБРАЖЕНИЕ ИСТОРИИ ----------------------

    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
        elif isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)

    # ---------------------- ОБРАБОТКА ВВОДА ----------------------

    if prompt := st.chat_input("Введите ваш вопрос..."):
        user_msg = HumanMessage(content=prompt)
        st.chat_message("user").write(prompt)
        st.session_state.messages.append(user_msg)

        try:
            if "retriever" in st.session_state:
                # Преобразуем сообщения в формат (вопрос, ответ)
                chat_history = []
                last_user_msg = None
                for m in st.session_state.messages:
                    if isinstance(m, HumanMessage):
                        last_user_msg = m.content
                    elif isinstance(m, AIMessage) and last_user_msg:
                        chat_history.append((last_user_msg, m.content))
                        last_user_msg = None

                # Инициализация RAG-цепочки
                qa_chain = ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=st.session_state.retriever,
                    return_source_documents=True
                )

                result = qa_chain.invoke({
                    "question": prompt,
                    "chat_history": chat_history
                })

                answer = result.get("answer", "(нет ответа)")
                st.chat_message("assistant").write(answer)
                st.session_state.messages.append(AIMessage(content=answer))

                # Логируем только вопрос и ответ
                log_interaction(prompt, answer)

                # Отображение источников
                sources = result.get("source_documents", [])
                if sources:
                    with st.expander("Источники:"):
                        for i, doc in enumerate(sources, 1):
                            filename = doc.metadata.get("source", "неизвестный файл")
                            st.markdown(f"**Источник {i}: `{filename}`**")
            else:
                st.warning("Сначала загрузите документы.")
        except Exception as e:
            error_msg = f"Ошибка: {e}"
            st.chat_message("assistant").write(error_msg)
            st.session_state.messages.append(AIMessage(content=error_msg))
