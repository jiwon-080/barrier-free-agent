# 결과물: ../fss_product.json 으로 제작
"""
금융감독원 금융상품통합비교공시 API 수집 스크립트
수집 대상: 예금 / 적금 / 연금저축(IRP) / ISA
출력: data/rag/fss_product.json
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FSS_API_KEY = os.getenv("FSS_API_KEY")
BASE_URL = "http://finlife.fss.or.kr/finlifeapi"
OUTPUT_PATH = Path(__file__).parent.parent / "fss_product.json"

# 은행권 코드
TOP_FIN_GRP_NO = "020000"

ENDPOINTS = {
    "deposit": f"{BASE_URL}/depositProductsSearch.json",    # 예금
    "saving":  f"{BASE_URL}/savingProductsSearch.json",     # 적금
    "annuity": f"{BASE_URL}/annuityProductsSearch.json",    # 연금저축
    "isa":     f"{BASE_URL}/isaProductsSearch.json",        # ISA
}

# 수집할 baseList 필드
BASE_FIELDS = [
    "fin_prdt_cd",   # 상품코드
    "kor_co_nm",     # 금융사명
    "fin_prdt_nm",   # 상품명
    "join_way",      # 가입방법 (영업점/인터넷/스마트폰 등)
    "join_member",   # 가입대상
    "join_deny",     # 가입제한 (1:없음, 2:서민전용, 3:일부제한)
    "spcl_cnd",      # 우대조건
    "etc_note",      # 기타 유의사항
    "max_limit",     # 최고한도
]

# 수집할 optionList 필드
OPTION_FIELDS = [
    "fin_prdt_cd",      # 상품코드 (baseList 연결용)
    "intr_rate_type_nm",# 금리유형명
    "save_trm",         # 저축기간(개월)
    "intr_rate",        # 기본금리
    "intr_rate2",       # 최고우대금리
]


def fetch_products(product_type: str, endpoint: str) -> tuple[list, list]:
    """FSS API에서 전체 페이지 수집 후 baseList, optionList 반환"""
    all_base = []
    all_options = []
    page = 1

    while True:
        params = {
            "auth": FSS_API_KEY,
            "topFinGrpNo": TOP_FIN_GRP_NO,
            "pageNo": page,
        }
        try:
            resp = requests.get(endpoint, params=params, timeout=15)
            data = resp.json().get("result", {})
        except Exception as e:
            print(f"  [오류] {product_type} 페이지 {page}: {e}")
            break

        err_cd = data.get("err_cd", "")
        if err_cd != "000":
            print(f"  [API 오류] {data.get('err_msg')}")
            break

        base_list = data.get("baseList", [])
        option_list = data.get("optionList", [])

        if not base_list:
            break

        # 필요한 필드만 추출
        for item in base_list:
            all_base.append({f: item.get(f, "") for f in BASE_FIELDS})

        for item in option_list:
            all_options.append({f: item.get(f, "") for f in OPTION_FIELDS})

        print(f"  페이지 {page}: 상품 {len(base_list)}개")
        page += 1
        time.sleep(0.3)  # API 과부하 방지

    return all_base, all_options


def merge_products(base_list: list, option_list: list) -> list:
    """baseList + optionList를 fin_prdt_cd 기준으로 합침"""
    option_map: dict[str, list] = {}
    for opt in option_list:
        cd = opt["fin_prdt_cd"]
        option_map.setdefault(cd, []).append({
            k: v for k, v in opt.items() if k != "fin_prdt_cd"
        })

    result = []
    for base in base_list:
        cd = base["fin_prdt_cd"]
        result.append({**base, "options": option_map.get(cd, [])})

    return result


def main():
    output = {}

    for product_type, endpoint in ENDPOINTS.items():
        print(f"\n[{product_type}] 수집 중...")
        base_list, option_list = fetch_products(product_type, endpoint)
        merged = merge_products(base_list, option_list)
        output[product_type] = merged
        print(f"  -> 총 {len(merged)}개 상품 수집 완료")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in output.values())
    print(f"\n✅ 저장 완료: {OUTPUT_PATH}")
    print(f"   총 {total}개 상품 (예금: {len(output.get('deposit',[]))}, "
          f"적금: {len(output.get('saving',[]))}, "
          f"연금저축: {len(output.get('annuity',[]))}, "
          f"ISA: {len(output.get('isa',[]))})")


if __name__ == "__main__":
    main()
