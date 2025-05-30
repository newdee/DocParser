from __future__ import annotations

from dataclasses import dataclass
from multiprocessing import parent_process
from pathlib import Path
from random import choice
from typing import Literal, Self, final

from loguru import logger
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
        save_dir: str | None = None,
        use_llm: bool = False,
    ) -> None:
        self.source = source
        self.address = address
        self.input_format = input_format
        self.output_format = output_format
        self.do_ocr = do_ocr
        self.gpu_enabled = gpu_enabled
        self.capbility = capbility if not capbility else ["text", "image", "table"]
        self.save_dir = Path(save_dir) if save_dir else None
        self.use_llm = use_llm

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


@dataclass
class SavePath:
    root: Path
    figure: list[Path]
    page: list[Path]
    markdown: Path | None = None
    json: Path | None = None
    html: Path | None = None

    def mkdir(self) -> Self:
        self.root.mkdir(parents=True, exist_ok=True)
        return self

    @staticmethod
    def default(root: Path) -> SavePath:
        return SavePath(root=root, figure=list(), page=list()).mkdir()


@dataclass
class ParseOutput:
    name: str
    text: list[TextElement]
    table: list[TableElement]
    figure: list[ImageElement]
    page: list[Image]
    markdown: str | None = None
    json: dict[str, object] | None = None
    html: str | None = None
    save_path: SavePath | None = None
    ok: bool = True

    @property
    def path(self):
        return self.save_path

    def save_figure(self) -> Self:
        if not self.save_path:
            logger.error("Save path has not been set!")
            return self
        for ind, fig in enumerate(self.figure):
            save_path = self.save_path.root / f"{self.name}-figure-{ind}.png"
            with open(save_path, "wb") as f:
                fig.image.save(f, "PNG")
            self.save_path.figure.append(save_path)
        return self

    def save_page(
        self,
    ) -> Self:
        if not self.save_path:
            logger.error("Save path has not been set!")
            return self
        for ind, pg in enumerate(self.page):
            save_path = self.save_path.root / f"{self.name}-{ind}.png"
            with open(save_path, "wb") as f:
                pg.save(f, "PNG")
            self.save_path.page.append(save_path)
        return self
