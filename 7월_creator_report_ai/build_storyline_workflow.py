"""
스토리라인판 Dify 워크플로우 YML 생성기.

손으로 1500줄 YML(HTML 템플릿을 escape해 code 노드에 박는)을 쓰면 반드시 깨지므로,
조각들을 읽어 프로그램으로 조립한다.

입력 조각:
  - creator_report_template_storyline.html  (마커 템플릿)
  - assemble_html_storyline.py              (Code 노드 본문 소스)
  - 아래 하드코딩된 3개 프롬프트

Dify Code 노드 규약(기존 YML에서 확인):
  - code 안에 `TEMPLATE_HTML = "..."` 상수 + `def main(report_json, <인사이트들>)` 정의
    (main 에는 template_html 파라미터가 없고 `out = TEMPLATE_HTML` 로 시작).
  - Dify가 variables 목록을 인자로 main(**variables) 호출, 반환 {"html": ...}.

출력: creator_report_storyline_workflow.yml

실행: ./.venv/bin/python report_template/build_storyline_workflow.py
"""

import json
import os
import yaml


HERE = os.path.dirname(os.path.abspath(__file__))

# 리포트 API 서버 주소. Dify(클라우드)가 접근 가능한 공개 주소여야 한다.
#   - 로컬 개발: Cloudflare Quick Tunnel 주소 (재시작 시 매번 바뀌므로 여기만 갱신하고 재실행)
#   - 배포: 실제 Cloud Run URL
BASE_URL = "https://your-report-api-host.example.com"


# ---------- literal block(`|`) 스타일 강제 ----------
class Literal(str):
    pass


def _literal_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.add_representer(Literal, _literal_representer)


# ---------- 노드 id ----------
N_START = "1751000000000"
N_HTTP = "1751000000001"
N_LEAD = "1751000000010"
N_IDENTITY = "1751000000020"
N_HIGHLIGHTS = "1751000000030"
N_AUDIENCE = "1751000000040"
N_CONTENT = "1751000000050"
N_CLOSING = "1751000000060"
N_SIGNATURE = "1751000000070"
N_CODE = "1751000000099"
N_END = "1751000000100"


# ---------- 프롬프트 ----------
COMMON = """너는 인스타그램 크리에이터를 광고주에게 소개하는 세일즈 리포트에 들어갈 글을 쓰는 작가다.

[숫자·근거]
- 숫자를 다시 읽어주는 문장("팔로워가 7만명입니다") 금지 — 숫자는 이미 리포트에 표·게이지로 다 나와 있다.
  숫자는 "그래서 그게 무슨 뜻인지"를 말할 때만 최대 1~2개 인용해라.
- 데이터에 없는 사실을 지어내지 마라(신뢰 훼손). 단, 데이터가 암시하는 것을 해석/추론/상상하는 건 네 역할이다.
- 과장 광고 카피 톤("무조건 성공!", "완벽한!") 금지. 근거 있는 자신감 있는 톤.

[톤·문체]
- 문체는 정중한 '~습니다/~합니다'체로 통일. (단 lead_headline과 ai_highlights의 제목은 명사구 헤드라인 톤 허용)
- 협찬이 아닌 콘텐츠는 "오가닉" 또는 "비협찬"으로만 부른다. "유기농"/"유기적" 금지.

[형식 — 매우 중요]
- 마크다운 문법(#, ##, -, *, **, 백틱, 표, --- 구분선) 절대 금지 — 이 리포트엔 마크다운 렌더러가 없어 기호가 그대로 노출된다.
- 출력 첫 글자부터 곧바로 본문(또는 지정 형식)이어야 한다. 슬롯 이름/라벨(예: '# audience_persona', 'CLOSING:')을
  앞이나 중간에 절대 붙이지 마라. 문단 사이에 '---' 같은 구분선을 넣지 마라.
- 지정된 출력 형식(길이·구분자)을 정확히 지켜라. Code 노드가 이 형식을 그대로 파싱한다.
- 설명·인사말·라벨 반복 없이 본문/지정 형식만 출력해라."""

MARKER_NOTE = ("\n[강조 마커] 제목에서 가장 핵심인 한 구절을 *별표*로 감쌀 수 있다(예: *단단한 자존감*). "
               "그 구절이 형광펜으로 강조된다. 한 제목에 최대 1개만, 안 써도 된다. 별표는 강조 표시 전용이며 "
               "그 외 용도로 * 를 쓰지 마라.")

# 창작형 슬롯에 붙이는 '생생함·구체성' 지침 — 실제 세일즈 담당자가 손으로 쓴 소개서 톤을 목표로.
VIVID = """

[생생함·구체성 — 사람이 손으로 쓴 크리에이터 소개서처럼]
목표 톤(실제 담당자 예시): "긍정 바이브에 털털하게 잘 먹는 브이로그", "이사 준비 과정을 함께 보여줘 일상을
가까이 느끼게 함", "자막이 은은하게 웃기고 최신 밈을 잘 녹임", "싸운 모습·리얼한 일상까지 브이로그에 담아
공감을 삼", "N차 협업 브랜드가 많아 구독자도 신뢰하고 제품을 눈여겨봄". 이렇게 구체적이고 체감되는 특징을 써라.

- 추상적 형용사("좋은 콘텐츠", "매력적", "퀄리티 높은", "영향력 있는")로 때우지 마라. 관찰 가능한 구체를 써라 —
  근거는 반드시 데이터 안에서: profile.description, top_posts의 실제 캡션 문구·소재, top_hashtags·keywords,
  무드/페르소나/토픽 라벨, 어떤 게시물·포맷이 실제로 터졌는지(조회·좋아요), collaborations의 브랜드들.
- 시청자의 감정·경험 시점을 최소 한 번 넣어라: 구독자가 왜 이 사람을 좋아하고 어떤 순간에 반응하는지
  ("…같은 느낌", "…라는 인상"처럼 해석임을 드러내며 생생하게).
- collaborations가 2개 이상이면 그 이력 자체를 "이미 여러 브랜드가 검증한 신뢰"로 프레이밍하고, 브랜드명을 1~2개 실제로 언급해도 좋다.
- 광고주가 바로 써먹을 실전 힌트를 한 조각 붙여라: 이 사람과 어떻게 협업해야 하는지
  (예: "각 잡고 소구하기보다 일상에 자연스럽게 녹이는 기획", "어떤 포맷/톤이 맞는지").
- 절대 금지: 데이터로 확인되지 않는 시청각·행동 디테일을 지어내는 것(화면에서 본 적 없는 표정·행동·발언 날조 금지).
  '~로 보입니다/느껴집니다/드뭅니다'처럼 해석은 허용하되, 근거 없는 단정은 금지. 없으면 있는 근거로 다르게 써라."""

P_LEAD = COMMON + """

## 표지 한 줄 (lead_headline)
입력: profile.description, identity.user_type_label, identity.topic_label, identity.persona_label, identity.mood_axes(상위3)

출력 형식: 한 줄. 공백 포함 18~34자. 명사구로 끝내고 마침표 없음.
추가 지시: 처음 보는 광고주가 3초 안에 "이 사람 뭐 하는 사람이구나"를 잡게 하는 한 줄. 숫자 쓰지 말고 정체성/톤을 압축.
같은 단어를 한 줄에서 두 번 반복하지 마라. 이 문장은 표지 대문짝만한 헤드라인으로 쓰인다.
다루지 않을 것: 성과 숫자, 오디언스 통계, 협찬 얘기.""" + MARKER_NOTE

P_IDENTITY = COMMON + """

## 한 줄 정체성 (identity_claim)
입력: identity 전체(user_type/topic/persona label+reason, content_function/mood/topic/persona 축 상위6)

출력 형식: 아래 정확한 2줄 형식만 출력한다 (Code 노드가 CLAIM:/BODY: 로 파싱한다. 다른 말 금지):
CLAIM: <여러 축을 종합한 한 문장 정체성 주장 — 명사구로 끝, 40자 이내>
BODY: <그 정체성이 왜 강점인지 2~3문장, 공백 포함 180자 이내, '~습니다'체>

추가 지시: 주제·무드·페르소나·콘텐츠기능을 따로 나열하지 말고 "이 조합이 만드는 하나의 캐릭터"를 그려라.
CLAIM은 헤드라인처럼, BODY는 그 근거를 담담하게.
다루지 않을 것: 오디언스(audience_persona 담당), 성과·협찬 숫자(content_read 담당), 캠페인 제안(closing 담당).""" + MARKER_NOTE

P_HIGHLIGHTS = COMMON + """

## AI 강조 포인트 3개 (ai_highlights) — 자유도 90 : 근거 10 ★리포트의 핵심
입력: 크리에이터 전체 데이터(JSON). 특히 잘 읽을 것 — profile.description, top_posts(실제 캡션/조회/좋아요/댓글),
top_hashtags, metrics.keywords, identity(무드/페르소나/토픽/콘텐츠기능 라벨), collaborations(협업 브랜드), metrics의 포맷별 성과.

역할: 실제 세일즈 담당자가 이 크리에이터를 브랜드에 손수 소개하듯, 가장 강조할 포인트 3개를 스스로 골라 쓴다.
무엇을 강조할지 고정 슬롯이 없다 — 크리에이터마다 완전히 다른 3가지여야 한다. 예시(얽매이지 말 것): 어떤 바이브·성격인지,
어떤 말투/자막/편집 센스가 있는지, 어떤 일상 순간을 보여주는지, 협찬을 어떻게 녹이는지, 어떤 콘텐츠가 실제로 터지는지,
N차 협업 신뢰가 있는지, 팬덤 결속은 어떤지 등. 이 3개는 리포트에서 가장 눈에 띄는 컬러 카드(스토리의 챕터)에 크게 들어간다.

출력 형식: 아래 형식으로 정확히 3줄. 각 줄은 파이프(|)로 4부분을 나눈다 (Code 노드가 파싱):
HIGHLIGHT: <제목: 명사구 헤드라인, 30자 이내> | <본문: 3~4문장, 공백 포함 260자 이내, '~습니다'체> | <한줄 임팩트: 광고주 실전 힌트 1문장, 65자 이내> | evidence:<이 강조점을 뒷받침하는 근거 블록 id들, 쉼표로>

[근거 블록 메뉴 — 4번째 칸에 이 id들만 골라 쓴다]
리포트는 2단 구성이다. 각 강조점 아래에는 그 주장을 실제로 뒷받침하는 '근거 블록'만 붙고, 나머지는 2차(그 외 데이터)로 빠진다.
그러니 각 강조점마다 그것을 가장 잘 증명하는 블록 1~3개를 골라라:
- identity   : 콘텐츠 성격·무드·페르소나·토픽 축 + 키워드 (정체성/캐릭터 주장의 근거)
- audience   : 성별·연령·국가 분포 + 대표 팔로워 상 (오디언스 주장의 근거)
- performance: 오가닉 vs 협찬 릴스 비교 + 동종 대비 백분위 (성과/반응 주장의 근거)
- content_mix: 릴스/피드 비중 + 최신 발행일 (콘텐츠 운영/발행 주장의 근거)
- brands     : 협업 브랜드 로고 + 광고 산업 + PPL (신뢰/협업 이력 주장의 근거)
- growth     : 동종 대비 3개월 성장률 등급 (성장세 주장의 근거)
- top_posts  : 인기 게시물 썸네일 (어떤 콘텐츠가 터졌나 주장의 근거)
- hashtags   : 대표 해시태그

추가 지시:
- 세 포인트는 서로 다른 각도여야 한다(같은 얘기를 세 번 변주 금지). 예: 하나는 화자의 개성·바이브, 하나는 콘텐츠/협찬 방식,
  하나는 팬덤·오디언스 관계처럼.
- 본문은 손글씨 소개서처럼 구체적이고 체감되게. top_posts 캡션에서 실제 소재·문구를 끌어오고, 협업 브랜드가 여럿이면 신뢰로 프레이밍.
- 세 번째 칸(한줄 임팩트)은 "그래서 이 사람과 어떻게 협업하면 되는지"의 실전 힌트다(예: 각 잡고 소구보다 자연스럽게 녹이기).
- 4번째 칸 evidence는 그 강조점이 **실제로 말하는 내용과 직접 관련된 블록만** 골라라(억지로 다 넣지 말 것). 한 블록은 한 강조점에만 배정되니, 서로 겹치지 않게 나눠 가진다.
- 각 줄은 반드시 'HIGHLIGHT: '로 시작하고 네 부분을 ' | ' 로만 나눈다. 본문/임팩트 안에서 | 를 쓰지 마라.""" + VIVID + MARKER_NOTE

P_AUDIENCE = COMMON + """

## 오디언스 대표 인물 상상 (audience_persona) — 자유도 80 : 근거 20
입력: audience 전체(성별/연령/국가 + 각 reason), identity.topic_label

출력 형식: 1문단 (3~4문장, 공백 포함 220자 이내). 마침표로 끝. 마커/마크다운 없음.
추가 지시: 이 팔로워층의 "대표 인물 한 명"을 생생하게 묘사해라(이름은 짓지 말 것). 나이대·상황·이 계정을 왜
팔로우하고 어떤 순간에 반응하는지까지 상상해서 서술. 가장 창작 자유도가 높은 슬롯이다. '~습니다'체 유지.
다루지 않을 것: 크리에이터 본인 정체성(identity_claim), 성과 숫자. 철저히 "보는 사람" 시점으로만.""" + VIVID

P_CONTENT = COMMON + """

## 협찬/오가닉 성과 해석 (content_read) — 근거 60 : 자유 40
입력: metrics 객체(ugwanggi가 최근 10개 게시물로 계산한 값 + 동종 대비 백분위/등급). 핵심 필드:
  avg_views_last_10_org_reel / avg_views_last_10_ad_reel (오가닉·협찬 릴스 평균 조회)
  engagement_pct_last_10_org_reel / _ad_reel (릴스 참여율)
  avg_likes_last_10_org_feed (피드 평균 좋아요), 각 값의 *_percentile_band (TOP_5/TOP_10/TOP_25/ABOVE_MEDIAN/BELOW_MEDIAN)

출력 형식: 1~2문장 (공백 포함 170자 이내). 마커/마크다운 없음.
추가 지시: 오가닉 vs 협찬 성과 차이를 해석하는 자리다. "동종 대비 상위권(예: 오가닉 릴스 조회 TOP 10%)"이라는
백분위 강점을 적극 활용하고, 협찬이 오가닉보다 낮으면 정직하게 쓰되 "그래서 광고주가 어떤 포맷/톤으로 협업하면
되는지" 실마리를 한 문장 붙여라. 협찬 외는 "오가닉"으로 부른다("유기농" 금지). 없는 지표는 지어내지 마라."""

P_SIGNATURE = COMMON + """

## 콘텐츠 캐릭터 종합 해석 (signature_read) — 근거 45 : 자유 55
입력: identity 전체(user_type/topic/mood/persona/content_function 라벨+축), metrics.keywords(대표 키워드)

출력 형식: 3~4문장 (공백 포함 300자 이내). 마커/마크다운 없음.
추가 지시: 콘텐츠 역할·무드·페르소나·토픽·키워드를 따로 나열하지 말고, 이 축들이 합쳐져 만드는 "하나의 콘텐츠
캐릭터"를 그려라. identity_claim(한 줄 정체성)과 중복되지 않게 — 여기선 그 조합이 만드는 화면의 질감·톤·시청
경험을 더 구체적으로 묘사한다. '~습니다'체.
다루지 않을 것: 오디언스 묘사(audience_persona 담당), 성과 숫자(content_read 담당).""" + VIVID

P_CLOSING = COMMON + """

## 마무리 종합 + 캠페인 제안 (closing) — 앞의 모든 것을 종합
입력: 크리에이터 전체 데이터(JSON) 핵심 수치(profile/benchmark/identity/content_performance)

출력 형식: 2~3문장 (공백 포함 240자 이내). 마커/마크다운 없음.
추가 지시: 광고주가 최종적으로 "그래서 이 사람과 뭘 하면 좋을까"에 답하는 결론부다. 시장 내 포지셔닝(예: 니치에서
신뢰받는 미드티어)을 한 문장으로 짚고, 이 크리에이터의 content_function/persona에 맞는 구체적 캠페인 포맷을
1~2개 제안해라(예: 개인 서사형 릴스, 루틴 시리즈 등). 앞 슬롯 문장을 그대로 복사하지 말고 새로 종합할 것.""" + VIVID

USER_MSG = "아래는 이 크리에이터의 전체 데이터(JSON)다. 위 지시에 필요한 필드만 참고해서 써라.\n\n{{#" + N_HTTP + ".body#}}"


# ---------- Code 노드 본문 만들기 ----------
def build_code_body() -> str:
    with open(os.path.join(HERE, "creator_report_template_storyline.html"), encoding="utf-8") as f:
        template = f.read()
    with open(os.path.join(HERE, "assemble_html_storyline.py"), encoding="utf-8") as f:
        src = f.read()

    # 모듈 docstring 제거 → import 부터
    src = src[src.index("import json"):]
    # Dify main() 은 template_html 인자가 없고 TEMPLATE_HTML 상수를 쓴다
    src = src.replace("    template_html: str,\n", "")
    src = src.replace("    out = template_html\n", "    out = TEMPLATE_HTML\n")

    # imports 바로 뒤에 TEMPLATE_HTML 상수 주입
    marker = "import re\n"
    idx = src.index(marker) + len(marker)
    template_const = "\n\nTEMPLATE_HTML = " + json.dumps(template, ensure_ascii=False) + "\n"
    code = src[:idx] + template_const + src[idx:]

    # literal block 안정화를 위해 라인 끝 공백 제거
    code = "\n".join(line.rstrip() for line in code.splitlines())
    return code


# ---------- 노드/엣지 빌더 ----------
def _node(nid, x, y, w, h, data):
    return {
        "id": nid, "type": "custom",
        "position": {"x": x, "y": y}, "positionAbsolute": {"x": x, "y": y},
        "width": w, "height": h, "selected": False,
        "sourcePosition": "right", "targetPosition": "left",
        "data": data,
    }


def _llm_node(nid, x, y, title, desc, system_prompt, temperature):
    return _node(nid, x, y, 260, 150, {
        "type": "llm", "title": title, "desc": desc,
        "model": {
            "provider": "langgenius/anthropic/anthropic",
            "name": "claude-sonnet-4-5-20250929",
            "mode": "chat",
            "completion_params": {"temperature": temperature},
        },
        "prompt_template": [
            {"role": "system", "text": Literal(system_prompt)},
            {"role": "user", "text": Literal(USER_MSG)},
        ],
        "context": {"enabled": False, "variable_selector": []},
        "vision": {"enabled": False},
        "variables": [],
        "selected": False,
    })


def _edge(source, target, source_type, target_type):
    return {
        "id": f"{source}-source-{target}-target",
        "type": "custom",
        "source": source, "sourceHandle": "source",
        "target": target, "targetHandle": "target",
        "selected": False, "zIndex": 0,
        "data": {"sourceType": source_type, "targetType": target_type, "isInIteration": False},
    }


def build():
    code_body = build_code_body()

    start = _node(N_START, 30, 400, 243, 140, {
        "type": "start", "title": "시작",
        "desc": "인스타그램 크리에이터 아이디와 API 키를 입력받는다",
        "variables": [
            {"variable": "creator_user_id", "label": "크리에이터 인스타그램 아이디",
             "type": "text-input", "required": True, "max_length": 100, "options": []},
            {"variable": "api_key", "label": "리포트 API 키",
             "type": "text-input", "required": True, "max_length": 200, "options": []},
        ],
        "selected": False,
    })

    http = _node(N_HTTP, 333, 400, 243, 140, {
        "type": "http-request", "title": "크리에이터 리포트 데이터 조회",
        "desc": "data-dify-external-api의 /creators/{user_id}/report 호출",
        "variables": [], "method": "get",
        "url": BASE_URL + "/creators/{{#" + N_START + ".creator_user_id#}}/report",
        "headers": "X-API-Key:{{#" + N_START + ".api_key#}}",
        "params": "",
        "body": {"type": "none", "data": []},
        "authorization": {"type": "no-auth", "config": None},
        "timeout": {"max_connect_timeout": 0, "max_read_timeout": 0, "max_write_timeout": 0},
        "selected": False,
    })

    lead = _llm_node(N_LEAD, 636, 120, "표지 한 줄", "인사이트 생성: lead_headline", P_LEAD, 0.7)
    identity = _llm_node(N_IDENTITY, 636, 300, "한 줄 정체성", "인사이트 생성: identity_claim", P_IDENTITY, 0.6)
    highlights = _llm_node(N_HIGHLIGHTS, 636, 480, "AI 강조 포인트 3개", "인사이트 생성: ai_highlights (자유도 90)", P_HIGHLIGHTS, 0.85)
    audience = _llm_node(N_AUDIENCE, 636, 660, "오디언스 대표 인물", "인사이트 생성: audience_persona", P_AUDIENCE, 0.8)
    content = _llm_node(N_CONTENT, 636, 840, "협찬/성과 해석", "인사이트 생성: content_read", P_CONTENT, 0.6)
    closing = _llm_node(N_CLOSING, 636, 1020, "마무리 종합", "인사이트 생성: closing", P_CLOSING, 0.7)
    signature = _llm_node(N_SIGNATURE, 636, 1200, "콘텐츠 캐릭터 해석", "인사이트 생성: signature_read", P_SIGNATURE, 0.75)

    code = _node(N_CODE, 980, 500, 260, 190, {
        "type": "code", "title": "HTML 리포트 조립(스토리라인)",
        "desc": "creator_report_template_storyline.html 을 JSON + 6개 인사이트로 치환. 결정적 Python.",
        "code_language": "python3",
        "code": Literal(code_body),
        "variables": [
            {"variable": "report_json", "value_selector": [N_HTTP, "body"]},
            {"variable": "lead_headline", "value_selector": [N_LEAD, "text"]},
            {"variable": "identity_claim", "value_selector": [N_IDENTITY, "text"]},
            {"variable": "ai_highlights", "value_selector": [N_HIGHLIGHTS, "text"]},
            {"variable": "audience_persona", "value_selector": [N_AUDIENCE, "text"]},
            {"variable": "content_read", "value_selector": [N_CONTENT, "text"]},
            {"variable": "closing", "value_selector": [N_CLOSING, "text"]},
            {"variable": "signature_read", "value_selector": [N_SIGNATURE, "text"]},
        ],
        "outputs": {"html": {"type": "string", "children": None}},
        "selected": False,
    })

    end = _node(N_END, 1290, 500, 243, 114, {
        "type": "end", "title": "종료", "desc": "",
        "outputs": [{"variable": "html", "value_selector": [N_CODE, "html"]}],
        "selected": False,
    })

    llm_ids = [N_LEAD, N_IDENTITY, N_HIGHLIGHTS, N_AUDIENCE, N_CONTENT, N_CLOSING, N_SIGNATURE]
    edges = [_edge(N_START, N_HTTP, "start", "http-request")]
    for lid in llm_ids:
        edges.append(_edge(N_HTTP, lid, "http-request", "llm"))
    edges.append(_edge(N_HTTP, N_CODE, "http-request", "code"))
    for lid in llm_ids:
        edges.append(_edge(lid, N_CODE, "llm", "code"))
    edges.append(_edge(N_CODE, N_END, "code", "end"))

    app = {
        "app": {
            "name": "크리에이터 세일즈 리포트 (스토리라인 + AI 강조 3종)",
            "description": "인스타그램 크리에이터 아이디를 받아 광고주 소개용 HTML 리포트를 생성한다. "
                           "데이터 추출/치환은 결정적 Code 노드가, 프로즈는 3개의 좁은 LLM 노드가 담당. "
                           "레이아웃은 설득 논리 스토리라인, AI 강조 3개가 스토리의 챕터.",
            "mode": "workflow", "icon": "📈", "icon_background": "#FFEAD5",
            "use_icon_as_answer_icon": False,
        },
        "kind": "app", "version": "0.1.5",
        "workflow": {
            "conversation_variables": [],
            "environment_variables": [],
            "features": {
                "file_upload": {"image": {"enabled": False, "number_limits": 3,
                                          "transfer_methods": ["local_file", "remote_url"]}},
                "opening_statement": "",
                "retriever_resource": {"enabled": False},
                "sensitive_word_avoidance": {"enabled": False},
                "speech_to_text": {"enabled": False},
                "suggested_questions": [],
                "suggested_questions_after_answer": {"enabled": False},
                "text_to_speech": {"enabled": False, "language": "", "voice": ""},
            },
            "graph": {
                "nodes": [start, http, lead, identity, highlights, audience, content, closing, signature, code, end],
                "edges": edges,
                "viewport": {"x": 0, "y": 0, "zoom": 0.7},
            },
        },
    }

    out_path = os.path.join(HERE, "creator_report_storyline_workflow.yml")
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(app, f, Dumper=yaml.Dumper, default_flow_style=False,
                  allow_unicode=True, sort_keys=False, width=10 ** 9)
    return out_path


if __name__ == "__main__":
    path = build()
    print("wrote", path)
