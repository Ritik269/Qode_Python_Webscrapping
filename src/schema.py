from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Tweet(BaseModel):
    tweet_id: str = Field(..., alias="id")
    username: str
    user_id: Optional[str] = None
    timestamp: datetime
    content: str
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    mentions: List[str] = []
    hashtags: List[str] = []
    url: Optional[str] = None
