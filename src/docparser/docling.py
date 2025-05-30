from collections.abc import Generator
from pathlib import Path
from typing import final, override
from loguru import logger

from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.document import ConversionResult
from docling_core.types.doc.document import PictureItem
from docling_core.types.doc.base import ImageRefMode
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import (
    DocItem,
    TextItem,
)
from PIL.Image import Image

from docparser.base_parser import BaseParser
from docparser.types import (
    CommonParseOutput,
    ImageElement,
    Metadata,
    ParseOpt,
    ParseOutput,
    SavePath,
    TableElement,
    TextElement,
)
from docparser.utils import get_time_sync


@final
class Parser(BaseParser):
    def __init__(self, opt: ParseOpt) -> None:
        super().__init__(opt)
        self._convert = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=self._opt_process(opt)
                )
            },
        )

    @staticmethod
    def _to_metadata(element: DocItem) -> Metadata:
        page_no, bbox = (element.prov[0].page_no, element.prov[0].bbox)
        bbox = (bbox.l, bbox.t, bbox.r, bbox.b)
        return Metadata(page_no=page_no, bbox=bbox)

    def _opt_process(self, opt: ParseOpt) -> PdfPipelineOptions:
        pipe_opt = PdfPipelineOptions()
        if opt.do_ocr:
            pipe_opt.do_ocr = True
            pipe_opt.ocr_options = EasyOcrOptions()
            pipe_opt.ocr_options.use_gpu = False
            pipe_opt.do_formula_enrichment = True
        pipe_opt.do_table_structure = True
        pipe_opt.generate_page_images = True
        pipe_opt.generate_picture_images = True
        pipe_opt.table_structure_options.do_cell_matching = False
        return pipe_opt

    def _run(self) -> Generator[ConversionResult, None, None]:
        source: list[str] | list[Path] = self.opt.address
        if self.opt.source == "local":
            source = [Path(addr) for addr in self.opt.address]
        yield from self._convert.convert_all(source=source, raises_on_error=True)

    def _extract_body(
        self, conv_res: ConversionResult
    ) -> tuple[list[TextElement], list[Image], list[ImageElement]]:
        pages: list[Image] = list()
        for _, page in conv_res.document.pages.items():
            if page.image and (img := page.image.pil_image):
                pages.append(img)
        figures: list[ImageElement] = list()
        texts: list[TextElement] = list()
        for element, _ in conv_res.document.iterate_items():
            if isinstance(element, PictureItem):
                image = element.get_image(conv_res.document)
                if image is None:
                    continue
                figures.append(
                    ImageElement(metadata=self._to_metadata(element), image=image)
                )
            if isinstance(element, TextItem):
                texts.append(
                    TextElement(page_no=element.prov[0].page_no, content=element.text)
                )

        return (texts, pages, figures)

    def _extract_table_md(self, conv_res: ConversionResult) -> list[TableElement]:
        tables: list[TableElement] = list()
        for tb in conv_res.document.tables:
            table = tb.export_to_markdown(conv_res.document)
            tables.append(TableElement(metadata=self._to_metadata(tb), markdown=table))
        return tables

    def _extract_table_html(self, conv_res: ConversionResult) -> list[TableElement]:
        tables: list[TableElement] = list()
        for tb in conv_res.document.tables:
            table = tb.export_to_html(conv_res.document)
            page_no, bbox = (tb.prov[0].page_no, tb.prov[0].bbox)
            bbox = (bbox.l, bbox.t, bbox.r, bbox.b)
            tables.append(
                TableElement(metadata=Metadata(page_no=page_no, bbox=bbox), html=table)
            )
        return tables

    def _transform(self, conv_res: ConversionResult) -> ParseOutput:
        (text, page, figure) = self._extract_body(conv_res)
        name = conv_res.input.file.stem
        match self.opt.output_format:
            case "html":
                tables = self._extract_table_html(conv_res)
                html = conv_res.document.export_to_html(
                    image_mode=ImageRefMode.REFERENCED
                )
                return ParseOutput(
                    name=name,
                    text=text,
                    table=tables,
                    figure=figure,
                    page=page,
                    html=html,
                    save_path=SavePath.default(root=self.opt.save_dir)
                    if self.opt.save_dir
                    else None,
                )
            case "json":
                tables = self._extract_table_md(conv_res)
                json = conv_res.document.export_to_dict()
                return ParseOutput(
                    name=name,
                    text=text,
                    table=tables,
                    figure=figure,
                    page=page,
                    json=json,
                    save_path=SavePath.default(root=self.opt.save_dir)
                    if self.opt.save_dir
                    else None,
                )

            case _:
                tables = self._extract_table_md(conv_res)
                markdown = conv_res.document.export_to_markdown(
                    image_mode=ImageRefMode.REFERENCED
                )
                return ParseOutput(
                    name=name,
                    text=text,
                    table=tables,
                    figure=figure,
                    page=page,
                    markdown=markdown,
                    save_path=SavePath.default(root=self.opt.save_dir)
                    if self.opt.save_dir
                    else None,
                )

    @get_time_sync
    @override
    def run_sp(self) -> Generator[ParseOutput, None, None]:
        for conv_res in self._run():
            if conv_res.status != ConversionStatus.SUCCESS:
                logger.error(f"failed to parse this file: {conv_res.errors}")
            yield self._transform(conv_res)

    @get_time_sync
    @override
    def run(self) -> Generator[CommonParseOutput, None, None]:
        for conv_res in self._run():
            if conv_res.status != ConversionStatus.SUCCESS:
                logger.error(f"failed to parse this file: {conv_res.errors}")
            save_dir = self.opt.save_dir / conv_res.input.file.stem
            save_dir.mkdir(parents=True, exist_ok=True)
            figure_count = 0
            for element, _ in conv_res.document.iterate_items():
                if isinstance(element, PictureItem):
                    figure_count += 1
                    with (save_dir / f"figure-{figure_count}.png").open("wb") as f:
                        image = element.get_image(conv_res.document)
                        if image is None:
                            continue
                        image.save(f, "PNG")
            match self.opt.output_format:
                case "html":
                    save_path = save_dir / "output-with-image-ref.html"
                    conv_res.document.save_as_html(
                        save_path,
                        image_mode=ImageRefMode.REFERENCED,
                    )
                case "json":
                    save_path = save_dir / "output-with-image-ref.json"
                    conv_res.document.save_as_json(
                        save_path,
                        image_mode=ImageRefMode.REFERENCED,
                    )
                case _:
                    save_path = save_dir / "output-with-image-ref.md"
                    conv_res.document.save_as_markdown(
                        save_path,
                        image_mode=ImageRefMode.REFERENCED,
                    )
            yield CommonParseOutput(
                output_format=self.opt.output_format, output_path=save_path
            )
