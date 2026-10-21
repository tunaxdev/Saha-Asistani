# Saha Asistanı — Offline Field Engineer Assistant

A fully offline AI assistant that answers questions about technical manuals. Field engineers often work at remote sites with no internet access but still need instant answers about fault codes, parameters or installation steps. Saha Asistanı ("Field Assistant") runs a local retrieval-augmented generation (RAG) pipeline on your own machine: no cloud, no API keys, no internet connection once the models are downloaded.

Built during the **Microsoft AI Innovators Summer Internship** (2026) using **Microsoft Foundry Local**.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Foundry Local](https://img.shields.io/badge/Microsoft-Foundry_Local-0078D4?logo=microsoft&logoColor=white)
![Phi-3.5](https://img.shields.io/badge/LLM-Phi--3.5--mini-5E5E5E)
![Offline](https://img.shields.io/badge/runs-100%25_offline-2EA44F)
![License](https://img.shields.io/badge/license-MIT-green)

## How It Works

```
 Indexing (once)                               Question answering
 ───────────────                               ──────────────────
 PDF manual                                    User question
    │  pdfplumber (text + tables)                 │  qwen3-embedding-0.6b
    ▼                                             ▼
 Markdown in docs/                             Query vector
    │  500-character chunks                       │  cosine similarity
    ▼                                             ▼
 qwen3-embedding-0.6b                          Top 3 most relevant chunks
    │                                             │  grounded prompt
    ▼                                             ▼
 SQLite embedding cache  ───────────────────▶  phi-3.5-mini (Foundry Local)
                                                  │  streamed answer
                                                  ▼
                                               Answer from the document only
```

1. **Extract:** `extract_pdf.py` converts a PDF manual to Markdown with `pdfplumber`, detecting parameter tables and turning them into Markdown tables.
2. **Index:** Documents in `docs/` are split into chunks and embedded with `qwen3-embedding-0.6b`. Embeddings are cached in SQLite and only recomputed when the documents change (detected by a content hash).
3. **Retrieve:** Each question is embedded and compared against every chunk with cosine similarity; the top 3 chunks become the context.
4. **Answer:** `phi-3.5-mini`, running locally through Foundry Local, answers using **only** that context and says so when the answer is not in the document.

## Features

- **Fully offline:** all models run locally through Foundry Local (internet is needed only for the first model download).
- **Table-aware PDF extraction:** detects ruled tables and falls back to a text-alignment strategy for borderless tables; table areas are removed from the plain text to avoid duplicates.
- **Embedding cache:** a SQLite cache keyed by a hash of the documents makes later start-ups near-instant.
- **Grounded answers:** the system prompt restricts the model to the retrieved context to reduce hallucinations.
- **Streaming output:** answers are printed token by token.
- **Tested with Turkish technical manuals.** The console interface is in Turkish.

## Tech Stack

| Component | Technology |
| --- | --- |
| Local AI runtime | Microsoft Foundry Local (`foundry-local-sdk-winml`) |
| Embedding model | qwen3-embedding-0.6b |
| Chat model | phi-3.5-mini |
| Vector store | SQLite + cosine similarity (pure Python) |
| PDF parsing | pdfplumber |
| Language | Python 3.11 |

## Getting Started

**Requirements:** Windows, Python 3.11+, about 8 GB of RAM, and ~2 GB of free disk space for the models.

```bash
git clone https://github.com/tunaxdev/saha-asistani.git
cd saha-asistani
pip install -r requirements.txt

# Convert your manual to Markdown (saved to docs/)
python extract_pdf.py "path/to/manual.pdf"

# Start the assistant
python main.py
```

On the first run the models are downloaded from the Foundry Local catalog. After that the assistant works completely offline. Type `quit` to exit.

> **Bring your own documents.** No manuals are included in this repository because they are copyrighted by their manufacturers. Place any PDF you are allowed to use in the pipeline above; `.md` and `.txt` files in `docs/` are indexed automatically.

## Example Session

Tested with the Turkish user guide of an industrial AC motor drive:

```text
Saha Mühendisi Asistanı başlatılıyor...

1155 chunk yüklendi (docs klasöründen)
  Cache'den yüklendi: 1155 chunk.

✓ Hazır! docs/ klasöründeki belgeler hakkında soru sorabilirsin.
  Çıkmak için 'quit' yaz.

Soru: Analog Giriş 1 Modu varsayılan değeri nedir?
Cevap: Varsayılan değer Volt (6)'dır.

Soru: Motor nominal akımı nasıl ayarlanır?
Cevap: Parametre 06 olan Motor Nominal Akımı, 0,00 ile maksimum
ağır yük çalışma değeri A arasında ayarlanabilir.
```

*(Q: "What is the default value of Analog Input 1 Mode?" · Q: "How is the motor rated current set?")*

## Project Structure

```
saha-asistani/
├── main.py            # RAG pipeline: chunking, embeddings, cache, retrieval, chat loop
├── extract_pdf.py     # PDF → Markdown converter with table detection (CLI)
├── requirements.txt
└── docs/              # Your documents go here (not tracked)
```

## License

This project is licensed under the [MIT License](LICENSE).
