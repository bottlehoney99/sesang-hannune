# 세상 한눈에 (Sesang Hannune)

바쁜 현대인을 위한 세상만사 한눈으로 보기 — 한국 뉴스 기사 제목에서 실제로 추출한 오늘의 트렌딩 키워드를 빈도수 기반 워드클라우드로 시각화하는 정적 웹앱입니다.

- `index.html` — 페이지 (Canvas 기반 워드클라우드, 클릭 시 관련 기사 목록 표시)
- `worldglance-data.json` — 오늘 수집된 키워드/기사 데이터 (매일 자동 갱신 예정)

## GitHub Pages
Settings → Pages → Source를 "Deploy from a branch", Branch를 `main` / `(root)`로 설정하면
`https://bottlehoney99.github.io/sesang-hannune/` 에서 바로 볼 수 있습니다.

## 데이터
- 출처: 한국경제(전체·정치·연예·사회·IT과학), 전자신문, 디지털데일리 RSS
- 방식: 기사 제목을 공백 분절 + 조사 제거 + 불용어 필터링한 규칙 기반 처리 (형태소 분석기 아님)
- SNS(X·인스타그램 등)는 로그인 없이 크롤링이 막혀 있어 아직 반영되지 않았습니다.
