# -*- coding: utf-8 -*-
"""데이터.json을 읽어 A4 인쇄용 표 문서를 생성한다.

용도: 종이에 뽑아 손으로 수정 표시하고 그대로 보고하는 형태.
- A4 세로, 9pt, 표 중심. 카드·색면·다크모드 없음 (흑백 인쇄 기준)
- 모든 표에 손글씨용 '확인' 칸
- 표 머리행은 페이지가 넘어가도 반복 출력 (thead: table-header-group)
- 집계는 전부 데이터.json에서 계산 (하드코딩 금지)

실행: python 보고용표생성.py
출력: 보고용표.html  → 브라우저에서 Ctrl+P → A4 세로 / 배율 100% / 배경 그래픽 켜기
"""
import io
import json
import collections

SRC = "데이터.json"
OUT = "보고용표.html"

도시순서 = ["DFW", "휴스턴", "샌안토니오", "오스틴"]
도시라벨 = {"DFW": "댈러스-포트워스", "휴스턴": "휴스턴",
            "샌안토니오": "샌안토니오", "오스틴": "오스틴"}

리그규정 = [
    ("NFL", "없음 — 4대 리그 중 유일하게 유니폼 광고 불허"),
    ("NBA", "패치 1개(좌측 상단). 4대 리그 중 가장 보수적"),
    ("NHL", "어깨 패치 + 헬멧. 홈·원정 광고주를 따로 판다"),
    ("MLB", "소매 패치(2023 시즌부터). 투수·타자 자세에서 가장 잘 걸리는 위치"),
    ("MLS", "최대 4개(가슴·좌소매·우소매·등하단). 2026 올스타 이후 등하단 신설"),
    ("WNBA", "복부 — NBA와 위치가 다름"),
]

확인필요 = [
    ("높음", "Reliant Stadium 개칭이 2026년 8월 중 실제 완료됐는지",
     "조사는 2026-04 발표 기준. 예정 시점이 이번 달이므로 발행 전 재확인 필수"),
    ("높음", "Dallas Memorial Auditorium 완공 시점",
     "건설 지연으로 미확정. Wings 대표 표기(2027 AAC)의 근거가 바뀔 수 있음"),
    ("중간", "Houston Texans 스폰서 전수 확인",
     "공식 파트너 페이지를 다 보지 못하고 검색으로 잡힌 3건만 기재"),
    ("중간", "스폰서 수집 편차 보강",
     "구단별 스폰서 수가 1~5건으로 고르지 않음. 공식 파트너 페이지 개별 확인 필요"),
    ("낮음", "표본 범위 명시",
     "Cowboys 150곳+·Stars 120곳+ 보도. 본 조사는 대표 3~5곳만 다룬 표본"),
]


def esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    T = d["구단"]
    기준 = d["메타"].get("기준시점", {})

    활성 = [(t, s) for t in T for s in t["스폰서"] if s.get("상태") != "종료"]
    종료 = [(t, s) for t in T for s in t["스폰서"] if s.get("상태") == "종료"]
    업종 = collections.Counter(s["업종"] for _, s in 활성)
    등급 = collections.Counter(s["계약"]["공개등급"] for _, s in 활성)
    한국 = [(t, s) for t, s in 활성 if s.get("한국기업")]

    def 네이밍(t):
        for s in t["스폰서"]:
            if s.get("상태") != "종료" and "구장 명칭" in s.get("노출영역", ""):
                return s
        return None

    # 표1(총람)의 유니폼 광고 칸은 산문을 자르지 않고 스폰서 목록에서 뽑는다.
    # 리그 규정 설명은 표3에만 두어 중복을 없앤다.
    위치키워드 = ["가슴", "소매", "헬멧", "복부", "등 하단", "좌측 상단"]

    def 유니폼광고(t):
        out = []
        for s in t["스폰서"]:
            if s.get("상태") == "종료":
                continue
            영역 = s.get("노출영역", "")
            if "유니폼" not in 영역 and "헬멧" not in 영역:
                continue
            위치 = next((k for k in 위치키워드 if k in 영역), None)
            홈원정 = "홈" if "홈경기" in 영역 else ("원정" if "원정경기" in 영역 else None)
            꼬리 = "·".join(x for x in (위치, 홈원정) if x)
            out.append(f'{s["기업명"]}({꼬리})' if 꼬리 else s["기업명"])
        return ", ".join(out) if out else f'<span class="dim">해당 없음 ({t["리그"]})</span>'

    구장 = {}
    for t in T:
        s = 네이밍(t)
        if s:
            구장.setdefault(t["홈구장"], {"s": s, "팀": []})
            if t["구단명"] not in 구장[t["홈구장"]]["팀"]:
                구장[t["홈구장"]]["팀"].append(t["구단명"])
    전체구장 = {t["홈구장"] for t in T}
    무기업명 = sorted(전체구장 - set(구장))
    금액확인 = [v for v in 구장.values() if not v["s"]["계약"]["금액"].startswith("미공개")]
    미공개수 = sum(1 for _, s in 활성 if s["계약"]["금액"] == "미공개")

    P = []
    A = P.append

    A("""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>미국 구단·스폰서 지도 — 텍사스 권역 보고용 표</title>
<style>
@page{size:A4 portrait;margin:12mm 10mm}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:"Malgun Gothic","맑은 고딕",sans-serif;font-size:9pt;line-height:1.42;color:#000;background:#fff}
.sheet{width:190mm;margin:0 auto;padding:6mm 2mm}
/* 머리말 */
.hd{border-bottom:2pt solid #000;padding-bottom:2.5mm;margin-bottom:3mm}
.hd h1{margin:0;font-size:14pt;letter-spacing:-.2pt}
.hd .l{display:flex;justify-content:space-between;gap:4mm;font-size:8pt;margin-top:1.5mm}
.hd .asof{margin-top:2mm;padding:1.5mm 2.5mm;border:.5pt solid #000;font-size:8pt;background:#f2f2f2}
.sig{display:flex;gap:0;margin-top:2.5mm;font-size:7.5pt}
.sig div{border:.5pt solid #000;padding:1mm 2mm;min-height:9mm;flex:1}
.sig div b{display:block;font-size:7pt;color:#444;font-weight:400}
/* 요약 */
.kpi{display:flex;flex-wrap:wrap;gap:0;margin:0 0 3mm;border:.5pt solid #000}
.kpi div{flex:1;min-width:24mm;padding:1.5mm 2mm;border-right:.5pt solid #000}
.kpi div:last-child{border-right:none}
.kpi b{display:block;font-size:12pt;line-height:1.15}
.kpi span{font-size:7pt;color:#333}
/* 표 */
h2{font-size:10.5pt;margin:5mm 0 1.5mm;padding-bottom:.8mm;border-bottom:1pt solid #000;
  page-break-after:avoid}
h2 .n{font-size:8pt;font-weight:400;color:#333;margin-left:2mm}
table{border-collapse:collapse;width:100%;font-size:8pt;table-layout:fixed}
thead{display:table-header-group}
tr{page-break-inside:avoid}
th,td{border:.5pt solid #666;padding:1.1mm 1.6mm;text-align:left;vertical-align:top;
  word-break:break-word;overflow-wrap:anywhere}
th{background:#e8e8e8;font-weight:700;font-size:7.5pt}
td.c{text-align:center}
td.n{text-align:right;white-space:nowrap}
.chk{width:11mm;background:#fafafa}
.g{font-size:7pt;padding:0 .8mm;border:.5pt solid #000}
.dim{color:#555}
.st{font-size:7pt;color:#555}
/* 각주·비고 */
.fn{margin:2mm 0 0;padding:2mm 2.5mm;border:.5pt solid #666;background:#f7f7f7;font-size:7.5pt}
.fn b{display:block;font-size:7pt;margin-bottom:.8mm}
.fn ol{margin:0;padding-left:4.5mm}
.fn li{margin:.4mm 0}
.note{font-size:7.5pt;color:#333;margin:1.5mm 0 0}
.memo{border:.5pt solid #000;margin-top:3mm;padding:2mm 2.5mm;min-height:26mm}
.memo b{font-size:7.5pt}
.memo .lines{margin-top:1.5mm;border-top:.4pt dotted #999;height:5mm}
.ft{margin-top:4mm;padding-top:1.5mm;border-top:.5pt solid #000;font-size:7pt;color:#444;
  display:flex;justify-content:space-between}
.brk{page-break-before:always}
@media screen{body{background:#eee;padding:8mm 0}
  .sheet{background:#fff;box-shadow:0 0 6px rgba(0,0,0,.25)}}
@media print{body{background:#fff;padding:0}.sheet{width:auto;margin:0;padding:0;box-shadow:none}}
</style></head><body><div class="sheet">""")

    # ---------- 머리말 ----------
    A(f"""<div class="hd">
<h1>미국 구단·스폰서 지도 — 텍사스 권역 조사 결과</h1>
<div class="l"><span>한국무역협회 달러스지부 · 인스타그램 정보전달 콘텐츠 기초 조사</span>
<span>작성 2026-08-05 · Phase 1</span></div>
<div class="asof"><b>기준 시점</b> {esc(기준.get("기준",""))}
&nbsp;/&nbsp;<b>예외</b> {esc(", ".join(t["구단명"] for t in T if t.get("기준시점예외")) or "없음")}
— {esc(기준.get("예외",""))}</div>
<div class="sig"><div><b>작성</b></div><div><b>검토</b></div><div><b>승인</b></div>
<div><b>수정 지시</b></div></div>
</div>""")

    A(f"""<div class="kpi">
<div><b>{len(T)}</b><span>구단</span></div>
<div><b>{len(활성)}</b><span>활성 스폰서</span></div>
<div><b>{len(종료)}</b><span>종료(참고)</span></div>
<div><b>{len(구장)}/{len(전체구장)}</b><span>기업명 구장</span></div>
<div><b>{등급.get('공식 발표',0)}/{등급.get('언론 보도',0)}</b><span>공식/언론</span></div>
<div><b>{미공개수}</b><span>금액 미공개</span></div>
<div><b>{len(한국)}</b><span>한국 기업</span></div>
</div>""")

    # ---------- 표1 구단 총람 ----------
    A(f'<h2>표1. 구단 총람<span class="n">{len(T)}개 구단</span></h2>')
    A('<table><colgroup><col style="width:20mm"><col style="width:32mm"><col style="width:12mm">'
      '<col style="width:42mm"><col style="width:28mm"><col><col class="chk"></colgroup>'
      '<thead><tr><th>도시</th><th>구단</th><th>리그</th><th>홈구장</th>'
      '<th>네이밍 라이츠</th><th>유니폼 광고<br><span class="st">규정은 표3</span></th>'
      '<th>확인</th></tr></thead><tbody>')
    for c in 도시순서:
        ts = [t for t in T if t["도시"] == c]
        for i, t in enumerate(ts):
            nr = 네이밍(t)
            도시칸 = (f'<td rowspan="{len(ts)}">{esc(도시라벨[c])}<br>'
                      f'<span class="st">{len(ts)}개 구단</span></td>') if i == 0 else ""
            예외 = ' <span class="g">기준예외</span>' if t.get("기준시점예외") else ""
            A(f'<tr>{도시칸}<td>{esc(t["구단명"])}{예외}</td><td class="c">{esc(t["리그"])}</td>'
              f'<td>{esc(t["홈구장"])}</td>'
              f'<td>{esc(nr["기업명"]) if nr else "<span class=dim>없음</span>"}</td>'
              f'<td>{유니폼광고(t)}</td><td class="chk"></td></tr>')
    A("</tbody></table>")
    A(f'<p class="note">기업명 없는 구장: {esc(", ".join(무기업명)) if 무기업명 else "없음"}. '
      f'공용 구장: ' + esc("; ".join(f'{k} = {"·".join(v["팀"])}'
                                    for k, v in 구장.items() if len(v["팀"]) > 1)) + "</p>")

    # ---------- 표2 네이밍 라이츠 ----------
    A(f'<h2>표2. 구장 네이밍 라이츠<span class="n">{len(구장)}건 · '
      f'금액 확인 {len(금액확인)}건</span></h2>')
    A('<table><colgroup><col style="width:35mm"><col style="width:27mm"><col style="width:17mm">'
      '<col><col style="width:36mm"><col style="width:14mm"><col class="chk"></colgroup>'
      '<thead><tr><th>구장</th><th>기업</th><th>업종</th><th>금액</th><th>계약 기간</th>'
      '<th>등급</th><th>확인</th></tr></thead><tbody>')
    for 구장명, v in 구장.items():
        s = v["s"]
        기간 = s["계약"]["내용"]
        기간 = 기간 if len(기간) <= 60 else 기간[:58] + "…"
        A(f'<tr><td>{esc(구장명)}<br><span class="st">{esc("·".join(v["팀"]))}</span></td>'
          f'<td>{esc(s["기업명"])}</td><td>{esc(s["업종"])}</td>'
          f'<td>{esc(s["계약"]["금액"])}</td><td>{esc(기간)}</td>'
          f'<td class="c">{esc(s["계약"]["공개등급"])}</td><td class="chk"></td></tr>')
    A("</tbody></table>")

    # ---------- 표3 리그별 광고 지면 ----------
    A('<h2>표3. 리그별 유니폼 광고 지면<span class="n">리그 규정이 자리를 정한다</span></h2>')
    A('<table><colgroup><col style="width:14mm"><col style="width:72mm"><col>'
      '<col class="chk"></colgroup>'
      '<thead><tr><th>리그</th><th>광고 지면</th><th>텍사스 권역 사례</th>'
      '<th>확인</th></tr></thead><tbody>')
    for lg, rule in 리그규정:
        사례 = []
        for t in [x for x in T if x["리그"] == lg]:
            v = 유니폼광고(t)
            if "해당 없음" not in v:
                사례.append(f'{t["구단명"]} = {v}')
        A(f'<tr><td class="c"><b>{lg}</b></td><td>{esc(rule)}</td>'
          f'<td>{" / ".join(사례) if 사례 else "<span class=dim>해당 없음</span>"}</td>'
          f'<td class="chk"></td></tr>')
    A("</tbody></table>")

    # ---------- 표4 업종 분포 ----------
    A(f'<h2>표4. 업종 분포<span class="n">활성 {len(활성)}건</span></h2>')
    A('<table><colgroup><col style="width:26mm"><col style="width:13mm"><col>'
      '<col class="chk"></colgroup>'
      '<thead><tr><th>업종</th><th>건수</th><th>사례</th><th>확인</th></tr></thead><tbody>')
    사례모음 = collections.defaultdict(list)
    for t, s in 활성:
        사례모음[s["업종"]].append(s["기업명"])
    for k, n in 업종.most_common():
        A(f'<tr><td>{esc(k)}</td><td class="c"><b>{n}</b></td>'
          f'<td>{esc(", ".join(사례모음[k]))}</td><td class="chk"></td></tr>')
    A("</tbody></table>")
    A(f'<p class="note"><b>설계 단계 예상과의 차이</b> — 에너지 1위({업종["에너지"]}건)는 맞았으나, '
      f'항공은 {업종["항공"]}건이 전부 American Airlines 한 기업이며 AAC를 3개 구단이 공유해 '
      f'구단 수만큼 잡힌 것이므로 실질 1건이다(예상 틀림). '
      f'예상하지 못한 것은 헬스케어 {업종["헬스케어"]}건으로, MLS·NWSL 유니폼 가슴은 사실상 전부 의료기관이다.</p>')

    # ---------- 표5 스폰서 상세 ----------
    A(f'<h2 class="brk">표5. 스폰서 상세<span class="n">전체 {len(활성)+len(종료)}건 '
      f'(활성 {len(활성)} / 종료 {len(종료)})</span></h2>')
    A('<table><colgroup><col style="width:30mm"><col style="width:28mm"><col style="width:15mm">'
      '<col style="width:26mm"><col style="width:12mm"><col><col class="chk"></colgroup>'
      '<thead><tr><th>구단</th><th>기업</th><th>업종</th><th>금액</th><th>등급</th>'
      '<th>노출 영역 / 하는 일</th><th>확인</th></tr></thead><tbody>')
    for c in 도시순서:
        for t in [x for x in T if x["도시"] == c]:
            for i, s in enumerate(t["스폰서"]):
                끝 = s.get("상태") == "종료"
                구단칸 = (f'<td rowspan="{len(t["스폰서"])}">{esc(t["구단명"])}<br>'
                          f'<span class="st">{esc(t["리그"])} · {esc(도시라벨[c])}</span></td>'
                          if i == 0 else "")
                태그 = ""
                if s.get("한국기업"):
                    태그 += ' <span class="g">한국</span>'
                if s.get("비고"):
                    태그 += f' <span class="st">{esc(s["비고"])}</span>'
                if 끝:
                    태그 += ' <span class="g">종료</span>'
                A(f'<tr{" class=dim" if 끝 else ""}>{구단칸}'
                  f'<td>{esc(s["기업명"])}{태그}</td><td>{esc(s["업종"])}</td>'
                  f'<td>{esc(s["계약"]["금액"])}</td>'
                  f'<td class="c">{esc(s["계약"]["공개등급"])}</td>'
                  f'<td>{esc(s["노출영역"])}<br><span class="st">{esc(s["하는일"])}</span></td>'
                  f'<td class="chk"></td></tr>')
    A("</tbody></table>")

    # ---------- 표6 각주 ----------
    각주팀 = [t for t in T if t.get("각주")]
    if 각주팀:
        A('<h2>표6. 예외 처리 구단 각주</h2>')
        for t in 각주팀:
            A(f'<div class="fn"><b>{esc(t["구단명"])} — {esc(t.get("기준시점예외",""))}</b><ol>')
            for x in t["각주"]:
                A(f"<li>{esc(x)}</li>")
            A("</ol>")
            if t.get("각주출처"):
                A(f'<p class="note">출처 — {esc(t["각주출처"])}</p>')
            A("</div>")

    # ---------- 표7 확인 필요 ----------
    A('<h2>표7. 발행 전 확인·보강 필요 항목</h2>')
    A('<table><colgroup><col style="width:14mm"><col style="width:60mm"><col>'
      '<col style="width:20mm"><col class="chk"></colgroup>'
      '<thead><tr><th>우선</th><th>항목</th><th>사유</th><th>담당</th>'
      '<th>완료</th></tr></thead><tbody>')
    for 우선, 항목, 사유 in 확인필요:
        A(f'<tr><td class="c">{esc(우선)}</td><td><b>{esc(항목)}</b></td>'
          f'<td>{esc(사유)}</td><td></td><td class="chk"></td></tr>')
    A("</tbody></table>")
    A(f'<p class="note"><b>금액 신뢰도</b> — 활성 {len(활성)}건 중 {미공개수}건이 미공개다. '
      f'금액이 확인된 것은 네이밍 라이츠 {len(금액확인)}건뿐이며 모두 언론 보도 등급이다. '
      f'유니폼 패치 계약 금액은 13개 구단 전부 미공개이며 추정치는 넣지 않았다.</p>')

    # ---------- 수정 메모 ----------
    A('<div class="memo"><b>수정 지시 / 메모</b>'
      + '<div class="lines"></div>' * 4 + "</div>")

    A(f'<div class="ft"><span>데이터 원본: 데이터.json · 이 문서는 보고용표생성.py로 생성</span>'
      f'<span>구단 {len(T)} / 활성 스폰서 {len(활성)}건 / 2026-08-05</span></div>')
    A("</div></body></html>")

    io.open(OUT, "w", encoding="utf-8").write("".join(P))
    print("generated: %s (%d teams / %d active / %d rows in 표5)"
          % (OUT, len(T), len(활성), len(활성) + len(종료)))


if __name__ == "__main__":
    main()
