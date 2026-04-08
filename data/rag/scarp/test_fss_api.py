"""
금융감독원 API 키 유효성 확인 스크립트
FSS 금융상품통합비교공시 API - 예금 상품 조회 테스트
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

FSS_API_KEY = os.getenv("FSS_API_KEY")
BASE_URL = "http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json"

def test_fss_api():
    params = {
        "auth": FSS_API_KEY,
        "topFinGrpNo": "020000",  # 은행권
        "pageNo": 1,
    }

    print(f"API 키: {FSS_API_KEY[:8]}...")
    print(f"요청 URL: {BASE_URL}")
    print("요청 중...\n")

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()

        result = data.get("result", {})
        err_cd = result.get("err_cd", "")
        err_msg = result.get("err_msg", "")

        if err_cd == "000":
            base_list = result.get("baseList", [])
            print(f"✅ API 키 유효! 상품 {len(base_list)}개 조회됨")
            if base_list:
                print(f"\n첫 번째 상품 예시:")
                first = base_list[0]
                print(f"  금융사: {first.get('kor_co_nm')}")
                print(f"  상품명: {first.get('fin_prdt_nm')}")
        else:
            print(f"❌ API 오류 - 코드: {err_cd}, 메시지: {err_msg}")

    except requests.exceptions.ConnectionError:
        print("❌ 네트워크 연결 실패 - URL 또는 인터넷 연결 확인")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_fss_api()
