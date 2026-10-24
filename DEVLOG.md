## Hạn chế đã biết (cập nhật sau khi chạy bộ test 11 câu)

Kết quả test gần nhất: **10/11 đạt** (từ khóa), nhưng đọc kỹ câu trả lời thì còn 2 câu chưa chính xác hoàn toàn.

### 1. Câu "tự ý nghỉ việc": sai điều kiện (nghiêm trọng nhất)
- Retrieval đúng (Điều 125 đứng đầu, ổn định 3/3 lần), nhưng model 7B viết **"05 ngày làm việc liên tục"**, trong khi luật ghi **"05 ngày cộng dồn trong 30 ngày hoặc 20 ngày cộng dồn trong 365 ngày"**.
- Nghi nguyên nhân: Điều 36 (đơn phương chấm dứt HĐLĐ) cũng có cụm "05 ngày làm việc liên tục", model trộn hai Điều.
- Đã thử: prompt viết lại dùng "sa thải/tự ý bỏ việc", cấm nhắc luật ngoài, `num_ctx=6144`, lọc Điều theo điểm rerank. Chưa hết hẳn.
- Hướng xử lý: hạ ngưỡng lọc điểm (4 → 2), thêm quy tắc "chỉ dùng Điều đúng hình thức xử lý", hoặc chỉ đưa đúng khoản liên quan thay vì cả Điều.

### 2. Câu "nợ lương": câu trả lời không ổn định
- Điều 35 và 97 đều nằm trong top 5, nhưng có lần model chỉ nêu ý Điều 35 (không cần báo trước), có lần chỉ nêu Điều 97 (đền bù lãi từ 15 ngày), hiếm khi nêu đủ cả hai.
- Câu hỏi cần ghép 2 Điều; model 7B không ổn định ở việc này.
- Hướng xử lý: thêm quy tắc "nêu ý từ TẤT CẢ các Điều liên quan, mỗi Điều một ý".

### 3. Giới hạn chung của model 7B
- Hay bỏ sót chi tiết phụ (ví dụ ngày nghỉ phép tăng theo thâm niên).
- Thỉnh thoảng sai chính tả ("la động"), ghi sai chữ cái điểm (a, b, c).
- Kết quả dao động nhẹ giữa các lần chạy dù `temperature=0` (do float16 và cách Ollama tính).
- Sửa prompt cho một câu có thể làm lệch câu khác. Luôn chạy lại đủ `test_questions.py` sau mỗi thay đổi.

### 4. Giới hạn của bộ test
- Chỉ kiểm tra từ khóa, không phát hiện được việc model bịa thêm ý hay kết luận ngược. Phải đọc lướt câu trả lời.
- Prompt viết lại có một mẫu cố định cho câu "tự ý bỏ việc": tốt cho câu test nhưng **không tổng quát** (cần thử thêm cách diễn đạt khác như "nghỉ 3 ngày không phép").

### 5. Phạm vi và hiệu năng
- Chỉ có Bộ luật Lao động 2019: câu về mức đóng BHXH (Luật BHXH) chỉ trả lời "không đủ thông tin". Hiện phụ thuộc model tự từ chối, chưa có ngưỡng điểm rerank.
- Chậm: khoảng 65-100 giây/câu (7B chạy lai CPU/GPU ~18%/82%, embedding và reranker chạy CPU, RAM 16 GB sát trần).
- Tìm kiếm chỉ dùng vector + rerank. Nếu Điều đúng không lọt top 25 của vector search thì reranker không cứu được (chưa có BM25/hybrid).

### 6. Môi trường
- Windows Application Control chặn `pyarrow`/`pandas` bản mới, nên không dùng được `sentence_transformers`, `FlagEmbedding` (đã tự viết embedding và reranker bằng `transformers`). Cẩn thận khi cài thêm thư viện (Streamlit, Gradio có thể kéo pandas/pyarrow): chạy `pip freeze` sao lưu trước.

### Lưu ý sử dụng
Chatbot chỉ mang tính tham khảo, không thay thế tư vấn pháp lý. Mọi câu trả lời đều kèm cảnh báo này (code tự thêm, không phụ thuộc model).

## Việc tiếp theo (cập nhật)
1. Giao diện Gradio + streaming (tách `chatbot.py`, `cli.py`, `app.py`).
2. Sửa 2 câu còn dao động nếu có thời gian (xem mục 1, 2).
3. Ngưỡng điểm rerank để từ chối câu ngoài phạm vi.
4. Hybrid search (BM25) nếu retrieval sót Điều; thêm Luật BHXH.