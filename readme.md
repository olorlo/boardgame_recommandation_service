# 🎲 보드게임 정보 제공 및 AI 맞춤 추천 서비스

본 프로젝트는 Django 프레임워크를 활용하여 보드게임 정보를 제공하고, 사용자들이 자유롭게 소통할 수 있는 커뮤니티 기능을 지원합니다. 특히, 생성형 AI(Gemini)와 YouTube API를 연동하여 상황에 맞는 보드게임을 추천받고 룰을 쉽게 학습할 수 있는 **스마트 보드게임 도우미 서비스**입니다.

---

## 📦 3000등 데이터 갱신 흐름

DB 파일을 공유하지 않고 CSV와 관리 명령어로 데이터를 재현합니다.

```bash
python manage.py import_boardgames_from_csv --path boardgames_ranks.csv --limit 3000
python manage.py import_boardlife_titles_from_csv --path boardlife_titles_1_40.csv
python manage.py fetch_game_details --all --rank-max 3000 --sleep 1.5
python manage.py export_game_details --path data/game_details.csv --rank-max 3000
```

팀원이 전달받은 `data/game_details.csv`를 DB에 반영할 때는 아래 명령어를 사용합니다.

```bash
python manage.py import_game_details --path data/game_details.csv
```

---

## 🚀 오늘 구현한 핵심 기능 (12회차 관통 프로젝트)

1. **기본 CRUD 및 인증 기능 보완**
   - **`accounts` 앱**: 기존 로그인/로그아웃에 이어 새로운 사용자를 받을 수 있는 `signup`(회원가입) 기능을 구현하고 UI 네비게이션과 연결했습니다.
   - **`community` 앱**: 낙서장(자유게시판) 글을 본인만 수정하고 삭제할 수 있도록 접근 권한 검증(`request.user == article.user`) 로직과 `update`, `delete` 뷰를 완성했습니다.

2. **상황 맞춤 AI 추천 & 상세 정보 모달(창 속의 창) 연동**
   - AI가 추천해 준 게임 리스트의 이름을 클릭하면, 화면 이동 없이 즉석에서 팝업되는 **상세 정보 모달창** 기능을 구현했습니다.
   - 클릭 시 내부적으로 `details_by_title`이라는 새로운 API를 호출하여, DB에 없는 게임이라도 즉시 유튜브와 AI를 통해 정보를 가져옵니다.
   - **YouTube API 연동**: "{게임이름} 보드게임 룰 설명" 키워드로 검색해 가장 관련성 높은 영상을 모달창 우측에 띄워줍니다.
   - **Gemini AI 연동 (GMS 프록시)**: 게임의 승리 조건과 턴 진행 방식을 초보자에게 설명하듯이 귀여운 이모지와 함께 요약해 주도록 프롬프트를 작성하여 좌측에 띄웁니다.

---

## 📝 단계별 구현 과정 중 학습한 내용 및 회고

### 1. 학습한 내용 (새로 배운 것들)
- **모달(Modal) 창의 비동기 렌더링**: 페이지 전체를 새로고침하지 않고, JS의 `fetch` API를 통해 백엔드(Django)와 통신한 뒤 받아온 JSON 데이터를 활용해 화면(DOM) 일부분만 부드럽게 갱신하는 방법을 깊이 이해하게 되었습니다.
- **REST API 직접 호출**: 기존에는 제조사(Google)에서 제공하는 공식 파이썬 SDK(`google.generativeai`)만 사용하다가, 사내망 혹은 프록시 환경(SSAFY GMS)에 맞게 커스텀 요청을 보내기 위해 파이썬 내장 `requests` 모듈로 직접 HTTP POST 요청을 만들고 JSON 페이로드를 조작하는 법을 배웠습니다.

### 2. 어려웠던 부분 (Troubleshooting)
- **API 인증 및 프록시 에러 (HTTP 400, 403, 404)**: 
  - 외부 프록시(SSAFY GMS)를 통과하도록 엔드포인트 URL을 맞추는 과정에서 여러 에러와 마주쳤습니다. 
  - 처음엔 공식 SDK에 프록시 엔드포인트를 강제로 씌우려다 URL이 중복되는 등(404 Not Found) 문제가 발생했고, 쿼리스트링 파라미터(`?key=...`)로 토큰을 넘겨야 하는 GMS 서버의 까다로운 인증 요구사항(403 Forbidden)을 맞추기가 가장 힘들었습니다.
- **AI 응답 지연 (Timeout)**: 
  - 모든 코드를 알맞게 고쳤음에도 불구하고 `Read timed out` 에러가 났습니다. AI의 텍스트 생성 속도가 일반적인 API보다 느리다는 것을 깨달았고, `requests.post`의 `timeout` 파라미터를 60초로 넉넉하게 늘려서 해결했습니다.

### 3. 느낀 점
그동안 제공된 프레임워크나 라이브러리를 있는 그대로 쓰기만 했는데, 이번에 외부 프록시 서버 연동을 진행하면서 **"블랙박스(SDK)를 벗어나 HTTP 요청의 기본(Method, Header, URL, Body)으로 돌아가 직접 문제를 해결하는 경험"**을 해볼 수 있었습니다. 원인을 하나씩 분석하고 타파해 나가는 디버깅 과정이 고달팠지만, 성공적으로 유튜브 영상과 AI 요약이 모달창에 예쁘게 뜨는 것을 보았을 때의 성취감은 정말 컸습니다!
