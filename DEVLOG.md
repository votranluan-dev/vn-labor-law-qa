1. Giải thích sự kết hợp Prompt và Context (TODO Combine Prompt)
Đoạn mã này đóng vai trò là cốt lõi của kỹ thuật RAG (Retrieval-Augmented Generation), nơi thông tin truy xuất từ Vector Database được đóng gói cùng câu hỏi của người dùng để gửi tới mô hình AI.

Python
combined_input = f"""Based on the following articles of Vietnam's Labor Code 2019, please answer the question: {query}

Articles:
{chr(10).join([f" - {doc.page_content}" for doc in relevant_docs])}

Please answer in Vietnamese, clearly and helpfully. Rules:
- Use ONLY the articles above. If they do not contain the answer, say that the provided articles do not have enough information. Do not use outside knowledge.
- Cite the article number and title (and clause if possible), for example "Điều 35. Quyền đơn phương chấm dứt hợp đồng lao động của người lao động".
- Pay attention to who the rule applies to (employee or employer). Do not mix them up.
"""

Phân tích chi tiết từng thành phần:
Kết hợp ngữ cảnh (Context Injection):

{chr(10).join([f" - {doc.page_content}" for doc in relevant_docs])}: Duyệt qua danh sách 5 văn bản (relevant_docs) được tìm thấy từ ChromaDB, trích xuất nội dung page_content của từng Điều luật và nối chúng lại với nhau bằng dấu xuống dòng (chr(10) tương đương với kí tự \n).

Việc truyền danh sách Điều luật này vào prompt giúp mô hình AI "đọc" trực tiếp dữ liệu chính xác trước khi trả lời.

Cấu trúc RAG Prompting & Ràng buộc (Prompt Constraints):

Giới hạn tri thức (Grounding): Yêu cầu mô hình chỉ sử dụng thông tin trong các Điều luật được cung cấp (ONLY the articles above). Nếu không tìm thấy thông tin, AI phải thông báo thiếu dữ liệu chứ không được tự bịa ra thông tin bên ngoài (chống ảo giác/hallucination).

Yêu cầu trích dẫn (Citation): Ép AI phải trích dẫn rõ ràng số Điều, tên Điều và khoản để câu trả lời có tính pháp lý và kiểm chứng được.

Phân định đối tượng: Nhắc nhở AI chú ý rõ quyền/nghĩa vụ áp dụng cho Người lao động hay Người sử dụng lao động, tránh nhầm lẫn đối tượng trong luật.

Cấu hình ChatOllama (num_ctx):

Python
model = ChatOllama(model="qwen2.5:3b", temperature=0, num_ctx=8192)
temperature=0: Giúp câu trả lời mang tính khách quan, chính xác và nhất quán nhất, hạn chế sự sáng tạo không cần thiết đối với văn bản pháp luật.

num_ctx=8192: Mở rộng cửa sổ ngữ cảnh (Context Window) lên 8192 tokens. Mặc định của Ollama thường chỉ là 2048 tokens; nếu giữ mặc định, việc gộp 5 Điều luật dài cùng một lúc sẽ khiến prompt bị cắt gọt (truncate), dẫn đến việc AI mất ngữ cảnh và trả lời sai.

2. Hướng dẫn cài đặt và vận hành Ollama chạy Local trên PowerShell
Ollama là một công cụ mã nguồn mở cho phép tải, quản lý và chạy các mô hình ngôn ngữ lớn (LLM) như Qwen, Llama, Mistral trực tiếp trên máy tính cá nhân mà không cần gửi dữ liệu ra bên ngoài.

Bước 1: Cài đặt Ollama trên Windows
Truy cập trang chủ: https://ollama.com

Tải file cài đặt OllamaSetup.exe dành cho Windows và tiến hành cài đặt.

Sau khi cài đặt xong, Ollama sẽ chạy ngầm dưới hệ thống.

Bước 2: Kiểm tra và tải mô hình bằng PowerShell
Mở PowerShell trên máy tính của bạn và thực hiện các câu lệnh sau:

Kiểm tra phiên bản Ollama đã cài đặt:

PowerShell
ollama --version
Tải mô hình qwen2.5:3b về máy:

PowerShell
ollama pull qwen2.5:3b
Kiểm tra danh sách các mô hình đã tải:

PowerShell
ollama list
Bước 3: Chạy và kiểm tra mô hình trên PowerShell
Chạy thử mô hình trực tiếp trên Terminal:

PowerShell
ollama run qwen2.5:3b
Sau khi chạy lệnh, bạn có thể gõ câu hỏi để trò chuyện trực tiếp với mô hình. Nhập /bypass hoặc ấn Ctrl + D để thoát.

Lưu ý khi tích hợp vào Python:
Khi file retrieval_pipeline.py chạy, thư viện langchain_ollama sẽ tự động kết nối tới service Ollama đang chạy ngầm trên máy bạn (mặc định tại địa chỉ http://localhost:11434). Do đó, bạn chỉ cần đảm bảo Ollama đang bật trên máy là ứng dụng sẽ hoạt động mượt mà.