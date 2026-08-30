"""Legal sources."""

from legallens_legal.sources.companies_act import SECTIONS as COMPANIES_ACT_SECTIONS
from legallens_legal.sources.companies_act import SOURCE as COMPANIES_ACT_SOURCE
from legallens_legal.sources.contract_act import SECTIONS as CONTRACT_ACT_SECTIONS
from legallens_legal.sources.contract_act import SOURCE as CONTRACT_ACT_SOURCE
from legallens_legal.sources.it_act import SECTIONS as IT_ACT_SECTIONS
from legallens_legal.sources.it_act import SOURCE as IT_ACT_SOURCE

ALL_SOURCES = [CONTRACT_ACT_SOURCE, COMPANIES_ACT_SOURCE, IT_ACT_SOURCE]
ALL_SECTIONS = CONTRACT_ACT_SECTIONS + COMPANIES_ACT_SECTIONS + IT_ACT_SECTIONS
