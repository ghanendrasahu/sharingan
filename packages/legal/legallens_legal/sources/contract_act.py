"""Indian Contract Act, 1872 - Key provisions."""

from __future__ import annotations

from legallens_legal.models import LegalSection, LegalSource

SOURCE = LegalSource(
    source_id="indian_contract_act_1872",
    name="Indian Contract Act, 1872",
    short_name="Contract Act",
    year=1872,
    status="active",
    description="Governs contracts in India. Covers formation, performance, and breach of contracts.",
    version="1.0",
)

SECTIONS: list[LegalSection] = [
    LegalSection(
        section_id="ica_2",
        source_id="indian_contract_act_1872",
        section_number="2",
        title="Definitions",
        content="""When one person signifies to another his willingness to do or to abstain from doing anything,
with a view to obtaining the assent of that other to such act or abstinence, he is said to make a proposal.""",
        is_definitions=True,
    ),
    LegalSection(
        section_id="ica_10",
        source_id="indian_contract_act_1872",
        section_number="10",
        title="What agreements are contracts",
        content="""All agreements are contracts if they are made by the free consent of parties competent to contract,
for a lawful consideration and with a lawful object, and are not hereby declared to be void.""",
    ),
    LegalSection(
        section_id="ica_23",
        source_id="indian_contract_act_1872",
        section_number="23",
        title="Consideration and object lawful",
        content="""The consideration or object of an agreement is lawful, unless it is forbidden by law,
or is of such a nature that, if permitted, it would defeat the purpose for which it was established,
or the court regards it as immoral, or opposed to public policy.""",
    ),
    LegalSection(
        section_id="ica_27",
        source_id="indian_contract_act_1872",
        section_number="27",
        title="Agreement in restraint of trade void",
        content="""Every agreement by which any one is restrained from exercising a lawful profession, trade or business
of any kind, is to that extent void.

Exception 1: A seller of goodwill of a business may agree with the buyer to refrain from
carrying on a similar business within specified local limits, so long as the buyer or any
person deriving title to the goodwill from him carries on a like business therein,
provided that such limits are reasonable.

Exception 2: Partners may agree that during the term of the partnership, or after its
dissolution, they will not carry on any business similar to that of the partnership
within specified limits, provided the agreement is reasonable.""",
    ),
    LegalSection(
        section_id="ica_73",
        source_id="indian_contract_act_1872",
        section_number="73",
        title="Compensation for loss or damage caused by breach of contract",
        content="""When a contract has been broken, the party who suffers by such breach is entitled to receive,
from the party who has broken the contract, compensation for any loss or damage caused to him
thereby, which naturally arose in the usual course of things from such breach, or which the
parties knew, when they made the contract, to be likely to result from the breach of it.""",
    ),
    LegalSection(
        section_id="ica_74",
        source_id="indian_contract_act_1872",
        section_number="74",
        title="Damages for breach where penalty is stipulated",
        content="""When a contract has been broken, if a sum is named in the contract as the amount to be paid
in case of such breach, the party complaining of the breach shall receive from the party who
has broken the contract reasonable compensation, not exceeding the amount so named.""",
    ),
    LegalSection(
        section_id="ica_106",
        source_id="indian_contract_act_1872",
        section_number="106",
        title="Determination of leases",
        content="""A lease of immovable property is deemed to be a lease from month to month where the
lease is voidable at the option of the lessor, and the lessor knows of the fact which
renders the lease voidable.""",
    ),
    LegalSection(
        section_id="ica_230",
        source_id="indian_contract_act_1872",
        section_number="230",
        title="Agent's personal liability on contracts",
        content="""In the absence of any contract to that effect, an agent cannot personally enforce contracts
entered into by him on behalf of his principal, nor is he personally bound by them.""",
    ),
]
