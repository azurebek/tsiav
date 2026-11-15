from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "11_build_provisional_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_dataset", MODULE_PATH)
assert SPEC and SPEC.loader
build_dataset = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_dataset)


class PipelineRuleTests(unittest.TestCase):
    def test_clean_title_removes_approval_wrapper(self) -> None:
        title = (
            "2012/3849 Türkiye Cumhuriyeti Hükümeti ile Katar Devleti Hükümeti "
            "Arasında Askeri Eğitim İş Birliği Anlaşmasının Onaylanması Hakkında Karar"
        )
        self.assertEqual(
            build_dataset.clean_title(title),
            "Türkiye Cumhuriyeti Hükümeti ile Katar Devleti Hükümeti Arasında "
            "Askeri Eğitim İş Birliği Anlaşması",
        )

    def test_actor_family_detection(self) -> None:
        self.assertEqual(
            build_dataset.infer_actor_type("Türkiye Cumhuriyeti Sahil Güvenlik Komutanlığı"),
            "coast_guard",
        )
        self.assertEqual(build_dataset.infer_actor_type("Jandarma Genel Komutanlığı"), "gendarmerie")

    def test_framework_is_independent_of_primary_type(self) -> None:
        title = "Askerî Eğitim, Teknik ve Bilimsel İş Birliği Çerçeve Anlaşması"
        self.assertIn("cerceve", build_dataset.fold_for_match(title))

    def test_partner_recognition_codes(self) -> None:
        self.assertEqual(build_dataset.infer_partner_recognition("Kosovo (XKX)"), "limited")
        self.assertEqual(build_dataset.infer_partner_recognition("Jordan (JOR)"), "un_member")

    def test_instrument_level_uses_named_parties(self) -> None:
        self.assertEqual(
            build_dataset.infer_instrument_level(
                "Türkiye Cumhuriyeti Hükûmeti ile Oman Sultanlığı Hükûmeti Arasında Mutabakat Muhtırası"
            ),
            "intergovernmental",
        )
        self.assertEqual(
            build_dataset.infer_instrument_level(
                "Türkiye Cumhuriyeti Genelkurmay Başkanlığı ile Romanya Ulusal Savunma Bakanlığı Arasında Protokol"
            ),
            "inter-agency",
        )


if __name__ == "__main__":
    unittest.main()
