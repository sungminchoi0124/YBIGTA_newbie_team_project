"""네이버 영화 관람평(리뷰) JSON API 크롤러.

대상: 영화 '백룸(Backrooms, 2026, 네이버 영화 코드 251490)'의 관람평을
제공하는 네이버 내부 프록시 API(ts-proxy.naver.com/dcontent/nqapirender.nhn,
fileKey=movieKBPointAPI)를 직접 호출해 별점 · 작성일 · 리뷰 내용을 수집한다.

이 API는 네이버 검색결과 페이지에서 관람평 위젯을 스크롤할 때 브라우저가
호출하는 것과 동일한 엔드포인트이며, JSONP로 감싸인 JSON
({"html": "<li class=\"area_card _item\">...</li>...", "hasNext": true|false})을
반환한다. 응답 헤더에 access-control-allow-origin: *가 설정되어 있어
Selenium/브라우저 없이 requests만으로 직접 호출 가능하다.

네이버는 리뷰를 두 갈래로 나눠서 제공한다(실제 브라우저 Network 탭 캡처로
확인함).

1. 관람객(실관람, 티켓 인증) 리뷰 - u5="true", u3="newest"
   HTML에 <span class="lego_badge_movie_visit">관람객</span> 뱃지가 있고
   버튼 onclick이 "tabreal..." 로 시작한다.
2. 네티즌(비인증 방문자) 리뷰 - u5="", u3="sympathyScore"
   뱃지가 없고 버튼 onclick이 "tabvisitor..." 로 시작한다. 완전히 다른
   rating-id 집합을 가진 별도의 리뷰 풀이다.

두 풀 다 각각 hasNext=false로 끝나는 지점(약 300개 안팎)이 있어서, 500개
이상을 채우려면 두 풀을 모두 수집해 data-rating-id 기준으로 중복 제거한
뒤 합쳐야 한다. u2 파라미터가 페이지 번호 역할을 한다(1부터 시작).

엔드포인트나 파라미터가 바뀌면 개발자도구(F12) Network 탭에서
"nqapirender.nhn" 요청을 다시 확인해 API_URL/params를 갱신해야 한다.
"""
import json
import os
import random
import re
import time
from typing import Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger

API_URL = "https://ts-proxy.naver.com/dcontent/nqapirender.nhn"
REVIEW_ITEM_SELECTOR = "li.area_card._item"

# (소스 이름, u5 값, u3 값) - 두 리뷰 풀을 각각 이 파라미터로 호출한다.
REVIEW_TRACKS = [
    ("관람객", "true", "newest"),
    ("네티즌", "", "sympathyScore"),
]


class NaverCrawler(BaseCrawler):
    """네이버 영화 관람평 JSON API에서 리뷰를 수집하는 크롤러.

    Selenium으로 페이지를 스크롤하며 DOM을 파싱하는 대신, 관람평 위젯이
    내부적으로 호출하는 JSON API(movieKBPointAPI)를 페이지 단위로 직접
    호출해 리뷰 HTML 조각을 받아온 뒤 BeautifulSoup으로 파싱한다.
    관람객(실관람) 풀과 네티즌(비인증) 풀을 모두 수집해 합친다.
    """

    def __init__(
        self,
        output_dir: str,
        movie_code: str = "251490",
        min_reviews: int = 500,
        max_pages: int = 300,
    ) -> None:
        """NaverCrawler를 초기화한다.

        Args:
            output_dir: 크롤링 결과 csv를 저장할 디렉토리 경로.
            movie_code: 네이버 영화 코드 (백룸은 251490).
            min_reviews: 최소 수집 리뷰 개수.
            max_pages: 풀 하나당 API를 최대 몇 번까지 호출할지 (무한루프 방지용).
        """
        super().__init__(output_dir)
        self.movie_code = movie_code
        self.min_reviews = min_reviews
        self.max_pages = max_pages
        self.reviews: List[Dict[str, str]] = []
        self._seen_rating_ids: set[str] = set()
        self.logger = setup_logger(log_file="naver_crawler.log")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
                "Referer": (
                    "https://search.naver.com/search.naver"
                    "?where=nexearch&query=%EC%98%81%ED%99%94+%EB%B0%B1%EB%A3%B8+%ED%8F%89%EC%A0%90"
                ),
                "Accept": "*/*",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

    def start_browser(self) -> None:
        """이 크롤러는 JSON API를 직접 호출하므로 별도 브라우저가 필요 없다.

        BaseCrawler의 추상 메서드 계약을 만족시키기 위해 존재하며, 실제
        수집은 scrape_reviews에서 requests로 처리한다.
        """
        self.logger.info("API 직접 호출 방식이라 별도 브라우저를 실행하지 않습니다.")

    def _fetch_page(self, page: int, u5: str, u3: str) -> Optional[Dict]:
        """API에서 page번째 리뷰 묶음을 가져와 JSONP 래핑을 벗긴 JSON을 반환한다.

        Args:
            page: 1부터 시작하는 페이지 번호(API의 u2 파라미터).
            u5: 관람객 풀은 "true", 네티즌 풀은 "" (빈 문자열).
            u3: 관람객 풀은 "newest", 네티즌 풀은 "sympathyScore".

        Returns:
            {"html": "<li>...</li>...", "hasNext": bool} 형태의 dict.
            요청/파싱 실패 시 None.
        """
        callback = "_nqapirender_cb"
        params = {
            "where": "nexearch",
            "pkid": "68",
            "fileKey": "movieKBPointAPI",
            "u1": self.movie_code,
            "u5": u5,
            "u3": u3,
            "u4": "false",
            "u2": str(page),
            "_callback": callback,
        }
        try:
            resp = self.session.get(API_URL, params=params, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as exc:
            self.logger.warning(f"{page}페이지 요청 실패: {exc}")
            return None

        text = resp.text.strip()
        match = re.search(rf"{re.escape(callback)}\((.*)\);?\s*$", text, re.DOTALL)
        if not match:
            self.logger.warning(f"{page}페이지 응답 형식을 파싱하지 못했습니다: {text[:200]}")
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            self.logger.warning(f"{page}페이지 JSON 파싱 오류: {exc}")
            return None

    def _scrape_track(self, source: str, u5: str, u3: str) -> None:
        """리뷰 풀 하나(관람객 또는 네티즌)를 끝까지(또는 min_reviews까지) 수집한다."""
        page = 1
        new_in_track = 0
        while len(self.reviews) < self.min_reviews and page <= self.max_pages:
            data = self._fetch_page(page, u5=u5, u3=u3)
            if data is None:
                self.logger.info(f"[{source}] 요청이 실패해 이 풀의 수집을 종료합니다.")
                break

            soup = BeautifulSoup(data.get("html", ""), "html.parser")
            items = soup.select(REVIEW_ITEM_SELECTOR)

            new_found = 0
            for item in items:
                parsed = self._parse_item(item, source=source)
                if parsed is None:
                    continue
                rating_id = parsed.pop("_rating_id", None)
                if rating_id and rating_id in self._seen_rating_ids:
                    continue
                if rating_id:
                    self._seen_rating_ids.add(rating_id)
                self.reviews.append(parsed)
                new_found += 1
                new_in_track += 1

            self.logger.info(
                f"[{source}] {page}페이지 요청 완료, 전체 누적 {len(self.reviews)}/{self.min_reviews}개 "
                f"(이번 페이지 신규 {new_found}개, 이 풀 누적 {new_in_track}개)"
            )

            if len(self.reviews) >= self.min_reviews:
                break

            if not data.get("hasNext", False):
                self.logger.info(f"[{source}] hasNext=false, 이 풀의 리뷰를 모두 수집했습니다 (총 {new_in_track}개).")
                break

            page += 1
            # 사람이 스크롤하는 속도에 가깝게 요청 간격을 두어(2~4초 + 지터)
            # 짧은 시간에 몰아치는 요청으로 인한 안티봇 제한을 피한다.
            time.sleep(random.uniform(2.0, 4.0))

    def scrape_reviews(self) -> None:
        """관람객 풀과 네티즌 풀을 순서대로 수집해 min_reviews개 이상을 채운다."""
        for source, u5, u3 in REVIEW_TRACKS:
            if len(self.reviews) >= self.min_reviews:
                break
            self.logger.info(f"[{source}] 수집 시작")
            self._scrape_track(source, u5=u5, u3=u3)

        self.logger.info(f"총 {len(self.reviews)}개의 리뷰 수집 완료 (중복 제거 후)")

    def _parse_item(self, item: Tag, source: str) -> Optional[Dict[str, str]]:
        """리뷰 li 태그에서 별점 · 작성일 · 내용 · 부가정보를 추출한다.

        Args:
            item: BeautifulSoup으로 파싱된 <li class="area_card _item"> 태그.
            source: "관람객" 또는 "네티즌" - 어느 풀에서 가져온 리뷰인지 표시.

        Returns:
            {"score", "date", "content", "writer_id", "like_count",
            "dislike_count", "source", "_rating_id"}를 담은 dict. 필수 값
            (별점/날짜/내용) 중 하나라도 비어있으면 None을 반환해 해당
            항목을 건너뛴다. "_rating_id"는 중복 제거용 내부 키로, 호출부에서
            pop해서 사용한 뒤 최종 결과에는 포함하지 않는다.
        """
        def get_str(attr_name: str) -> str:
            val = item.get(attr_name)
            return "".join(val) if isinstance(val, list) else str(val or "")

        try:
            # 별점: div.area_text_box 안에서 '별점(10점 만점 중)' 스크린리더용
            # 텍스트(span.blind)를 제거하고 남는 숫자만 사용한다.
            score = ""
            score_box = item.select_one("div.area_text_box")
            if score_box is not None:
                blind = score_box.select_one("span.blind")
                if blind is not None:
                    blind.extract()
                score = score_box.get_text(strip=True)

            # 내용: data-report-title 속성을 우선 사용(가장 깔끔한 원문),
            # 없으면 span.desc._text에서 추출.
            content = get_str("data-report-title").strip()
            if not content:
                content_tag = item.select_one("span.desc._text")
                content = content_tag.get_text(strip=True) if content_tag else ""

            # 날짜: data-report-time 속성("20260527 19:07")을
            # "2026.05.27 19:07" 형태로 변환. 실패 시 화면에 보이는
            # dd.this_text_normal 텍스트로 대체.
            date = self._format_date(get_str("data-report-time").strip())
            if not date:
                date_tag = item.select_one("dl.cm_upload_info dd.this_text_normal")
                date = date_tag.get_text(strip=True) if date_tag else ""

            if not score or not content or not date:
                return None

            return {
                "score": score,
                "date": date,
                "content": content,
                "writer_id": get_str("data-report-writer-id"),
                "like_count": self._extract_count(item, "button._btn_upvote span._count_num"),
                "dislike_count": self._extract_count(item, "button._btn_downvote span._count_num"),
                "source": source,
                "_rating_id": get_str("data-rating-id"),
            }
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"리뷰 파싱 중 오류로 해당 항목을 건너뜁니다: {exc}")
            return None

    @staticmethod
    def _format_date(raw_time: str) -> str:
        """'20260527 19:07' 형태를 '2026.05.27 19:07'로 변환한다."""
        match = re.match(r"(\d{4})(\d{2})(\d{2})\s+(\d{2}:\d{2})", raw_time)
        if not match:
            return ""
        year, month, day, hm = match.groups()
        return f"{year}.{month}.{day} {hm}"

    @staticmethod
    def _extract_count(item: Tag, selector: str) -> str:
        """item 내부에서 selector로 찾은 첫 태그의 텍스트(숫자)를 반환한다."""
        tag = item.select_one(selector)
        return tag.get_text(strip=True) if tag else ""

    def save_to_database(self) -> None:
        """수집한 리뷰를 output_dir/reviews_naver.csv 로 저장한다."""
        os.makedirs(self.output_dir, exist_ok=True)
        save_path = os.path.join(self.output_dir, "reviews_naver.csv")
        df = pd.DataFrame(
            self.reviews,
            columns=[
                "score",
                "date",
                "content",
                "writer_id",
                "like_count",
                "dislike_count",
                "source",
            ],
        )
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        self.logger.info(f"{len(df)}개의 리뷰를 {save_path}에 저장했습니다.")


if __name__ == "__main__":
    crawler = NaverCrawler(output_dir="../../database")
    crawler.start_browser()
    crawler.scrape_reviews()
    crawler.save_to_database()
