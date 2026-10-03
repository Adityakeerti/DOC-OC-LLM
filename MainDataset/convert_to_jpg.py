import os
import io
import shutil
from PIL import Image
import fitz  # PyMuPDF


def convert_pdf_to_jpg(pdf_path, output_dir):
    """Convert first page of PDF to JPG"""
    try:
        doc = fitz.open(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # higher resolution
        img_data = pix.tobytes("ppm")

        img = Image.open(io.BytesIO(img_data))
        output_path = os.path.join(output_dir, f"{base_name}.jpg")
        img.convert("RGB").save(output_path, "JPEG", quality=95)

        print(f"[✅] PDF → JPG: {output_path}")
        doc.close()

    except Exception as e:
        print(f"[❌] Error converting PDF '{pdf_path}': {e}")


def convert_image_to_jpg(img_path, output_dir):
    """Convert PNG, BMP, TIFF, GIF, WEBP to JPG"""
    try:
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.jpg")

        with Image.open(img_path) as img:
            img.convert("RGB").save(output_path, "JPEG", quality=95)

        print(f"[✅] Image converted: {output_path}")

    except Exception as e:
        print(f"[❌] Error converting image '{img_path}': {e}")


def copy_jpg(img_path, output_dir):
    """Copy existing JPG image to output directory"""
    try:
        base_name = os.path.basename(img_path)
        output_path = os.path.join(output_dir, base_name)
        shutil.copy(img_path, output_path)
        print(f"[📋] Copied JPG: {output_path}")
    except Exception as e:
        print(f"[❌] Error copying JPG '{img_path}': {e}")


def main():
    input_dir = "."
    output_dir = "first_page_jpg"

    os.makedirs(output_dir, exist_ok=True)

    print(f"📂 Input directory: {os.path.abspath(input_dir)}")
    print(f"💾 Output directory: {os.path.abspath(output_dir)}")
    print("-" * 60)

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

        # Skip directories and output folder
        if os.path.isdir(file_path) or file_path.startswith(output_dir):
            continue

        lower_name = filename.lower()

        if lower_name.endswith('.pdf'):
            convert_pdf_to_jpg(file_path, output_dir)
        elif lower_name.endswith('.jpg'):
            copy_jpg(file_path, output_dir)
        elif lower_name.endswith(('.png', '.bmp', '.tiff', '.gif', '.webp')):
            convert_image_to_jpg(file_path, output_dir)

    print("\n✅ All files processed successfully!")


if __name__ == "__main__":
    main()
