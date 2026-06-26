import redis
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

try:
    redis_client.ping()
    print("✅ Redis Connected")
except Exception:
    print("❌ Redis Not Available")

model = ChatMistralAI(model = "mistral-small-2506")

embedding_model = MistralAIEmbeddings()

vector_store = Chroma(
    persist_directory="Chroma_deep_learning-DB",
    embedding_function=embedding_model
                      )

retriever = vector_store.as_retriever(
    search_type="mmr", 
    search_kwargs={"k": 4,"fetch_k":10, "lambda_multi":0.5 },  
      # how many diverse results we want, 0.5 means we want equal balance of relevance and diversity
)


prompt = ChatPromptTemplate.from_messages([
    ("system", """ you are a helpful AI assistant .
     Use ONLY the provided context to answer the question.

    If the answwer is not in the context,
      say " I couldn't find the answer in the document"
    """),

("human", """
    this is the context : {context}
    this is the question : {question}
    """)
])   


print("---------------to exit enter 0-------------------------")
while True:
    query = input("Enter your question : ")
    if query == "0":
        print("exicted")
        break

    try:
        cached_answer = redis_client.get(query.strip().lower())
    except Exception as e:
        print(f"Error occurred while fetching from cache: {e}")
        cached_answer = None

    if cached_answer:
        print("-----------------------------------------------------------------------------------")
        print("Cache Hit ✅")
        print("AI : " + cached_answer)
        continue

    docs = retriever.invoke(query)
    context = "".join([doc.page_content for doc in docs])

    final_prompt = prompt.invoke({"context":context, "question":query})

    response = model.invoke(final_prompt)

    try:
        redis_client.set(query.strip().lower(), response.content, ex=3600)  # Cache the answer for 1 hour
    except Exception as e:
        print(f"Error occurred while saving to cache: {e}")

    print("-----------------------------------------------------------------------------------")
    print("AI : " + response.content)