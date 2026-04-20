# SPDX-License-Identifier: AGPL-3.0-or-later

import typing as t
from urllib.parse import urlparse

from flask_babel import gettext  # pyright: ignore[reportUnknownVariableType]

from searx.plugins import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result
    from searx.plugins import PluginCfg

# 技术/高质量站点加权
TECH_DOMAINS = {
    # 代码托管
    'github.com': 1.5,
    'gitlab.com': 1.4,
    # 编程问答
    'stackoverflow.com': 1.4,
    'stackexchange.com': 1.3,
    # 官方文档
    'developer.mozilla.org': 1.3,
    'docs.python.org': 1.3,
    # 包管理
    'pypi.org': 1.2,
    'npmjs.com': 1.2,
    'hub.docker.com': 1.2,
    # 学术
    'arxiv.org': 1.3,
    # 新闻/社区
    'news.ycombinator.com': 1.2,
}

# 来源类型映射
SOURCE_TYPE_MAP = {
    # 代码托管
    'github.com': 'repository',
    'gitlab.com': 'repository',
    # 问答
    'stackoverflow.com': 'qa',
    'stackexchange.com': 'qa',
    # 官方文档
    'developer.mozilla.org': 'official_doc',
    'docs.python.org': 'official_doc',
    # 包管理
    'pypi.org': 'package',
    'npmjs.com': 'package',
    'hub.docker.com': 'package',
    # 学术
    'arxiv.org': 'academic',
    # 视频
    'bilibili.com': 'video',
    'acfun.cn': 'video',
    'iqiyi.com': 'video',
    # 新闻/社区
    'news.ycombinator.com': 'forum',
    # 游戏
    'store.steampowered.com': 'game_store',
    'steamcommunity.com': 'game_community',
    # 地图
    'openstreetmap.org': 'map',
    # 博客
    'medium.com': 'blog',
    'dev.to': 'blog',
    'juejin.cn': 'blog',
    'cnblogs.com': 'blog',
    'jianshu.com': 'blog',
    # 微信公众号文章
    'mp.weixin.qq.com': 'wechat_article',
    'weixin.sogou.com': 'wechat_article',
}

# 黑名单 - 低质量/内容农场站点直接过滤
BLACKLIST = {
    'w3schools.com',
    'tutorialspoint.com',
    'geeksforgeeks.org',
    'php.cn',
    'jb51.net',
    'code84.com',
}

# 低优先级 - 不过滤但降权
LOW_PRIORITY_DOMAINS = {
    'csdn.net': 0.7,
    'zhidao.baidu.com': 0.6,
    'baijiahao.baidu.com': 0.6,
}


def _match_domain(domain: str, domain_set) -> str | None:
    """支持子域名匹配，比如 gist.github.com 匹配 github.com"""
    if domain in domain_set:
        return domain
    parts = domain.split('.')
    while len(parts) > 2:
        parts.pop(0)
        parent = '.'.join(parts)
        if parent in domain_set:
            return parent
    return None


def _match_domain_value(domain: str, domain_dict: dict) -> float | None:
    """匹配域名并返回对应的值"""
    if domain in domain_dict:
        return domain_dict[domain]
    parts = domain.split('.')
    while len(parts) > 2:
        parts.pop(0)
        parent = '.'.join(parts)
        if parent in domain_dict:
            return domain_dict[parent]
    return None


@t.final
class SXNGPlugin(Plugin):
    """Boost technical domains, filter low-quality sites, and add structured metadata."""

    id = "tech_boost"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Tech Domain Boost"),
            description=gettext("Boost technical domains, filter low-quality sites, and add structured metadata"),
            preference_section="general",
        )

    def on_result(self, request: "SXNG_Request", search: "SearchWithPlugins", result: "Result") -> bool:
        url = result.url if hasattr(result, 'url') else None
        if not url:
            return True

        domain = urlparse(url).netloc.removeprefix('www.')

        # 黑名单直接过滤
        if _match_domain(domain, BLACKLIST):
            return False

        # 低优先级降权
        low_priority_factor = _match_domain_value(domain, LOW_PRIORITY_DOMAINS)
        if low_priority_factor is not None:
            score = getattr(result, 'score', None) or 1.0
            result.score = score * low_priority_factor  # type: ignore
        else:
            # 技术站点加权
            boost_factor = _match_domain_value(domain, TECH_DOMAINS)
            if boost_factor is not None:
                score = getattr(result, 'score', None) or 1.0
                result.score = score * boost_factor  # type: ignore

        return True

