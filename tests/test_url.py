import pytest
from docparser.utils import is_valid_url


# 测试有效的 URL
@pytest.mark.parametrize(
    "url",
    [
        [
            "https://www.example.com",
            "http://example.com",
            "https://arxiv.org/pdf/2501.17887",
        ],
    ],
)
def test_valid_url(url: list[str]):
    assert is_valid_url(url) is True


# 测试无效的 URL
@pytest.mark.parametrize(
    "url",
    [
        [
            "htp://invalid-url",  # 错误的协议
            "www.example.com",  # 缺少协议部分
            "ftp://example.com",
            "example",  # 没有协议和域名
            "https://",  # 协议存在但缺少域名
            "ftp:/example.com",  # 错误的 FTP 协议
            "https://subdomain.example.com/path?query#fragment",
        ]
    ],
)
def test_invalid_url(url: list[str]):
    assert is_valid_url(url) is False
