"""
WebSocket 消息模型定义
用于智能荐股系统的消息结构
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import json


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
        return cls(**data)


@dataclass
class Analysis:
    """分析结果"""
    利好版块: List[str] = field(default_factory=list)
    利好股票: List[str] = field(default_factory=list)
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
        return cls(
            利好版块=data.get("利好版块", []),
            利好股票=data.get("利好股票", []),
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
    """消息类型常量"""
    RECOMMENDATION = "recommendation"  # 推荐消息
    HEARTBEAT = "heartbeat"            # 心跳
    SYSTEM = "system"                  # 系统消息
    SUBSCRIBE = "subscribe"           # 订阅
    UNSUBSCRIBE = "unsubscribe"       # 取消订阅
    CONNECT = "connect"               # 连接
    DISCONNECT = "disconnect"         # 断开
