from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

persistent_directory = "db"

# Load embeddings and vector store
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True},
)

db = Chroma(
    persist_directory=persistent_directory,
    embedding_function=embedding_model,
    collection_metadata={"hnsw:space": "cosine"},
)

# Search for relevant documents
query = "Người lao động nghỉ việc phải báo trước bao nhiêu ngày?"

retriever = db.as_retriever(search_kwargs={"k": 5})

relevant_docs = retriever.invoke(query)

print(f"User Query: {query}")
print("--- Context ---")
for i, doc in enumerate(relevant_docs, 1):
    print(f"Document {i}: Điều {doc.metadata['article']}. {doc.metadata['title']}")

# Combine the query and the relevant articles
combined_input = f"""Các Điều luật sau thuộc Bộ luật Lao động 2019:

{chr(10).join([f" - {doc.page_content}" for doc in relevant_docs])}

Hướng dẫn trả lời:
- Chỉ dùng các Điều luật ở trên, không dùng kiến thức bên ngoài.
- Nếu quy định khác nhau theo từng trường hợp, PHẢI liệt kê ĐẦY ĐỦ, mỗi trường hợp một gạch đầu dòng.
- Chỉ nêu những gì có trong các Điều luật, giữ nguyên các điều kiện của quy định, không thêm lời khuyên chung chung.
- Chú ý quy định áp dụng cho người lao động hay người sử dụng lao động, không nhầm lẫn.
- Nếu không đủ thông tin thì chỉ nói rõ là không đủ thông tin, không ghi dòng "Căn cứ".
- Kết thúc bằng đúng một dòng nguồn: "Căn cứ: Điều X. Tên Điều (khoản Y nếu có)".

Câu hỏi: {query}
Trả lời:"""

# Local model with Ollama
model = ChatOllama(model="qwen2.5:7b", temperature=0, num_ctx=8192)

messages = [
    SystemMessage(content="Bạn là trợ lý trả lời câu hỏi về Bộ luật Lao động Việt Nam 2019, chỉ dựa trên các Điều luật được cung cấp và lịch sử trò chuyện. Luôn trả lời bằng tiếng Việt."),
    HumanMessage(content=combined_input),
]

result = model.invoke(messages)

print("\n--- Generated Response ---")
print("Content only:")
print(result.content)