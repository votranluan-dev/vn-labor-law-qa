import os
import re
import unicodedata
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

# Mẫu nhận dạng cấu trúc văn bản luật
CHAPTER_RE = re.compile(r"^Chương\s+([IVXLC]+)\b(.*)$", re.IGNORECASE)
SECTION_RE = re.compile(r"^Mục\s+(\d+)\b(.*)$", re.IGNORECASE)
ARTICLE_RE = re.compile(r"^Điều\s+(\d+)\.\s*(.*)$")


# TODO: Load files 
def load_documents(docs_path="docs"):
    """
    Load documents from the specified path
    """
    print(f"Loading documents from {docs_path}")

    # Check if the path exists
    if not os.path.exists(docs_path):
        raise FileNotFoundError(f"The specified path '{docs_path}' does not exist !!!")

    # Load all text files from the directory
    loader = DirectoryLoader(
        docs_path, 
        glob="**/*.txt", 
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()

    if len(documents) == 0:
        raise FileNotFoundError(f"No text files found in the specified path '{docs_path}' !!!")

    # Show firt 2 documents
    for i, doc in enumerate(documents[:2]):
        print(f"\nDocument {i+1}:")
        print(f"  Source: {doc.metadata['source']}")
        print(f"  Content length: {len(doc.page_content)} characters")  
        print(f"  Content preview: {doc.page_content[:200]}")
        print(f"  Metadata: {doc.metadata}")

    return documents


def parse_law(text, source=""):
    """
    Cắt văn bản luật thành từng Điều, mỗi Điều là một Document kèm metadata
    """
    text = unicodedata.normalize("NFC", text)  # chuẩn hóa dấu tiếng Việt
    chunks = []
    chapter, section = "", ""
    article = None   # Điều đang đọc dở
    expect = None    # đang chờ dòng tên Chương/Mục ở dòng kế tiếp

    def flush():
        """Đóng Điều đang đọc, đưa vào danh sách chunks"""
        nonlocal article
        if article:
            chunks.append(
                Document(
                    page_content="\n".join(article["lines"]).strip(),
                    metadata={
                        "source": source,
                        "article": article["number"],
                        "title": article["title"],
                        "chapter": chapter,
                        "section": section,
                    },
                )
            )
            article = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.isdigit():  # bỏ dòng trống và số trang
            continue

        # Dòng ngay sau "Chương I" hoặc "Mục 1" là tên của nó
        if expect and not ARTICLE_RE.match(line):
            if expect == "chapter":
                chapter = f"{chapter} - {line}"
            else:
                section = f"{section} - {line}"
            expect = None
            continue
        expect = None

        m = CHAPTER_RE.match(line)
        if m:
            flush()
            chapter = f"Chương {m.group(1).upper()}"
            section = ""
            rest = m.group(2).strip(" .-")
            if rest:
                chapter += f" - {rest}"
            else:
                expect = "chapter"
            continue

        m = SECTION_RE.match(line)
        if m:
            flush()
            section = f"Mục {m.group(1)}"
            rest = m.group(2).strip(" .-")
            if rest:
                section += f" - {rest}"
            else:
                expect = "section"
            continue

        m = ARTICLE_RE.match(line)
        if m:
            flush()  # gặp "Điều mới" thì đóng Điều cũ
            article = {
                "number": int(m.group(1)),
                "title": m.group(2),
                "lines": [line],
            }
            continue

        if article:  # dòng thường: nối vào Điều đang đọc
            article["lines"].append(line)

    flush()
    return chunks


# TODO: Chunk file
def split_documents(documents):
    """
    Split documents into chunks (mỗi chunk là một Điều của văn bản luật)
    """
    print("Splitting documents into chunks by Điều")

    chunks = []
    for doc in documents:
        chunks.extend(parse_law(doc.page_content, source=doc.metadata["source"]))

    # Kiểm tra: Bộ luật Lao động 2019 có 220 Điều
    numbers = {c.metadata["article"] for c in chunks}
    missing = sorted(set(range(1, 221)) - numbers)
    print(f"Tách được {len(chunks)} Điều | Điều bị thiếu: {missing if missing else 'không có'}")

    # Show first 2 chunks
    for i, chunk in enumerate(chunks[:2]):
        print(f"\nChunk {i+1}:")
        print(f"  Source: {chunk.metadata['source']}")
        print(f"  Content length: {len(chunk.page_content)} characters")  
        print(f"  Content preview: {chunk.page_content[:200]}")
        print(f"  Metadata: {chunk.metadata}")

    if len(chunks) > 2:
        print(f"\n... and {len(chunks) - 2} more chunks")

    return chunks


# TODO: Embed & Store in vector in db
def create_vector_store(chunks, persist_directory="db"):
    """
    Create a vector store from the chunks and persist it to the specified directory
    """
    print(f"Creating vector store and persisting to {persist_directory}")

    # Create embeddings (chạy trên máy, miễn phí, hỗ trợ tiếng Việt)
    embeddings_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        encode_kwargs={"normalize_embeddings": True},
    )

    # Create vector store
    print("Creating vector store")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings_model,
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"}
    )

    # Persist the vector store
    # (Chroma bản mới tự lưu xuống ổ đĩa, không cần gọi persist() nữa)

    print(f"Vector store created and persisted to {persist_directory}")


# TODO: Main function
def main():
    print("Main function started")

    # 1. Load files
    documents = load_documents(docs_path="docs")

    # 2. Chunk files
    chunks = split_documents(documents)

    # 3. Embed & Store in vector in db
    create_vector_store(chunks, persist_directory="db")


if __name__ == "__main__":
    main()