"""Tests for the schema validation analyzer."""

import json
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from app.analyzers.schema_validator import (
    analyze_schema_validation,
    _extract_jsonld,
    _extract_microdata,
    _extract_rdfa,
)
from app.schema_defs import is_valid_type, get_valid_properties


# --- Helpers ---

def _make_page(html: str):
    """Create a mock FetchResult from HTML string."""
    import requests
    import datetime
    from app.fetcher import FetchResult

    resp = MagicMock()
    resp.text = html
    resp.content = html.encode()
    resp.status_code = 200
    resp.elapsed = datetime.timedelta(milliseconds=10)
    resp.headers = {"Content-Type": "text/html"}
    soup = BeautifulSoup(html, "html.parser")
    page = FetchResult.__new__(FetchResult)
    page.url = "https://example.com"
    page.response = resp
    page.soup = soup
    page.elapsed_ms = 10
    page.page_size_kb = len(html) / 1024
    page.scheme = "https"
    page.domain = "example.com"
    page.base_url = "https://example.com"
    return page


# --- Schema Defs Tests ---

def test_valid_type_product():
    assert is_valid_type("Product") is True


def test_valid_type_unknown():
    assert is_valid_type("FakeType123") is False


def test_valid_properties_product():
    props = get_valid_properties("Product")
    assert "name" in props
    assert "offers" in props
    assert "brand" in props


# --- JSON-LD Extraction ---

def test_extract_valid_jsonld():
    html = '''<html><head><script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Product","name":"Widget"}
    </script></head><body></body></html>'''
    soup = BeautifulSoup(html, "html.parser")
    results = _extract_jsonld(soup)
    assert len(results) == 1
    assert results[0][0]["@type"] == "Product"


def test_extract_jsonld_with_graph():
    html = '''<html><head><script type="application/ld+json">
    {"@context":"https://schema.org","@graph":[
        {"@type":"WebSite","name":"Test"},
        {"@type":"Organization","name":"Org"}
    ]}</script></head><body></body></html>'''
    soup = BeautifulSoup(html, "html.parser")
    results = _extract_jsonld(soup)
    assert len(results) == 1
    assert "@graph" in results[0][0]


def test_extract_malformed_jsonld():
    html = '''<html><head><script type="application/ld+json">
    {not valid json}
    </script></head><body></body></html>'''
    soup = BeautifulSoup(html, "html.parser")
    results = _extract_jsonld(soup)
    assert len(results) == 1
    assert results[0][0].get("_parse_error") is True


# --- Microdata Extraction ---

def test_extract_microdata():
    html = '''<html><body>
    <div itemscope itemtype="https://schema.org/Product">
        <span itemprop="name">Widget</span>
        <span itemprop="description">A nice widget</span>
    </div>
    </body></html>'''
    soup = BeautifulSoup(html, "html.parser")
    results = _extract_microdata(soup)
    assert len(results) == 1
    assert results[0][0]["@type"] == "Product"
    assert "name" in results[0][0]["_properties"]
    assert "description" in results[0][0]["_properties"]


# --- RDFa Extraction ---

def test_extract_rdfa():
    html = '''<html><body>
    <div vocab="https://schema.org/" typeof="Person">
        <span property="name">John</span>
    </div>
    </body></html>'''
    soup = BeautifulSoup(html, "html.parser")
    results = _extract_rdfa(soup)
    assert len(results) == 1
    assert results[0][0]["@type"] == "Person"


# --- Full Analysis ---

def test_analyze_valid_product():
    html = '''<html><head><script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Product","name":"Widget","description":"A widget","offers":{"@type":"Offer","price":"9.99"}}
    </script></head><body></body></html>'''
    page = _make_page(html)
    result = analyze_schema_validation(page)
    assert result.status == "ok"
    assert result.metrics["entities_found"] >= 1
    assert result.metrics["syntax_errors"] == 0


def test_analyze_unknown_type():
    html = '''<html><head><script type="application/ld+json">
    {"@context":"https://schema.org","@type":"FakeType","name":"Test"}
    </script></head><body></body></html>'''
    page = _make_page(html)
    result = analyze_schema_validation(page)
    assert result.metrics["type_errors"] >= 1
    assert any("Unknown schema.org type" in i.message for i in result.issues)


def test_analyze_malformed_json():
    html = '''<html><head><script type="application/ld+json">
    {invalid json here}
    </script></head><body></body></html>'''
    page = _make_page(html)
    result = analyze_schema_validation(page)
    assert result.metrics["syntax_errors"] >= 1
    assert any("syntax error" in i.message.lower() for i in result.issues)


def test_analyze_no_schema():
    html = '<html><head></head><body><p>No schema here</p></body></html>'
    page = _make_page(html)
    result = analyze_schema_validation(page)
    assert result.metrics["entities_found"] == 0
    assert any("No schema markup" in i.message for i in result.issues)


def test_analyze_microdata_entity():
    html = '''<html><body>
    <div itemscope itemtype="https://schema.org/Person">
        <span itemprop="name">Jane</span>
        <span itemprop="jobTitle">Engineer</span>
    </div>
    </body></html>'''
    page = _make_page(html)
    result = analyze_schema_validation(page)
    assert result.metrics["microdata_count"] == 1
    assert any(e.entity_type == "Person" for e in result.entities)
