from docparser.docling import Parser
from docparser.types import ParseOpt


def test_parse_url_markdown():
    opt = ParseOpt(
        source="url",
        address=["https://arxiv.org/pdf/2501.17887"],
        input_format="pdf",
        output_format="markdown",
        do_ocr=False,
    )
    parser = Parser(opt)
    for result in parser.run():
        print("=== URL-Markdown Output ===")
        print(result.markdown)
        break


def test_parse_local_html():
    opt = ParseOpt(
        source="local",
        address=["tests/1.pdf"],
        input_format="pdf",
        output_format="html",
        do_ocr=False,
    )
    parser = Parser(opt)
    for result in parser.run():
        print("=== Local-HTML Output ===")
        print(result.html)
        break


def test_parse_url_json():
    opt = ParseOpt(
        source="url",
        address=["https://arxiv.org/pdf/2501.17887"],
        input_format="pdf",
        output_format="json",
        do_ocr=False,
    )
    parser = Parser(opt)
    for result in parser.run():
        print("=== URL-JSON Output ===")
        print(result.json)
        break


def test_parse_local_markdown():
    opt = ParseOpt(
        source="local",
        address=["tests/1.pdf"],
        input_format="pdf",
        output_format="markdown",
        do_ocr=True,
    )
    parser = Parser(opt)
    for result in parser.run():
        print("=== Local-Markdown Output ===")
        print(result.markdown)
        print("=== Table===")
        print(result.table)
        print("=== figure===")
        print(result.figure)
        # print("=== text===")
        # print(result.text)
        print("=== page===")
        print(result.page)
        break


def test_parse_url_html():
    opt = ParseOpt(
        source="url",
        address=["https://arxiv.org/pdf/2501.17887"],
        input_format="pdf",
        output_format="html",
        do_ocr=False,
    )
    parser = Parser(opt)
    for result in parser.run():
        print("=== URL-HTML Output ===")
        print(result.html)
        break


def test_parse_local_json():
    opt = ParseOpt(
        source="local",
        address=["tests/1.pdf"],
        input_format="pdf",
        output_format="json",
        do_ocr=False,
    )
    parser = Parser(opt)
    for result in parser.run():
        print("=== Local-JSON Output ===")
        print(result.json)
        break


if __name__ == "__main__":
    test_parse_local_markdown()
    # test_parse_url_markdown()
    # test_parse_local_html()
    # test_parse_url_json()
    # test_parse_url_html()
    # test_parse_local_json()
