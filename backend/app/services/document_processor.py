import hashlib
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for parsing and chunking documents."""

    def __init__(self):
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )

    def parse_document(self, file_path: str) -> List[Dict]:
        """Parse PDF/DOCX into structured chunks with metadata.

        Args:
            file_path: Path to the document file

        Returns:
            List of chunk dictionaries with metadata
        """
        try:
            path = Path(file_path)
            extension = path.suffix.lower()

            if extension == '.pdf':
                return self._parse_pdf(file_path)
            elif extension in ['.docx', '.doc']:
                return self._parse_docx(file_path)
            elif extension in ['.txt']:
                return self._parse_text(file_path)
            else:
                logger.warning(f"Unsupported file type: {extension}")
                return []
        except Exception as e:
            logger.error(f"Failed to parse document {file_path}: {e}")
            raise

    def _parse_pdf(self, file_path: str) -> List[Dict]:
        """Parse PDF document using PyMuPDF with OCR fallback."""
        try:
            import fitz  # PyMuPDF
            processed_chunks = []
            chunk_index = 0

            doc = fitz.open(file_path)
            total_pages = len(doc)
            total_text_length = 0
            ocr_used = False

            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text()
                total_text_length += len(page_text)

                # If no text found, try OCR
                if not page_text.strip():
                    logger.debug(f"Page {page_num + 1} has no text, attempting OCR")
                    page_text = self._ocr_page(page, page_num)
                    if page_text:
                        ocr_used = True
                        total_text_length += len(page_text)

                if not page_text.strip():
                    continue

                # Split page text into chunks
                splits = self.splitter.split_text(page_text)

                for split in splits:
                    if not split.strip():
                        continue

                    char_start = page_text.find(split)
                    processed_chunks.append({
                        "chunk_index": chunk_index,
                        "text": split,
                        "page_number": page_num + 1,
                        "char_offset_start": max(0, char_start),
                        "char_offset_end": char_start + len(split) if char_start >= 0 else len(split),
                        "content_hash": hashlib.sha256(split.encode()).hexdigest()[:16],
                        "token_count": len(split.split())
                    })
                    chunk_index += 1

            doc.close()
            ocr_msg = " (OCR used)" if ocr_used else ""
            logger.info(f"Parsed PDF {file_path}: {total_pages} pages, {total_text_length} chars, {len(processed_chunks)} chunks{ocr_msg}")

            if len(processed_chunks) == 0 and total_text_length == 0:
                logger.warning(f"PDF appears to be image-based with no extractable text and OCR failed: {file_path}")

            return processed_chunks
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise

    def _ocr_page(self, page, page_num: int) -> str:
        """Extract text from a PDF page using OCR.

        Args:
            page: PyMuPDF page object
            page_num: Page number (0-indexed)

        Returns:
            Extracted text from OCR
        """
        try:
            import pytesseract
            from PIL import Image
            import io
            import fitz

            # Render page to image at higher resolution for better OCR quality
            zoom = 2.0  # 2x zoom for better quality
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Perform OCR
            text = pytesseract.image_to_string(img, lang='eng')
            logger.debug(f"OCR extracted {len(text)} characters from page {page_num + 1}")

            return text
        except Exception as e:
            logger.error(f"OCR failed for page {page_num + 1}: {e}")
            return ""

    def _parse_docx(self, file_path: str) -> List[Dict]:
        """Parse DOCX document."""
        try:
            from docx import Document

            doc = Document(file_path)
            full_text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])

            processed_chunks = []
            splits = self.splitter.split_text(full_text)

            for idx, split in enumerate(splits):
                if not split.strip():
                    continue

                char_start = full_text.find(split)
                processed_chunks.append({
                    "chunk_index": idx,
                    "text": split,
                    "page_number": None,
                    "char_offset_start": max(0, char_start),
                    "char_offset_end": char_start + len(split) if char_start >= 0 else len(split),
                    "content_hash": hashlib.sha256(split.encode()).hexdigest()[:16],
                    "token_count": len(split.split())
                })

            logger.info(f"Parsed DOCX {file_path}: {len(processed_chunks)} chunks")
            return processed_chunks
        except Exception as e:
            logger.error(f"Failed to parse DOCX {file_path}: {e}")
            raise

    def _parse_text(self, file_path: str) -> List[Dict]:
        """Parse plain text document."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()

            processed_chunks = []
            splits = self.splitter.split_text(full_text)

            for idx, split in enumerate(splits):
                if not split.strip():
                    continue

                char_start = full_text.find(split)
                processed_chunks.append({
                    "chunk_index": idx,
                    "text": split,
                    "page_number": None,
                    "char_offset_start": max(0, char_start),
                    "char_offset_end": char_start + len(split) if char_start >= 0 else len(split),
                    "content_hash": hashlib.sha256(split.encode()).hexdigest()[:16],
                    "token_count": len(split.split())
                })

            logger.info(f"Parsed text file {file_path}: {len(processed_chunks)} chunks")
            return processed_chunks
        except Exception as e:
            logger.error(f"Failed to parse text file {file_path}: {e}")
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        api_key: str,
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI with provided API key.

        Args:
            texts: List of text strings to embed
            api_key: OpenAI API key (decrypted)
            model: Embedding model name

        Returns:
            List of embedding vectors
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            response = client.embeddings.create(
                model=model,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings using model {model}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
