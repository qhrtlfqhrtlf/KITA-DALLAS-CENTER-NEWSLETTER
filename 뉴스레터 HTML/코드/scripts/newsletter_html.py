"""Trade Newsline 발송용 이미지맵 HTML 생성 도구.

서브커맨드:
  render   커버 PDF를 세로 스티칭한 이메일용 JPG로 변환
  build    이슈 설정(JSON)으로 발송용 euc-kr HTML 생성
  preview  클릭영역 오버레이가 얹힌 검수용 HTML 생성

이슈 설정(JSON) 스키마 — scripts/templates/newsletter_map.json 을 복사해
image_url, pdf_url 을 채우고 areas 의 page/coords 를 호에 맞게 수정한다:
  {
    "image_url": "https://www.kita.net/mailclub/NeDM/edm_YYYYMMDD.jpg",
    "pdf_url": "https://files.constantcontact.com/.../xxxx.pdf",
    "areas": [
      {"id": "...", "label": "...", "kind": "fixed", "coords": [x1,y1,x2,y2], "href": "..."},
      {"id": "...", "label": "...", "kind": "pdf",   "coords": [x1,y1,x2,y2], "page": 2, "warn": false}
    ]
  }
"""
import json
from pathlib import Path


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def area_href(area, pdf_url):
    """영역의 최종 링크. pdf 영역은 CC PDF URL + #page=N (1페이지는 프래그먼트 생략)."""
    if area.get("kind") == "pdf":
        page = area.get("page", 1)
        return pdf_url if page == 1 else f"{pdf_url}#page={page}"
    return area["href"]


def build_html(config):
    """13호 발송본과 동일한 마크업 구조의 이미지맵 HTML 문자열 생성."""
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


def render_pdf(pdf_path, width, out_path):
    """커버 PDF 전 페이지를 지정 폭으로 렌더링해 세로로 이어붙인 JPG 저장."""
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


def render_pages(pdf_path, out_dir, prefix, dpi=200):
    """커버 PDF 각 페이지를 고화질 PNG로 개별 저장 (IT SR 첨부 규격: ..._Coverpages_FINAL_N.png).

    발송용 HTML은 render_pdf()의 스티칭 JPG 하나로 충분하지만, IT 운영센터에 SR을 넣어야
    하는 예외 상황이나 원본 보관용으로 페이지별 고화질 PNG가 필요할 때 사용한다.
    """
    import fitz

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    zoom = dpi / 72
    paths = []
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        out_path = out_dir / f"{prefix}_{i}.png"
        pix.save(str(out_path))
        paths.append(out_path)
    doc.close()
    return paths


def build_preview(config, image_src):
    """로컬 이미지 위에 클릭영역을 반투명 오버레이로 표시한 검수용 HTML.

    warn=true 영역은 빨간색으로 강조된다(좌표 자동 감지 편차 초과 등).
    """
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
            f'style="position:absolute; left:{x1}px; top:{y1}px; width:{x2 - x1}px; height:{y2 - y1}px; '
            f'background:{color}; border:2px solid {border}; box-sizing:border-box; '
            f'font:11px sans-serif; color:#fff; overflow:hidden">{label}</a>'
        )
    parts += ['</div>', '</body>']
    return "\n".join(parts)


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(prog="newsletter_html", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("render", help="커버 PDF → 세로 스티칭 JPG")
    p.add_argument("--pdf", required=True)
    p.add_argument("--width", type=int, default=700)
    p.add_argument("--out", required=True)

    p = sub.add_parser("pages", help="커버 PDF → 페이지별 고화질 PNG (IT SR 첨부 규격)")
    p.add_argument("--pdf", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--prefix", required=True)
    p.add_argument("--dpi", type=int, default=200)

    p = sub.add_parser("build", help="이슈 설정 JSON → 발송용 euc-kr HTML")
    p.add_argument("--config", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("preview", help="이슈 설정 JSON + 이미지 → 검수용 오버레이 HTML")
    p.add_argument("--config", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--out", required=True)

    args = ap.parse_args(argv)
    if args.cmd == "render":
        print(json.dumps(render_pdf(args.pdf, args.width, args.out)))
    elif args.cmd == "pages":
        paths = render_pages(args.pdf, args.out_dir, args.prefix, args.dpi)
        print(json.dumps([str(p) for p in paths]))
    elif args.cmd == "build":
        write_euckr(args.out, build_html(load_config(args.config)))
        print(f"saved: {args.out}")
    elif args.cmd == "preview":
        Path(args.out).write_text(build_preview(load_config(args.config), args.image), encoding="utf-8")
        print(f"saved: {args.out}")


if __name__ == "__main__":
    main()
