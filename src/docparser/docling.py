from collections.abc import Generator
from pathlib import Path
from typing import final

from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import (
    DocItem,
    PictureItem,
    TextItem,
)
from PIL.Image import Image

from docparser.types import (
    ImageElement,
    Metadata,
    ParseOpt,
    ParseOutput,
    TableElement,
    TextElement,
)


@final
class Parser:
    def __init__(self, opt: ParseOpt) -> None:
        if not opt.ok:
            return
        self.opt = opt
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
        pipe_opt.do_ocr = opt.do_ocr
        pipe_opt.ocr_options = EasyOcrOptions()
        pipe_opt.ocr_options.use_gpu = False
        pipe_opt.do_table_structure = True
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
            table = tb.export_to_markdown()
            tables.append(TableElement(metadata=self._to_metadata(tb), markdown=table))
        return tables

    def _extract_table_html(self, conv_res: ConversionResult) -> list[TableElement]:
        tables: list[TableElement] = list()
        for tb in conv_res.document.tables:
            table = tb.export_to_html()
            page_no, bbox = (tb.prov[0].page_no, tb.prov[0].bbox)
            bbox = (bbox.l, bbox.t, bbox.r, bbox.b)
            tables.append(
                TableElement(metadata=Metadata(page_no=page_no, bbox=bbox), html=table)
            )
        return tables

    def _transform(self, conv_res: ConversionResult) -> ParseOutput:
        (text, page, figure) = self._extract_body(conv_res)
        match self.opt.output_format:
            case "html":
                tables = self._extract_table_html(conv_res)
                html = conv_res.document.export_to_html()
                return ParseOutput(
                    text=text, table=tables, figure=figure, page=page, html=html
                )
            case "json":
                tables = self._extract_table_md(conv_res)
                json = conv_res.document.export_to_dict()
                return ParseOutput(
                    text=text, table=tables, figure=figure, page=page, json=json
                )

            case _:
                tables = self._extract_table_md(conv_res)
                markdown = conv_res.document.export_to_markdown()
                return ParseOutput(
                    text=text, table=tables, figure=figure, page=page, markdown=markdown
                )

    def run(self) -> Generator[ParseOutput, None, None]:
        for conv_res in self._run():
            yield self._transform(conv_res)
