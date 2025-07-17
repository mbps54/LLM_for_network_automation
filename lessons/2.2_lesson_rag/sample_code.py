from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Загружаем документы
loader = TextLoader("./docs/corporate_wiki.md")
documents = loader.load()

# 2. Индексируем
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)
retriever = vectorstore.as_retriever()

# 3. Инициализируем LLM
llm = init_chat_model("gpt-4o-mini", model_provider="openai")

# 4. Prompt-шаблон
prompt = ChatPromptTemplate.from_messages([
    ("system", "Ты — ассистент сетевого инженера. Отвечай с учетом документации."),
    ("human", "Контекст:\n{context}\n\nВопрос: {question}")
])

# 5. Вопрос
question = "Как оформить командировку?"

# 6. Создаем LCEL-цепочку
rag_chain = (
    {"context": retriever, "question": lambda x: x}
    | prompt
    | llm
    | StrOutputParser()
)

# 7. Выполняем цепочку
response = rag_chain.invoke(question)
print(response)

# 8. Отладка — смотрим реальный prompt
docs = retriever.invoke(question)
context_text = "\n\n".join([doc.page_content for doc in docs])
prompt_value = prompt.format_prompt(context=context_text, question=question)
print("\n==> Сформированный prompt:\n")
print(prompt_value.to_string())

# 9. Источники
print("\nИспользованные источники:")
for i, doc in enumerate(docs, 1):
    source = doc.metadata.get("source", "неизвестный файл")
    print(f"  - документ {i}: {source}")