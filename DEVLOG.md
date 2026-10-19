# DEVLOG: Nhật ký và hướng dẫn quay lại

File này viết cho **chính mình trong tương lai**. Nếu bạn (tôi) quay lại một commit cũ và không nhớ gì, hãy đọc file này từ trên xuống. Mục mới nhất ở trên cùng, mỗi mốc lớn thêm một mục.

Mẫu để thêm mục mới nằm ở cuối file.

---

# Mốc 1: Ingestion pipeline hoàn chỉnh

- **Ngày:** 2026-10-19
- **Git tag gợi ý:** `v0.1-ingestion`
- **Môi trường:** Windows, PowerShell, VS Code, Python 3.13.16

## 1. Dự án này là gì

Chatbot hỏi đáp **Bộ luật Lao động 2019 (45/2019/QH14)**. Người dùng hỏi bằng tiếng Việt, hệ thống tìm các Điều luật liên quan rồi dùng chúng làm căn cứ trả lời, kèm trích dẫn "Điều X".

Kỹ thuật dùng là **RAG** (Retrieval-Augmented Generation): thay vì để mô hình ngôn ngữ trả lời theo trí nhớ (dễ bịa), ta **tìm đoạn luật đúng trước**, rồi mới đưa cho mô hình đọc và trả lời dựa trên đó.

## 2. Trạng thái tại mốc này

| Phần | Trạng thái |
|---|---|
| Lấy dữ liệu luật, lưu thành `.txt` | Xong |
| Tách văn bản thành 220 Điều, kèm metadata | Xong |
| Tạo embedding và lưu vào Chroma (`db/`) | Xong |
| Truy vấn (retrieval): hỏi và lấy Điều liên quan | **Chưa làm** |
| Sinh câu trả lời bằng LLM | **Chưa làm** |
| Bộ test và đánh giá độ chính xác | **Chưa làm** |
| Giao diện, deploy | **Chưa làm** |

Nói gọn: ở mốc này mới xong nửa "chuẩn bị dữ liệu". Chưa hỏi đáp được gì.

## 3. Cấu trúc thư mục

```
vn-labor-law-qa/
├── docs/
│   └── bo_luat_lao_dong_2019.txt   # văn bản luật (nguồn vbpl.vn, UTF-8)
├── db/                             # vector store của Chroma (KHÔNG đưa lên git, tạo lại được)
├── venv/                           # môi trường ảo Python (KHÔNG đưa lên git)
├── .env                            # biến môi trường, hiện không còn dùng (KHÔNG đưa lên git)
├── .gitignore
├── ingestion_pipeline.py           # chương trình chính của mốc này
├── README.md                       # giới thiệu cho người ngoài
└── DEVLOG.md                       # file này
```

## 4. Các khái niệm cần nhớ

- **Chunk**: một đoạn văn bản nhỏ cắt ra từ tài liệu lớn. Hệ thống tìm kiếm theo chunk, không tìm theo cả bộ luật. Ở đây **1 chunk = 1 Điều luật**.
- **Embedding**: biến một đoạn văn thành một dãy số (vector). Hai đoạn có nghĩa gần nhau thì vector gần nhau. Nhờ vậy câu hỏi "nghỉ việc phải báo trước bao lâu" tìm ra được Điều nói về đơn phương chấm dứt hợp đồng, dù không trùng từ khóa.
- **Vector store (Chroma)**: cơ sở dữ liệu lưu các vector và tìm nhanh "vector nào gần vector câu hỏi nhất". Dữ liệu lưu ở thư mục `db/`.
- **Metadata**: thông tin đi kèm mỗi chunk (số Điều, tiêu đề, Chương, Mục, nguồn). Đây là thứ giúp chatbot trích dẫn được "Điều 35", không chỉ trả về một đoạn chữ vô danh.
- **Retriever**: bước nhận câu hỏi, đổi thành vector, rồi lấy ra k chunk gần nhất.

## 5. Code chạy như thế nào

File `ingestion_pipeline.py` có 3 bước, đúng theo khung tutorial (tên hàm giữ nguyên để đối chiếu video):

```
main()
 ├── 1. load_documents()       đọc file .txt trong docs/
 ├── 2. split_documents()      cắt thành từng Điều (gọi parse_law)
 └── 3. create_vector_store()  embedding + lưu vào db/
```

### Bước 1: `load_documents`
Dùng `DirectoryLoader` + `TextLoader` để đọc mọi file `.txt` trong `docs/`. Bắt buộc có `loader_kwargs={"encoding": "utf-8"}`, nếu thiếu thì Windows đọc bằng bảng mã `cp1252` và lỗi tiếng Việt.

Kết quả: 1 Document khổng lồ chứa cả bộ luật (khoảng 190.000 ký tự).

### Bước 2: `split_documents` và `parse_law`
Đây là phần **khác tutorial gốc**. Tutorial dùng `CharacterTextSplitter` cắt theo độ dài (800 ký tự), làm đứt Điều giữa chừng. Ở đây `parse_law` đọc từng dòng và nhận dạng cấu trúc bằng regex:

- Dòng bắt đầu bằng `Chương I`, `Chương II`... thì cập nhật Chương hiện tại. Dòng ngay sau đó là tên Chương.
- Dòng bắt đầu bằng `Mục 1`... thì cập nhật Mục hiện tại.
- Dòng bắt đầu bằng `Điều 12.` thì **đóng Điều đang đọc** và **mở Điều mới**.
- Các dòng còn lại (khoản `1.`, điểm `a)`...) được nối vào Điều đang mở.
- Dòng trống và dòng chỉ có số (số trang) bị bỏ.
- Trước khi xử lý, văn bản được chuẩn hóa Unicode (`NFC`) để dấu tiếng Việt khớp regex.

Sau khi tách, hàm tự kiểm tra: Bộ luật có 220 Điều, nên in ra "Điều bị thiếu" nếu có. **Đây là dòng để xác nhận pipeline đúng.**

Mỗi chunk có metadata dạng:
```python
{'source': 'docs\\bo_luat_lao_dong_2019.txt', 'article': 1,
 'title': 'Phạm vi điều chỉnh', 'chapter': 'Chương I - NHỮNG QUY ĐỊNH CHUNG', 'section': ''}
```

### Bước 3: `create_vector_store`
- Tạo model embedding `BAAI/bge-m3` qua `HuggingFaceEmbeddings` (chạy trên máy, hỗ trợ tiếng Việt, tải về lần đầu khoảng 2 GB).
- `Chroma.from_documents(...)` tính vector cho từng chunk và lưu vào `db/`. Cấu hình `hnsw:space = cosine` nghĩa là đo độ gần bằng cosine.
- Chroma bản mới tự lưu xuống ổ đĩa, **không cần** gọi `vector_store.persist()`.

## 6. Các quyết định kỹ thuật và lý do

| Quyết định | Lý do |
|---|---|
| Chunk theo Điều, bỏ `CharacterTextSplitter` | Cắt theo độ dài làm đứt Điều, chunk mất số Điều, trích dẫn sẽ sai |
| Embedding `bge-m3` chạy cục bộ, bỏ OpenAI | Không có tiền nạp API. bge-m3 đa ngôn ngữ, có tiếng Việt, miễn phí |
| Python 3.13, không dùng 3.15 | 3.15 quá mới, nhiều thư viện chưa có bản build sẵn cho Windows, pip phải tự biên dịch và đòi C++ Build Tools |
| Giữ tên hàm theo tutorial | Để đối chiếu video hướng dẫn mà không phải đoán |
| Lấy dữ liệu từ tab "Nội dung" của vbpl.vn, không dùng PDF | PDF là bản scan, phải OCR, dễ sai dấu. Tab "Nội dung" có chữ thật |
| Tắt công tắc "Hiển thị chi tiết cập nhật" khi copy | Công tắc này có thể chèn ghi chú sửa đổi vào giữa nội dung |

## 7. Cách chạy lại từ đầu

Giả sử vừa clone repo về máy mới, hoặc quay lại sau thời gian dài.

```powershell
# 1. Tạo môi trường ảo bằng Python 3.13
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python --version                      # phải ra Python 3.13.x

# 2. Cài thư viện
pip install -r requirements.txt

# 3. Chạy (xóa db cũ trước nếu có, để không bị trùng dữ liệu)
Remove-Item -Recurse -Force db
python ingestion_pipeline.py
```

Nếu chưa có `requirements.txt` thì tạo từ môi trường đang chạy được: `pip freeze > requirements.txt`. Hoặc cài tay:

```powershell
pip install langchain-community langchain-core langchain-huggingface langchain-chroma sentence-transformers python-dotenv
```

### Dấu hiệu chạy đúng
- In ra `Tách được 220 Điều | Điều bị thiếu: không có`.
- Metadata của Chunk 1 có `article`, `title`, `chapter`.
- Cuối cùng in `Vector store created and persisted to db`.
- Thư mục `db/` xuất hiện, mở `chroma.sqlite3` thấy bảng `embeddings` có **220 dòng**.

Lần chạy đầu sẽ đứng yên một lúc để tải model (khoảng 2 GB). Bình thường.

## 8. Lỗi đã gặp và cách xử lý

| Lỗi | Nguyên nhân thật | Cách sửa |
|---|---|---|
| `Microsoft Visual C++ 14.0 or greater is required` khi `pip install` | Dùng Python 3.15, thư viện không có bản build sẵn nên pip tự biên dịch | Dùng Python 3.13 |
| Tải nhầm file có `configure`, `Makefile.pre.in` | Đó là mã nguồn Python cho Linux/macOS. Bản 3.12.15 chỉ phát hành mã nguồn | Dùng Python install manager (`py install 3.13`) |
| `py list` báo "legacy py.exe" | Máy còn Python Launcher bản cũ | Gỡ "Python Launcher" trong Installed apps, mở terminal mới |
| `UnicodeDecodeError: 'charmap' codec can't decode` | `TextLoader` không chỉ định encoding, Windows đọc bằng cp1252 | Thêm `loader_kwargs={"encoding": "utf-8"}` |
| `Sync client is not available...` | **Thông báo gây hiểu lầm.** Thật ra `api_key` là `None` vì tên biến trong `.env` bị sai (`OPENAI_ADMIN_KEY` thay vì `OPENAI_API_KEY`) | Đổi đúng tên biến |
| `429 insufficient_quota` | Tài khoản OpenAI API không có credit | Chuyển sang embedding cục bộ `bge-m3` |
| Cảnh báo `langchain-community is being sunset` | Gói sắp ngừng bảo trì | Vô hại, chưa xử lý |
| Cảnh báo `symlinks` của Hugging Face | Windows không bật Developer Mode | Vô hại, chỉ tốn thêm dung lượng cache |

Bài học chung: khi báo lỗi lạ, in giá trị biến ra kiểm tra trước (ví dụ `bool(os.getenv("..."))`) rồi mới đoán nguyên nhân.

## 9. Cách quay lại commit này bằng git

Xem lịch sử:
```powershell
git log --oneline
git tag
```

Quay về mốc này (chỉ để xem, ở trạng thái "detached HEAD"):
```powershell
git checkout v0.1-ingestion        # hoặc: git checkout <mã-commit>
```

Muốn sửa gì tiếp từ mốc này thì tạo nhánh mới, đừng sửa trực tiếp:
```powershell
git switch -c thu-nghiem-tu-v0.1
```

Xong việc, quay về nhánh chính:
```powershell
git switch main
```

Tạo tag cho mốc này (nếu chưa có):
```powershell
git tag -a v0.1-ingestion -m "Ingestion pipeline hoàn chỉnh, chưa có retrieval"
```

### Lưu ý khi quay lại
Những thứ **không nằm trong git** nên sau khi checkout phải tạo lại:
- `venv/`: tạo lại theo mục 7.
- `db/`: chạy lại `python ingestion_pipeline.py`.
- `.env`: hiện không cần. Nếu sau này dùng API key thì tự tạo lại, **không bao giờ commit**.

File `docs/bo_luat_lao_dong_2019.txt` **có** nằm trong git nên không phải tải lại.

## 10. Việc tiếp theo

1. Viết `retrieval_pipeline.py`: mở lại `db/`, hỏi một câu, in ra 3 Điều gần nhất. **Phải dùng đúng model `bge-m3` như lúc tạo `db`**, khác model thì vector không so sánh được.
2. Thử 5-10 câu hỏi (nghỉ việc, thai sản, lương, thử việc, sa thải...), ghi lại câu nào ra đúng Điều, câu nào sai.
3. Chọn LLM miễn phí để viết câu trả lời dựa trên các Điều tìm được, bắt buộc kèm trích dẫn.
4. Viết bộ test khoảng 40 câu hỏi kèm Điều đúng, đo độ chính xác retrieval.
5. Giao diện (Streamlit) và deploy.

## 11. Vấn đề còn mở

- Một số Điều rất dài, chunk có thể quá lớn so với giới hạn tốt của model. Cân nhắc cắt nhỏ bên trong Điều nhưng vẫn giữ số Điều trong metadata.
- Chưa biết `bge-m3` tìm tiếng Việt pháp lý tốt đến đâu. Cần đo bằng bộ test, không đoán.
- Văn bản dùng là bản gốc 2019, "hết hiệu lực một phần" theo vbpl.vn. Chưa cập nhật các sửa đổi sau đó. Có thể xem bản "Văn bản hợp nhất" sau.
- Chạy `ingestion_pipeline.py` lần 2 mà không xóa `db/` sẽ thêm trùng dữ liệu. Có thể sửa code để tự xóa hoặc kiểm tra trước khi tạo.
- Chưa có `requirements.txt` cố định phiên bản.

---

# Mẫu cho mục mới

Copy khối này, dán lên **trên** mục cũ nhất, điền vào.

```markdown
# Mốc N: <tên ngắn gọn>

- **Ngày:**
- **Git tag / commit:**

## Đã làm
-

## Trạng thái (chạy được / chưa)
-

## Quyết định kỹ thuật và lý do
-

## Lỗi gặp và cách xử lý
-

## Cách chạy và kiểm tra đúng
-

## Việc tiếp theo
-

## Vấn đề còn mở
-
```