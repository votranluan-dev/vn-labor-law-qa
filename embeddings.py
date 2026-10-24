import torch
from langchain_core.embeddings import Embeddings
from transformers import AutoTokenizer, AutoModel


class BgeM3Embeddings(Embeddings):
    def __init__(self, model_name="BAAI/bge-m3", batch_size=8):
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, torch_dtype=torch.float16).eval()
        self.batch_size = batch_size

    def _encode(self, texts):
        out = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            inputs = self.tok(batch, padding=True, truncation=True,
                              max_length=1024, return_tensors="pt")
            with torch.no_grad():
                cls = self.model(**inputs).last_hidden_state[:, 0].float()
            cls = torch.nn.functional.normalize(cls, p=2, dim=1)
            out.extend(cls.tolist())
        return out

    def embed_documents(self, texts):
        return self._encode(texts)

    def embed_query(self, text):
        return self._encode([text])[0]