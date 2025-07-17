import json
import streamlit as st
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


def log_analysis_main():
    st.title("AI Assistant — Logs analyzer")

    model_name = st.sidebar.selectbox(
        "Выберите модель:",
        ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"]
    )

    # ---------------------------- STRUCT ----------------------------

    class LogEntry(BaseModel):
        message: str
        severity: str  # Возможные значения: low, mid, high

    parser = PydanticOutputParser(pydantic_object=LogEntry)

    # ---------------------------- PROMPTS ----------------------------

    SEVERITY_PROMPT = (
        "Ты ассистент по анализу логов сетевого оборудования Cisco Systems.\n"
        "Определи критичность события: 'low', 'mid' или 'high'.\n"
        "Ответ верни строго в формате ниже (JSON):\n\n"
        "{{" + parser.get_format_instructions().replace("{", "{{").replace("}", "}}") + "}}"
    )

    EXPLANATION_PROMPT = (
        "Ты сетевой инженер с опытом в Cisco IOS.\n"
        "Объясни лог, который предоставил пользователь.\n"
        "Что это значит? Как влияет на устройство? Что предпринять?\n"
        "Опиши кратко, но профессионально. Не придумывай, бери только достоверные данные."
    )

    # ---------------------------- LLM ----------------------------

    llm = init_chat_model(
        model_name,
        model_provider="openai",
        temperature=0.7,
    )

    # ---------------------------- LOAD LOGS ----------------------------

    if st.button("Загрузить логи"):
        try:
            with open("logs/logs.json", "r") as file:
                logs = json.load(file)
            st.session_state["logs"] = logs
            st.session_state["severity_done"] = False
            st.success(f"Загружено записей: {len(logs)}")
        except Exception as error:
            st.error(f"Ошибка при загрузке логов: {error}")

    if "logs" in st.session_state:
        logs = st.session_state["logs"]

    # ---------------------------- SEVERITY ----------------------------

        if st.button("Оценка критичности логов"):
            with st.spinner("Оцениваем критичность..."):
                severity_prompt = ChatPromptTemplate.from_messages([
                    ("system", SEVERITY_PROMPT),
                    ("user", "{log}")
                ])
                chain = severity_prompt | llm | parser

                severity_map = {}

                for log in logs:
                    try:
                        item_descriptions = [
                            f'IP: {item["ip"]}, Count: {item["count"]}, Message: {item["message"]}'
                            for item in log["items"]
                        ]
                        combined_items = "\n".join(item_descriptions)
                        input_msg = (
                            f'Event Type: {log["event_type"]}\n'
                            f'Total Count: {log["count"]}\n'
                            f'Items:\n{combined_items}'
                        )

                        result = chain.invoke({"log": input_msg})
                        severity_map[log["event_type"]] = result.severity
                    except Exception as e:
                        severity_map[log["event_type"]] = "n/a"
                        st.warning(f"Ошибка для event_type '{log['event_type']}': {e}")

                for log in logs:
                    log["severity"] = severity_map.get(log["event_type"], "n/a")

                st.session_state["severity_done"] = True

        # ---------------------------- SORTING ----------------------------

        sort_by = st.radio("Сортировать по:", ["Частоте", "Критичности"])

        if sort_by == "Критичности":
            if not st.session_state.get("severity_done"):
                st.warning("Сначала выполните оценку критичности логов")
                return
            logs.sort(
                key=lambda x: {"high": 0, "mid": 1, "low": 2}.get(x.get("severity", "mid"), 1)
            )
        else:
            logs.sort(key=lambda x: x["count"], reverse=True)

        # ---------------------------- DISPLAY ----------------------------

        messages_list = [f'{i + 1}. {log["event_type"]}' for i, log in enumerate(logs)]

        for index, log in enumerate(logs, start=1):
            event_type = log["event_type"]
            example = log["items"][0]["message"] if log["items"] else "(нет примера)"
            ips = ", ".join({item["ip"] for item in log["items"]})
            count = log["count"]
            severity = log.get("severity", "—")

            st.markdown(f"""
            <div style="font-size: 16px; line-height: 1.4; margin-bottom: 6px;">
                <b>N:</b> {index}<br>
                <b>Event type:</b> {event_type}<br>
                <b>Example:</b> {example}<br>
                <b>Devices:</b> {ips}<br>
                <b>Count:</b> {count}<br>
                <b>Severity:</b> {severity}
            </div>
            <hr style="margin: 6px 0;">
            """, unsafe_allow_html=True)

        # ---------------------------- ANALYZE SELECTED ----------------------------

        selected_index = messages_list.index(
            st.selectbox("🔍 Выберите лог для анализа", messages_list)
        )
        selected_info = logs[selected_index]

        if selected_info and st.button("Проанализировать"):
            event_type = selected_info["event_type"]
            count = selected_info["count"]

            # Генерируем подробный ввод на основе всех items
            item_lines = [
                f"IP: {item['ip']}, Count: {item['count']}, Message: {item['message']}"
                for item in selected_info["items"]
            ]
            items_text = "\n".join(item_lines)

            full_context = (
                f"Тип события: {event_type}\n"
                f"Общее количество: {count}\n"
                f"Подробности по устройствам:\n{items_text}"
            )

            explanation_prompt = ChatPromptTemplate.from_messages([
                ("system", EXPLANATION_PROMPT),
                ("user", "{input_text}")
            ])
            explanation_chain = explanation_prompt | llm
            try:
                response = explanation_chain.invoke({"input_text": full_context})
                st.subheader("💡 Анализ от LLM:")
                st.write(response.content)
            except Exception as e:
                st.error(f"Ошибка при анализе: {e}")
