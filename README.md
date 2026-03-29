# AIFT Search — Kurumsal Bilgi Erişim Sistemi

AIFT Search, yerel bir bilgi tabanı üzerinden (RAG) yüksek doğruluklu ve doğrulanmış yanıtlar sunan profesyonel bir veri analiz sistemidir. Bu proje, kurumsal düzeyde bir bilgi asistanının nasıl yapılandırılması gerektiğini gösteren, yüksek performanslı ve güvenli bir açık kaynak çalışmasıdır.

## 🚀 Öne Çıkan Özellikler

- **Vektör Tabanlı Arama (RAG):** FAISS ve BGE-M3 (BAAI) modelleri ile milisaniye bazında anlamsal arama.
- **Asenkron Mimari (FastAPI):** Çoklu kullanıcı desteği ve I/O operasyonlarında sıfır bloklama.
- **Gerçek Zamanlı Streaming:** Server-Sent Events (SSE) teknolojisi ile yanıtları anlık olarak iletir (TTFT < 1s).
- **Kurumsal UI:** Dark-mode glassmorphism temalı, modern ve kullanıcı dostu arayüz.
- **Güvenlik (Guardrails):** Prompt injection ve unauthorized instruction saldırılarına karşı özelleştirilmiş koruma katmanı.
- **100% Local:** Verileriniz asla yerel ağınız dışına çıkmaz, tamamen gizlilik odaklıdır.

## 🛠️ Teknik Yığın

- **Backend:** Python, FastAPI, Uvicorn
- **AI/ML:** PyTorch, FAISS, `sentence-transformers` (BGE-M3)
- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript (Vanilla)
- **LLM Entegrasyonu:** AsyncOpenAI Client (LM Studio / Local Inference Engine)

## 🏗️ Mimari Yapı

Sistem, modern asenkron prensiplerle optimize edilmiştir:
1. **İnce Arama Katmanı:** Dokümanlar önce vektör uzayına projekte edilir (BGE-M3).
2. **Bağlamsal Zenginleştirme:** En alakalı 3 doküman LLM'e bağlam (context) olarak sunulur.
3. **Kısıtlı Üretim:** LLM, sadece sunulan bağlamdaki gerçekleri kullanarak yanıt üretmesi için talimatlandırılır.

## 📦 Kurulum ve Çalıştırma

### 1. Python Gereksinimleri
Python 3.10+ sürümüne sahip olduğunuzdan emin olun.
```bash
pip install -r requirements.txt
```

### 2. LLM Sunucusu ve Model Yapılandırması

Bu proje, **AIFT** için özel olarak ince ayar yapılmış (fine-tuned) bir model kullanır. Standart genel modeller (instruct vb.) bu proje için özelleştirilmemiştir ve tam performans vermeyebilir.

1.  **Model İndirme:** [Qwen2.5-1.5B-AIFT.gguf](https://huggingface.co/Jwo4/AIFT/resolve/main/Qwen2.5-1.5B-AIFT.gguf) dosyasını indirin.
2.  **Vektör Dizini İndirme:** [rag_index.faiss](https://huggingface.co/Jwo4/AIFT/resolve/main/rag_index.faiss) dosyasını indirin.
3.  **Dosya Konumu:** İndirdiğiniz `.gguf` ve `.faiss` dosyalarını projenin kök dizinine (root) kopyalayın.
3.  **LM Studio Yapılandırması:**
    - [LM Studio](https://lmstudio.ai/) uygulamasını çalıştırın.
    - İndirdiğiniz `Qwen2.5-1.5B-AIFT.gguf` modelini yükleyin.
    - **Local Server** sekmesinden sunucuyu başlatın (Port: 1234).
    - Sunucunun `RUNNING` durumunda olduğundan emin olun.

### 3. Uygulamayı Başlatın
```bash
python server.py
```
Tarayıcıda `http://localhost:5000` adresine giderek sistemi kullanmaya başlayabilirsiniz.

## 🔒 Güvenlik Katmanı
Sistem, kullanıcı girdilerini filtreleyen bir `_is_query_safe` katmanına sahiptir. Bu katman; prompt injection, instruction bypass ve DoS saldırılarını tespit ederek sistemi korur.

---
