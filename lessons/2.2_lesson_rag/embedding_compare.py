from langchain_openai import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

emb = OpenAIEmbeddings()
vec1 = emb.embed_query("Как оформить командировку?")
vec2 = emb.embed_query("Как получить доступ в офис?")

similarity = cosine_similarity([vec1], [vec2])[0][0]
print(f"\nСходство между текстом: {similarity:.2f}")
