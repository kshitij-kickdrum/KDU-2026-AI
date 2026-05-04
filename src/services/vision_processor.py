from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

import pypdfium2 as pdfium
from openai import OpenAI

from src.models.file_models import TokenUsage, VisionExtractionResponse
from src.services.openai_utils import call_openai_with_retry

logger = logging.getLogger(__name__)


class VisionProcessor:
    def __init__(
        self,
        client: OpenAI,
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        base_delay: int = 2,
        pdf_render_scale: float = 1.35,
        pdf_page_max_tokens: int = 1200,
        pdf_max_pages: int = 0,
    ) -> None:
        self.client = client
        self.model = model
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.pdf_render_scale = pdf_render_scale
        self.pdf_page_max_tokens = pdf_page_max_tokens
        self.pdf_max_pages = pdf_max_pages

    def _extract_from_image_bytes(
        self,
        image_bytes: bytes,
        system_prompt: str,
        max_tokens: int,
        instruction: str = "Extract only visible text and preserve reading order.",
    ) -> VisionExtractionResponse:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:image/png;base64,{encoded}"

        def _call() -> object:
            return self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": instruction},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    },
                ],
                max_tokens=max_tokens,
                temperature=0.1,
            )

        response = call_openai_with_retry(_call, max_retries=self.max_retries, base_delay=self.base_delay)
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        text = response.choices[0].message.content or ""

        return VisionExtractionResponse(
            text=text,
            page_count=1,
            confidence_score=0.9,
            tokens_used=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            cost_usd=0.0,
        )

    def _extract_image_file(
        self,
        file_path: str,
        system_prompt: str,
        max_tokens: int,
    ) -> VisionExtractionResponse:
        path = Path(file_path)
        return self._extract_from_image_bytes(
            image_bytes=path.read_bytes(),
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

    def extract_text_from_pdf(self, file_path: str) -> VisionExtractionResponse:
        system_prompt = (
            "Extract only the visible text from this document page. "
            "Preserve heading and paragraph order. Do not add explanations or extra descriptions."
        )
        pdf = pdfium.PdfDocument(file_path)
        all_text: list[str] = []
        total_input_tokens = 0
        total_output_tokens = 0

        total_pages = len(pdf)
        pages_to_process = total_pages if self.pdf_max_pages <= 0 else min(total_pages, self.pdf_max_pages)

        for idx in range(pages_to_process):
            page = pdf[idx]
            pil_image = page.render(scale=self.pdf_render_scale).to_pil()
            try:
                buf = io.BytesIO()
                pil_image.save(buf, format="PNG")
                page_png = buf.getvalue()
            finally:
                page.close()

            page_result = self._extract_from_image_bytes(
                image_bytes=page_png,
                system_prompt=system_prompt,
                max_tokens=self.pdf_page_max_tokens,
                instruction=f"This is page {idx + 1}. Extract only text in reading order.",
            )
            all_text.append(f"[Page {idx + 1}]\n{page_result.text}".strip())
            total_input_tokens += page_result.tokens_used.input_tokens
            total_output_tokens += page_result.tokens_used.output_tokens

        if pages_to_process < total_pages:
            all_text.append(
                f"[Notice] Processed first {pages_to_process} pages out of {total_pages} pages to control cost."
            )

        return VisionExtractionResponse(
            text="\n\n".join(all_text).strip(),
            page_count=pages_to_process,
            confidence_score=0.9,
            tokens_used=TokenUsage(
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            ),
            cost_usd=0.0,
        )

    def extract_text_from_image(self, file_path: str) -> VisionExtractionResponse:
        return self._extract_image_file(
            file_path=file_path,
            system_prompt=(
                "Extract all visible text from this image. "
                "Describe visual elements only if they contain essential information."
            ),
            max_tokens=1536,
        )
