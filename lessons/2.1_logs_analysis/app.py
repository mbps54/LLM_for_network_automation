#!/usr/bin/env python

import streamlit as st

from functions.log_analysis import log_analysis_main

SCENARIOS = {
    "Logs analyzer": log_analysis_main,
}


def main() -> None:
    st.set_page_config(layout="wide")

    page = st.sidebar.radio("Выберите сценарий:", list(SCENARIOS.keys()))
    SCENARIOS[page]()


if __name__ == "__main__":
    main()