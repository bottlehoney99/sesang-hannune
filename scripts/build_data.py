#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
세상 한눈에 - 일일 데이터 수집 스크립트

이 스크립트는 GitHub Actions에서 실행되는 것을 전제로 합니다.
(pytrends가 접속하는 trends.google.com은 Claude의 샌드박스 환경에서는
 네트워크 정책상 막혀 있어, 이 스크립트를 Claude의 예약 작업 안에서
 직접 돌릴 수 없습니다. GitHub Actions 러너는 이 제한이 없습니다.)

1. 한국 뉴스 RSS에서 오늘자 기사 제목을 모아 단어 빈도를 계산합니다
   (규칙 기반 처리 - 형태소 분석기가 아닙니다).
2. pytrends로 구글 트렌드의 한국 실시간/일간 급상승 검색어를 가져옵니다.
   (구글이 API를 바꾸면 실패할 수 있어, 실패 시 빈 리스트로 남기고
   이유를 정직하게 기록합니다 - 절대 데이터를 지어내지 않습니다.)
3. worldglance-data.json 으로 저장합니다 (index.html이 읽는 파일).
"""

import json
import re
import sys
import collections
from datetime import datetime, timezone, timedelta

import requests
import feedparser

KST = timezone(timedelta(hours=9))

RSS_SOURCES = [
    {"name": "한국경제 전체기사", "url": "https://www.hankyung.com/feed/all-news"},
    {"name": "한국경제 정치", "url": "https://www.hankyung.com/feed/politics"},
    {"name": "한국경제 연예", "url": "https://www.hankyung.com/feed/entertainment"},
    {"name": "한국경제 사회", "url": "https://www.hankyung.com/feed/society"},
    {"name": "한국경제 IT과학", "url": "https://www.hankyung.com/feed/it"},
    {"name": "전자신문", "url": "https://rss.etnews.com/Section901.xml"},
    {"name": "전자신문", "url": "https://rss.etnews.com/Section902.xml"},
    {"name": "전자신문", "url": "https://rss.etnews.com/Section903.xml"},
    {"name": "디지털데일리", "url": "https://www.ddaily.co.kr/rss/rss.xml"},
]

STOPWORDS = set("""
있다 없다 한다 된다 위해 대한 통해 이번 오늘 가장 이후 관련 전망 발표 등 것 수 중 더 또 및
만큼 보다 위한 에서 한테 까지 부터 라며 라고 이라며 했다 한다는 됐다는 이라는 라는 인한 인해
위해서는 대해 대해서 그리고 하지만 그러나 때문 처럼 통한 오는 지난 올해 내년 최근 현재 당시
""".split())

JOSA = sorted([
    "으로부터", "에서부터", "이라고", "에게서", "로서", "이나", "에서", "으로", "에는", "에도",
    "까지", "부터", "에게", "한테", "처럼", "만큼", "보다", "이란", "라는", "이라", "라며",
    "한다", "했다", "된다", "됐다", "이다", "는다", "이라며", "은", "는", "이", "가", "을",
    "를", "의", "도", "만", "와", "과", "랑", "로", "에", "께",
], key=len, reverse=True)

BRACKET_RE = re.compile(r"\[[^\]]*\]|\([^)]*\)|【[^】]*】|<[^>]*>")
PUNCT_RE = re.compile(r"[\"'‘’“”…·,\.!?~%\-–—/|:;]+")

UA = "Mozilla/5.0 (compatible; SesangHannuneBot/1.0; +https://github.com/bottlehoney99/sesang-hannune)"


def fetch_feed(url, timeout=20):
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)
    items = []
    for e in parsed.entries:
        title = getattr(e, "title", None)
        link = getattr(e, "link", None)
        if title and link:
            items.append({"t": title.strip(), "u": link.strip()})
    return items


def collect_articles():
    articles = []
    sources_report = []
    by_display_name = collections.OrderedDict()

    for src in RSS_SOURCES:
        name = src["name"]
        try:
            items = fetch_feed(src["url"])
            ok = len(items) > 0
            for it in items:
                articles.append({"t": it["t"], "u": it["u"], "s": name})
            entry = by_display_name.setdefault(name, {"name": name, "url": src["url"], "ok": False, "count": 0})
            entry["ok"] = entry["ok"] or ok
            entry["count"] += len(items)
        except Exception as e:
            entry = by_display_name.setdefault(name, {"name": name, "url": src["url"], "ok": False, "count": 0})
            print(f"[WARN] failed to fetch {name} ({src['url']}): {e}", file=sys.stderr)

    sources_report = list(by_display_name.values())

    seen = set()
    deduped = []
    for a in articles:
        if a["u"] in seen:
            continue
        seen.add(a["u"])
        deduped.append(a)

    return deduped, sources_report


def strip_josa(tok):
    for j in JOSA:
        if len(tok) > len(j) + 1 and tok.endswith(j):
            return tok[: -len(j)]
    return tok


def extract_keywords(articles, top_n=50, min_count=2):
    counter = collections.Counter()
    keyword_articles = collections.defaultdict(list)

    for a in articles:
        title = a["t"]
        clean = BRACKET_RE.sub(" ", title)
        clean = PUNCT_RE.sub(" ", clean)
        tokens = clean.split()
        seen_in_title = set()
        for tok in tokens:
            tok = strip_josa(tok.strip())
            if len(tok) < 2 or tok.isdigit() or tok in STOPWORDS or tok in seen_in_title:
                continue
            seen_in_title.add(tok)
            counter[tok] += 1
            if len(keyword_articles[tok]) < 4:
                keyword_articles[tok].append({"t": a["t"], "u": a["u"], "s": a["s"]})

    top = counter.most_common(top_n)
    return [
        {"word": w, "count": c, "articles": keyword_articles[w]}
        for w, c in top if c >= min_count
    ]


def collect_google_trends():
    """
    구글 트렌드 한국 실시간/일간 급상승 검색어를 가져온다.
    pytrends 내부 API는 구글이 예고 없이 바꿀 수 있어 여러 방식을 순서대로 시도하고,
    전부 실패하면 정직하게 빈 리스트 + 실패 사유를 남긴다 (지어내지 않음).
    """
    try:
        from pytrends.request import TrendReq
    except Exception as e:
        return [], f"pytrends 라이브러리를 불러오지 못했습니다: {e}"

    try:
        pytrends = TrendReq(hl="ko-KR", tz=540, timeout=(10, 25))
    except Exception as e:
        return [], f"pytrends 초기화 실패: {e}"

    # 1) 실시간 급상승 검색어 (있으면 우선 사용)
    try:
        df = pytrends.realtime_trending_searches(pn="KR")
        if df is not None and len(df) > 0:
            words = []
            for _, row in df.iterrows():
                title = row.get("title") if hasattr(row, "get") else None
                if isinstance(title, dict):
                    title = title.get("query")
                if title:
                    words.append(str(title))
            if words:
                return [{"word": w, "rank": i + 1} for i, w in enumerate(words[:20])], ""
    except Exception as e:
        print(f"[INFO] realtime_trending_searches 실패, 일간 검색어로 대체 시도: {e}", file=sys.stderr)

    # 2) 일간 급상승 검색어
    try:
        df = pytrends.trending_searches(pn="south_korea")
        if df is not None and len(df) > 0:
            words = [str(w) for w in df[0].tolist()]
            return [{"word": w, "rank": i + 1} for i, w in enumerate(words[:20])], ""
    except Exception as e:
        return [], f"구글 트렌드 급상승 검색어를 가져오지 못했습니다 (pytrends/구글 트렌드 API 변경 가능성): {e}"

    return [], "구글 트렌드에서 데이터를 받았지만 형식이 비어 있었습니다."


def main():
    now_kst = datetime.now(KST)

    articles, sources_report = collect_articles()
    keywords = extract_keywords(articles)

    sources_note_parts = []
    failed = [s["name"] for s in sources_report if not s["ok"]]
    if failed:
        sources_note_parts.append("다음 소스는 이번 수집에서 실패했습니다: " + ", ".join(sorted(set(failed))))

    trending_now, trends_note = collect_google_trends()

    out = {
        "collected_at": now_kst.strftime("%Y-%m-%d %H:%M KST"),
        "date": now_kst.strftime("%Y-%m-%d"),
        "method": (
            f"한국경제/전자신문/디지털데일리 RSS에서 실제로 수집한 기사 제목 {len(articles)}건을 "
            "공백 분절 + 조사 제거 + 불용어 필터링(규칙 기반 처리)으로 단어 빈도를 계산했습니다. "
            "형태소 분석기가 아니라 규칙 기반 처리라 정확도에 한계가 있습니다."
        ),
        "sources": sources_report,
        "sources_note": " ".join(sources_note_parts),
        "sns_note": (
            "SNS(X·인스타그램·페이스북·틱톡 등)는 로그인 없이 크롤링이 막혀 있어 아직 반영하지 못했습니다. "
            "대신 구글 트렌드의 실시간/일간 급상승 검색어를 GitHub Actions에서 별도로 수집해 "
            "'지금 급상승 검색어' 항목으로 보여드립니다."
        ),
        "keywords": keywords,
        "trending_now": trending_now,
        "trending_now_note": trends_note,
    }

    with open("worldglance-data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"[OK] articles={len(articles)} keywords={len(keywords)} trending_now={len(trending_now)}")
    if trends_note:
        print(f"[NOTE] {trends_note}")


if __name__ == "__main__":
    main()
