import pandas as pd
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from review_analysis.preprocessing.base_processor import BaseDataProcessor

class CommonProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_dir: str, site_name: str):
        super().__init__(input_path, output_dir)
        self.site_name = site_name
        self.df = pd.read_csv(self.input_path)
        self._standardize_columns() # 자식 클래스에서 컬럼명을 통일하는 메서드

    def _standardize_columns(self):
        """자식 클래스에서 반드시 오버라이딩하여 컬럼명을 ['별점', '날짜', '내용']으로 맞출 것"""
        pass

    def preprocess(self):
        """결측치, 이상치, 텍스트 데이터 전처리"""
        # 1. 결측치 처리 (null값 제거 및 의미 없는 텍스트 제거)
        self.df = self.df.dropna(subset=['별점', '내용'])
        self.df = self.df[self.df['내용'] != '내용 없음']
        
        # 2. 이상치 처리 (별점 범위가 0~10이 아닌 경우 제거)
        self.df['별점'] = pd.to_numeric(self.df['별점'], errors='coerce')
        self.df = self.df.dropna(subset=['별점'])
        self.df = self.df[(self.df['별점'] >= 0) & (self.df['별점'] <= 10)]

        # 3. 텍스트 데이터 전처리 (특수문자 제거 및 너무 짧은 리뷰 제거)
        def clean_text(text):
            text = re.sub(r'[^a-zA-Z가-힣\s]', '', str(text)) 
            return text.lower().strip()
            
        self.df['정제된_내용'] = self.df['내용'].apply(clean_text)
        self.df = self.df[self.df['정제된_내용'].str.len() >= 2]

    def feature_engineering(self):
        """파생 변수 생성 및 텍스트 벡터화"""
        # 1. 파생 변수 생성 (요일, 리뷰 길이)
        self.df['날짜'] = pd.to_datetime(self.df['날짜'], errors='coerce')
        self.df = self.df.dropna(subset=['날짜'])
        self.df['요일'] = self.df['날짜'].dt.day_name()
        self.df['리뷰길이'] = self.df['내용'].astype(str).apply(len)

        # 2. 텍스트 벡터화 (TF-IDF 임베딩)
        vectorizer = TfidfVectorizer(max_features=30) # 상위 30개 핵심 키워드 추출
        tfidf_matrix = vectorizer.fit_transform(self.df['정제된_내용'])
        
        tfidf_df = pd.DataFrame(
            tfidf_matrix.toarray(), 
            columns=[f'tfidf_{word}' for word in vectorizer.get_feature_names_out()]
        )
        
        # 인덱스 초기화 후 원본 데이터와 가로로 병합
        self.df = self.df.reset_index(drop=True)
        self.df = pd.concat([self.df, tfidf_df], axis=1)

    def save_to_database(self):
        """결과 저장"""
        save_path = os.path.join(self.output_dir, f'preprocessed_reviews_{self.site_name}.csv')
        self.df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"[{self.site_name}] 전처리 완료 및 저장 성공: {save_path}")

# ==========================================
# 자식 클래스: 각각의 사이트에 맞게 컬럼명만 통일
# ==========================================

class IMDbProcessor(CommonProcessor):
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir, 'IMDb')

    def _standardize_columns(self):
        self.df['별점'] = self.df['별점'].astype(str).str.split('/').str[0]
        self.df = self.df[['별점', '날짜', '내용']]

class MegaboxProcessor(CommonProcessor):
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir, 'megabox')
        
    def _standardize_columns(self):
        self.df = self.df[['rating', 'date', 'review']]
        self.df.columns = ['별점', '날짜', '내용']

class NaverProcessor(CommonProcessor):
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir, 'naver')
        
    def _standardize_columns(self):
        self.df = self.df[['score', 'date', 'content']]
        self.df.columns = ['별점', '날짜', '내용']