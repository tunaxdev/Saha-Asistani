# 🔧 Saha Mühendisi Asistanı
**Microsoft AI Innovators Summer Internship — Local RAG Application with Foundry Local**

> Teknik kılavuzlara internet olmadan soru sorulabilen, tamamen çevrimdışı çalışan bir yapay zeka asistanı.

---

## 💡 Proje Fikri

Bir saha mühendisi, uzak bir lokasyonda internet bağlantısı olmadan çalışırken cihaz hata koduna veya kurulum prosedürüne anında erişmek isteyebilir. Bu uygulama tam olarak bu sorunu çözer:

- ☁️ Bulut yok  
- 🔑 API key yok  
- 🌐 İnternet yok  
- ✅ Sadece kendi bilgisayarın ve belgeler

---

## 🏗️ Mimari

```
PDF Kılavuz
    │
    ▼
pdfplumber (tablo destekli metin çıkarma)
    │
    ▼
Chunker (500 karakterlik parçalar)
    │
    ▼
qwen3-embedding-0.6b (vektörleştirme)
    │
    ▼
SQLite Cache (embeddings_cache.db)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Kullanıcı Sorusu
    │
    ▼
qwen3-embedding-0.6b (sorgu vektörü)
    │
    ▼
Cosine Similarity → En alakalı 3 chunk
    │
    ▼
phi-3.5-mini (Foundry Local üzerinde)
    │
    ▼
Cevap (yalnızca belgeden)
```

---

## 🛠️ Kullanılan Teknolojiler

| Bileşen | Teknoloji |
|---|---|
| Local AI runtime | Microsoft Foundry Local |
| Embedding modeli | qwen3-embedding-0.6b |
| Chat modeli | phi-3.5-mini |
| Vector store | SQLite (cosine similarity) |
| PDF okuma | pdfplumber |
| Dil | Python 3.11 |

---

## 📁 Proje Yapısı

```
SahaAsistanı/
├── main.py                 # Ana uygulama
├── extract_pdf.py          # PDF → Markdown dönüştürücü (CLI argümanlı)
├── requirements.txt        # Bağımlılıklar
├── docs/
│   └── commander_c200.md   # Çıkarılmış kılavuz metni
├── embeddings_cache.db     # SQLite cache (otomatik oluşur, git'e dahil değil)
└── README.md
```

---

## ⚙️ Kurulum

**Gereksinimler:** Windows, Python 3.11+, 8 GB RAM

```bash
# 1. Depoyu klonla
git clone https://github.com/KULLANICI_ADI/SahaAsistani
cd SahaAsistani

# 2. Bağımlılıkları kur
pip install -r requirements.txt

# 3. PDF'yi markdown'a çevir (docs/ klasörüne koyar)
python extract_pdf.py "yol/kilavuz.pdf"

# 4. Uygulamayı başlat
python main.py
```

> **Not:** Uygulama çalışırken tamamen çevrimdışıdır, ancak **ilk çalıştırmada** modeller Foundry Local kataloğundan otomatik indirilir (~2 GB) ve bunun için internet bağlantısı gerekir. Modeller bir kez indirildikten sonra sonraki çalıştırmalar tamamen çevrimdışı ve cache sayesinde saniyeler içinde hazır olur.

---

## 🎯 Nasıl Kullanılır

```
Saha Mühendisi Asistanı başlatılıyor...

1155 chunk yüklendi (docs klasöründen)
Cache'den yüklendi: 1155 chunk.

✓ Hazır! Commander C200-C300 kılavuzu hakkında soru sorabilirsin.
  Çıkmak için 'quit' yaz.

Soru: Analog Giriş 1 Modu varsayılan değeri nedir?
Cevap: Varsayılan değer Volt (6)'dır.

─────────────────────────────────────

Soru: Motor nominal akımı nasıl ayarlanır?
Cevap: Parametre 06 olan Motor Nominal Akımı, 0,00 ile maksimum
ağır yük çalışma değeri A arasında ayarlanabilir.

─────────────────────────────────────

Soru: quit
Modeller kapatıldı.
```

---

## 🔑 Temel Özellikler

- **Tamamen çevrimdışı:** Foundry Local sayesinde tüm modeller yerel çalışır (ilk indirme hariç)
- **Tablo desteği:** pdfplumber ile parametre tabloları tespit edilir; çizgisiz (borderless) tablolarda metin-hizalama stratejisine otomatik geçilir, tablo alanları düz metinden çıkarılıp tekrar etmesi önlenir
- **Akıllı cache:** Embedding'ler SQLite'a kaydedilir, tekrar hesaplanmaz
- **Hallucination önleme:** Model yalnızca belgede bulunan bilgiyi kullanır
- **Türkçe kılavuz desteği:** Türkçe teknik belgelerle test edilmiştir

---

## 📄 Lisans

MIT License — Katkılar açıktır.