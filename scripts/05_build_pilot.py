#!/usr/bin/env python3
"""Build the reviewed, deduplicated 2017 pilot dataset."""

from __future__ import annotations

import csv
from pathlib import Path


CANDIDATES = Path("data/interim/candidates.csv")
REVIEW = Path("data/interim/review.csv")
OUTPUT = Path("data/final/tsiav_pilot_2017.csv")


AGREEMENTS = [
    {
        "id": "TR-MNE-2014-01",
        "partner": "Montenegro (MNE)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Karadağ Hükümeti Arasında Askeri Eğitim İş Birliği Anlaşması",
        "type": "training",
        "date_signed": "2014-10-16",
        "date_approved": "2016-12-27",
        "law_no": "",
        "decision_no": "2016/9695",
    },
    {
        "id": "TR-KOR-2016-01",
        "partner": "South Korea (KOR)",
        "title_tr": "Türkiye Cumhuriyeti Hava Kuvvetleri ile Kore Cumhuriyeti Hava Kuvvetleri Arasında Hava Kuvvetleri Uçakları İçin Karşılıklı Lojistik Destek İş Birliği Sistemine İlişkin Mutabakat Muhtırası",
        "type": "other_military",
        "date_signed": "2016-08-02",
        "date_approved": "2017-01-23",
        "law_no": "",
        "decision_no": "2017/9806",
    },
    {
        "id": "TR-BEN-2014-01",
        "partner": "Benin (BEN)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Benin Cumhuriyeti Hükümeti Arasında Savunma Sanayi İşbirliği Anlaşması",
        "type": "defence_industry",
        "date_signed": "2014-09-15",
        "date_approved": "2017-05-01",
        "law_no": "6780",
        "decision_no": "2017/10178",
    },
    {
        "id": "TR-KWT-2013-01",
        "partner": "Kuwait (KWT)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Kuveyt Devleti Hükümeti Arasında Savunma Sanayi İşbirliği Mutabakat Muhtırası",
        "type": "defence_industry",
        "date_signed": "2013-04-29",
        "date_approved": "2017-05-29",
        "law_no": "6781",
        "decision_no": "2017/10372",
    },
    {
        "id": "TR-GBR-2011-01",
        "partner": "United Kingdom (GBR)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Büyük Britanya ve Kuzey İrlanda Birleşik Krallık Hükümeti Arasında Savunma Sanayi Alanında İşbirliği Mutabakat Muhtırası",
        "type": "defence_industry",
        "date_signed": "2011-11-23",
        "date_approved": "2017-05-01",
        "law_no": "6785",
        "decision_no": "2017/10207",
    },
    {
        "id": "TR-IDN-2010-01",
        "partner": "Indonesia (IDN)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Endonezya Cumhuriyeti Hükümeti Arasında Savunma Sanayi İş Birliği Anlaşması",
        "type": "defence_industry",
        "date_signed": "2010-06-29",
        "date_approved": "2017-05-01",
        "law_no": "6790",
        "decision_no": "2017/10284",
    },
    {
        "id": "TR-NER-2013-01",
        "partner": "Niger (NER)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Nijer Cumhuriyeti Hükümeti Arasında Askeri Alanda Eğitim, Teknik ve Bilimsel İş Birliği Çerçeve Anlaşması",
        "type": "training",
        "date_signed": "2013-07-10",
        "date_approved": "2017-05-01",
        "law_no": "6846",
        "decision_no": "2017/10184",
        "notes": "Signed on different dates: Ankara 2013-05-30 and Niamey 2013-07-10. Actual entry-into-force date is not stated.",
    },
    {
        "id": "TR-SEN-2012-01",
        "partner": "Senegal (SEN)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Senegal Cumhuriyeti Hükümeti Arasında Savunma Sanayi İş Birliği Anlaşması",
        "type": "defence_industry",
        "date_signed": "2012-12-20",
        "date_approved": "2017-05-01",
        "law_no": "6847",
        "decision_no": "2017/10273",
    },
    {
        "id": "TR-COG-2012-01",
        "partner": "Republic of the Congo (COG)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Kongo Cumhuriyeti Hükümeti Arasında Savunma Sanayisi İş Birliği Anlaşması",
        "type": "defence_industry",
        "date_signed": "2012-11-15",
        "date_approved": "2017-05-01",
        "law_no": "6848",
        "decision_no": "2017/10204",
    },
    {
        "id": "TR-NGA-2011-01",
        "partner": "Nigeria (NGA)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Nijerya Federal Cumhuriyeti Hükümeti Arasında Askeri İş Birliği Hususunda İkili Anlaşma",
        "type": "framework",
        "date_signed": "2011-02-02",
        "date_approved": "2017-05-01",
        "law_no": "6849",
        "decision_no": "2017/10156",
    },
    {
        "id": "TR-GMB-2014-01",
        "partner": "Gambia (GMB)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Gambiya Cumhuriyeti Hükümeti Arasında Savunma Alanında Sanayi ve Teknik İş Birliği Anlaşması",
        "type": "defence_industry",
        "date_signed": "2014-02-11",
        "date_approved": "2017-05-01",
        "law_no": "6850",
        "decision_no": "2017/10271",
    },
    {
        "id": "TR-MLI-2015-01",
        "partner": "Mali (MLI)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Mali Cumhuriyeti Hükümeti Arasında Savunma Sanayi İş Birliği Anlaşması",
        "type": "defence_industry",
        "date_signed": "2015-02-03",
        "date_approved": "2017-05-01",
        "law_no": "6852",
        "decision_no": "2017/10277",
    },
    {
        "id": "TR-DJI-2015-01",
        "partner": "Djibouti (DJI)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Cibuti Cumhuriyeti Hükümeti Arasında Askeri Alanda Eğitim, Teknik ve Bilimsel İş Birliği Anlaşması",
        "type": "training",
        "date_signed": "2015-01-24",
        "date_approved": "2017-05-29",
        "law_no": "6854",
        "decision_no": "2017/10373",
    },
    {
        "id": "TR-TCD-2014-01",
        "partner": "Chad (TCD)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Çad Cumhuriyeti Hükümeti Arasında Savunma Sanayi İş Birliği Anlaşması",
        "type": "defence_industry",
        "date_signed": "2014-12-16",
        "date_approved": "2017-05-29",
        "law_no": "6855",
        "decision_no": "2017/10425",
    },
    {
        "id": "TR-CIV-2015-01",
        "partner": "Cote d'Ivoire (CIV)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Fildişi Sahili Cumhuriyeti Hükümeti Arasında Askerî Alanda Eğitim, Teknik ve Bilimsel İş Birliği Çerçeve Anlaşması",
        "type": "training",
        "date_signed": "2015-03-26",
        "date_approved": "2017-05-01",
        "law_no": "6933",
        "decision_no": "2017/10197",
    },
    {
        "id": "TR-ARE-2011-01",
        "partner": "United Arab Emirates (ARE)",
        "title_tr": "Türkiye Cumhuriyeti Milli Savunma Bakanlığı ile Birleşik Arap Emirlikleri Silahlı Kuvvetleri Genel Karargahı Arasında Savunma Sanayi İş Birliği Mutabakat Muhtırası",
        "type": "defence_industry",
        "date_signed": "2011-10-06",
        "date_approved": "2017-05-01",
        "law_no": "6992",
        "decision_no": "2017/10144",
    },
    {
        "id": "TR-MLI-2010-01",
        "partner": "Mali (MLI)",
        "title_tr": "Türkiye Cumhuriyeti Genelkurmay Başkanlığı ile Mali Cumhuriyeti Savunma ve Mücahitler Bakanlığı Arasında Askeri Eğitim İş Birliği Anlaşmasına Dair 1 Numaralı Değişiklik Protokolü",
        "type": "protocol_amendment",
        "date_signed": "2010-06-09",
        "date_approved": "2017-05-01",
        "law_no": "6987",
        "decision_no": "2017/10282",
    },
    {
        "id": "TR-LBY-2017-01",
        "partner": "Libya (LBY)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Libya Başkanlık Konseyi Arasında Askerî Alanda Lojistik Hibe Anlaşması",
        "type": "other_military",
        "date_signed": "2017-02-08",
        "date_approved": "2017-03-03",
        "law_no": "",
        "decision_no": "2017/10060",
    },
    {
        "id": "TR-AZE-2017-01",
        "partner": "Azerbaijan (AZE)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Azerbaycan Cumhuriyeti Hükümeti Arasında SAT/SAS/BSD (Sualtı Taarruz/Sualtı Savunma/Birinci Sınıf Dalgıç) Müşterek Tatbikatı Süresince Ev Sahibi Ülke Desteğinin Koşullarına İlişkin Mutabakat Muhtırası",
        "type": "other_military",
        "date_signed": "2017-05-05",
        "date_approved": "2017-09-11",
        "law_no": "",
        "decision_no": "2017/10835",
    },
    {
        "id": "TR-ESP-2014-01",
        "partner": "Spain (ESP)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile İspanya Krallığı Arasında Savunma Sanayi Konusunda Gizlilik Dereceli Bilginin Korunması Hakkında Anlaşma",
        "type": "defence_industry",
        "date_signed": "2014-06-25",
        "date_approved": "2017-10-12",
        "law_no": "7037",
        "decision_no": "",
        "notes": "Only the approval law was published in the 2017 pilot period. Actual entry-into-force date is not stated.",
    },
    {
        "id": "TR-ESP-2016-01",
        "partner": "Spain (ESP)",
        "title_tr": "Türkiye Cumhuriyeti Genelkurmay Başkanlığı Adına Türk Deniz Kuvvetleri Komutanlığı ile İspanya Krallığı Savunma Bakanlığı Adına İspanya Deniz Kuvvetleri Komutanlığı Arasında Çok Maksatlı Amfibi Hücum Gemisi (LHD) Projesi İş Birliği Faaliyetlerine İlişkin Mutabakat Muhtırası",
        "type": "defence_industry",
        "date_signed": "2016-02-26",
        "date_approved": "2017-10-12",
        "law_no": "7038",
        "decision_no": "",
        "notes": "Only the approval law was published in the 2017 pilot period. Actual entry-into-force date is not stated.",
    },
    {
        "id": "TR-BHR-2017-01",
        "partner": "Bahrain (BHR)",
        "title_tr": "Türkiye Cumhuriyeti Hükümeti ile Bahreyn Krallığı Hükümeti Arasında Savunma Sanayi İşbirliği Mutabakat Muhtırası",
        "type": "defence_industry",
        "date_signed": "2017-02-12",
        "date_approved": "2017-09-22",
        "law_no": "",
        "decision_no": "2017/10848",
    },
]


def find_publication(rows: list[dict[str, str]], number: str) -> dict[str, str] | None:
    if not number:
        return None
    prefix = number + " "
    matches = [row for row in rows if row["title_tr"].startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one publication for {number}, found {len(matches)}")
    return matches[0]


def exclusion_reason(title: str) -> str:
    folded = title.casefold()
    if any(word in folded for word in ("atama", "vekâlet", "atanmalarına")):
        return "Domestic personnel appointment or acting-minister notice; not a bilateral agreement."
    if "lojistik merkez" in folded:
        return "Domestic transport and expropriation decision; not a defence agreement."
    if "yurt dışına gönderilmesi" in folded or "harekâtına iştirak" in folded:
        return "Parliamentary overseas-deployment mandate; not a bilateral agreement."
    return "Domestic regulation or administrative measure; not a bilateral agreement."


def main() -> None:
    with CANDIDATES.open(encoding="utf-8-sig", newline="") as handle:
        candidates = list(csv.DictReader(handle))

    publication_to_id: dict[str, str] = {}
    output_rows = []
    for agreement in AGREEMENTS:
        law = find_publication(candidates, agreement["law_no"])
        decision = find_publication(candidates, agreement["decision_no"])
        publications = [item for item in (law, decision) if item]
        for publication in publications:
            publication_to_id[publication["source_url"]] = agreement["id"]

        channel = "both" if law and decision else "law" if law else "decision"
        notes = agreement.get(
            "notes",
            "Actual entry-into-force date is not stated in the publication.",
        )
        output_rows.append(
            {
                "id": agreement["id"],
                "partner": agreement["partner"],
                "title_tr": agreement["title_tr"],
                "type": agreement["type"],
                "is_framework": "true" if "çerçeve" in agreement["title_tr"].casefold() else "false",
                "date_signed": agreement["date_signed"],
                "date_approved": agreement["date_approved"],
                "date_in_force": "",
                "channel": channel,
                "law_no": agreement["law_no"],
                "decision_no": agreement["decision_no"],
                "rg_date": "; ".join(item["rg_date"] for item in publications),
                "rg_issue": "; ".join(item["rg_issue"] for item in publications),
                "source_url": "; ".join(item["source_url"] for item in publications),
                "notes": notes,
                "status": "included",
            }
        )

    review_rows = []
    for candidate in candidates:
        agreement_id = publication_to_id.get(candidate["source_url"], "")
        included = bool(agreement_id)
        review_rows.append(
            {
                **candidate,
                "agreement_id": agreement_id,
                "status": "included" if included else "excluded",
                "review_reason": (
                    "Bilateral defence cooperation agreement publication."
                    if included
                    else exclusion_reason(candidate["title_tr"])
                ),
            }
        )

    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0]))
        writer.writeheader()
        writer.writerows(review_rows)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "partner",
        "title_tr",
        "type",
        "is_framework",
        "date_signed",
        "date_approved",
        "date_in_force",
        "channel",
        "law_no",
        "decision_no",
        "rg_date",
        "rg_issue",
        "source_url",
        "notes",
        "status",
    ]
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(review_rows)} reviewed candidates to {REVIEW}")
    print(f"Wrote {len(output_rows)} agreements to {OUTPUT}")


if __name__ == "__main__":
    main()
