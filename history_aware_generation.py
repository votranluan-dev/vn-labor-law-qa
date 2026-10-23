from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

import re

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModel

_tok = AutoTokenizer.from_pretrained("BAAI/bge-reranker-v2-m3")
_rerank_model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-v2-m3").eval()

def rerank_scores(query, texts, batch_size=8):
    scores = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        inputs = _tok([query] * len(batch), batch, padding=True, truncation=True,
                      max_length=1024, return_tensors="pt")
        with torch.no_grad():
            logits = _rerank_model(**inputs).logits.view(-1)
        scores.extend(logits.tolist())
    return scores

# Load environment variables
load_dotenv()

class BgeM3Embeddings(Embeddings):
    def __init__(self, model_name="BAAI/bge-m3", batch_size=8):
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).eval()
        self.batch_size = batch_size

    def _encode(self, texts):
        out = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            inputs = self.tok(batch, padding=True, truncation=True,
                              max_length=1024, return_tensors="pt")
            with torch.no_grad():
                cls = self.model(**inputs).last_hidden_state[:, 0]
            cls = torch.nn.functional.normalize(cls, p=2, dim=1)
            out.extend(cls.tolist())
        return out

    def embed_documents(self, texts):
        return self._encode(texts)

    def embed_query(self, text):
        return self._encode([text])[0]

embeddings = BgeM3Embeddings()

# Connect to your document database
persistent_directory = "db"

db = Chroma(
    persist_directory=persistent_directory,
    embedding_function=embeddings,
    collection_metadata={"hnsw:space": "cosine"},
)

# Set up AI model (local)
model = ChatOllama(model="qwen2.5:7b", temperature=0, num_ctx=4096)

# Store our conversation as messages
chat_history = []
MAX_HISTORY = 6  # chỉ giữ 6 tin nhắn gần nhất (3 lượt hỏi-đáp) để không tràn num_ctx


def ask_question(user_question):
    print(f"\n--- Bạn hỏi: {user_question} ---")
    recent_history = chat_history[-MAX_HISTORY:]

    # Step 1: Viết lại câu hỏi thành dạng độc lập, dùng thuật ngữ pháp lý (chạy mọi lượt)
    past_questions = [m.content for m in recent_history if isinstance(m, HumanMessage)]
    history_text = "\n".join(f"- {q}" for q in past_questions) if past_questions else "(không có)"

    messages = [
        SystemMessage(content=(
            "Bạn là công cụ viết lại câu hỏi để tìm kiếm trong Bộ luật Lao động Việt Nam. "
            "Dựa vào các câu hỏi trước đó (nếu có), hãy viết lại câu hỏi mới thành MỘT CÂU HỎI "
            "đầy đủ, tự đứng độc lập, bằng tiếng Việt. "
            "Dùng thuật ngữ pháp lý: 'người lao động', 'người sử dụng lao động', "
            "'đơn phương chấm dứt hợp đồng lao động', 'kỷ luật sa thải', "
            "'không trả lương đầy đủ hoặc đúng thời hạn'... thay cho cách nói đời thường. "
            "Giữ nguyên ý nghĩa, không thêm thông tin mới. "
            "Câu viết lại phải kết thúc bằng dấu '?'. KHÔNG trả lời câu hỏi, KHÔNG giải thích."
        )),
        HumanMessage(content=(
            f"Các câu hỏi trước đó:\n{history_text}\n\n"
            f"Câu hỏi mới: {user_question}\n\n"
            "Câu hỏi viết lại:"
        )),
    ]

    result = model.invoke(messages)
    search_question = result.content.strip()
    print(f"Đang tìm với câu hỏi: {search_question}")

    # Step 2: Lấy nhiều ứng viên, rerank, gộp theo Điều, lấy 5 Điều tốt nhất
    hits = db.similarity_search(search_question, k=40)

    scores = rerank_scores(search_question, [h.page_content for h in hits])
    ranked = sorted(zip(hits, scores), key=lambda x: x[1], reverse=True)

    docs, seen = [], set()
    for h, s in ranked:
        art = h.metadata["article"]
        if art in seen:
            continue
        seen.add(art)
        docs.append(Document(page_content=h.metadata["full_text"], metadata=h.metadata))
        if len(docs) == 5:
            break

    print(f"Tìm thấy {len(docs)} Điều liên quan:")
    for i, doc in enumerate(docs, 1):
        print(f"  Doc {i}: Điều {doc.metadata['article']}. {doc.metadata['title']}")

    # Step 3: Create final prompt
    articles_text = "\n".join([f" - {doc.page_content}" for doc in docs])
    combined_input = f"""Các Điều luật sau thuộc Bộ luật Lao động 2019: 

{articles_text}

Hướng dẫn trả lời:
- Chỉ dùng các Điều luật ở trên, không dùng kiến thức bên ngoài. Nếu không đủ thông tin thì chỉ nói rõ là không đủ thông tin.
- Nếu quy định khác nhau theo từng trường hợp (ví dụ theo loại công việc), PHẢI liệt kê ĐẦY ĐỦ tất cả trường hợp, mỗi trường hợp một gạch đầu dòng.
- Khi nêu điều kiện hay con số, chép NGUYÊN VĂN cụm từ trong Điều luật (ví dụ "cộng dồn trong thời hạn 30 ngày", "không có lý do chính đáng"), không thay bằng từ khác như "liên tục". Không chép cả Điều, chỉ nêu phần liên quan. Không thêm lời khuyên không có trong Điều luật.
- Chú ý quy định áp dụng cho người lao động hay người sử dụng lao động, không nhầm lẫn.
- Trả lời bằng tiếng Việt. Không viết riêng dòng "Căn cứ" hay "Nguồn" ở cuối; chỉ nhắc số Điều ngay trong câu trả lời khi nêu quy định.
- Với câu hỏi tình huống ("tôi làm gì được", "có đúng không"), hãy nêu đủ: (1) quyền hoặc quy định áp dụng, (2) điều kiện hoặc thời hạn kèm theo (ví dụ số ngày báo trước, trường hợp ngoại lệ), (3) nghĩa vụ của bên còn lại nếu có. Mỗi ý ghi rõ Điều nào.
- Khi trích một điểm (a, b, c...) của một khoản, PHẢI nêu kèm câu dẫn của khoản đó (ví dụ khoản đó nói về trường hợp được nghỉ "không cần báo trước" hay "phải báo trước"). Chỉ ghi chữ cái điểm nếu nó xuất hiện đúng trong Điều luật ở trên; nếu không chắc thì chỉ ghi số khoản. Nếu Điều luật khác trong danh sách có quy định liên quan đến cùng tình huống (ví dụ nghĩa vụ bồi thường, đền bù), nêu thêm ý đó.

Câu hỏi: {search_question}
Trả lời:"""

    # Step 4: Get the answer
    messages = [
        SystemMessage(content="Bạn là trợ lý trả lời câu hỏi về Bộ luật Lao động Việt Nam 2019, chỉ dựa trên các Điều luật được cung cấp và lịch sử trò chuyện. Luôn trả lời bằng tiếng Việt.")
    ] + recent_history + [
        HumanMessage(content=combined_input)
    ]

    result = model.invoke(messages)
    raw_answer = result.content.strip()

    # Chỉ thêm nguồn và cảnh báo khi hiển thị, KHÔNG lưu vào lịch sử
    answer = raw_answer
    if "không đủ thông tin" not in raw_answer.lower():
        cited = sorted({int(n) for n in re.findall(r"Điều\s+(\d+)", raw_answer)})
        used = [d for d in docs if d.metadata["article"] in cited]
        if used:
            sources = "; ".join(f"Điều {d.metadata['article']}. {d.metadata['title']}" for d in used)
            answer += f"\n\nNguồn: {sources}"
    answer += "\n\n⚠️ Thông tin chỉ mang tính tham khảo, không thay thế tư vấn pháp lý."

    # Step 5: Remember this conversation (chỉ lưu câu hỏi gốc và câu trả lời gốc)
    chat_history.append(HumanMessage(content=user_question))
    chat_history.append(AIMessage(content=raw_answer))

    print(f"\nTrả lời: {answer}")
    return answer


# Simple chat loop
def start_chat():
    print("Hãy hỏi mình về Bộ luật Lao động 2019! Gõ 'quit' để thoát.")

    while True:
        question = input("\nCâu hỏi của bạn: ")

        if question.lower() == "quit":
            print("Tạm biệt!")
            break

        ask_question(question)


if __name__ == "__main__":
    start_chat()