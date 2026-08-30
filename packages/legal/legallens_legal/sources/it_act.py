"""Information Technology Act, 2000 - Key provisions."""

from __future__ import annotations

from legallens_legal.models import LegalSection, LegalSource

SOURCE = LegalSource(
    source_id="it_act_2000",
    name="Information Technology Act, 2000",
    short_name="IT Act",
    year=2000,
    status="active",
    description="Governs electronic transactions, digital signatures, and cyber crimes in India.",
    version="1.0",
)

SECTIONS: list[LegalSection] = [
    LegalSection(
        section_id="it_2",
        source_id="it_act_2000",
        section_number="2",
        title="Definitions",
        content="""(1) "Access" with its grammatical variations and cognate expressions means gaining entry
to, instructing or communicating with the logical, arithmetical or memory function
resources of a computer, computer system or computer network.
(10) "Computer network" means the interconnection of one or more computers through—
(i) the use of satellite, microwave, terrestrial line or other communication media; and
(ii) terminals or a complex consisting of two or more interconnected computers.
(18) "Data" means a representation of information, knowledge, facts, concepts or
instructions which are being prepared or have been prepared in a formalised manner,
and is intended to be processed, is being processed or has been processed in a
computer system or computer network.""",
        is_definitions=True,
    ),
    LegalSection(
        section_id="it_4",
        source_id="it_act_2000",
        section_number="4",
        title="Legal recognition of electronic records",
        content="""Where any law provides that information or any other matter shall be in writing or in the
typewritten or printed form, then, notwithstanding anything contained in such law, such
requirement shall be deemed to have been satisfied if such information or matter is—
(a) rendered or made available in an electronic form; and
(b) accessible so as to be usable for a subsequent reference.""",
    ),
    LegalSection(
        section_id="it_5",
        source_id="it_act_2000",
        section_number="5",
        title="Legal recognition of electronic signatures",
        content="""Where any law provides that information or any other matter shall be authenticated by
affixing the signature or any document shall be signed or bear the signature of any
person—
(a) the requirement shall be deemed to have been satisfied, if the information or
matter is authenticated by means of electronic signature; and
(b) references to any writing, signed or signature shall be construed as references to
electronic signature.""",
    ),
    LegalSection(
        section_id="it_43",
        source_id="it_act_2000",
        section_number="43",
        title="Penalty for damage to computer system",
        content="""Without prejudice to the provisions contained in any other law for the time being in force,
if any person accesses or secures access to a computer, computer system or computer network
or causes damage to, or downloads, copies or extracts any data from, any computer, computer
system or computer network, he shall be liable to pay damages by way of compensation to
the affected party not exceeding five crore rupees.""",
    ),
    LegalSection(
        section_id="it_65",
        source_id="it_act_2000",
        section_number="65",
        title="Tampering with computer source documents",
        content="""Whoever, knowingly or intentionally conceals, destroys or alters or intentionally or knowingly
causes another to conceal, destroy or alter any computer source code used for a computer
resource with an intention to cause damage, shall be punishable with imprisonment up to
three years, or with fine up to two lakh rupees, or with both.""",
    ),
    LegalSection(
        section_id="it_66",
        source_id="it_act_2000",
        section_number="66",
        title="Computer related offences",
        content="""If any person, dishonestly or fraudulently, does any act referred to in section 43, he shall
be punishable with imprisonment for a term which may extend to three years or with fine
which may extend to five lakh rupees or with both.""",
    ),
    LegalSection(
        section_id="it_72",
        source_id="it_act_2000",
        section_number="72",
        title="Breach of confidentiality and privacy",
        content="""Save as otherwise provided in this Act or any other law for the time being in force,
if any person who, in pursuance of any of the powers conferred under this Act,
has secured access to any electronic record, book, register, correspondence,
information, document or other material discloses, without the consent of the person
concerned, any electronic record, book, register, correspondence, information,
document or other material to any other person, he shall be punished with imprisonment
for a term which may extend to two years, or with fine which may extend to one lakh
rupees, or with both.""",
    ),
    LegalSection(
        section_id="it_85",
        source_id="it_act_2000",
        section_number="85",
        title="Offences by companies",
        content="""(1) Where a person committing a contravention of any of the provisions of this Act
is a company, every person who, at the time the contravention was committed,
was in charge of, and was responsible to the company for the conduct of the
business of the company, as well as the company, shall be deemed to be guilty
of the contravention and shall be liable to be proceeded against and punished
accordingly.""",
    ),
]
