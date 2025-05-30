from collections.abc import Generator
from typing import cast, final, override

from loguru import logger
from pydantic import BaseModel
from docparser.base_parser import BaseParser
from docparser.types import ParseOpt, ParseOutput
from docparser.utils import download, get_time_sync
from marker.config.parser import ConfigParser
from marker.models import create_model_dict
from marker.converters.pdf import PdfConverter
from marker.output import text_from_rendered


@final
class Parser(BaseParser):
    def __init__(self, opt: ParseOpt) -> None:
        super().__init__(opt)
        config = self._generate_config(opt)
        self._converter = PdfConverter(
            config=config,
            artifact_dict=create_model_dict(),
            processor_list=config.get_processors(),
            renderer=config.get_renderer(),
            llm_service=config.get_llm_service(),
        )

    @staticmethod
    def _generate_config(opt: ParseOpt) -> ConfigParser:
        config = {"output_format": opt.output_format, "use_llm": opt.use_llm}
        if opt.save_dir:
            config["output_dir"] = str(opt.save_dir)
        return ConfigParser(config)

    def _run(self) -> Generator[ParseOutput, None, None]:
        for addr in self.opt.address:
            match self.opt.source:
                case "local":
                    rendered = self._converter(addr)
                case _:
                    fetch_file = download(addr)
                    if fetch_file.is_err():
                        logger.error(f"failed to fetch pdf from url: {fetch_file}")
                    rendered = self._converter(fetch_file.unwrap())
            text, _, images = text_from_rendered(rendered)
            match self.opt.output_format:
                case "markdown":
                    yield ParseOutput(
                        name=addr.split("/")[-1],
                        text=list(),
                        markdown=cast(str, text),
                        figure=images,
                        table=list(),
                        page=list(),
                    )

    @get_time_sync
    @override
    def run(self) -> Generator[ParseOutput, None, None]:
        return self._run()
