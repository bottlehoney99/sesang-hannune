# 세상 한눈에 (Sesang Hannune)

바쁜 현대인을 위한 세상만사 한눈으로 보기 — 한국 뉴스 기사 제목에서 실제로 추출한 오늘의 트렌딩 키워드를 빈도수 기반 워드클라우드로 시각화하는 정적 웹앱입니다.

- `index.html` — 페이지 (Canvas 기반 워드클라우드, 클릭 시 관련 기사 목록 표시)
- `worldglance-data.json` — 오늘 수집된 키워드/기사 데이터 (매일 자동 갱신 예정)

## GitHub Pages
Settings → Pages → Source를 "Deploy from a branch", Branch를 `main` / `(root)`로 설정하면
`https://bottlehoney99.github.io/sesang-hannune/` 에서 바로 볼 수 있습니다.

## 데이터
- 뉴스 키워드 출처: 한국경제(전체·정치·연예·사회·IT과학), 전자신문, 디지털데일리 RSS
- 처리 방식: 기사 제목을 공백 분절 + 조사 제거 + 불용어 필터링한 규칙 기반 처리 (형태소 분석기 아님)
- 급상승 검색어: 구글 트렌드(`pytrends`)에서 한국 실시간/일간 급상승 검색어를 가져와 `trending_now`로 별도 표시
- SNS(X·인스타그램 등)는 로그인 없이 크롤링이 막혀 있어 아직 반영되지 않았습니다.

## 자동 갱신 (GitHub Actions)
`.github/workflows/update-data.yml`이 매일 00:07 UTC(한국시간 09:07)에 `scripts/build_data.py`를 실행해
`worldglance-data.json`을 새로 만들고, 변경이 있으면 자동으로 커밋·푸시합니다.

> **왜 GitHub Actions인가요?** 구글 트렌드(`pytrends`)가 접속하는 `trends.google.com`은
> Claude가 이 저장소를 관리하는 샌드박스 환경에서는 네트워크 정책상 막혀 있어 Claude의
> 예약 작업 안에서는 직접 실행할 수 없습니다. GitHub Actions 러너는 이 제한이 없어서
> 데이터 수집을 여기로 옮겼습니다.

### 수동 실행
Actions 탭 → "세상 한눈에 - 일일 데이터 갱신" → **Run workflow**로 즉시 갱신할 수 있습니다.

### 로컬 실행
```bash
pip install -r requirements.txt
python scripts/build_data.py
```

### 참고
`pytrends`가 사용하는 구글 트렌드 비공식 API는 구글이 예고 없이 형식을 바꿀 수 있습니다.
실패하면 `trending_now`는 빈 배열로, `trending_now_note`에 실패 사유가 정직하게 남고
페이지에는 급상승 검색어 섹션이 자동으로 숨겨지거나 안내 문구로 대체됩니다 — 절대 데이터를
지어내지 않습니다.
