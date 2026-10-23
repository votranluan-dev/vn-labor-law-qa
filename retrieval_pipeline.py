from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

persistence_directory = "db"


# TODO: Load embeddings and vector store
embeddings_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True},
)

db = Chroma(
    persist_directory=persistence_directory,
    embedding_function=embeddings_model,
    collection_metadata={"hnsw:space": "cosine"}
)


# TODO: Search for relevant documents
query = "Mức đóng bảo hiểm xã hội bắt buộc là bao nhiêu phần trăm lương?"

retriever = db.as_retriever(search_kwargs={"k": 5})  # Retrieve top 5 relevant documents

# retriever = db.as_retriever(
#     search_type="similarity_score_threshold",  # Use similarity search
#     search_kwargs={
#         "k": 5, 
#         "score_threshold": 0.5,
#     }
# )  # Retrieve top 5 relevant documents with source filter

relevant_docs = retriever.invoke(query)

print(f"User query: {query}")

print("--- Context ---")
for i, doc in enumerate(relevant_docs, 1):
    print(f"Document {i}: Điều {doc.metadata['article']}. {doc.metadata['title']}")


# Test
# 1. Người lao động nghỉ việc phải báo trước bao nhiêu ngày?
# 2. Thời gian thử việc tối đa là bao nhiêu ngày?
# 3. Lao động nữ được nghỉ thai sản bao lâu?
# 4. Thời giờ làm việc bình thường tối đa là bao nhiêu giờ trong một ngày?
# 5. Người lao động được nghỉ phép năm bao nhiêu ngày?

# 6. Làm thêm giờ vào ngày lễ được trả lương bao nhiêu phần trăm?
# 7. Hợp đồng lao động có những loại nào?
# 8. Người sử dụng lao động có được giữ bản chính giấy tờ tùy thân của người lao động không?

# 9. Công ty nợ lương tôi mấy tháng rồi thì tôi làm gì được?
# 10. Tôi tự ý nghỉ việc mấy ngày liền thì công ty cho nghỉ luôn có đúng không?

# 11. Mức đóng bảo hiểm xã hội bắt buộc là bao nhiêu phần trăm lương?


# TODO: Combine the query and relevant articles (Điều) into one prompt
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

# Create a local model with Ollama (free, runs on this machine)
# num_ctx phải đủ lớn để chứa 5 Điều, nếu mặc định quá nhỏ thì prompt bị cắt mất
model = ChatOllama(model="qwen2.5:7b", temperature=0, num_ctx=8192)

# Define messages for the model
messages = [
    SystemMessage(content="Bạn là trợ lý trả lời câu hỏi về Bộ luật Lao động Việt Nam 2019, chỉ dựa trên các Điều luật được cung cấp và lịch sử trò chuyện. Luôn trả lời bằng tiếng Việt."),
    HumanMessage(content=combined_input)
]

# Invoke the model with combined input
result = model.invoke(messages)

# Display the result
print("--- Content only ---")
print(result.content)