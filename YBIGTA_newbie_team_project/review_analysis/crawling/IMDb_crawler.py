from review_analysis.crawling.base_crawler import BaseCrawler
import time
import os
import random
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from utils.logger import setup_logger

class IMDbCrawler(BaseCrawler):
    """
    IMDb의 영화 백룸 리뷰를 크롤링하는 크롤러 클래스
    BaseCrawler 추상 클래스를 상속받음.
    """
    def __init__(self, output_dir: str):
        """
        초기화 메서드. 부모 클래스의 설정을 상속받고 URL과 로거 세팅
        """
        super().__init__(output_dir)
        self.base_url = 'https://www.imdb.com/title/tt26657236/reviews/?ref_=ttrt_ov_ql_2&sort=submission_date%2Cdesc'
        self.reviews_data: list[dict[str, str]] = []
        self.logger = setup_logger(log_file='IMDb_crawler.log')
        self.driver = None
        self.max_text_length = 300

    def start_browser(self):
        """
        Selenium WebDriver를 실행하고 봇 탐지 우회 옵션을 적용하여 접속
        """
        self.logger.info("브라우저 시작")
        options = Options()
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled") #봇 탐지 우회
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.implicitly_wait(10)
        self.driver.get(self.base_url)

        self.logger.info("수동 로그인을 위해 30초간 대기합니다...로그인 실패시 다시 실행해주세요.")
        time.sleep(30) #수동 로그인 시간 30초

    def scrape_reviews(self):
        self.start_browser()
        self.logger.info("리뷰 크롤링 시작")
        review_count = 700
        
        try:
            try:
                self.logger.info("See all 클릭 시도...")
                see_all_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'see all')] | //button[contains(@class, 'see-all')] | //a[contains(@class, 'see-all')]"))
                )

                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", see_all_btn)
                time.sleep(2)

                self.driver.execute_script("arguments[0].click();", see_all_btn)
                self.logger.info("'See all' 버튼 클릭 완료. 본격적인 스크롤 자동 로딩을 준비합니다.")
                
                time.sleep(5)

            except Exception as e:
                self.logger.warning(f"'See all' 버튼을 찾지 못했습니다. 버튼이 없거나 이미 펼쳐진 상태일 수 있으므로 바로 스크롤을 시도합니다. ({e})")

            
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                loaded_reviews = self.driver.find_elements(By.CSS_SELECTOR, "div.ipc-list-card")
                self.logger.info(f"현재 로드된 리뷰 개수: {len(loaded_reviews)}")
                
                if len(loaded_reviews) >= review_count:
                    self.logger.info(f"목표치({review_count}개) 달성. 스크롤을 중지하고 파싱을 시작합니다.")
                    break
                    
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                time.sleep(random.uniform(1.0, 3.0))
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    time.sleep(3)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    
                    if new_height == last_height:
                        self.logger.warning("더 이상 스크롤할 데이터가 없습니다.")
                        break
                        
                last_height = new_height
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            review_blocks = soup.select('article[class*="user-review-item"]')

            if not review_blocks:
                review_blocks = soup.select('div.ipc-list-card')
                self.logger.warning("article.user-review-item을 찾지 못해 div.ipc-list-card로 합니다.")

            if not review_blocks:
                self.logger.warning("리뷰를 찾을 수 없습니다.")

            for block in review_blocks[:review_count]:
                rating_elem = block.select_one('span.ipc-rating-star')
                rating = rating_elem.text.strip() if rating_elem else "N/A"

                date = "N/A"
                date_elem = block.select_one('li.review-date')          # 스크린샷에서 확인된 정확한 class
                if date_elem and date_elem.text.strip():
                    date = date_elem.text.strip()

                if date == "N/A":
                    date_elem = block.select_one('[class*="review-date"]')
                    if date_elem and date_elem.text.strip():
                        date = date_elem.text.strip()

                if date == "N/A":
                    meta_items = block.select('.ipc-inline-list__item')
                    for item in meta_items:
                        txt = item.text.strip()
                        if "202" in txt or "201" in txt:
                            date = txt
                            break
                
                content_elem = block.select_one('div.ipc-html-content-inner-div')
                content = content_elem.text.strip() if content_elem else "내용 없음"

                #너무 길면 300자로 자르고 ... 붙임
                if len(content) > self.max_text_length:
                    content = content[:self.max_text_length] + "..."

                self.reviews_data.append({
                    '별점': rating,
                    '날짜': date,
                    '내용': content
                })

            self.logger.info(f"수집한 리뷰 개수: {len(self.reviews_data)}")

        except Exception as e:
            self.logger.error(f"크롤링 중 예기치 못한 오류 발생: {e}")
        finally:
            self.driver.quit()
    
    def save_to_database(self):
        """
        수집된 리뷰 데이터를 지정된 경로와 파일명으로 저장
        """
        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "reviews_IMDb.csv")
        
        df = pd.DataFrame(self.reviews_data)
        
        df = df.drop_duplicates(subset=['내용'], keep='first')
        
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        self.logger.info(f"데이터 저장 완료: {file_path} (최종 행 개수: {len(df)})")