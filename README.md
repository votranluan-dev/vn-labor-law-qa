# vn-labor-law-qa

Chatbot hỏi đáp **Bộ luật Lao động 2019 (số 45/2019/QH14)** của Việt Nam. Người dùng hỏi bằng tiếng Việt, hệ thống tìm các Điều luật liên quan nhất và dùng chúng làm căn cứ để trả lời, kèm trích dẫn số Điều.

> ⚠️ **Lưu ý:** Đây là dự án học tập. Nội dung chỉ mang tính tham khảo, **không phải tư vấn pháp lý**. Khi cần giải quyết vấn đề thực tế, hãy tham khảo văn bản chính thức hoặc luật sư.

## Ví dụ câu hỏi

- Người lao động nghỉ việc phải báo trước bao nhiêu ngày?
- Lao động nữ được nghỉ thai sản bao lâu?
- Thời gian thử việc tối đa là bao nhiêu?
- Người sử dụng lao động được sa thải trong những trường hợp nào?

## Điểm nổi bật

- **Chia văn bản theo cấu trúc của luật.** Mỗi Điều là một đơn vị tìm kiếm, kèm thông tin Chương, Mục, tiêu đề. Cách này giữ trọn ngữ cảnh và cho phép trích dẫn chính xác "Điều X", khác với cách cắt theo độ dài ký tự thường thấy.
- **Tìm kiếm theo ngữ nghĩa**, không chỉ theo từ khóa: câu hỏi diễn đạt khác với văn bản luật vẫn có thể tìm đúng Điều.
- **Chạy hoàn toàn trên máy, miễn phí**: dùng mô hình embedding đa ngôn ngữ `BAAI/bge-m3` (hỗ trợ tiếng Việt), không cần API key trả phí cho phần tìm kiếm.
- **Lưu trữ vector bằng Chroma**, tạo một lần và dùng lại.

## Trạng thái dự án

Dự án đang phát triển.

- [x] Thu thập và làm sạch văn bản luật
- [x] Tách 220/220 Điều, kèm metadata
- [x] Tạo embedding và lưu vào vector store
- [ ] Truy vấn: hỏi và lấy ra các Điều liên quan
- [ ] Sinh câu trả lời bằng mô hình ngôn ngữ, kèm trích dẫn
- [ ] Bộ câu hỏi kiểm thử và đánh giá độ chính xác
- [ ] Giao diện web và triển khai

## Cách hoạt động

```
Văn bản luật (.txt)
      │
      ▼
 Tách thành 220 Điều + metadata
      │
      ▼
 Embedding (BAAI/bge-m3)  ──►  Chroma (thư mục db/)
```

Khi có câu hỏi: câu hỏi được đổi thành vector bằng cùng mô hình, Chroma trả về các Điều có vector gần nhất, rồi các Điều đó được dùng làm căn cứ để trả lời (phần này đang phát triển).

## Công nghệ

Python 3.13, LangChain, Chroma, Hugging Face (sentence-transformers), model `BAAI/bge-m3`.

## Cài đặt và chạy

Yêu cầu: Python 3.13, khoảng 3 GB dung lượng trống (cho thư viện và model).

**Windows (PowerShell):**
```powershell
git clone <đường-dẫn-repo>
cd vn-labor-law-qa

py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
python ingestion_pipeline.py
```

**macOS / Linux:**
```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python ingestion_pipeline.py
```

Lần chạy đầu tiên sẽ tải model embedding (khoảng 2 GB), nên mất một lúc. Chạy thành công sẽ thấy:

```
Tách được 220 Điều | Điều bị thiếu: không có
...
Vector store created and persisted to db
```

Nếu chạy lại, hãy xóa thư mục `db/` trước để tránh trùng dữ liệu.

## Cấu trúc thư mục

```
vn-labor-law-qa/
├── docs/
│   └── bo_luat_lao_dong_2019.txt   # văn bản luật
├── ingestion_pipeline.py           # đọc, tách Điều, tạo embedding, lưu vector store
├── requirements.txt
├── DEVLOG.md                       # nhật ký phát triển và giải thích chi tiết
└── README.md
```

Thư mục `db/` (vector store) được tạo ra khi chạy `ingestion_pipeline.py` và không được đưa lên git.

## Dữ liệu

Văn bản lấy từ Cơ sở dữ liệu quốc gia về văn bản pháp luật ([vbpl.vn](https://vbpl.vn)), Bộ luật Lao động số 45/2019/QH14, có hiệu lực từ 01/01/2021.

Lưu ý: trên vbpl.vn, văn bản này có trạng thái "hết hiệu lực một phần". Dữ liệu trong dự án là **bản gốc năm 2019**, chưa cập nhật các sửa đổi, bổ sung về sau, nên có thể có Điều đã thay đổi so với hiện hành.

## Kết quả đánh giá

_Sẽ bổ sung sau khi hoàn thành bộ câu hỏi kiểm thử._

## Tài liệu phát triển

Ghi chú kỹ thuật, các quyết định thiết kế, lỗi đã gặp và cách xử lý nằm trong [DEVLOG.md](DEVLOG.md).