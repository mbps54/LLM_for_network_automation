import json
from pydantic import BaseModel
from langchain.chat_models import init_chat_model  # инициализация модели
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# 1. Описание структуры вывода
class LogEntry(BaseModel):
    message: str
    severity: str  # значения: low, mid, high

# 2. Парсер, соответствующий структуре
parser = PydanticOutputParser(pydantic_object=LogEntry)

# 3. Инструкция + экранируем формат согласно PydanticOutputParser
instruction = (
    "Ты ассистент по анализу сетевых логов с сетевого оборудования. "
    "Определи критичность сообщения: 'low', 'mid' или 'high'. "
    "Ответ верни строго в формате ниже (JSON):\n\n"
    "{{" + parser.get_format_instructions().replace("{", "{{").replace("}", "}}") + "}}"
)

# 4. Шаблон промпта с переменной
prompt = ChatPromptTemplate.from_messages([
    ("system", instruction),
    ("user", "{log}")
])

# 5. Инициализация модели через LangChain
llm = init_chat_model(
    model="gpt-4o-mini",
    model_provider="openai",
    temperature=0.3
)

# 6. Построение цепочки: prompt → model → parser
chain = prompt | llm | parser

# 7. Пример входного сообщения
log_message = "Сегодня получили такой лог от коммутатора  %SYS-3-CPUHOG: Task ran for 3000ms"

# 8. Вызов цепочки
result = chain.invoke({"log": log_message})

# 9. Вывод результата в JSON-формате
print(json.dumps(result.model_dump(), indent=2))