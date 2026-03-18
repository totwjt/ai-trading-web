"""
WebSocket 消息模型定义
用于智能荐股系统的消息结构
"""
from dataclasses import dataclass, field
from typing import List, Optional, Union
from datetime import datetime
import json


@dataclass
class StockInfo:
    stock_code: str
    stock_name: str
    score: str

    def to_dict(self) -> dict:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "score": self.score
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'StockInfo':
        return cls(
            stock_code=data.get("stock_code", ""),
            stock_name=data.get("stock_name", ""),
            score=data.get("score", "0")
        )


@dataclass
class News:
    """新闻信息"""
    title: str
    content: str
    publish_time: str
    crawl_time: str
    source: str
    url: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "publish_time": self.publish_time,
            "crawl_time": self.crawl_time,
            "source": self.source,
            "url": self.url
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'News':
        return cls(
            title=data.get("title", ""),
            content=data.get("content", ""),
            publish_time=data.get("publish_time", ""),
            crawl_time=data.get("crawl_time", ""),
            source=data.get("source", ""),
            url=data.get("url", "")
        )


def parse_stock(stock_data: Union[str, dict]) -> Optional[StockInfo]:
    if isinstance(stock_data, dict):
        return StockInfo.from_dict(stock_data)
    elif isinstance(stock_data, str):
        import re
        match = re.match(r'(\d{6})\(([^)]+?)(\d+)?\)', stock_data)
        if match:
            return StockInfo(
                stock_code=match.group(1),
                stock_name=match.group(2),
                score=match.group(3) or "0"
            )
    return None


@dataclass
class Analysis:
    """分析结果"""
    利好版块: List[str] = field(default_factory=list)
    利好股票: List[Union[str, StockInfo]] = field(default_factory=list)
    分析因素: List[str] = field(default_factory=list)
    详细分析: str = ""

    def to_dict(self) -> dict:
        return {
            "利好版块": self.利好版块,
            "利好股票": self.利好股票,
            "分析因素": self.分析因素,
            "详细分析": self.详细分析
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Analysis':
        利好股票 = data.get("利好股票", [])
        parsed_stocks = []
        for stock in 利好股票:
            parsed = parse_stock(stock)
            if parsed:
                parsed_stocks.append(parsed)
            else:
                parsed_stocks.append(stock)
        
        return cls(
            利好版块=data.get("利好版块", []),
            利好股票=parsed_stocks,
            分析因素=data.get("分析因素", []),
            详细分析=data.get("详细分析", "")
        )


@dataclass
class RecommendationMessage:
    """荐股消息（完整结构）"""
    news: News
    analysis: Analysis

    def to_dict(self) -> dict:
        return {
            "news": self.news.to_dict(),
            "analysis": self.analysis.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RecommendationMessage':
        return cls(
            news=News.from_dict(data.get("news", {})),
            analysis=Analysis.from_dict(data.get("analysis", {}))
        )


@dataclass
class WSMessage:
    """WebSocket 传输消息格式"""
    type: str  # message_type: "recommendation", "heartbeat", "system"
    payload: dict
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    message_id: str = field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'WSMessage':
        data = json.loads(json_str)
        return cls(
            type=data.get("type", "message"),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            message_id=data.get("message_id", "")
        )


# 消息类型常量
class MessageType:
    RECOMMENDATION = "recommendation"
    HEARTBEAT = "heartbeat"
    SYSTEM = "system"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PUSH = "push"
