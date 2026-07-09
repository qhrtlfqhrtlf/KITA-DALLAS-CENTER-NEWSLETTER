# Trade Newsline 발송용 HTML 자동 생성 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 커버 PDF + 호별 값(발행일, CC PDF URL, 페이지 매핑)만으로 발송용 이미지맵 HTML을 생성하는 `/html변환` 스킬과 Python 헬퍼 구축.

**Architecture:** 결정적(deterministic) 작업은 `scripts/newsletter_html.py`(render/build/preview 서브커맨드)가 담당하고, 지능적 작업(좌표 검증, 페이지 매핑 제안)은 Claude 스킬(`.claude/skills/html변환/SKILL.md`)이 담당한다. 기준 좌표와 고정 링크는 `scripts/templates/newsletter_map.json`에 저장하고 매 호 갱신한다.

**Tech Stack:** Python 3.14 (Windows), PyMuPDF(fitz), Pillow, pytest. 출력 HTML은 euc-kr 인코딩.

## Global Constraints

- 발송 HTML은 13호 형식과 동일한 마크업 구조 + euc-kr 인코딩으로 생성한다.
- 스티칭 이미지 기본 폭 700px (커버 PDF 페이지 1048×1757pt 기준, 실측 후 조정 가능).
- 경로에 한글·공백 포함(예: `001. 뉴스레터`) — 셸 명령에서 항상 따옴표로 감싼다.
- 업무 자료 폴더(001~999)는 git 추적 금지 — 코드/템플릿/스킬/문서만 커밋.
- 작업 브랜치: `feature/newsletter-html-auto`.
- 유튜브 링크의 후행 공백(`...KITA_Dallas_Center `)은 13호 원본 그대로 보존한다 (골든 테스트 일치용).

---

### Task 1: 좌표 템플릿 JSON + 설정 로더 + href 조립

**Files:**
- Create: `scripts/templates/newsletter_map.json`
- Create: `scripts/newsletter_html.py`
- Test: `tests/test_newsletter_html.py`

**Interfaces:**
- Produces: `load_config(path: str|Path) -> dict`, `area_href(area: dict, pdf_url: str) -> str`
- 템플릿 스키마: `{"image_width": int, "image_url_pattern": str, "areas": [{"id","label","kind"("fixed"|"pdf"),"coords"[4],"href"?(fixed),"page"?(pdf)}]}`

- [ ] **Step 1: 템플릿 JSON 작성** — 13호 HTML에서 추출한 18개 영역 (전체 내용은 실행 시 13호 html.html 원본과 대조하여 coords/href를 그대로 옮긴다):

```json
{
  "image_width": 700,
  "image_url_pattern": "https://www.kita.net/mailclub/NeDM/edm_{date}.jpg",
  "areas": [
    {"id": "subscribe",       "label": "구독신청(헤더)",              "kind": "fixed", "coords": [392,273,482,300],    "href": "https://lp.constantcontactpages.com/sl/SIIBJQl"},
    {"id": "back-issues",     "label": "지난 호 다시보기(헤더)",       "kind": "fixed", "coords": [486,274,612,299],    "href": "https://overseas.kita.net/dal/marketReport/marketReportList.do"},
    {"id": "hot-issue",       "label": "경제통상 핫이슈 자세히보기",    "kind": "pdf",   "coords": [554,1056,660,1088],  "page": 1},
    {"id": "econ-news",       "label": "경제뉴스 전체보기",            "kind": "pdf",   "coords": [503,1517,644,1551],  "page": 2},
    {"id": "trade-news",      "label": "통상뉴스 전체보기",            "kind": "pdf",   "coords": [501,1871,645,1909],  "page": 2},
    {"id": "region-news",     "label": "지역·산업뉴스 전체보기",       "kind": "pdf",   "coords": [472,2208,644,2244],  "page": 3},
    {"id": "report",          "label": "보고서 톺아보기 자세히보기",    "kind": "pdf",   "coords": [553,2949,663,2983],  "page": 4},
    {"id": "column",          "label": "전문가 칼럼(좌측 버튼)",       "kind": "pdf",   "coords": [55,3388,163,3419],   "page": 5},
    {"id": "indicators",      "label": "주요 경제지표 자세히보기",      "kind": "pdf",   "coords": [472,3580,638,3610],  "page": 7},
    {"id": "events",          "label": "행사 알리미 자세히보기",        "kind": "pdf",   "coords": [535,4275,640,4306],  "page": 8},
    {"id": "banner-gsos",     "label": "해외지사화사업 배너(우)",       "kind": "fixed", "coords": [357,4765,646,4917],  "href": "https://kita.net/gsos/application/applicationList.do"},
    {"id": "banner-insta",    "label": "인스타그램 배너(좌)",          "kind": "fixed", "coords": [72,4766,323,4917],   "href": "https://www.instagram.com/kita_dallas_center/"},
    {"id": "banner-commerce", "label": "통상뉴스 게시판 배너(우)",      "kind": "fixed", "coords": [390,5129,619,5284],  "href": "https://kita.net/board/commerceNews/commerceNewsList.do"},
    {"id": "banner-gmk",      "label": "굿모닝KITA 배너(좌)",          "kind": "fixed", "coords": [83,5130,316,5284],   "href": "https://kita.net/board/goodMorningKita/goodMorningKitaList.do"},
    {"id": "asoc-biz",        "label": "협회 사업 자세히보기",          "kind": "fixed", "coords": [556,5395,661,5425],  "href": "https://kita.net/asocBiz/asocBiz/asocBizOngoingList.do"},
    {"id": "sns-youtube",     "label": "유튜브 아이콘",               "kind": "fixed", "coords": [593,5756,630,5793],  "href": "https://www.youtube.com/@KITA_Dallas_Center "},
    {"id": "sns-linkedin",    "label": "링크드인 아이콘",              "kind": "fixed", "coords": [550,5756,587,5793],  "href": "https://www.linkedin.com/company/kita-dallas-center"},
    {"id": "sns-instagram",   "label": "인스타그램 아이콘",            "kind": "fixed", "coords": [507,5757,543,5792],  "href": "https://www.instagram.com/kita_dallas_center/"}
  ]
}
```

- [ ] **Step 2: 실패하는 테스트 작성** (`tests/test_newsletter_html.py`):

```python
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import newsletter_html as nh

TEMPLATE = ROOT / "scripts" / "templates" / "newsletter_map.json"


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
```

- [ ] **Step 3: 실패 확인** — `python -m pytest tests/test_newsletter_html.py -v` → FAIL (`newsletter_html` 모듈 없음)

- [ ] **Step 4: 최소 구현** (`scripts/newsletter_html.py`):

```python
"""Trade Newsline 발송용 이미지맵 HTML 생성 도구."""
import json
from pathlib import Path


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def area_href(area, pdf_url):
    if area.get("kind") == "pdf":
        page = area.get("page", 1)
        return pdf_url if page == 1 else f"{pdf_url}#page={page}"
    return area["href"]
```

- [ ] **Step 5: 통과 확인** — `python -m pytest tests/test_newsletter_html.py -v` → 4 PASS
- [ ] **Step 6: 커밋** — `git add scripts/templates/newsletter_map.json scripts/newsletter_html.py tests/test_newsletter_html.py && git commit -m "feat: newsletter 좌표 템플릿과 href 조립 로직"`

---

### Task 2: build — 발송용 euc-kr HTML 생성 (13호 골든 테스트)

**Files:**
- Modify: `scripts/newsletter_html.py`
- Test: `tests/test_newsletter_html.py`

**Interfaces:**
- Consumes: `load_config`, `area_href` (Task 1)
- Produces: `build_html(config: dict) -> str` — config는 `{"image_url": str, "pdf_url": str, "areas": [...]}`; `write_euckr(path, html) -> None`

- [ ] **Step 1: 골든 테스트 작성** — 13호 실제 발송 HTML의 (coords, href) 18쌍을 테스트에 내장:

```python
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
import re

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
```

- [ ] **Step 2: 실패 확인** — FAIL (`build_html` 없음)
- [ ] **Step 3: 구현** — 13호 마크업 구조를 그대로 재현:

```python
def build_html(config):
    lines = [
        '<meta http-equiv="Content-Type" content="text/html; charset=euc-kr">',
        '<body style="margin:0; padding:0; color:333; text-align:center">',
        '<div>',
        '<table align="center" border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto;">',
        '\t<tbody>',
        '    \t<tr>',
        f'        \t<td><img src="{config["image_url"]}" alt="" usemap="#Map" border="0"></td>',
        '        </tr> ',
        '    </tbody>',
        '  </table>',
        '</div>',
        '',
        '',
        '<map name="Map">',
    ]
    for area in config["areas"]:
        coords = ",".join(str(c) for c in area["coords"])
        href = area_href(area, config.get("pdf_url", ""))
        lines.append(f'  <area shape="rect" coords="{coords}" href="{href}" target="_blank">')
    lines += ['</map>', '</body>']
    return "\n".join(lines)


def write_euckr(path, html):
    Path(path).write_bytes(html.encode("euc-kr"))
```

- [ ] **Step 4: 통과 확인** — 전체 테스트 PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat: build_html — 13호 골든 테스트 통과하는 euc-kr HTML 생성"`

---

### Task 3: render — 커버 PDF 스티칭 JPG (+의존성)

**Files:**
- Modify: `scripts/newsletter_html.py`, `scripts/requirements.txt`
- Test: `tests/test_newsletter_html.py`

**Interfaces:**
- Produces: `render_pdf(pdf_path, width, out_path) -> dict` — 반환 `{"width","height","pages","page_offsets"}`

- [ ] **Step 1: requirements.txt에 `pymupdf`, `pillow` 추가 후 `pip install pymupdf pillow`**
- [ ] **Step 2: 실패하는 테스트 작성** (합성 PDF 픽스처):

```python
import pytest

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
```

- [ ] **Step 3: 실패 확인** — FAIL (`render_pdf` 없음)
- [ ] **Step 4: 구현**:

```python
def render_pdf(pdf_path, width, out_path):
    import fitz
    from PIL import Image
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        zoom = width / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        if img.width != width:
            img = img.resize((width, round(img.height * width / img.width)))
        images.append(img)
    doc.close()
    total_h = sum(i.height for i in images)
    sheet = Image.new("RGB", (width, total_h), "white")
    y, offsets = 0, []
    for img in images:
        sheet.paste(img, (0, y))
        offsets.append(y)
        y += img.height
    sheet.save(out_path, "JPEG", quality=90)
    return {"width": width, "height": total_h, "pages": len(images), "page_offsets": offsets}
```

- [ ] **Step 5: 통과 확인 → 커밋** — `git commit -m "feat: render_pdf — 커버 PDF 세로 스티칭 JPG 생성"`

---

### Task 4: preview — 클릭영역 오버레이 검수 HTML + CLI

**Files:**
- Modify: `scripts/newsletter_html.py`
- Test: `tests/test_newsletter_html.py`

**Interfaces:**
- Produces: `build_preview(config, image_src) -> str`; CLI `python scripts/newsletter_html.py {render|build|preview}`

- [ ] **Step 1: 실패하는 테스트 작성**:

```python
def test_build_preview_overlays_all_areas():
    cfg = _golden_config()
    html = nh.build_preview(cfg, "stitched.jpg")
    assert html.count("position:absolute") == 18
    assert 'src="stitched.jpg"' in html

def test_build_preview_warn_area_is_red():
    cfg = _golden_config()
    cfg["areas"][2] = dict(cfg["areas"][2], warn=True)
    html = nh.build_preview(cfg, "s.jpg")
    assert "#d00" in html

def test_cli_build(tmp_path):
    cfg_path = tmp_path / "issue.json"
    cfg_path.write_text(json.dumps(_golden_config(), ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out.html"
    nh.main(["build", "--config", str(cfg_path), "--out", str(out)])
    assert b"usemap" in out.read_bytes()
```

- [ ] **Step 2: 실패 확인** → **Step 3: 구현**:

```python
def build_preview(config, image_src):
    parts = [
        '<!doctype html>',
        '<meta charset="utf-8">',
        '<title>뉴스레터 클릭영역 검수</title>',
        '<body style="margin:0; background:#555">',
        '<div style="position:relative; margin:0 auto; width:fit-content">',
        f'<img src="{image_src}" style="display:block">',
    ]
    for area in config["areas"]:
        x1, y1, x2, y2 = area["coords"]
        href = area_href(area, config.get("pdf_url", ""))
        warn = area.get("warn")
        color = "rgba(255,0,0,.35)" if warn else "rgba(30,120,255,.30)"
        border = "#d00" if warn else "#06c"
        label = area.get("label", area.get("id", ""))
        parts.append(
            f'<a href="{href}" target="_blank" title="{label} → {href}" '
            f'style="position:absolute; left:{x1}px; top:{y1}px; width:{x2-x1}px; height:{y2-y1}px; '
            f'background:{color}; border:2px solid {border}; box-sizing:border-box; '
            f'font:11px sans-serif; color:#fff; overflow:hidden">{label}</a>'
        )
    parts += ['</div>', '</body>']
    return "\n".join(parts)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="newsletter_html")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("render"); p.add_argument("--pdf", required=True); p.add_argument("--width", type=int, default=700); p.add_argument("--out", required=True)
    p = sub.add_parser("build"); p.add_argument("--config", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("preview"); p.add_argument("--config", required=True); p.add_argument("--image", required=True); p.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "render":
        print(json.dumps(render_pdf(args.pdf, args.width, args.out)))
    elif args.cmd == "build":
        write_euckr(args.out, build_html(load_config(args.config)))
        print(f"saved: {args.out}")
    elif args.cmd == "preview":
        Path(args.out).write_text(build_preview(load_config(args.config), args.image), encoding="utf-8")
        print(f"saved: {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 전체 테스트 통과 확인 → 커밋** — `git commit -m "feat: preview 오버레이와 CLI 서브커맨드"`

---

### Task 5: /html변환 스킬 + .gitignore 조정 + CLAUDE.md 갱신

**Files:**
- Create: `.claude/skills/html변환/SKILL.md`
- Modify: `.gitignore` (`.claude/` → `.claude/*` + `!.claude/skills/`), `CLAUDE.md` (스킬 커맨드 표에 행 추가)

- [ ] **Step 1: .gitignore 수정** — `.claude/` 를 아래로 교체 (스킬만 추적, 나머지는 계속 제외):

```gitignore
.claude/*
!.claude/skills/
```

- [ ] **Step 2: SKILL.md 작성** — 스킬 본문에 포함할 내용: 목적, 필요 입력(커버 PDF 경로·발행일 YYYYMMDD·CC PDF URL·섹션별 페이지 번호), 5단계 워크플로우(render 실행 → 스티칭 이미지를 Claude가 직접 보고 템플릿 좌표와 대조·보정(편차 80px 초과 시 기준값 유지+warn 플래그) → 호 폴더에 issue.json 생성 → build로 euc-kr HTML 생성 → preview 생성 후 브라우저로 열어 검수), 검수 통과 후 확정 좌표를 newsletter_map.json에 반영하는 마무리 규칙, 경로 따옴표 주의.

- [ ] **Step 3: CLAUDE.md 스킬 커맨드 표에 행 추가**:

```markdown
| `/html변환 [커버 PDF]` | 뉴스레터 발송용 이미지맵 HTML 자동 생성 (좌표 감지+검수) |
```

- [ ] **Step 4: 커밋** — `git add .gitignore ".claude/skills/html변환/SKILL.md" CLAUDE.md && git commit -m "feat: /html변환 스킬 정의 및 저장소 설정 갱신"`

---

### Task 6: E2E 검증 — 13호 실데이터 재현

**Files:** (신규 파일 없음 — 검증 전용, 산출물은 scratchpad)

- [ ] **Step 1: render 실행** — `python scripts/newsletter_html.py render --pdf "001. 뉴스레터/001.아카이브/2026년/13호(07-02)/13호 커버.pdf" --out "<scratchpad>/edm_20260702_test.jpg"` → pages=5 확인
- [ ] **Step 2: 13호 issue.json 구성** (템플릿 + 13호 실제 값) 후 build 실행 → 생성 HTML의 18개 area가 실제 `13호 html.html`과 일치하는지 파이썬 diff로 확인
- [ ] **Step 3: preview 생성** — 스티칭 JPG 위 오버레이가 실제 버튼 위치와 맞는지 Claude가 이미지로 직접 확인 + 사용자 브라우저 검수 안내
- [ ] **Step 4: 결과 보고 및 편차 발견 시 템플릿/스킬 문서에 반영 후 커밋**
