import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import newsletter_html as nh

TEMPLATE = ROOT / "scripts" / "templates" / "newsletter_map.json"

# ── Task 1: 템플릿 / href 조립 ──────────────────────────────────────────


def test_template_has_18_areas():
    cfg = nh.load_config(TEMPLATE)
    assert len(cfg["areas"]) == 18
    kinds = {a["kind"] for a in cfg["areas"]}
    assert kinds == {"fixed", "pdf"}
    assert sum(1 for a in cfg["areas"] if a["kind"] == "pdf") == 8


def test_area_href_fixed():
    area = {"kind": "fixed", "href": "https://example.com/x"}
    assert nh.area_href(area, "https://cc.com/a.pdf") == "https://example.com/x"


def test_area_href_pdf_page1_no_fragment():
    area = {"kind": "pdf", "page": 1}
    assert nh.area_href(area, "https://cc.com/a.pdf") == "https://cc.com/a.pdf"


def test_area_href_pdf_page_n():
    area = {"kind": "pdf", "page": 4}
    assert nh.area_href(area, "https://cc.com/a.pdf") == "https://cc.com/a.pdf#page=4"


# ── Task 2: build — 13호 골든 테스트 ────────────────────────────────────

GOLDEN_IMAGE = "https://www.kita.net/mailclub/NeDM/edm_20260702.jpg"
GOLDEN_PDF = "https://files.constantcontact.com/33c5970e901/13d04a80-fd58-4481-aab7-2bf6f2b9d8b2.pdf"
GOLDEN_AREAS = [
    ("392,273,482,300", "https://lp.constantcontactpages.com/sl/SIIBJQl"),
    ("486,274,612,299", "https://overseas.kita.net/dal/marketReport/marketReportList.do"),
    ("554,1056,660,1088", GOLDEN_PDF),
    ("503,1517,644,1551", GOLDEN_PDF + "#page=2"),
    ("501,1871,645,1909", GOLDEN_PDF + "#page=2"),
    ("472,2208,644,2244", GOLDEN_PDF + "#page=3"),
    ("553,2949,663,2983", GOLDEN_PDF + "#page=4"),
    ("55,3388,163,3419", GOLDEN_PDF + "#page=5"),
    ("472,3580,638,3610", GOLDEN_PDF + "#page=7"),
    ("535,4275,640,4306", GOLDEN_PDF + "#page=8"),
    ("357,4765,646,4917", "https://kita.net/gsos/application/applicationList.do"),
    ("72,4766,323,4917", "https://www.instagram.com/kita_dallas_center/"),
    ("390,5129,619,5284", "https://kita.net/board/commerceNews/commerceNewsList.do"),
    ("83,5130,316,5284", "https://kita.net/board/goodMorningKita/goodMorningKitaList.do"),
    ("556,5395,661,5425", "https://kita.net/asocBiz/asocBiz/asocBizOngoingList.do"),
    ("593,5756,630,5793", "https://www.youtube.com/@KITA_Dallas_Center "),
    ("550,5756,587,5793", "https://www.linkedin.com/company/kita-dallas-center"),
    ("507,5757,543,5792", "https://www.instagram.com/kita_dallas_center/"),
]


def _golden_config():
    cfg = nh.load_config(TEMPLATE)
    return {"image_url": GOLDEN_IMAGE, "pdf_url": GOLDEN_PDF, "areas": cfg["areas"]}


def test_build_html_matches_issue13():
    html = nh.build_html(_golden_config())
    assert f'<img src="{GOLDEN_IMAGE}"' in html
    areas = re.findall(r'coords="([^"]+)" href="([^"]+)"', html)
    assert areas == GOLDEN_AREAS


def test_build_html_euckr_encodable():
    html = nh.build_html(_golden_config())
    html.encode("euc-kr")  # 예외 없이 인코딩 가능해야 함


def test_write_euckr(tmp_path):
    out = tmp_path / "out.html"
    nh.write_euckr(out, nh.build_html(_golden_config()))
    raw = out.read_bytes()
    assert b"charset=euc-kr" in raw


# ── Task 3: render — PDF 스티칭 ─────────────────────────────────────────


@pytest.fixture
def tiny_pdf(tmp_path):
    import fitz

    p = tmp_path / "cover.pdf"
    doc = fitz.open()
    for _ in range(3):
        page = doc.new_page(width=1048, height=1757)
        page.draw_rect(fitz.Rect(500, 900, 660, 960), color=(0, 0, 1), fill=(0, 0, 1))
    doc.save(str(p))
    doc.close()
    return p


def test_render_pdf_stitches_vertically(tiny_pdf, tmp_path):
    out = tmp_path / "stitched.jpg"
    info = nh.render_pdf(str(tiny_pdf), 700, str(out))
    assert out.exists()
    assert info["pages"] == 3
    assert info["width"] == 700
    per_page = round(700 * 1757 / 1048)
    assert abs(info["height"] - per_page * 3) <= 3
    assert info["page_offsets"][0] == 0
    from PIL import Image

    with Image.open(out) as im:
        assert im.size == (info["width"], info["height"])


# ── Task 4: preview + CLI ──────────────────────────────────────────────


def test_build_preview_overlays_all_areas():
    cfg = _golden_config()
    html = nh.build_preview(cfg, "stitched.jpg")
    assert html.count("position:absolute") == 18
    assert 'src="stitched.jpg"' in html


def test_build_preview_warn_area_is_red():
    cfg = _golden_config()
    cfg["areas"] = [dict(a) for a in cfg["areas"]]
    cfg["areas"][2]["warn"] = True
    html = nh.build_preview(cfg, "s.jpg")
    assert "#d00" in html


def test_cli_build(tmp_path):
    cfg_path = tmp_path / "issue.json"
    cfg_path.write_text(json.dumps(_golden_config(), ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out.html"
    nh.main(["build", "--config", str(cfg_path), "--out", str(out)])
    assert b"usemap" in out.read_bytes()
