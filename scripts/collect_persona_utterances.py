"""네이버 지식iN 금융 발화 수집 → LLM이 말투 기준으로 페르소나 대표 발화 선별.

목적: 페르소나 라우팅용 퓨샷 예시 확보.
      키워드 일치가 아니라 '이 페르소나가 실제로 이렇게 말한다'는
      말투·표현 패턴을 보여주는 발화를 선별한다.

사용법:
    uv run python scripts/collect_persona_utterances.py              # 전체
    uv run python scripts/collect_persona_utterances.py --persona 고령층
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

NAVER_ID = os.environ["NAVER_CLIENT_ID"]
NAVER_SECRET = os.environ["NAVER_CLIENT_SECRET"]

OUT_DIR = Path("data/personas")
FEWSHOT_FILE = OUT_DIR / "few_shot_examples.json"

# ── 페르소나 설정 ──────────────────────────────────────────────────────────────
# target: 최종 선별 수
# keywords: 수집용 검색어 (해당 페르소나가 실제로 올릴 법한 질문 유형)
# speech_style: LLM 선별 기준 — 말투·표현 특성 중심으로 기술

PERSONA_CONFIG: dict[str, dict] = {
    "고령층": {
        "target": 10,
        "keywords": [
            "국민연금 수령 신청",
            "기초연금 신청 서류",
            "노령연금 수령 시기",
            "퇴직 후 연금 받는데",
            "은퇴 후 자금 관리",
            "60대 예금 추천",
            "손주 명의 통장",
            "정년퇴직 후 재테크",
            "노후 건강보험료",
        ],
        "speech_style": """이 페르소나(60대 이상 고령층)의 말투·표현 특성:
- 나이·연령대·생년을 직접 명시 ("저 이제 만 65세인데요", "1958년생이고요", "67세 노인입니다")
- 존댓말이지만 맞춤법·띄어쓰기가 다소 어색하거나 구어적 ("받을수있나요", "어떻게되나요")
- 디지털·금융 용어에 낯설어하는 표현 ("처음이라 어렵네요", "잘 모르겠어요", "막막해서요")
- 연금·은퇴·손주 등 노년 특유 상황 언급
- 장문 설명 대신 핵심 질문 위주, 가끔 "자세히 알려주시면 감사하겠습니다" 같은 정중한 마무리""",
    },
    "사회초년생": {
        "target": 5,
        "keywords": [
            "사회초년생 재테크 시작",
            "청년도약계좌 가입",
            "첫 직장 연말정산",
            "주린이 주식 시작",
            "알바 퇴직금",
            "대학생 알바 세금",
            "20대 보험 추천",
            "청년주택드림통장",
        ],
        "speech_style": """이 페르소나(20대 초중반, 사회초년생/학생)의 말투·표현 특성:
- 나이·상황을 직접 언급 ("저 22살인데요", "이제 막 취직했는데", "대학생이고요")
- 반말체나 구어적 줄임말 ("ㅠㅠ", "뭐부터 해야하나요", "완전 처음이라서요")
- '처음', '입문', '모르겠어요' 등 금융 경험 없음을 솔직히 표현
- 청년 전용 상품명을 직접 언급하거나, 소액 자금("알바비", "용돈")으로 시작하는 맥락
- 친구 추천·인터넷 보고 알게 됐다는 식의 맥락 많음""",
    },
    "주부": {
        "target": 5,
        "keywords": [
            "남편 연말정산 대신",
            "배우자 소득공제",
            "어린이보험 추천",
            "아이 청약통장",
            "가계 절약 재테크",
            "남편 퇴직금 수령",
            "육아 중 보험",
            "주부 소득 없을 때 연금",
        ],
        "speech_style": """이 페르소나(30~40대 주부, 가계 담당)의 말투·표현 특성:
- 남편/배우자/아이를 주어로 질문 ("남편이 다음 달 퇴직하는데요", "아이 보험 들어주려고요")
- 본인이 직접 겪는 것보다 가계 전체 상황을 대리 설명하는 경우 많음
- "저는 소득이 없고요", "남편 혼자 벌어서요" 같은 외벌이·육아 맥락
- 자녀 교육·보험·청약 등 가계 금융 관리자 역할 강조
- 일상 생활비 절약, 가계부 관리 관점에서 질문""",
    },
    "직장인": {
        "target": 5,
        "keywords": [
            "연말정산 환급 조건",
            "퇴직금 계산 방법",
            "중도퇴사 처리 절차",
            "직장인 절세 방법",
            "사대보험 미납 신고",
            "연차 미사용 수당 청구",
            "IRP 퇴직연금 납입",
            "월급 세전 세후 계산",
        ],
        "speech_style": """이 페르소나(20~30대 직장 근로자)의 말투·표현 특성:
- 재직·퇴사 상황을 구체적으로 설명 ("재직 중인데요", "이번 달에 퇴사 예정이고요")
- 급여·연봉·세금을 수치로 제시 ("세전 300이고요", "연봉 4천인데")
- 연말정산·퇴직금·연차 등 근로소득 관련 용어를 자연스럽게 사용
- 회사 상황을 함께 설명 ("중소기업인데요", "회사에서 IRP 가입시켜줬는데")
- 비교적 간결하고 목적 지향적인 질문 스타일""",
    },
    "중장년": {
        "target": 5,
        "keywords": [
            "40대입니다 재테크",
            "50대입니다 노후",
            "40대 남자 보험",
            "40대 여자 보험",
            "50대 연금 준비",
            "자녀 증여 40대",
            "40대 암보험",
            "50대 퇴직 준비",
            "40대 재테크 방법",
            "50대 재무 설계",
        ],
        "age_hints": ["40대", "50대", "41세", "42세", "43세", "44세", "45세",
                      "46세", "47세", "48세", "49세", "51세", "52세", "53세",
                      "54세", "55세", "56세", "57세", "마흔", "쉰"],
        "speech_style": """이 페르소나(40~50대 중장년)의 말투·표현 특성:
- 나이를 직접 언급 ("저 40대 중반인데요", "50대 초반입니다", "47세 직장인인데요")
- 노후 준비·보험 리모델링·자녀 독립 등 중장년 특유 재무 전환점 고민
- "이제 슬슬 준비해야 할 것 같아서요", "늦지 않았을까요?" 같은 표현
- 안정적이고 구체적인 문체, 상황을 길게 설명하는 경향
- 부부 자산, 자녀 증여, 보험 점검 등 가족 단위 자산 관리 맥락
- 선별 완화: 40대·50대 나이가 title이나 description에 직접 명시된 경우 우선 선별""",
    },
}

# ── 답변 텍스트 필터 ──────────────────────────────────────────────────────────
ANSWER_SIGNALS = [
    "질문자님", "결론부터", "말씀드리면", "답변 드립니다",
    "정리해드리면", "설명드리면", "참고하시기 바랍니다", "도움이 되셨으면",
    "하시면 됩니다", "하셔야 합니다", "이점 참고", "이상입니다",
    "축하드립니다", "쾌차하시길",
    "#60대", "#70대", "#80대", "#노후",
]


def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def is_answer_text(desc: str) -> bool:
    return any(sig in desc for sig in ANSWER_SIGNALS)


# ── 수집 ─────────────────────────────────────────────────────────────────────
def collect_for_persona(persona: str) -> list[dict]:
    keywords = PERSONA_CONFIG[persona]["keywords"]
    seen_links: set[str] = set()
    results: list[dict] = []

    for kw in keywords:
        try:
            r = requests.get(
                "https://openapi.naver.com/v1/search/kin.json",
                headers={
                    "X-Naver-Client-Id": NAVER_ID,
                    "X-Naver-Client-Secret": NAVER_SECRET,
                },
                params={"query": kw, "display": 100, "sort": "date"},
                timeout=10,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"    수집 오류 [{kw}]: {e}")
            continue

        for item in r.json().get("items", []):
            link = item.get("link", "")
            if link in seen_links:
                continue
            seen_links.add(link)

            title = clean_html(item.get("title", ""))
            desc  = clean_html(item.get("description", ""))

            if not title:
                continue
            if is_answer_text(desc):
                continue

            results.append({"title": title, "description": desc, "link": link})

    # age_hints 있는 페르소나는 해당 단서가 포함된 항목을 앞으로 정렬
    age_hints = PERSONA_CONFIG[persona].get("age_hints")
    if age_hints:
        def has_age_hint(item: dict) -> bool:
            text = item["title"] + " " + item.get("description", "")
            return any(h in text for h in age_hints)
        results.sort(key=lambda x: 0 if has_age_hint(x) else 1)

        time.sleep(0.2)

    print(f"  {persona} 후보 수집: {len(results)}개")
    return results


# ── LLM 선별 (말투 중심) ──────────────────────────────────────────────────────
_SELECTION_PROMPT = """\
당신은 금융 상담 AI의 페르소나 라우팅 시스템을 위한 퓨샷 예시를 선별합니다.

목적: 사용자 발화를 보고 어떤 페르소나인지 판단하기 위한 대표 예시.
      따라서 주제·키워드 일치보다 **이 페르소나가 실제로 이렇게 말한다는 말투·표현 방식**이 중요합니다.

페르소나: {persona}

이 페르소나의 말투·표현 특성:
{speech_style}

아래 후보 발화 목록에서, 위 말투 특성을 가장 잘 보여주는 것 {target}개를 골라주세요.

선별 기준:
1. 이 페르소나임을 나이·상황·말투·어휘로 **자연스럽게** 식별할 수 있어야 함
2. 금융 질문이어야 함 (상담·법률·의료 질문 제외)
3. description이 답변 텍스트인 것 제외
4. 비슷한 내용은 하나만 선택 (다양성 우선)

응답 형식: JSON 배열만 출력. 각 항목: {{"title": "...", "description": "...", "reason": "왜 이 발화가 말투 특성을 잘 보여주는지 한 줄"}}

후보 목록:
{candidates}
"""


def llm_select(candidates: list[dict], persona: str) -> list[dict]:
    target = PERSONA_CONFIG[persona]["target"]
    speech_style = PERSONA_CONFIG[persona]["speech_style"]
    client = genai.Client()
    results: list[dict] = []

    for i in range(0, len(candidates), 300):
        batch = candidates[i:i + 300]
        items_text = "\n".join(
            f"{j+1}. 제목: {it['title']}\n   설명: {it.get('description','')[:200]}"
            for j, it in enumerate(batch)
        )
        prompt = _SELECTION_PROMPT.format(
            persona=persona,
            speech_style=speech_style,
            target=target,
            candidates=items_text,
        )
        try:
            resp = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.3),
            )
            text = resp.text.strip()
            text = re.sub(r"^```(?:json)?", "", text).rstrip("```").strip()
            selected = json.loads(text)
        except Exception as e:
            m = re.search(r"\[[\s\S]*\]", text if "text" in dir() else "")
            try:
                selected = json.loads(m.group(0)) if m else []
            except Exception:
                selected = []
                print(f"    경고: 배치 {i//300+1} 파싱 실패 ({e})")

        for s in selected:
            s["persona"] = persona
        results.extend(selected)
        print(f"    LLM 배치 {i//300+1}: {len(batch)}개 후보 → {len(selected)}개 선별")
        time.sleep(1.5)

    # target 초과 시 앞에서 자름
    return results[:target]


# ── 페르소나 파이프라인 ────────────────────────────────────────────────────────
def run_persona(persona: str) -> list[dict]:
    target = PERSONA_CONFIG[persona]["target"]
    print(f"\n=== {persona} (목표 {target}개) ===")
    candidates = collect_for_persona(persona)
    if not candidates:
        print(f"  후보 없음, 건너뜀")
        return []
    selected = llm_select(candidates, persona)
    print(f"  최종 선별: {len(selected)}개")
    return selected


# ── 엔트리포인트 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if "--persona" in args:
        idx = args.index("--persona")
        persona = args[idx + 1]
        if persona not in PERSONA_CONFIG:
            print(f"알 수 없는 페르소나: {persona}")
            print(f"가능: {list(PERSONA_CONFIG)}")
            sys.exit(1)

        # 기존 데이터에서 해당 페르소나만 교체
        existing = json.loads(FEWSHOT_FILE.read_text(encoding="utf-8")) if FEWSHOT_FILE.exists() else []
        others = [x for x in existing if x.get("persona") != persona]
        new_items = run_persona(persona)
        final = others + new_items

    else:
        # 전체 재수집
        final = []
        for persona in PERSONA_CONFIG:
            final.extend(run_persona(persona))

    FEWSHOT_FILE.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    dist = Counter(x.get("persona") for x in final)
    print(f"\n=== 저장 완료: 총 {len(final)}개 ===")
    for p, c in sorted(dist.items()):
        tgt = PERSONA_CONFIG.get(p, {}).get("target", "?")
        print(f"  {p}: {c}개 / 목표 {tgt}개")
