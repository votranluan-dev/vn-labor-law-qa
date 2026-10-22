from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
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