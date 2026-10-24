# DEVLOG: Chatbot Luật Lao động 2019

## Mục tiêu
Chatbot hỏi đáp Bộ luật Lao động Việt Nam 2019, chạy hoàn toàn local, có nhớ hội thoại.

## Cách hoạt động
1. **Ingest** (`ingestion_pipeline.py`, chạy 1 lần): cắt luật theo Điều, Điều dài cắt tiếp theo khoản, embed bằng `bge-m3`, lưu vào `db/` (Chroma).
2. **Chat** (`history_aware_generation.py`):
   - Viết lại câu hỏi thành câu pháp lý, độc lập (dùng các câu hỏi trước).
   - Lấy 25 chunk gần nghĩa nhất, rerank bằng `bge-reranker-v2-m3`, gộp theo Điều, lấy 5 Điều.
   - `qwen2.5:7b` (Ollama) trả lời chỉ dựa trên 5 Điều đó.
   - Code tự sinh dòng Nguồn và cảnh báo (không để model tự ghi).

## File chính
- `ingestion_pipeline.py`: tạo `db/`
- `embeddings.py`: lớp `BgeM3Embeddings` (viết bằng transformers)
- `history_aware_generation.py`: chatbot

## Quyết định quan trọng
- **Cắt theo Điều/khoản**, không dùng semantic/agentic chunking: luật có cấu trúc rõ.
- **Có reranker**: Điều 35 từ hạng 19 lên hạng 3 (vector search thuần bỏ sót).
- **Tự viết embedding** thay `HuggingFaceEmbeddings`: Windows Application Control chặn `pyarrow` (qua `sentence_transformers` → `datasets`).
- **qwen2.5:7b thay 3b**: 3b liệt kê thiếu và chép sai điều kiện ("liên tục" thay vì "cộng dồn").
- **Prompt ép chép nguyên văn điều kiện** và liệt kê đủ trường hợp.

## Thông số tối ưu (RTX 4050 6GB, RAM 16GB)
`float16`, `k=25`, rerank `max_length=512`, `batch_size=4`, `num_ctx=4096`.
Ingest lại phải dùng **cùng cấu hình embedding** (và xóa `db/` trước).

## Hạn chế
- Mất 1-2 phút/câu (7B chạy lai CPU/GPU, embed/rerank chạy CPU).
- Hay bỏ sót chi tiết phụ (VD: đền bù lãi khi nợ lương từ 15 ngày).
- Câu ngoài phạm vi (BHXH) phụ thuộc model tự nói "không đủ thông tin".

## Việc tiếp theo
1. Bộ test 11 câu tự động.
2. Giao diện Gradio + streaming (tách `chatbot.py`, `cli.py`, `app.py`).
3. Ngưỡng điểm reranker để từ chối câu ngoài phạm vi.
4. Hybrid search (BM25) nếu retrieval sót Điều; thêm Luật BHXH.