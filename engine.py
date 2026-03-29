""" AIFT Core Engine """

import os
import time
import json
import torch
import faiss
import torch.nn.functional as F
from openai import AsyncOpenAI
from transformers import AutoTokenizer, AutoModel

# Retrieval engine
class RetrievalEngine:

    def __init__(self, model_name=None, index_path=None, corpus_path=None):

        self.model_name = model_name or os.environ.get("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
        self.index_path = index_path or os.environ.get("FAISS_INDEX_PATH", "rag_index.faiss")
        self.corpus_path = corpus_path or os.environ.get("CORPUS_PATH", "corpus.json")

        print(f"Engine: '{self.model_name}' yükleniyor...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.eval()
        
        if torch.cuda.is_available():
            self.model.to("cuda")

        print(f"Engine: '{self.index_path}' vektör tabanı yükleniyor...")
        self.index = faiss.read_index(self.index_path)
        
        print(f"Engine: '{self.corpus_path}' veri tabanı yükleniyor...")
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            self.corpus = json.load(f)

    def encode_query(self, query):
        inputs = self.tokenizer(query, padding=True, truncation=True, return_tensors="pt", max_length=512)
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.inference_mode():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0]
            embeddings = F.normalize(embeddings, p=2, dim=1)
            
        return embeddings.cpu().numpy()

    def search(self, query, k=3):
        query_vector = self.encode_query(query)
        distances, indices = self.index.search(query_vector, k)
        
        retrieved_docs = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.corpus):
                retrieved_docs.append(self.corpus[idx])
        
        return retrieved_docs # List for UI

# LLM Bridge
class LLMBridge:

    def __init__(self, base_url=None, api_key=None):

        self.base_url = base_url or os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "lm-studio")
        
        self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)

    def _is_query_safe(self, query):
        
        malicious_patterns = [
            "ignore previous", "forget previous", "system prompt",
            "dan mode", "jailbreak", "instruction manual",
            "önceki talimatları", "sistem komutlarını", "yoksay"
        ]
        query_lower = query.lower()
        
        # Keywords

        for pattern in malicious_patterns:
            if pattern in query_lower:
                return False, f"Güvenlik ihlali tespit edildi: '{pattern}' kullanımı yasaktır."
        
        # Length check

        if len(query) > 500:
            return False, "Sorgu çok uzun (max 500 karakter)."

        return True, None

    async def generate_response(self, query, context_list):
        """ Streaming generation with safety check """

        # Security check

        is_safe, error_msg = self._is_query_safe(query)
        if not is_safe:
            print(f"SECURITY ALERT: {error_msg}")
            yield error_msg
            return

        print(f"DEBUG: Retrieval results for '{query}':")
        for i, ctx in enumerate(context_list):
            print(f"  [{i}] {ctx[:100]}...")
            
        faiss_context = "\n\n".join(context_list)
        
        # System prompt

        system_prompt = (
            "Aşağıdaki [BAĞLAM] metnine dayalı olarak soruyu yanıtlayan teknik bir yardımcıdır.\n"
            "UYULMASI GEREKEN KURALLAR:\n"
            "1. Yalnızca sağlanan bağlamdaki gerçekleri kullanın.\n"
            "2. Bağlam dışı bilgi eklemeyin ve varsayımlarda bulunmayın.\n"
            "3. Yanıt bağlamda mevcut değilse, 'Belirtilen kaynaklarda bu bilgiye ulaşılamadı.' ifadesini kullanın.\n"
            "4. Yanıtları doğrudan, kısa ve öz tutun."
        )
        
        user_content = f"""[BAĞLAM]:
{faiss_context}

[SORU]: {query}

Yukarıdaki verilere dayanarak doğrudan yanıt veriniz:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        model_name = os.environ.get("LLM_MODEL_NAME", "local-model")

        response = await self.client.chat.completions.create(
            model=model_name, 
            messages=messages,
            stream=True,
            stop=["\n\n", "[SORU]", "[BİLGİ]", "[BAĞLAM]"],
            temperature=0.0,
            extra_body={
                "repetition_penalty": 1.1 
            }
        )
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
