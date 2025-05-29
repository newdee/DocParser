from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import choice
from typing import Literal, final

from pandas import DataFrame as PdData
from PIL.Image import Image

from docparser.utils import is_valid_path, is_valid_url

default_providers = ["pymupdf", "docling", "marker", "random"]
DefaultCapbility = Literal["text", "image", "table"]


@final
class ParseOpt:
    def __init__(
        self,
        source: Literal["url", "local"],
        address: list[str],
        input_format: Literal["pdf"],
        output_format: Literal["markdown", "json", "html"],
        capbility: list[DefaultCapbility] | None = None,
        do_ocr: bool = True,
        gpu_enabled: bool = False,
        save_dir: Path | None = None,
    ) -> None:
        self.source = source
        self.address = address
        self.input_format = input_format
        self.output_format = output_format
        self.do_ocr = do_ocr
        self.gpu_enabled = gpu_enabled
        self.capbility = capbility if not capbility else ["text", "image", "table"]

    @property
    def ok(self) -> bool:
        match self.source:
            case "url":
                return is_valid_url(self.address)
            case _:
                return is_valid_path(self.address)


@final
class ParseReq:
    def __init__(
        self,
        option: ParseOpt,
        provider: Literal["pymupdf", "docling", "marker", "random"] = "random",
    ):
        self.option = option
        self.provider = choice(default_providers) if provider == "random" else provider

    @property
    def ok(self):
        return self.option.ok


@dataclass(frozen=True)
class Metadata:
    page_no: int
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class TableElement:
    metadata: Metadata
    markdown: str | None = None
    html: str | None = None
    pandas: PdData | None = None


@dataclass(frozen=True)
class ImageElement:
    metadata: Metadata
    image: Image


@dataclass(frozen=True)
class TextElement:
    page_no: int
    content: str


@dataclass(frozen=True)
class ParseOutput:
    text: list[TextElement]
    table: list[TableElement]
    figure: list[ImageElement]
    page: list[Image]
    markdown: str | None = None
    json: dict[str, object] | None = None
    html: str | None = None
    ok: bool = True
