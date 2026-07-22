from __future__ import annotations

import csv
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger


class MegaboxCrawler(BaseCrawler):
    """Crawl at least 500 Megabox audience reviews for the movie '백룸'.

    The crawler discovers the movie detail URL from Megabox's movie page,
    opens the audience-review tab, parses reviews with BeautifulSoup, moves
    through Selenium pagination, removes duplicates, and writes a CSV file.
    """

    MOVIE_TITLE = "백룸"
    MIN_REVIEWS = 500
    OUTPUT_FILENAME = "reviews_megabox.csv"
    MOVIE_LIST_URL = "https://www.megabox.co.kr/movie"
    DIRECT_COMMENT_URL_ENV = "MEGABOX_BACKROOMS_URL"
    DEFAULT_COMMENT_URL = (
        "https://www.megabox.co.kr/movie-detail/comment"
        "?rpstMovieNo=26027600"
    )

    def __init__(self, output_dir: str):
        """Initialize output paths and in-memory review storage."""
        super().__init__(output_dir)
        self.driver: Optional[WebDriver] = None
        self.reviews: List[Dict[str, str]] = []
        self._seen: Set[Tuple[str, str, str]] = set()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        self.output_path = output_path / self.OUTPUT_FILENAME
        self.checkpoint_path = output_path / "reviews_megabox_checkpoint.csv"
        self.logger: logging.Logger = setup_logger(
            str(output_path / "megabox_crawler.log")
        )
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def start_browser(self) -> WebDriver:
        """Start a Chrome browser and return its WebDriver."""
        if self.driver is not None:
            return self.driver

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=ko-KR")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        )
        options.add_experimental_option(
            "prefs",
            {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
            },
        )

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(40)
        return self.driver

    @staticmethod
    def _clean_text(text: str) -> str:
        """Collapse whitespace and strip surrounding spaces."""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _first_text(node: Tag, selectors: List[str]) -> str:
        """Return cleaned text from the first matching CSS selector."""
        for selector in selectors:
            found = node.select_one(selector)
            if found is not None:
                text = MegaboxCrawler._clean_text(
                    found.get_text(" ", strip=True)
                )
                if text:
                    return text
        return ""

    @staticmethod
    def _normalize_rating(raw_rating: str) -> str:
        """Extract a numeric Megabox rating from arbitrary visible text."""
        match = re.search(
            r"(?:10(?:\.0)?|[0-9](?:\.\d+)?)",
            raw_rating,
        )
        return match.group(0) if match else raw_rating.strip()

    @staticmethod
    def _normalize_date(raw_date: str) -> str:
        """Convert a Megabox relative date into an absolute date."""
        text = MegaboxCrawler._clean_text(raw_date)
        now = datetime.now()

        patterns = (
            (r"(\d+)\s*분\s*전", "minutes"),
            (r"(\d+)\s*시간\s*전", "hours"),
            (r"(\d+)\s*일\s*전", "days"),
            (r"(\d+)\s*주\s*전", "weeks"),
        )
        for pattern, unit in patterns:
            match = re.search(pattern, text)
            if match:
                value = int(match.group(1))
                converted = now - timedelta(**{unit: value})
                return converted.strftime("%Y-%m-%d")

        month_match = re.search(r"(\d+)\s*개월\s*전", text)
        if month_match:
            months = int(month_match.group(1))
            converted = now - timedelta(days=30 * months)
            return converted.strftime("%Y-%m-%d")

        return text

    def _discover_comment_url(self) -> str:
        """Return the configured or default Megabox comment-page URL."""
        env_url = os.getenv(
            self.DIRECT_COMMENT_URL_ENV,
            self.DEFAULT_COMMENT_URL,
        ).strip()
        return self._to_comment_url(env_url)

    @staticmethod
    def _to_comment_url(url: str) -> str:
        """Convert a Megabox movie detail URL into its comment-tab URL."""
        if url.startswith("/"):
            url = f"https://www.megabox.co.kr{url}"
        url = url.replace("m.megabox.co.kr", "www.megabox.co.kr")

        movie_no_match = re.search(r"rpstMovieNo=(\d+)", url)
        if not movie_no_match:
            raise RuntimeError(f"rpstMovieNo가 없는 메가박스 URL입니다: {url}")
        movie_no = movie_no_match.group(1)
        return (
            "https://www.megabox.co.kr/movie-detail/comment"
            f"?rpstMovieNo={movie_no}"
        )

    def _parse_current_page(self) -> List[Dict[str, str]]:
        """Parse visible review cards from the current page source."""
        if self.driver is None:
            raise RuntimeError("Browser has not been started.")

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        containers = soup.select(
            "#contentData .movie-idv-story li, "
            "#contentData li.type01, "
            ".movie-idv-story li, "
            ".review-list li"
        )

        parsed: List[Dict[str, str]] = []
        for container in containers:
            if not isinstance(container, Tag):
                continue

            rating_raw = self._first_text(
                container,
                [
                    ".story-point span",
                    ".story-point",
                    "[class*='point'] span",
                    "[class*='score']",
                ],
            )
            content = self._first_text(
                container,
                [
                    ".story-txt",
                    ".story-cont .story-txt",
                    "[class*='review'] [class*='txt']",
                    "[class*='comment']",
                ],
            )
            date = self._first_text(
                container,
                [
                    ".story-date",
                    ".story-util .date",
                    ".story-util span:last-child",
                    "[class*='date']",
                ],
            )
            date = self._normalize_date(date)

            # Ignore navigation/empty list elements accidentally caught by broad selectors.
            if not rating_raw or not content or not date:
                continue

            rating = self._normalize_rating(rating_raw)
            parsed.append(
                {
                    "movie": self.MOVIE_TITLE,
                    "site": "megabox",
                    "rating": rating,
                    "review": content,
                    "date": date,
                }
            )
        return parsed

    def _add_reviews(self, items: List[Dict[str, str]]) -> int:
        """Append non-duplicate reviews and return the number newly added."""
        added = 0
        for item in items:
            key = (item["rating"], item["review"], item["date"])
            if key in self._seen:
                continue
            self._seen.add(key)
            self.reviews.append(item)
            added += 1
        return added

    def _wait_for_review_change(self, previous_signature: str) -> None:
        """Wait until AJAX pagination changes the first visible review."""
        if self.driver is None:
            return

        def changed(current_driver: WebDriver) -> bool:
            soup = BeautifulSoup(current_driver.page_source, "html.parser")
            first = soup.select_one(
                "#contentData .story-txt, #contentData [class*='review'] [class*='txt']"
            )
            if first is None:
                return False
            signature = self._clean_text(first.get_text(" ", strip=True))
            return bool(signature and signature != previous_signature)

        WebDriverWait(self.driver, 15).until(changed)

    def _click_next_page(self, current_page: int) -> bool:
        """Click the next review page, returning False when pagination ends."""
        if self.driver is None:
            return False

        previous_items = self._parse_current_page()
        previous_signature = previous_items[0]["review"] if previous_items else ""
        next_page = current_page + 1

        candidate_xpaths = [
            f"//div[@id='contentData']//nav//a[normalize-space()='{next_page}']",
            f"//div[@id='contentData']//nav//*[self::a or self::button][normalize-space()='{next_page}']",
            "//div[@id='contentData']//nav//a[contains(@class,'next')]",
            "//div[@id='contentData']//nav//a[contains(@title,'다음')]",
            "//div[@id='contentData']//nav//a[normalize-space()='다음']",
        ]

        for xpath in candidate_xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if not element.is_displayed() or not element.is_enabled():
                        continue
                    classes = (element.get_attribute("class") or "").lower()
                    if "disabled" in classes or "off" in classes:
                        continue
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", element
                    )
                    time.sleep(0.2)
                    try:
                        element.click()
                    except ElementClickInterceptedException:
                        self.driver.execute_script("arguments[0].click();", element)
                    if previous_signature:
                        self._wait_for_review_change(previous_signature)
                    else:
                        time.sleep(1)
                    return True
            except (NoSuchElementException, StaleElementReferenceException, TimeoutException):
                continue
        return False

    def _save_rows(self, path: Path) -> None:
        """Write current reviews to a UTF-8-SIG CSV file."""
        fieldnames = ["movie", "site", "rating", "review", "date"]
        with path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.reviews)

    def scrape_reviews(self) -> None:
        """Collect at least 500 unique reviews using Selenium and BeautifulSoup."""
        driver = self.start_browser()
        try:
            comment_url = self._discover_comment_url()
            self.logger.info("Opening Megabox review page: %s", comment_url)
            driver.get(comment_url)
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.ID, "contentData"))
            )
            time.sleep(2)

            page = 1
            consecutive_empty_pages = 0
            while len(self.reviews) < self.MIN_REVIEWS:
                items = self._parse_current_page()
                added = self._add_reviews(items)
                self.logger.info(
                    "Page %d: parsed=%d, added=%d, total=%d",
                    page,
                    len(items),
                    added,
                    len(self.reviews),
                )

                if added == 0:
                    consecutive_empty_pages += 1
                else:
                    consecutive_empty_pages = 0

                if page % 5 == 0:
                    self._save_rows(self.checkpoint_path)

                if consecutive_empty_pages >= 3:
                    raise RuntimeError(
                        "3개 페이지 연속으로 새 리뷰를 얻지 못했습니다. "
                        "메가박스 페이지 구조 또는 페이지네이션을 확인하세요."
                    )

                if len(self.reviews) >= self.MIN_REVIEWS:
                    break
                if not self._click_next_page(page):
                    break

                page += 1
                time.sleep(0.5)

            if len(self.reviews) < self.MIN_REVIEWS:
                raise RuntimeError(
                    f"수집 리뷰가 {len(self.reviews)}개로 최소 조건 "
                    f"{self.MIN_REVIEWS}개를 충족하지 못했습니다."
                )
        except (WebDriverException, TimeoutException) as error:
            error_name = type(error).__name__
            self.logger.error(
                "Megabox crawling failed. Error type: %s",
                error_name,
            )
            if self.reviews:
                self._save_rows(self.checkpoint_path)
            raise RuntimeError(
                f"메가박스 크롤링 중 {error_name} 오류가 발생했습니다."
            ) from None
        finally:
            if self.driver is not None:
                self.driver.quit()
                self.driver = None

    def save_to_database(self) -> None:
        """Save validated reviews to reviews_megabox.csv under output_dir."""
        if len(self.reviews) < self.MIN_REVIEWS:
            raise RuntimeError(
                f"저장 중단: 리뷰가 {len(self.reviews)}개뿐입니다. "
                f"최소 {self.MIN_REVIEWS}개가 필요합니다."
            )

        invalid = [
            row
            for row in self.reviews
            if not row["rating"] or not row["review"] or not row["date"]
        ]
        if invalid:
            raise RuntimeError(
                f"별점·리뷰·날짜 중 누락된 행이 {len(invalid)}개 있습니다."
            )

        self._save_rows(self.output_path)
        if self.checkpoint_path.exists():
           self.checkpoint_path.unlink()
        self.logger.info("Saved %d reviews to %s", len(self.reviews), self.output_path)