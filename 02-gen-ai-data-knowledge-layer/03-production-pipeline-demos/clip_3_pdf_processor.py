import pdfplumber
import pytesseract
from PIL import Image
import io

def extract_content_from_pdf(pdf_path):
    content_chunks = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract text
            text = page.extract_text()
            if text:
                content_chunks.append({
                    "type": "text",
                    "page": page_num,
                    "content": text
                })
            
            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                # Convert table to markdown-like string
                table_str = "\n".join(["| " + " | ".join(row) + " |" for row in table if any(row)])
                content_chunks.append({
                    "type": "table",
                    "page": page_num,
                    "content": table_str
                })
            
            # Extract images (if any)
            for img in page.images:
                # Get image data
                img_data = img["stream"].get_data()
                image = Image.open(io.BytesIO(img_data))
                # Perform OCR
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():
                    content_chunks.append({
                        "type": "image_text",
                        "page": page_num,
                        "content": ocr_text
                    })
                # Optionally, generate a caption using a vision model (skipped for brevity)
    
    return content_chunks

# Example usage
chunks = extract_content_from_pdf("sample_document.pdf")
for chunk in chunks:
    print(f"Type: {chunk['type']}, Page: {chunk['page']}")
    print(f"Content preview: {chunk['content'][:100]}...\n")