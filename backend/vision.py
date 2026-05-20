import fitz  # PyMuPDF
import os
import base64
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain_core.documents import Document

# Comprehensive MIME type map for common image formats
MIME_TYPE_MAP = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".bmp":  "image/bmp",
    ".tiff": "image/tiff",
    ".tif":  "image/tiff",
}
DEFAULT_MIME_TYPE = "image/jpeg"


BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

def extract_images_from_pdf(pdf_path, output_dir=None):
    """Extracts images from a PDF and saves them to the output directory."""
    if output_dir is None:
        output_dir = os.path.join(BACKEND_DIR, "data", "images")
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []
    base_name = os.path.basename(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Skip very small images (like logos or icons)
            if len(image_bytes) < 10000:
                continue

            image_filename = f"{base_name}_page{page_num + 1}_img{img_index}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)
            with open(image_path, "wb") as f:
                f.write(image_bytes)

            image_paths.append({
                "path": image_path,
                "page": page_num + 1,
                "source_file": base_name
            })

    return image_paths


import json

CACHE_FILE = os.path.join(BACKEND_DIR, "data", "image_summaries.json")

def _load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def get_image_summary(image_path: str) -> str:
    """Generates a text summary of an image using a Vision LLM (Groq Llama Vision)."""
    # 1. Check disk cache first
    cache = _load_cache()
    if image_path in cache:
        print(f"  -> Found cached summary for {os.path.basename(image_path)}")
        return cache[image_path]

    # 2. Call Vision LLM
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        ext = os.path.splitext(image_path)[1].lower()
        mime_type = MIME_TYPE_MAP.get(ext, DEFAULT_MIME_TYPE)

        groq_key = os.getenv("GROQ_API_KEY")
        chat = ChatGroq(
            api_key=groq_key,
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0
        )
        msg = chat.invoke(
            [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": (
                                "Describe this image in detail. "
                                "Extract any text, data, charts, diagrams, and key visual elements. "
                                "This will be used as a searchable summary for Retrieval-Augmented Generation."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{encoded_string}"},
                        },
                    ]
                )
            ]
        )
        summary = msg.content
        
        # 3. Store in cache
        cache[image_path] = summary
        _save_cache(cache)
        return summary

    except Exception as e:
        print(f"Failed to summarize image {image_path}: {e}")
        return "Image without description."


def process_pdf_images(pdf_path: str) -> list[Document]:
    """Extracts images from a PDF, generates summaries, and returns them as Document objects."""
    images_info = extract_images_from_pdf(pdf_path)
    docs = []
    for info in images_info:
        print(f"Summarizing image: {info['path']}")
        summary = get_image_summary(info['path'])

        content = f"[VISUAL CONTENT SUMMARY]\n{summary}"

        doc = Document(
            page_content=content,
            metadata={
                "source_file": info["source_file"],
                "page": info["page"],
                "image_path": info["path"],
                "type": "image"
            }
        )
        docs.append(doc)
    return docs
