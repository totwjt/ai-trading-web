"""
数据库连接模块
用于连接 stock_strategy 数据库
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional

# 数据库配置
DB_CONFIG = {
    "host": "192.168.66.26",
    "port": 5432,
    "user": "vonstars",
    "password": "vonstars123.com",
    "database": "stock_strategy"
}


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_cursor(cursor_factory=RealDictCursor):
    """获取数据库游标的上下文管理器"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


def get_latest_news(limit: int = 10) -> list:
    """
    获取最新资讯列表（含分析详情和利好股票/板块）
    只返回有利好股票的资讯
    
    Args:
        limit: 返回数量，默认10条
        
    Returns:
        资讯列表，每条包含 news_base、analysis_detail、impact_mapping 数据
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT nb.id
            FROM news_base nb
            INNER JOIN news_impact_mapping nim ON nb.id = nim.news_id
            WHERE nim.entity_type = 'stock'
            GROUP BY nb.id
            ORDER BY MAX(nb.publish_time) DESC
            LIMIT %s
        """, (limit,))
        
        news_ids = [row['id'] for row in cursor.fetchall()]
        
        if not news_ids:
            return []
        
        # 查询这些资讯的详情
        cursor.execute("""
            SELECT 
                nb.id,
                nb.source_id,
                nb.title,
                nb.content,
                nb.source,
                nb.url,
                nb.publish_time,
                nb.crawl_time,
                nad.id as detail_id,
                nad.analysis_text,
                nad.factors
            FROM news_base nb
            LEFT JOIN news_analysis_detail nad ON nb.id = nad.news_id
            WHERE nb.id = ANY(%s)
            ORDER BY nb.publish_time DESC
        """, (news_ids,))
        
        news_list = cursor.fetchall()
        
        if not news_list:
            return []
        
        # 批量查询利好板块和股票
        cursor.execute("""
            SELECT 
                news_id,
                entity_type,
                entity_name,
                entity_code,
                score
            FROM news_impact_mapping
            WHERE news_id = ANY(%s)
            ORDER BY news_id, entity_type, score DESC NULLS LAST
        """, (news_ids,))
        
        impacts = cursor.fetchall()
        
        # 按 news_id 分组
        impacts_by_news = {}
        for impact in impacts:
            news_id = impact['news_id']
            if news_id not in impacts_by_news:
                impacts_by_news[news_id] = {'sectors': [], 'stocks': []}
            
            if impact['entity_type'] == 'sector':
                impacts_by_news[news_id]['sectors'].append(impact['entity_name'])
            elif impact['entity_type'] == 'stock':
                impacts_by_news[news_id]['stocks'].append({
                    'name': impact['entity_name'],
                    'code': impact['entity_code'],
                    'score': impact['score']
                })
        
        # 组装结果
        result = []
        for row in news_list:
            news_id = row['id']
            impact_data = impacts_by_news.get(news_id, {'sectors': [], 'stocks': []})
            
            # 解析 factors (JSON 数组字符串)
            factors_list = []
            if row['factors']:
                import json
                try:
                    # factors 可能是 JSON 数组格式
                    factors_list = json.loads(row['factors']) if isinstance(row['factors'], str) else row['factors']
                except:
                    factors_list = []
            
            result.append({
                'id': news_id,
                'title': row['title'],
                'content': row['content'],
                'source': row['source'],
                'url': row['url'],
                'publish_time': row['publish_time'].isoformat() if row['publish_time'] else None,
                'crawl_time': row['crawl_time'].isoformat() if row['crawl_time'] else None,
                'analysis': row['analysis_text'] or '',
                'factors': factors_list,
                'sectors': impact_data['sectors'],
                'stocks': impact_data['stocks']
            })
        
        return result


def get_news_by_id(news_id: int) -> Optional[dict]:
    """根据 ID 获取单条资讯详情"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                nb.id,
                nb.source_id,
                nb.title,
                nb.content,
                nb.source,
                nb.url,
                nb.publish_time,
                nb.crawl_time,
                nad.analysis_text,
                nad.factors
            FROM news_base nb
            LEFT JOIN news_analysis_detail nad ON nb.id = nad.news_id
            WHERE nb.id = %s
        """, (news_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # 查询关联的利好板块和股票
        cursor.execute("""
            SELECT entity_type, entity_name, entity_code, score
            FROM news_impact_mapping
            WHERE news_id = %s
            ORDER BY entity_type, score DESC NULLS LAST
        """, (news_id,))
        
        impacts = cursor.fetchall()
        sectors = []
        stocks = []
        
        for impact in impacts:
            if impact['entity_type'] == 'sector':
                sectors.append(impact['entity_name'])
            elif impact['entity_type'] == 'stock':
                stocks.append({
                    'name': impact['entity_name'],
                    'code': impact['entity_code'],
                    'score': impact['score']
                })
        
        return {
            'id': row['id'],
            'title': row['title'],
            'content': row['content'],
            'source': row['source'],
            'url': row['url'],
            'publish_time': row['publish_time'].isoformat() if row['publish_time'] else None,
            'analysis': row['analysis_text'] or '',
            'sectors': sectors,
            'stocks': stocks
        }
