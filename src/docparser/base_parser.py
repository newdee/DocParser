from collections.abc import Generator
from docparser.types import ParseOpt, ParseOutput


class BaseParser:
    def __init__(self, opt: ParseOpt) -> None:
        if not opt.ok:
            return
        self.opt: ParseOpt = opt

    def run(self) -> Generator[ParseOutput, None, None]: ...
