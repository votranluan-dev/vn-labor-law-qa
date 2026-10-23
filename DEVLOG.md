# DEVLOG: Cách hoạt động của chatbot Luật Lao động 2019

## Hình dung đơn giản

Hãy tưởng tượng một **thư viện** chỉ có một cuốn sách là Bộ luật Lao động.

- **Thủ thư** (embedding + reranker): tìm đúng những trang liên quan đến câu hỏi.
- **Người trả lời** (model qwen2.5:7b chạy bằng Ollama): đọc những trang đó rồi trả lời bằng tiếng Việt.
- **Cuốn sổ nhớ** (chat_history): ghi lại các câu đã hỏi để hiểu những câu như "Còn với trường hợp kia thì sao?".

Người trả lời **không được dùng kiến thức bên ngoài**, chỉ được dựa vào các trang thủ thư đưa.

## Chuẩn bị trước (ingestion_pipeline.py)

1. Đọc file luật, cắt thành từng **Điều**. Điều nào dài thì cắt tiếp theo **khoản** để tìm kiếm chính xác hơn.
2. Mỗi mảnh được đổi thành một dãy số (vector) bằng model `bge-m3`, rồi lưu vào thư mục `db/` (Chroma).
3. Mỗi mảnh giữ kèm toàn văn cả Điều trong metadata `full_text`, để lúc trả lời có thể đưa cả Điều cho model.

Chỉ cần chạy một lần. Phải xóa `db/` rồi chạy lại nếu đổi cách cắt.

---

## File 1: history_aware_generation.py (bản chính, có nhớ hội thoại)

Mỗi lần người dùng hỏi, chương trình đi qua 6 bước:

**Bước 1. Viết lại câu hỏi.**
Câu đời thường như "Công ty nợ lương tôi thì làm gì?" khó khớp với văn luật. Chương trình nhờ model viết lại thành câu pháp lý, ví dụ "Người lao động không được trả lương đầy đủ hoặc đúng thời hạn thì có quyền làm gì?". Câu này cũng được bổ sung ngữ cảnh từ các câu hỏi trước. Chỉ gửi các **câu hỏi cũ của người dùng**, không gửi câu trả lời cũ, để model không chép lại đáp án.

**Bước 2. Tìm thô.**
Câu đã viết lại được đổi thành vector, rồi lấy **40 mảnh** gần nghĩa nhất trong `db/`.

**Bước 3. Chấm điểm lại (reranker).**
Tìm theo vector hay xếp sai thứ tự (Điều 35 từng đứng hạng 19). Model `bge-reranker-v2-m3` đọc kỹ từng cặp (câu hỏi, mảnh) và chấm lại. Sau đó gộp các mảnh cùng một Điều, lấy **5 Điều** tốt nhất, mỗi Điều lấy trọn văn bản.

**Bước 4. Hỏi model.**
Prompt gồm 5 Điều luật, các quy tắc (chỉ dùng Điều ở trên, liệt kê đủ mọi trường hợp, chép nguyên văn điều kiện như "cộng dồn", "không có lý do chính đáng") và câu hỏi. `temperature=0` để câu trả lời ổn định.

**Bước 5. Hoàn thiện bằng code, không nhờ model.**
- Quét câu trả lời, thấy "Điều X" nào thì ghi thành dòng **Nguồn** (model hay ghi nguồn sai nên để code làm).
- Luôn thêm cảnh báo "chỉ mang tính tham khảo, không thay thế tư vấn pháp lý".
- Nếu model nói "không đủ thông tin" thì không ghi nguồn.

**Bước 6. Ghi nhớ.**
Lưu câu hỏi gốc và câu trả lời gốc (chưa có phần nguồn) vào `chat_history`. Chỉ giữ 6 tin gần nhất (`MAX_HISTORY=6`) để không tràn bộ nhớ của model.

### Các thông số quan trọng

| Thông số | Giá trị | Ý nghĩa |
|---|---|---|
| Embedding | bge-m3 (tự viết bằng transformers) | Đổi chữ thành vector |
| Reranker | bge-reranker-v2-m3 | Chấm lại độ liên quan |
| Số mảnh tìm thô | 40 | Rộng để không bỏ sót |
| Số Điều đưa cho model | 5 | Sau khi rerank |
| Model trả lời | qwen2.5:7b | Chạy local bằng Ollama |
| num_ctx | 4096 | Giảm để vừa VRAM 6 GB |

### Vì sao tự viết embedding mà không dùng HuggingFaceEmbeddings?

Windows (Application Control) chặn file `pyarrow` mà `sentence_transformers` cần. Lớp `BgeM3Embeddings` gọi thẳng `transformers`, nên né được lỗi, và vector vẫn khớp DB cũ.

---

## File 2: answer_generation.py (bản đơn giản, không nhớ)

Cùng ý tưởng nhưng **đơn giản hơn nhiều**, chỉ có 4 việc:

1. Có sẵn **một câu hỏi cố định** trong code (biến `query`).
2. Tìm **5 mảnh** gần nghĩa nhất (không viết lại câu hỏi, không rerank).
3. Đưa các mảnh và quy tắc cho qwen2.5:7b, yêu cầu model tự ghi dòng "Căn cứ".
4. In câu trả lời rồi kết thúc.

Không có `chat_history`, không có vòng lặp chat, nên không nhớ gì giữa các lần hỏi.

### So sánh nhanh

| | answer_generation.py | history_aware_generation.py |
|---|---|---|
| Nhớ hội thoại | Không | Có (6 tin gần nhất) |
| Viết lại câu hỏi | Không | Có |
| Rerank | Không | Có |
| Nguồn trích dẫn | Model tự ghi (hay sai) | Code tự sinh |
| Vòng lặp chat | Không (1 câu cố định) | Có |
| Dùng làm gì | Thử nhanh một câu hỏi | Chatbot hoàn chỉnh |

### Lưu ý

`answer_generation.py` vẫn dùng `HuggingFaceEmbeddings`, nên **hiện sẽ báo lỗi trên máy này** (bị Application Control chặn). Nó còn giữ prompt kiểu cũ, chưa cập nhật các quy tắc mới. Coi nó là bản nháp để học. Muốn dùng thì thay phần embedding bằng lớp `BgeM3Embeddings` như file 1.

---

## Cách chạy

1. Bật Ollama (mở app, hoặc kiểm tra bằng `ollama list`).
2. Chạy ingest một lần: `python ingestion_pipeline.py`.
3. Chạy chatbot: `python history_aware_generation.py`.

## Hạn chế đã biết

- Model 7B đôi khi bỏ sót chi tiết phụ (ví dụ ngày nghỉ tăng theo thâm niên, hay ý đền bù lãi khi nợ lương từ 15 ngày).
- Câu hỏi cần ghép nhiều Điều (như nợ lương) khó hơn câu hỏi trực tiếp.
- Luật BHXH không nằm trong Bộ luật Lao động, nên chatbot đúng ra phải trả lời "không đủ thông tin".
- Qwen 7B chưa nằm trọn trong GPU (khoảng 18% chạy bằng CPU) nên hơi chậm.