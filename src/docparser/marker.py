import json
from collections.abc import Generator
from pathlib import Path
from typing import cast, final, override

from loguru import logger
from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import convert_if_not_rgb, text_from_rendered
from pydantic import BaseModel

from docparser.base_parser import BaseParser
from docparser.types import CommonParseOutput, ParseOpt, ParseOutput
from docparser.utils import download_pdf, get_time_sync


@final
class Parser(BaseParser):
    def __init__(self, opt: ParseOpt) -> None:
        super().__init__(opt)
        config = self._generate_config(opt)
        self._converter = PdfConverter(
            config=config.generate_config_dict(),
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

    def _run(self) -> Generator[CommonParseOutput, None, None]:
        for addr in self.opt.address:
            match self.opt.source:
                case "local":
                    file_name = Path(addr).stem
                    rendered = self._converter(addr)
                case _:
                    fetch_result = download_pdf(addr)
                    if fetch_result.is_err():
                        logger.error(f"failed to fetch pdf from url: {fetch_result}")
                    file_name, content = fetch_result.unwrap()
                    rendered = self._converter(content)
            text, ext, images = text_from_rendered(rendered)
            output_dir = Path(self.opt.save_dir / file_name.removesuffix(".pdf"))
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / "metadata.json", "w") as f:
                json.dump(rendered.metadata, f)
            with open(output_dir / f"output.{ext}", "w") as f:
                f.write(text)
            for img_name, img in images.items():
                img = convert_if_not_rgb(img)  # RGBA images can't save as JPG
                img.save(output_dir / img_name, "PNG")
            yield CommonParseOutput(
                output_format=self.opt.output_format,
                output_path=output_dir / f"output.{ext}",
            )

    @get_time_sync
    @override
    def run(self) -> Generator[CommonParseOutput, None, None]:
        return self._run()
