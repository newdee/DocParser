from docparser import docling, marker
from docparser.types import ParseOpt
import json


def test_parse_local_markdown_with_docling():
    opt = ParseOpt(
        source="local",
        address=["tests/1.pdf"],
        input_format="pdf",
        output_format="markdown",
        do_ocr=True,
        save_dir="./output",
    )
    parser = docling.Parser(opt)
    for result in parser.run():
        print(result)
        break


def test_parse_local_markdown_with_marker():
    opt = ParseOpt(
        source="local",
        address=["tests/1.pdf"],
        input_format="pdf",
        output_format="markdown",
        do_ocr=True,
        save_dir="./output",
    )
    parser = marker.Parser(opt)
    for result in parser.run():
        print(result)
        break


def test_parse_url_markdown_with_docling():
    opt = ParseOpt(
        source="url",
        address=["https://arxiv.org/pdf/2501.17887"],
        input_format="pdf",
        output_format="markdown",
        save_dir="./output",
        do_ocr=False,
    )
    parser = docling.Parser(opt)
    for result in parser.run_sp():
        print("=== URL-Markdown Output ===")
        print(result.markdown)
        print("=== figure===")
        print(result.figure)
        # print("=== text===")
        # print(result.text)
        print("=== page===")
        print(result.page)
        print("=== page===")
        print(result.path)
        _ = result.save_page().save_figure()
        break


def test_parse_local_html():
    opt = ParseOpt(
        source="local",
        address=["tests/1.pdf"],
        input_format="pdf",
        output_format="html",
        do_ocr=False,
        save_dir="output",
    )
    parser = docling.Parser(opt)
    for result in parser.run_sp():
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
        save_dir="output",
    )
    parser = docling.Parser(opt)
    for result in parser.run_sp():
        print("=== URL-JSON Output ===")
        print(result.json)
        break


def test_parse_url_html():
    opt = ParseOpt(
        source="url",
        address=["https://arxiv.org/pdf/2501.17887"],
        input_format="pdf",
        output_format="html",
        do_ocr=False,
        save_dir="output",
    )
    parser = docling.Parser(opt)
    for result in parser.run_sp():
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
        save_dir="output",
    )
    parser = docling.Parser(opt)
    for result in parser.run_sp():
        print("=== Local-JSON Output ===")
        # print(json.dumps(result.json))
        with open("tests/1.json", "w") as f:
            json.dump(result.json, f)
        break


if __name__ == "__main__":
    test_parse_local_markdown_with_docling()
    # test_parse_local_markdown_with_marker()
    # test_parse_url_markdown()
    # test_parse_local_html()
    # test_parse_url_json()
    # test_parse_url_html()
    # test_parse_local_json()
