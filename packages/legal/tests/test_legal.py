"""Tests for LegalLens Legal package."""

from legallens_legal.chunking import chunk_section, chunk_text
from legallens_legal.ingestion import load_all_sources, load_source, search_sections
from legallens_legal.models import LegalChunk, LegalSection, LegalSource
from legallens_legal.versioning import get_current_version, get_version_history


def test_legal_source_creation():
    source = LegalSource(
        source_id="test",
        name="Test Act",
        short_name="TA",
        year=2024,
    )
    assert source.source_id == "test"
    assert source.year == 2024


def test_legal_section_creation():
    section = LegalSection(
        section_id="sec_1",
        source_id="test_source",
        section_number="1",
        title="Test Section",
        content="Test content",
    )
    assert section.full_reference == "Section 1, test_source"


def test_legal_chunk_creation():
    chunk = LegalChunk(
        chunk_id="chunk_1",
        source_id="test_source",
        section_number="1",
        title="Test",
        content="Test content here",
    )
    assert chunk.word_count == 3
    assert chunk.char_end == len("Test content here")


def test_load_source():
    source, sections = load_source("indian_contract_act_1872")
    assert source is not None
    assert source.short_name == "Contract Act"
    assert len(sections) > 0


def test_load_all_sources():
    all_sources = load_all_sources()
    assert len(all_sources) == 3


def test_search_sections():
    results = search_sections("penalty")
    assert len(results) > 0
    assert any("penalty" in s.title.lower() or "penalty" in s.content.lower() for s in results)


def test_chunk_section():
    _source, sections = load_source("indian_contract_act_1872")
    chunks = chunk_section(sections[0])
    assert len(chunks) == 1
    assert chunks[0].chunk_id.startswith("chunk_")


def test_chunk_text():
    text = " ".join(["word"] * 1000)
    chunks = chunk_text(text, max_words=200)
    assert len(chunks) == 5
    assert chunks[0]["word_count"] == 200


def test_version_history():
    history = get_version_history("indian_contract_act_1872")
    assert len(history) >= 2


def test_current_version():
    current = get_current_version("indian_contract_act_1872")
    assert current is not None
    assert current.is_current is True
