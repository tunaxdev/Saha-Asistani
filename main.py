import math
import os
import sqlite3
import json
import hashlib
from foundry_local_sdk import Configuration, FoundryLocalManager

# ── Belgeleri yükle ve parçala ───────────────────────────────────────────────
def load_documents(docs_folder="docs", chunk_size=500):
    chunks = []
    for filename in os.listdir(docs_folder):
        if filename.endswith(".md") or filename.endswith(".txt"):
            filepath = os.path.join(docs_folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size].strip()
                if chunk:
                    chunks.append({"text": chunk, "source": filename})
    print(f"{len(chunks)} chunk yüklendi ({docs_folder} klasöründen)")
    return chunks

# ── Cosine similarity ────────────────────────────────────────────────────────
def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

# ── En alakalı chunk'ları bul ────────────────────────────────────────────────
def find_relevant(query_embedding, doc_embeddings, top_k=3):
    scores = [(i, cosine_similarity(query_embedding, emb))
              for i, emb in enumerate(doc_embeddings)]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]

# ── Cache fonksiyonları ──────────────────────────────────────────────────────
def get_docs_hash(chunks):
    content = "".join(c["text"] for c in chunks)
    return hashlib.md5(content.encode()).hexdigest()

def load_cache(db_path, docs_hash):
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT hash, embeddings FROM cache LIMIT 1").fetchone()
    conn.close()
    if row and row[0] == docs_hash:
        return json.loads(row[1])
    return None

def save_cache(db_path, docs_hash, embeddings):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS cache (hash TEXT, embeddings TEXT)")
    conn.execute("DELETE FROM cache")
    conn.execute("INSERT INTO cache VALUES (?, ?)", (docs_hash, json.dumps(embeddings)))
    conn.commit()
    conn.close()

# ── Ana uygulama ─────────────────────────────────────────────────────────────
def main():
    print("Saha Mühendisi Asistanı başlatılıyor...\n")

    # Belgeleri yükle
    chunks = load_documents("docs")
    if not chunks:
        print("docs/ klasöründe belge bulunamadı!")
        return

    # SDK başlat
    config = Configuration(app_name="saha_asistani")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    # Embedding modeli
    print("Embedding modeli yükleniyor...")
    emb_model = manager.catalog.get_model("qwen3-embedding-0.6b")
    emb_model.download(lambda p: print(f"\r  İndiriliyor: {p:.1f}%", end="", flush=True))
    print()
    emb_model.load()
    emb_client = emb_model.get_embedding_client()

    # Cache kontrolü
    DB_PATH = "embeddings_cache.db"
    docs_hash = get_docs_hash(chunks)
    doc_embeddings = load_cache(DB_PATH, docs_hash)

    if doc_embeddings:
        print(f"  Cache'den yüklendi: {len(doc_embeddings)} chunk.\n")
    else:
        print("Belgeler vektöre çevriliyor (ilk seferinde biraz sürer)...")
        texts = [c["text"] for c in chunks]
        doc_embeddings = []
        batch_size = 32

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = emb_client.generate_embeddings(batch)
            doc_embeddings.extend([item.embedding for item in response.data])
            print(f"\r  {len(doc_embeddings)}/{len(texts)} chunk indexlendi...", end="", flush=True)

        save_cache(DB_PATH, docs_hash, doc_embeddings)
        print(f"\n  Tamamlandı ve cache'e kaydedildi.\n")

    # Chat modeli
    print("Chat modeli yükleniyor...")
    chat_model = manager.catalog.get_model("phi-3.5-mini")
    chat_model.download(lambda p: print(f"\r  İndiriliyor: {p:.1f}%", end="", flush=True))
    print()
    chat_model.load()
    chat_client = chat_model.get_chat_client()

    print("\n✓ Hazır! Commander C200-C300 kılavuzu hakkında soru sorabilirsin.")
    print("  Çıkmak için 'quit' yaz.\n")

    # Soru-cevap döngüsü
    while True:
        query = input("Soru: ").strip()
        if not query or query.lower() == "quit":
            break

        # Soruyu vektöre çevir
        q_response = emb_client.generate_embedding(query)
        q_embedding = q_response.data[0].embedding

        # En alakalı chunk'ları bul
        results = find_relevant(q_embedding, doc_embeddings, top_k=3)
        context = "\n\n".join(
            f"[Source: {chunks[i]['source']}]\n{chunks[i]['text']}"
            for i, _ in results
        )

        # Prompt oluştur
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a technical assistant. Answer the user's question using ONLY the context below. "
                    "Be concise. If the answer is not in the context, say 'Bu bilgi belgede bulunamadı.'\n\n"
                    f"Context:\n{context}"
                ),
            },
            {"role": "user", "content": query},
        ]

        # Cevabı stream et
        print("\nCevap: ", end="", flush=True)
        for chunk in chat_client.complete_streaming_chat(messages):
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
        print("\n\n─────────────────────────────────────\n")

    # Temizle
    emb_model.unload()
    chat_model.unload()
    print("Modeller kapatıldı.")

if __name__ == "__main__":
    main()