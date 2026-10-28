# example1


import fitz
from pathlib import Path

# Arquivo original
input_pdf = Path.home() / "Downloads" / "acrf.pdf"

# Arquivo comprimido
output_pdf = input_pdf.with_name("acrf_compressed.pdf")

TARGET_MB = 24

def size_mb(path):
    return path.stat().st_size / (1024 * 1024)

with fitz.open(input_pdf) as doc:
    # Primeira tentativa: otimização sem reduzir
    # a resolução das imagens
    doc.save(
        str(output_pdf),
        garbage=4,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
        use_objstms=1
    )

print(f"Original: {size_mb(input_pdf):.2f} MB")
print(f"Comprimido: {size_mb(output_pdf):.2f} MB")

if size_mb(output_pdf) > TARGET_MB:
    print("Aplicando compressão de imagens...")

    with fitz.open(input_pdf) as doc:
        doc.rewrite_images(
            dpi_threshold=180,
            dpi_target=150,
            quality=75,
            lossy=True,
            lossless=True,
            bitonal=True,
            color=True,
            gray=True
        )

        doc.save(
            str(output_pdf),
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            use_objstms=1
        )

    print(f"Novo tamanho: {size_mb(output_pdf):.2f} MB")

if size_mb(output_pdf) < TARGET_MB:
    print("PDF pronto para upload no GitHub!")
else:
    print("Ainda acima do limite. Será necessário comprimir mais.")
