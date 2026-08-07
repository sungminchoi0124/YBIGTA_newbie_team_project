import pandas as pd
from fastapi import APIRouter, HTTPException

from database.mongodb_connection import mongo_db
from review_analysis.preprocessing.site_processors import (
    IMDbProcessor,
    MegaboxProcessor,
    NaverProcessor,
)


review = APIRouter(prefix="/review")


PROCESSORS = {
    "imdb": IMDbProcessor,
    "megabox": MegaboxProcessor,
    "naver": NaverProcessor,
}


@review.post("/preprocess/{site_name}")
def preprocess_reviews(site_name: str):
    site_key = site_name.lower()

    if site_key not in PROCESSORS:
        raise HTTPException(
            status_code=400,
            detail="site_name must be one of: imdb, megabox, naver",
        )

    raw_collection_name = f"reviews_{site_key}"
    processed_collection_name = f"preprocessed_reviews_{site_key}"

    raw_collection = mongo_db[raw_collection_name]
    documents = list(raw_collection.find({}, {"_id": 0}))

    if not documents:
        raise HTTPException(
            status_code=404,
            detail=f"No review data found for {site_key}",
        )

    df = pd.DataFrame(documents)

    processor_class = PROCESSORS[site_key]
    processor = processor_class(df)

    processor.preprocess()
    processor.feature_engineering()

    processed_df = processor.df.copy()

    if "날짜" in processed_df.columns:
        processed_df["날짜"] = processed_df["날짜"].astype(str)

    records = processed_df.to_dict(orient="records")

    processed_collection = mongo_db[processed_collection_name]
    processed_collection.delete_many({})

    if records:
        processed_collection.insert_many(records)

    return {
        "status": "success",
        "site_name": site_key,
        "input_count": len(documents),
        "output_count": len(records),
        "collection": processed_collection_name,
    }