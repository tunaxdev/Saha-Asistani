import argparse
import os

import pdfplumber

# Bazı PDF'lerdeki tablolar çizgisiz (borderless) olduğu için varsayılan
# "lines" stratejisi hiçbir tablo bulamayabilir. Böyle durumlarda metin
# hizalamasına dayalı strateji ile tekrar denenir.
FALLBACK_TABLE_SETTINGS = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "intersection_tolerance": 5,
}


def _bbox_overlaps(obj, bbox):
    x0, top, x1, bottom = bbox
    return not (
        obj["x1"] < x0 or obj["x0"] > x1 or obj["bottom"] < top or obj["top"] > bottom
    )


def _table_to_markdown(table):
    md_rows = []
    for i, row in enumerate(table):
        cleaned = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
        md_rows.append("| " + " | ".join(cleaned) + " |")
        if i == 0:
            md_rows.append("|" + "|".join(["---"] * len(row)) + "|")
    return "\n".join(md_rows)


def pdf_to_markdown(pdf_path, output_path):
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    pages_output = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_content = [f"## Sayfa {page_num}"]

            found_tables = page.find_tables()
            if not found_tables:
                found_tables = page.find_tables(table_settings=FALLBACK_TABLE_SETTINGS)

            table_bboxes = [t.bbox for t in found_tables]
            for table in found_tables:
                data = table.extract()
                if data:
                    page_content.append(_table_to_markdown(data))

            # Tablo alanlarına denk gelen kelimeleri düz metinden çıkararak
            # aynı içeriğin iki kez (hem tablo hem düz metin olarak) eklenmesini
            # önlüyoruz.
            if table_bboxes:
                text_page = page.filter(
                    lambda obj: not any(_bbox_overlaps(obj, b) for b in table_bboxes)
                )
            else:
                text_page = page

            text = text_page.extract_text()
            if text and text.strip():
                page_content.append(text.strip())

            pages_output.append("\n\n".join(page_content))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(pages_output))

    print(f"Bitti! {len(pages_output)} sayfa çıkarıldı -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF kılavuzunu markdown'a çevirir.")
    parser.add_argument("pdf_path", help="Kaynak PDF dosyasının yolu")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Çıktı markdown dosyasının yolu (varsayılan: docs/<pdf_adı>.md)",
    )
    args = parser.parse_args()

    output_path = args.output
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
        output_path = os.path.join("docs", f"{base_name}.md")

    pdf_to_markdown(args.pdf_path, output_path)
