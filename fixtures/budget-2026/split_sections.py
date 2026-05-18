"""Split budget_speech.txt into named sections and write an index.

Idempotent: rerunning overwrites cleanly. Hand-curated section boundaries
(line ranges) and summaries live in the SECTIONS table below. The Budget
speech's structure is real but does not match clean section IDs verbatim,
so heuristic regex was rejected in favour of an auditable static map.

Run from the repo root:
    python fixtures/budget-2026/split_sections.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

SPEECH = Path("fixtures/budget-2026/budget_speech.txt")
OUT_DIR = Path("fixtures/budget-2026/sections")
INDEX = OUT_DIR / "index.json"

# (id, title, summary, start_line, end_line). Lines are 1-indexed inclusive.
SECTIONS: list[tuple[str, str, str, int, int]] = [
    (
        "intro.budget_overview",
        "Budget overview and the three kartavyas",
        "Speech opener, macro framing, and the three-kartavya structure (growth, aspirations, inclusion) that organises the rest of Part A.",
        1,
        56,
    ),
    (
        "manufacturing.strategic_sectors",
        "Scaling up manufacturing in 7 strategic sectors",
        "Biopharma SHAKTI, ISM 2.0, Electronics Components, Rare Earth Corridors, Chemical Parks, and Capital Goods schemes with specific outlays.",
        57,
        77,
    ),
    (
        "manufacturing.textile_integrated_programme",
        "Textile, sports goods, and village industries",
        "Integrated Textile Programme with five sub-parts, Mega Textile Parks, Mahatma Gandhi Gram Swaraj, and a sports goods manufacturing initiative.",
        78,
        100,
    ),
    (
        "industry.legacy_clusters_and_msmes",
        "Legacy industrial clusters and Champion MSMEs",
        "Revival of 200 legacy industrial clusters and a three-pronged Champion MSMEs approach: equity (SME Growth Fund), liquidity (TReDS), and professional support.",
        101,
        120,
    ),
    (
        "infrastructure.capex_freight_aviation_energy_cities",
        "Infrastructure, energy, and city economic regions",
        "Public capex trajectory, Infrastructure Risk Guarantee Fund, REITs, freight corridors, seaplanes, ₹20,000 crore CCUS outlay, City Economic Regions framework, and seven High-Speed Rail corridors.",
        121,
        147,
    ),
    (
        "finance.banking_bonds_ease_and_ai",
        "Financial sector, capital markets, and AI",
        "High Level Committee on Banking, NBFC restructuring, FEMA review, corporate and municipal bond reforms, PROI investment limits, ease of doing business, and emerging technologies.",
        148,
        174,
    ),
    (
        "welfare.education_to_employment_and_health",
        "Education-to-employment, health, and AYUSH",
        "High-Powered E3 Standing Committee, Allied Health Professionals expansion, Care Ecosystem, medical value tourism hubs, and three new All India Institutes of Ayurveda.",
        175,
        208,
    ),
    (
        "welfare.livestock_avgc_design_and_telescopes",
        "Livestock, orange economy, design, and university townships",
        "Veterinary college subsidy scheme, AVGC Content Creator Labs, new National Institute of Design, five University Townships, girls' hostels, and four telescope facilities.",
        209,
        228,
    ),
    (
        "welfare.tourism_heritage_and_sports",
        "Tourism, heritage, and sports",
        "National Institute of Hospitality, guide upskilling, National Destination Digital Knowledge Grid, mountain and turtle trails, Global Big Cat Summit, 15 archaeological sites, and the Khelo India sports mission pathway.",
        229,
        254,
    ),
    (
        "agriculture.farmer_welfare_and_high_value_crops",
        "Agriculture: fisheries, animal husbandry, high-value crops",
        "Third kartavya opening, fisheries development of 500 reservoirs, animal husbandry credit-linked subsidy, high-value crops including coconut, cashew, cocoa, sandalwood, and Bharat-VISTAAR AI advisory.",
        255,
        284,
    ),
    (
        "welfare.women_divyangjan_mental_health_regional",
        "Women's livelihoods, Divyangjan, mental health, and regional development",
        "Lakhpati Didi follow-on (SHE-Marts), Divyangjan Kaushal and Sahara Yojanas, NIMHANS-2 and Trauma Care Centres, and Purvodaya states with East Coast Industrial Corridor plus North-East Buddhist sites.",
        285,
        309,
    ),
    (
        "fiscal.finance_commission_and_consolidation",
        "16th Finance Commission and fiscal consolidation",
        "Acceptance of the 16th Finance Commission's 41% vertical devolution recommendation, debt-to-GDP trajectory toward 50%, fiscal deficit at 4.3% of GDP in BE 2026-27, and Revised and Budget Estimates.",
        310,
        336,
    ),
    (
        "taxes.direct_new_income_tax_act_and_ease",
        "Direct Taxes: new Income Tax Act, ease of living, penalty rationalization",
        "Introduction of the Income Tax Act, 2025 effective 1 April 2026, Direct Tax ease-of-living measures, and rationalisation of penalty and prosecution provisions.",
        337,
        409,
    ),
    (
        "taxes.direct_cooperatives_global_business_admin",
        "Direct Taxes: cooperatives, global business, tax administration",
        "Cooperative sector tax relief, measures to attract global business and investment, tax administration reforms, and other direct tax proposals.",
        410,
        471,
    ),
    (
        "taxes.indirect_overview_exemptions_exports",
        "Indirect Taxes: review of exemptions and export promotion",
        "Indirect tax framing, review of exemptions and tariff simplification, and promotion of exports of marine, leather, and textile products.",
        472,
        490,
    ),
    (
        "taxes.indirect_energy_minerals_aviation_electronics",
        "Indirect Taxes: energy, critical minerals, aviation, electronics",
        "Customs duty changes covering energy transition, nuclear power, critical minerals, biogas-blended CNG, civil and defence aviation, and electronics.",
        491,
        523,
    ),
    (
        "taxes.indirect_sez_ease_customs_exports",
        "Indirect Taxes: SEZs, customs process, ease of living",
        "Special Economic Zone provisions, ease-of-living and ease-of-doing-business changes in customs, trust-based systems, new export opportunities, and customs process simplification.",
        524,
        585,
    ),
    (
        "annexure.e3_committee_terms_of_reference",
        "Annexure to Part A: E3 Standing Committee Terms of Reference",
        "Indicative Terms of Reference for the High-Level Education-to-Employment-and-Enterprise Standing Committee announced in Part A.",
        586,
        607,
    ),
    (
        "annexure.direct_tax_amendments",
        "Annexure to Part B: Direct Tax amendments",
        "Detailed clause-by-clause amendments relating to direct taxes, including rates, exemptions, and procedural changes.",
        608,
        925,
    ),
    (
        "annexure.indirect_tax_amendments",
        "Annexure to Part B: Indirect Tax amendments",
        "Detailed amendments relating to indirect taxes, including customs duty changes, tariff schedules, and NCCD revisions.",
        926,
        1434,
    ),
]


def slice_lines(all_lines: list[str], start: int, end: int) -> str:
    """Return lines[start-1:end] joined back together, preserving newlines."""
    return "".join(all_lines[start - 1 : end])


def main() -> None:
    if not SPEECH.exists():
        raise SystemExit(f"speech file not found: {SPEECH}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_lines = SPEECH.read_text().splitlines(keepends=True)
    index: list[dict] = []

    for sid, title, summary, start, end in SECTIONS:
        text = slice_lines(all_lines, start, end).strip() + "\n"
        filename = f"{sid}.txt"
        (OUT_DIR / filename).write_text(text)
        index.append(
            {
                "id": sid,
                "title": title,
                "summary": summary,
                "filename": filename,
                "char_count": len(text),
            }
        )

    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")

    total_chars = sum(s["char_count"] for s in index)
    print(f"Wrote {len(index)} sections to {OUT_DIR} ({total_chars:,} chars total)")
    print(f"Index at {INDEX}")
    too_small = [s for s in index if s["char_count"] < 2000]
    too_big = [s for s in index if s["char_count"] > 12000]
    if too_small:
        print(f"\nSmall sections (under ~500 tokens):")
        for s in too_small:
            print(f"  {s['id']}: {s['char_count']} chars")
    if too_big:
        print(f"\nLarge sections (over ~3000 tokens):")
        for s in too_big:
            print(f"  {s['id']}: {s['char_count']} chars")


if __name__ == "__main__":
    main()
