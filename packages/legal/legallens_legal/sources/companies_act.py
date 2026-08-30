"""Companies Act, 2013 - Key provisions."""

from __future__ import annotations

from legallens_legal.models import LegalSection, LegalSource

SOURCE = LegalSource(
    source_id="companies_act_2013",
    name="Companies Act, 2013",
    short_name="Companies Act",
    year=2013,
    status="active",
    description="Governs incorporation, management, and dissolution of companies in India.",
    version="1.0",
)

SECTIONS: list[LegalSection] = [
    LegalSection(
        section_id="ca_2",
        source_id="companies_act_2013",
        section_number="2",
        title="Definitions",
        content="""(13) "Company" means a company incorporated under this Act or under any previous company law.
(42) "Offer for sale" means the offer of securities or debentures of a company for sale to the public.""",
        is_definitions=True,
    ),
    LegalSection(
        section_id="ca_3",
        source_id="companies_act_2013",
        section_number="3",
        title="Formation of company",
        content="""(1) There may be formed for any lawful purpose by seven or more persons,
where the company to be formed is to be a public company, or by two or more persons,
where the company to be formed is to be a private company, by subscribing their names
to a memorandum and complying with the requirements of this Act.""",
    ),
    LegalSection(
        section_id="ca_27",
        source_id="companies_act_2013",
        section_number="27",
        title="Prohibition of thin capitalisation",
        content="""(1) No company limited by shares shall borrow in excess of the limit as may be prescribed.""",
    ),
    LegalSection(
        section_id="ca_62",
        source_id="companies_act_2013",
        section_number="62",
        title="Further issue of share capital",
        content="""(1) Where at any time after the company has formed a company with limited liability,
the company proposes to increase the subscribed capital of the company by allotment
of further shares, such further shares shall be offered to the persons who at the time
of the allotment are the holders of the equity shares of the company in proportion,
as nearly as circumstances admit, to the paid-up share capital on those shares.""",
    ),
    LegalSection(
        section_id="ca_73",
        source_id="companies_act_2013",
        section_number="73",
        title="Debentures",
        content="""(1) A company may issue debentures with an option to convert such debentures into
shares, either wholly or partly at the time of redemption.""",
    ),
    LegalSection(
        section_id="ca_185",
        source_id="companies_act_2013",
        section_number="185",
        title="Loan to directors, etc.",
        content="""(1) No company shall, directly or indirectly, advance any loan, including any loan
represented by a book debt to, or give any guarantee or provide any security in
connection with any loan taken by—
(a) any director of the company, or of a company which is its holding company; or
(b) any partner or relative of any director of the company, or of a company which is
its holding company.""",
    ),
    LegalSection(
        section_id="ca_186",
        source_id="companies_act_2013",
        section_number="186",
        title="Loan and investment by company",
        content="""(1) Without prejudice to the provisions contained in section 185, a company shall,
if so authorised by its articles, make loans and investments, and give guarantees
and provide securities in connection with loans to any person or body corporate.""",
    ),
]
