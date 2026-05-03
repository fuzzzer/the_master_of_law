"""Parser sub-package — extracts structured legal content from raw HTML/PDF/DOCX."""

from pipeline.parser.html_parser import HtmlLegalParser
from pipeline.parser.structure_extractor import StructureExtractor
from pipeline.parser.metadata_extractor import MetadataExtractor

__all__ = ["HtmlLegalParser", "StructureExtractor", "MetadataExtractor"]
