# DEVLOG: Nhật ký và hướng dẫn quay lại

File này viết cho **chính mình trong tương lai**. Nếu quay lại một commit cũ mà không nhớ gì, hãy đọc từ trên xuống:

- **Phần A: Tổng quan** (dự án là gì, khái niệm, cấu trúc thư mục, cách quay lại commit). Đọc trước.
- **Phần B: Các mốc**, mục mới nhất ở trên cùng. Mỗi mốc có giảng source code, kết quả, lỗi đã gặp, việc tiếp theo.
- **Phần C: Mẫu** để thêm mốc mới.

---

# Phần A: Tổng quan

## A1. Dự án này là gì

Chatbot hỏi đáp **Bộ luật Lao động 2019 (45/2019/QH14)**. Người dùng hỏi bằng tiếng Việt, hệ thống tìm các Điều luật liên quan rồi dùng chúng làm căn cứ trả lời, kèm trích dẫn "Điều X".

Kỹ thuật dùng là **RAG** (Retrieval-Augmented Generation): thay vì để mô hình ngôn ngữ trả lời theo trí nhớ (dễ bịa), ta **tìm đoạn luật đúng trước**, rồi mới đưa cho mô hình đọc và trả lời dựa trên đó.

```
HAI GIAI ĐOẠN

[Chuẩn bị, chạy 1 lần]   ingestion_pipeline.py
  văn bản luật ──► tách 220 Điều ──► embedding ──► lưu vào db/

[Mỗi lần có câu hỏi]     retrieval_pipeline.py
  câu hỏi ──► embedding ──► tìm 5 Điều gần nhất trong db/ ──► (sau này) đưa cho LLM viết câu trả lời
```

## A2. Các khái niệm cần nhớ

- **Chunk**: một đoạn văn bản nhỏ cắt ra từ tài liệu lớn. Hệ thống tìm kiếm theo chunk. Ở đây **1 chunk = 1 Điều luật**.
- **Embedding**: biến một đoạn văn thành một dãy số (vector). Hai đoạn có nghĩa gần nhau thì vector gần nhau. Nhờ vậy câu hỏi "nghỉ việc phải báo trước bao lâu" tìm ra Điều nói về đơn phương chấm dứt hợp đồng, dù không trùng từ khóa.
- **Vector store (Chroma)**: cơ sở dữ liệu lưu các vector và tìm nhanh "vector nào gần vector câu hỏi nhất". Dữ liệu nằm ở thư mục `db/`.
- **Metadata**: thông tin đi kèm mỗi chunk (số Điều, tiêu đề, Chương, Mục, nguồn). Giúp chatbot trích dẫn được "Điều 35".
- **Retriever**: thành phần nhận câu hỏi, đổi thành vector, rồi lấy ra `k` chunk gần nhất.
- **Cosine similarity**: cách đo "gần nhau" giữa hai vector, dựa trên góc giữa chúng. Càng gần 1 càng giống.
- **Hit@1 / Hit@5**: Điều đúng có nằm ở hạng 1 / trong 5 kết quả đầu hay không. Đây là thước đo chính của retrieval.

## A3. Cấu trúc thư mục

```
vn-labor-law-qa/
├── docs/
│   └── bo_luat_lao_dong_2019.txt   # văn bản luật (nguồn vbpl.vn, UTF-8)
├── db/                             # vector store Chroma (KHÔNG đưa lên git, tạo lại được)
├── venv/                           # môi trường ảo Python (KHÔNG đưa lên git)
├── .env                            # hiện không còn dùng (KHÔNG đưa lên git)
├── .gitignore                      # phải có: venv/, .env, db/, __pycache__/
├── ingestion_pipeline.py           # chuẩn bị dữ liệu (chạy 1 lần)
├── retrieval_pipeline.py           # hỏi và lấy Điều liên quan
├── requirements.txt                # danh sách thư viện (nhớ ghim scikit-learn==1.7.2)
├── README.md                       # giới thiệu cho người ngoài
└── DEVLOG.md                       # file này
```

## A4. Cách quay lại một commit cũ bằng git

Xem lịch sử và các mốc:
```powershell
git log --oneline
git tag
```

Quay về một mốc (chỉ để xem, trạng thái "detached HEAD"):
```powershell
git checkout v0.2-retrieval        # hoặc v0.1-ingestion, hoặc <mã-commit>
```

Muốn sửa gì từ mốc đó thì **tạo nhánh mới**, đừng sửa trực tiếp:
```powershell
git switch -c thu-nghiem-tu-v0.2
```

Xong việc, quay về nhánh chính (xem tên bằng `git branch`, có thể là `main` hoặc `master`):
```powershell
git switch main
```

**Những thứ không nằm trong git**, sau khi checkout phải tạo lại:
- `venv/`: xem mục B2.7 (cách chạy lại từ đầu).
- `db/`: chạy lại `python ingestion_pipeline.py`.
- `.env`: hiện không cần. Nếu sau này dùng API key thì tự tạo lại, **không bao giờ commit**.

File `docs/bo_luat_lao_dong_2019.txt` **có** nằm trong git nên không phải tải lại.

---

# Phần B: Các mốc

# Mốc 2: Retrieval chạy được, test sơ bộ 10 câu

- **Ngày:** 2026-10-22
- **Git tag gợi ý:** `v0.2-retrieval`
- **Môi trường:** Windows 11 Pro, PowerShell, VS Code, Python 3.13.16, `scikit-learn==1.7.2`

## B1.1 Trạng thái tại mốc này

| Phần | Trạng thái |
|---|---|
| Ingestion: 220 Điều vào Chroma | Xong (mốc 1) |
| Retrieval: hỏi và lấy 5 Điều gần nhất | **Xong** |
| Test sơ bộ 10 câu | **Xong, chưa chính thức** (xem B1.3) |
| Sinh câu trả lời bằng LLM | Chưa làm |
| Bộ test 40 câu có đáp án độc lập | Chưa làm |
| Giao diện, deploy | Chưa làm |

Nói gọn: ở mốc này hệ thống đã **tìm đúng Điều luật** cho phần lớn câu hỏi. Chưa viết ra câu trả lời hoàn chỉnh.

## B1.2 Giảng source: `retrieval_pipeline.py`

Cấu trúc file bám theo tutorial. Các tên biến (`persistence_directory`, `embeddings_model`, `db`, `retriever`, `relevant_docs`) giữ nguyên để đối chiếu video.

```python
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
query = "Người lao động nghỉ việc phải báo trước bao nhiêu ngày?"

retriever = db.as_retriever(search_kwargs={"k": 5})  # Retrieve top 5 relevant documents

# (khối similarity_score_threshold bị comment, xem giải thích bên dưới)

relevant_docs = retriever.invoke(query)

print(f"User query: {query}")

print("--- Context ---")
for i, doc in enumerate(relevant_docs, 1):
    print(f"Document {i}: Điều {doc.metadata['article']}. {doc.metadata['title']}")
```

### Đoạn 1: import và cấu hình
- `Chroma`: lớp để **mở lại** vector store đã lưu trong `db/`.
- `HuggingFaceEmbeddings`: lớp nạp model embedding chạy trên máy.
- `load_dotenv()`: nạp file `.env`. Hiện không còn cần vì không dùng API key, giữ lại cho khớp tutorial, bỏ cũng được.
- `persistence_directory = "db"`: thư mục chứa dữ liệu. **Phải trùng với `persist_directory` của ingestion.** Tutorial gốc dùng `db/chroma_db`, ở đây là `db`. Trỏ sai thì Chroma âm thầm tạo một kho **rỗng** mới và không trả về gì.

### Đoạn 2: nạp model và mở vector store
- `embeddings_model` phải **giống hệt** lúc ingestion: cùng `BAAI/bge-m3`, cùng `normalize_embeddings=True`. Lý do: vector của câu hỏi và vector của các Điều phải do cùng một "thước đo" tạo ra thì mới so sánh được. Khác model là kết quả vô nghĩa.
- `db = Chroma(...)`: mở kho vector đã có. `embedding_function` là cái dùng để đổi **câu hỏi** thành vector khi tìm kiếm. `collection_metadata` ghi lại cho khớp lúc tạo (đo bằng cosine).

### Đoạn 3: tìm kiếm
- `query`: câu hỏi cần thử. Mỗi lần test chỉ đổi dòng này.
- `retriever = db.as_retriever(search_kwargs={"k": 5})`: tạo bộ tìm kiếm trả về **đúng 5** kết quả gần nhất.
- `relevant_docs = retriever.invoke(query)`: thực sự chạy tìm kiếm. Bên trong: (1) đổi `query` thành vector bằng `embeddings_model`, (2) Chroma tính cosine giữa vector đó và 220 vector Điều, (3) trả về 5 Document gần nhất, xếp từ gần đến xa.
- Mỗi phần tử trong `relevant_docs` là một `Document` có `page_content` (toàn văn Điều) và `metadata` (số Điều, tiêu đề...).

### Khối bị comment: `similarity_score_threshold`
```python
# retriever = db.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={"k": 5, "score_threshold": 0.5}
# )
```
Cách này chỉ trả về kết quả có độ giống **vượt một ngưỡng**, thay vì luôn trả đủ 5. Có ích để loại kết quả nhiễu. **Chưa dùng** vì chưa biết ngưỡng nào hợp với bge-m3. Ngưỡng 0.5 có thể lọc sạch hoặc không lọc được gì. Phải đo bằng bộ test rồi mới chọn, không đoán.

### Đoạn 4: in kết quả
Dòng `print` được sửa so với tutorial: in **số Điều và tiêu đề** (từ metadata) thay vì toàn văn, cho dễ đọc khi test nhiều câu. Muốn đọc nội dung thì thêm `\n{doc.page_content}` vào cuối chuỗi.

### Một điểm cần biết
Mỗi lần chạy script, model `bge-m3` được nạp lại (vài giây). Test 10 câu bằng cách sửa `query` rồi chạy 10 lần thì hơi chậm. Sau này có thể gom các câu hỏi vào một danh sách và lặp, nạp model một lần.

## B1.3 Kết quả test sơ bộ 10 câu

> ⚠️ **Đọc kỹ trước khi dùng số liệu này.**
> - Cột "Điều kỳ vọng" được xác định dựa trên **tiêu đề Điều trong kết quả** và hiểu biết chung về Bộ luật, **chưa được tự đối chiếu với văn bản gốc** bằng `Ctrl+F`. Cần làm bước đó trước khi coi là đáp án chuẩn.
> - 10 câu là **mẫu quá nhỏ**, câu hỏi do mình chọn, chỉ dùng để thấy xu hướng. **Không đưa vào README như số liệu đánh giá.** Số liệu chính thức phải đến từ bộ test 40 câu có đáp án độc lập.
> - [ ] Đã đối chiếu từng đáp án kỳ vọng với văn bản gốc

| # | Câu hỏi | Điều kỳ vọng | Top 5 trả về | Hạng của Điều đúng |
|---|---|---|---|---|
| 1 | Thời gian thử việc tối đa? | 25 | 25, 24, 53, 27, 26 | **1** |
| 2 | Lao động nữ nghỉ thai sản bao lâu? | 139 | 139, 137, 138, 140, 113 | **1** |
| 3 | Thời giờ làm việc bình thường tối đa/ngày? | 105 | 105, 146, 109, 107, 116 | **1** |
| 4 | Nghỉ phép năm bao nhiêu ngày? | 113 (và 114) | 113, 111, 112, 114, 115 | **1** |
| 5 | Làm thêm giờ ngày lễ trả bao nhiêu %? | 98 | 98, 112, 107, 108, 97 | **1** |
| 6 | Hợp đồng lao động có những loại nào? | 20 | 20, 14, 13, 21, 179 | **1** |
| 7 | Có được giữ bản chính giấy tờ tùy thân không? | 17 | 17, 153, 12, 16, 21 | **1** |
| 8 | Công ty nợ lương mấy tháng thì làm gì? | 35 (khoản 2 điểm b), 97 | 48, 41, 97, 131, 124 | 97 ở hạng **3**; **35 không có** trong top 5 |
| 9 | Tự ý nghỉ mấy ngày liền, công ty cho nghỉ có đúng không? | 36 (khoản 1 điểm e), 125 | 115, 111, 113, 36, 35 | 36 ở hạng **4**; **125 không có** |
| 10 | Mức đóng BHXH bắt buộc là bao nhiêu %? | Ngoài phạm vi (nằm ở luật BHXH) | 168, 219, 102, 46, 91 | Không có Điều đúng để so |

Điều 35 và Điều 36 đã được kiểm tra nội dung ở lần chạy đầu tiên (đoạn in toàn văn), nên các khoản trích ở câu 8 và 9 có căn cứ. Các Điều còn lại cần bạn xác minh.

## B1.4 Phân tích

### Điểm mạnh
- **Câu hỏi có từ khóa rõ (câu 1 đến 7): Điều chính đều ở hạng 1.** Chunk theo Điều phát huy tác dụng: tiêu đề Điều nằm ngay trong nội dung chunk ("Điều 25. Thời gian thử việc"), nên các câu hỏi chứa đúng chủ đề khớp rất tốt.
- Nhiều kết quả hạng 2 đến 4 là các Điều **liên quan hợp lý** (ví dụ câu 1 ra cả 24, 26, 27 là các Điều cùng nhóm thử việc; câu 2 ra cả 137, 138, 140 cùng nhóm thai sản). Tức là hệ thống "hiểu" chủ đề chứ không chỉ khớp chữ.
- `bge-m3` xử lý tiếng Việt khá ổn ở mức thử nghiệm này.

### Điểm yếu
1. **Luôn trả đủ 5 kết quả nên có nhiễu.** Ví dụ câu 1 ra Điều 53 (cho thuê lại lao động), câu 2 ra Điều 113 (nghỉ hằng năm), câu 6 ra Điều 179 (tranh chấp lao động).
2. **Câu hỏi đời thường, không dùng từ pháp lý (câu 8, 9) yếu hơn rõ rệt.** Cả hai đều không đưa Điều quan trọng nhất lên hạng 1. Câu 8 thiếu hẳn Điều 35 (NLĐ được nghỉ không cần báo trước khi bị nợ lương). Câu 9 thiếu Điều 125 (sa thải khi tự ý bỏ việc), còn top 3 là các Điều về nghỉ phép không liên quan.
3. **Giả thuyết chưa kiểm chứng:** Điều 35 là một Điều **dài và nhiều chủ đề** (báo trước, các trường hợp nghỉ không cần báo trước, nợ lương, quấy rối, thai sản, hưu trí...). Vector của cả Điều là một "trung bình" của nhiều chủ đề nên có thể không đủ gần với một câu hỏi chỉ về nợ lương. Nếu đúng, giải pháp là **cắt nhỏ theo khoản** nhưng vẫn giữ số Điều trong metadata. **Cần thí nghiệm để xác nhận, không kết luận sớm.**
4. **Câu ngoài phạm vi (câu 10):** hệ thống vẫn trả về 5 Điều "gần nhất" (Điều 168 về tham gia BHXH đứng đầu) dù văn bản này **không chứa** mức đóng. Retrieval không tự biết "không có đáp án". Việc từ chối phải xử lý ở bước sinh câu trả lời (dặn LLM nói "không đủ thông tin") hoặc bằng ngưỡng điểm.
5. **Điều 35 và Điều 36 dễ bị nhầm** (cùng bộ số 45/30/03 ngày nhưng khác bên báo trước). Khi đưa cho LLM phải dặn rõ ai báo trước cho ai.

## B1.5 Lỗi gặp và cách xử lý

| Lỗi | Nguyên nhân thật | Cách sửa |
|---|---|---|
| `retrieval_pipeline.py` theo tutorial dùng `OpenAIEmbeddings(model_name=...)` | Tutorial dùng OpenAI, project này dùng model cục bộ | Đổi sang `HuggingFaceEmbeddings` giống ingestion |
| Đường dẫn `db/chroma_db` | Tutorial lưu ở đó, ingestion của mình lưu ở `db` | Đổi thành `db` |
| `ImportError: DLL load failed while importing _expected_mutual_info_fast: An Application Control policy has blocked this file` | **Smart App Control** của Windows 11 chặn file DLL của `scikit-learn 1.9.1`. Dòng báo "Could not import sentence_transformers" ở cuối log gây hiểu lầm vì thư viện đã cài rồi | Hạ xuống bản cũ hơn: `pip install --no-cache-dir scikit-learn==1.7.2`. Kiểm tra bằng `python -c "import sentence_transformers; print('OK')"` |

Ghi chú về Smart App Control:
- Màn hình Windows Security cho thấy trạng thái **On**. Tắt (Off) thì **không bật lại được nếu không cài lại Windows**, nên đã chọn cách đổi phiên bản thư viện thay vì tắt.
- Nguyên nhân Smart App Control chặn bản 1.9.1 mà không chặn 1.7.2 là suy đoán (bản mới chưa đủ uy tín trên hệ thống đánh giá). Nếu sau này `pip install` kéo lại bản mới hơn, lỗi có thể quay lại. **Vì vậy phải ghim `scikit-learn==1.7.2` trong `requirements.txt`.**

## B1.6 Cách chạy và kiểm tra

```powershell
.\venv\Scripts\Activate.ps1
python retrieval_pipeline.py
```

Dấu hiệu chạy đúng: in ra `User query: ...` và 5 dòng `Document N: Điều ...`. Cảnh báo `HF_TOKEN` là vô hại.

Nếu in ra **rỗng** (không có Document nào): kiểm tra `persistence_directory` có đúng `"db"` không, và `db/` có dữ liệu không (`chroma.sqlite3` bảng `embeddings` phải có 220 dòng).

## B1.7 Việc tiếp theo

1. **Xác minh đáp án** của 10 câu bằng `Ctrl+F` trong văn bản gốc, tick ô ở B1.3.
2. **Viết bộ test 40 câu**: mỗi câu kèm danh sách Điều đúng, **do mình tự tra**, không lấy từ chính hệ thống. Gồm cả câu đời thường và vài câu ngoài phạm vi. Đo Hit@1 và Hit@5. Đây mới là số liệu cho README.
3. **Thí nghiệm cải thiện retrieval, mỗi lần đổi một thứ và đo lại:**
   - `k` khác nhau (3, 5, 8).
   - Ngưỡng `score_threshold`.
   - Cắt nhỏ Điều dài theo khoản (kiểm chứng giả thuyết ở B1.4 mục 3).
   - So sánh với chunk theo độ dài ký tự của tutorial (làm bằng chứng cho README).
4. **Sinh câu trả lời bằng LLM miễn phí**, prompt phải: chỉ dựa trên các Điều đã tìm, trích dẫn "Điều X, khoản Y", phân biệt bên báo trước (NLĐ hay NSDLĐ), và trả lời "không đủ thông tin" khi ngoài phạm vi. Cần kiểm tra lựa chọn miễn phí còn khả dụng tại thời điểm đó.
5. Giao diện Streamlit và deploy.

## B1.8 Vấn đề còn mở

- Giả thuyết "Điều dài đa chủ đề làm vector bị loãng" chưa kiểm chứng.
- Chưa biết ngưỡng điểm hợp lý cho `bge-m3`.
- Ground truth của 10 câu chưa được xác minh độc lập.
- Mỗi lần chạy phải nạp lại model (chậm khi test nhiều câu).
- Smart App Control có thể chặn thêm thư viện khác khi cài mới.
- Văn bản dùng là bản gốc 2019, chưa cập nhật các sửa đổi sau đó (vbpl.vn ghi "hết hiệu lực một phần").

## B1.9 Git cho mốc này

```powershell
pip freeze > requirements.txt        # nhớ kiểm tra có dòng scikit-learn==1.7.2
git status                           # KHÔNG được thấy .env, db/, venv/
git add .
git commit -m "Retrieval: truy vấn bge-m3 trên Chroma, test sơ bộ 10 câu, ghim scikit-learn 1.7.2"
git tag -a v0.2-retrieval -m "Retrieval chạy được, chưa có LLM"
git push
git push origin v0.2-retrieval
```

---

# Mốc 1: Ingestion pipeline hoàn chỉnh

- **Ngày:** 2026-10-19
- **Git tag gợi ý:** `v0.1-ingestion`
- **Môi trường:** Windows, PowerShell, VS Code, Python 3.13.16

## B2.1 Trạng thái tại mốc này

Xong: lấy dữ liệu luật, tách 220 Điều kèm metadata, embedding và lưu vào Chroma (`db/`, 220 vector). Chưa làm: truy vấn, LLM, test, giao diện.

## B2.2 Giảng source: `ingestion_pipeline.py`

File có 3 bước, đúng khung tutorial (tên hàm giữ nguyên để đối chiếu video):

```
main()
 ├── 1. load_documents()       đọc file .txt trong docs/
 ├── 2. split_documents()      cắt thành từng Điều (gọi parse_law)
 └── 3. create_vector_store()  embedding + lưu vào db/
```

### Phần đầu file: import và 3 mẫu regex
```python
CHAPTER_RE = re.compile(r"^Chương\s+([IVXLC]+)\b(.*)$", re.IGNORECASE)
SECTION_RE = re.compile(r"^Mục\s+(\d+)\b(.*)$", re.IGNORECASE)
ARTICLE_RE = re.compile(r"^Điều\s+(\d+)\.\s*(.*)$")
```
Regex là "mẫu để nhận dạng chuỗi". Đọc `ARTICLE_RE` từng mảnh:

| Mảnh | Nghĩa |
|---|---|
| `^` | Bắt đầu dòng |
| `Điều` | Đúng chữ "Điều" |
| `\s+` | Một hoặc nhiều khoảng trắng |
| `(\d+)` | Một hoặc nhiều chữ số, **bắt lại** thành nhóm 1 (số Điều) |
| `\.` | Dấu chấm thật (có `\` vì `.` thường nghĩa là "ký tự bất kỳ") |
| `\s*` | Khoảng trắng (có thể không có) |
| `(.*)` | Phần còn lại của dòng, bắt lại thành nhóm 2 (tiêu đề) |
| `$` | Hết dòng |

Dòng `Điều 35. Quyền đơn phương chấm dứt...` cho `group(1) = "35"` và `group(2) = "Quyền đơn phương chấm dứt..."`. Với `CHAPTER_RE`: `([IVXLC]+)` bắt số La Mã (I, II, ..., XVII), `\b` là ranh giới từ.

### Bước 1: `load_documents`
- `DirectoryLoader` + `TextLoader` đọc mọi file `.txt` trong `docs/`.
- `loader_kwargs={"encoding": "utf-8"}` **bắt buộc** trên Windows. Thiếu thì Windows đọc bằng `cp1252` và lỗi tiếng Việt.
- Kết quả: **một Document khổng lồ** chứa cả bộ luật (khoảng 190.000 ký tự). Chưa cắt.

### Bước 2: `split_documents` và `parse_law`
Đây là phần **khác tutorial gốc**. Tutorial dùng `CharacterTextSplitter` cắt theo độ dài (800 ký tự), làm đứt Điều giữa chừng và mất số Điều. `parse_law` đọc từng dòng và nhận dạng cấu trúc luật.

`parse_law` hoạt động như một cái máy có **trạng thái**. Nó nhớ 4 thứ trong lúc đọc:

| Biến | Nhớ gì |
|---|---|
| `chapter` | Chương hiện tại |
| `section` | Mục hiện tại |
| `article` | Điều **đang đọc dở** (số, tiêu đề, danh sách dòng) |
| `expect` | Có đang chờ dòng "tên Chương/Mục" ở dòng kế tiếp không |

**Ví dụ chạy tay.** Giả sử văn bản như sau:

```
Chương I
NHỮNG QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
Bộ luật Lao động quy định tiêu chuẩn lao động...
Điều 2. Đối tượng áp dụng
1. Người lao động, người học nghề...
```

| Dòng đọc được | Chuyện gì xảy ra |
|---|---|
| `Chương I` | Khớp `CHAPTER_RE`, phần sau trống nên đặt `expect = "chapter"`, `chapter = "Chương I"` |
| `NHỮNG QUY ĐỊNH CHUNG` | `expect` đang bật nên coi đây là tên Chương: `chapter = "Chương I - NHỮNG QUY ĐỊNH CHUNG"` |
| `Điều 1. Phạm vi điều chỉnh` | Khớp `ARTICLE_RE`. `flush()` (chưa có Điều nào để đóng), mở Điều 1 |
| `Bộ luật Lao động quy định...` | Dòng thường, nối vào `article["lines"]` của Điều 1 |
| `Điều 2. Đối tượng áp dụng` | Khớp `ARTICLE_RE`. `flush()` **đóng Điều 1**, đóng gói thành Document, rồi mở Điều 2 |
| `1. Người lao động...` | Dòng thường, nối vào Điều 2 |
| (hết file) | `flush()` lần cuối để đóng Điều 2 |

Các chi tiết đáng nhớ:
- **`flush()`**: đóng Điều đang đọc, tạo một `Document` (nội dung = các dòng nối lại, metadata = số Điều, tiêu đề, Chương, Mục, nguồn), thêm vào `chunks`. Gặp "Điều mới" hoặc "Chương mới" hoặc hết file thì gọi `flush()`.
- **`nonlocal article`**: `flush()` là hàm con, muốn **gán lại** `article = None` của hàm cha thì phải khai báo `nonlocal`.
- **`expect`**: do văn bản vbpl để tên Chương ở dòng riêng ngay sau "Chương I". Điều kiện `not ARTICLE_RE.match(line)` là chốt an toàn.
- **`unicodedata.normalize("NFC", text)`**: chuẩn hóa dấu tiếng Việt. Cùng một chữ "Điều" có thể được mã hóa theo hai cách khác nhau (ký tự dựng sẵn hoặc chữ cái + dấu rời), và regex chỉ khớp một cách.
- **`line.isdigit()`**: bỏ dòng chỉ có số (số trang).

Cuối `split_documents` có đoạn **tự kiểm tra**: đối chiếu số Điều tách được với tập 1 đến 220, in "Điều bị thiếu". Đây là dòng để xác nhận pipeline đúng.

Metadata mỗi chunk có dạng:
```python
{'source': 'docs\\bo_luat_lao_dong_2019.txt', 'article': 1,
 'title': 'Phạm vi điều chỉnh', 'chapter': 'Chương I - NHỮNG QUY ĐỊNH CHUNG', 'section': ''}
```

Lưu ý quan trọng: **chỉ `page_content` được đem đi tạo embedding**, metadata thì không. Nhưng dòng đầu của `page_content` chính là "Điều 25. Thời gian thử việc", nên tiêu đề vẫn góp vào vector. Đó là một lý do chunk theo Điều tìm tốt.

### Bước 3: `create_vector_store`
- `HuggingFaceEmbeddings(model_name="BAAI/bge-m3", ...)`: nạp model chạy trên máy (tải về lần đầu khoảng 2 GB). Hỗ trợ đa ngôn ngữ gồm tiếng Việt.
- `normalize_embeddings=True`: chuẩn hóa vector về độ dài 1, để đo cosine ổn định.
- `Chroma.from_documents(...)`: tính vector cho toàn bộ 220 chunk rồi lưu vào `persist_directory`. `hnsw:space = cosine` nghĩa là đo độ gần bằng cosine.
- Chroma bản mới **tự lưu** xuống ổ đĩa, không cần `vector_store.persist()` nữa.

### `main()`
Gọi ba hàm theo thứ tự, truyền kết quả từ bước này sang bước sau.

## B2.3 Quyết định kỹ thuật và lý do

| Quyết định | Lý do |
|---|---|
| Chunk theo Điều, bỏ `CharacterTextSplitter` | Cắt theo độ dài làm đứt Điều, chunk mất số Điều, trích dẫn sẽ sai |
| Embedding `bge-m3` chạy cục bộ, bỏ OpenAI | Không có tiền nạp API. bge-m3 đa ngôn ngữ, có tiếng Việt, miễn phí |
| Python 3.13, không dùng 3.15 | 3.15 quá mới, nhiều thư viện chưa có bản build sẵn cho Windows nên pip tự biên dịch và đòi C++ Build Tools |
| Giữ tên hàm theo tutorial | Đối chiếu video mà không phải đoán |
| Lấy dữ liệu từ tab "Nội dung" của vbpl.vn, không dùng PDF | PDF là bản scan, phải OCR, dễ sai dấu. Tab "Nội dung" có chữ thật |
| Tắt công tắc "Hiển thị chi tiết cập nhật" khi copy | Công tắc này có thể chèn ghi chú sửa đổi vào giữa nội dung |

## B2.4 Lỗi gặp và cách xử lý

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

Bài học chung: khi gặp lỗi lạ, **in giá trị biến ra kiểm tra trước** (ví dụ `bool(os.getenv("..."))`) rồi mới đoán nguyên nhân. Thông báo lỗi cuối cùng của thư viện nhiều khi không phải nguyên nhân gốc.

## B2.5 Cách chạy lại từ đầu

Giả sử vừa clone repo về máy mới, hoặc quay lại sau thời gian dài.

```powershell
# 1. Tạo môi trường ảo bằng Python 3.13
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python --version                      # phải ra Python 3.13.x

# 2. Cài thư viện
pip install -r requirements.txt

# 3. Chạy ingestion (xóa db cũ trước nếu có, để không bị trùng dữ liệu)
Remove-Item -Recurse -Force db
python ingestion_pipeline.py
```

Nếu chưa có `requirements.txt`, cài tay:
```powershell
pip install langchain-community langchain-core langchain-huggingface langchain-chroma sentence-transformers python-dotenv
pip install --no-cache-dir scikit-learn==1.7.2
```

### Dấu hiệu chạy đúng
- In ra `Tách được 220 Điều | Điều bị thiếu: không có`.
- Metadata Chunk 1 có `article`, `title`, `chapter`.
- Cuối cùng in `Vector store created and persisted to db`.
- `db/chroma.sqlite3` bảng `embeddings` có **220 dòng**.

Lần chạy đầu sẽ đứng yên một lúc để tải model (khoảng 2 GB). Bình thường.

---

# Phần C: Mẫu cho mốc mới

Copy khối này, dán lên **trên** mốc cũ nhất trong Phần B, điền vào.

```markdown
# Mốc N: <tên ngắn gọn>

- **Ngày:**
- **Git tag / commit:**
- **Môi trường:**

## Trạng thái (chạy được / chưa)
-

## Giảng source (file nào thay đổi, thay đổi gì và vì sao)
-

## Kết quả (số liệu thật, ghi rõ cách đo)
-

## Phân tích: điểm mạnh, điểm yếu
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