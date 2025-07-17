#!/usr/bin/env python

import streamlit as st

from functions.log_analysis import log_analysis_main
from functions.chat_rag import chat_rag_main
from functions.chat_rag_tools import chat_rag_tools_main
from functions.chat_rag_multitools import chat_rag_multitools_main
from functions.chat_rag_multitools_memory import chat_rag_multitools_memory_main

SCENARIOS = {
    "Logs analyzer": log_analysis_main,
    "Chat & RAG": chat_rag_main,
    "Chat & RAG & Tools": chat_rag_tools_main,
    "Chat & RAG & Multitools": chat_rag_multitools_main,
    "Chat & RAG & Multitools & Memory": chat_rag_multitools_memory_main,
}


def main() -> None:
    st.set_page_config(layout="wide")

    page = st.sidebar.radio("Выберите сценарий:", list(SCENARIOS.keys()))
    SCENARIOS[page]()


if __name__ == "__main__":
    main()