import pytest
from app.utils import normalize_domain, check_ssrf


class TestNormalizeDomain:
    def test_full_url(self):
        assert normalize_domain("https://www.example.com/path?q=1") == "example.com"

    def test_bare_domain(self):
        assert normalize_domain("example.com") == "example.com"

    def test_www_stripped(self):
        assert normalize_domain("http://www.test.org") == "test.org"

    def test_uppercase(self):
        assert normalize_domain("HTTPS://WWW.EXAMPLE.COM") == "example.com"

    def test_subdomain_preserved(self):
        assert normalize_domain("https://blog.example.com") == "blog.example.com"

    def test_port_removed(self):
        assert normalize_domain("http://example.com:8080/page") == "example.com"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            normalize_domain("")

    def test_whitespace_stripped(self):
        assert normalize_domain("  example.com  ") == "example.com"


class TestCheckSSRF:
    def test_localhost_blocked(self):
        with pytest.raises(ValueError, match="loopback"):
            check_ssrf("localhost")

    def test_127_blocked(self):
        with pytest.raises(ValueError, match="loopback"):
            check_ssrf("127.0.0.1")

    def test_public_domain_ok(self):
        # Should not raise
        check_ssrf("example.com")
