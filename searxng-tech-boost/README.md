# searxng-tech-boost

SearXNG 外部插件，用于优化搜索结果质量。主要功能：

1. **技术站点加权** — GitHub、Stack Overflow、MDN 等高质量技术站点的结果排序提升
2. **低质量站点过滤** — 直接过滤内容农场（w3schools、jb51 等）
3. **低优先级降权** — CSDN、百度知道等质量不稳定的站点降低排序，但不完全过滤
4. **结构化元数据补充** — 为每条结果添加 `source_type`（repository/qa/video/blog 等）和 `domain` 字段，方便 Agent 做筛选决策

## 工作原理

利用 SearXNG 的 `on_result` 钩子，对每条搜索结果做处理：

- 匹配黑名单 → 丢弃结果（返回 False）
- 匹配低优先级 → score 乘以降权系数（如 0.6）
- 匹配技术站点 → score 乘以加权系数（如 1.5）
- 为所有结果补充 `source_type` 和 `domain` 元数据

支持子域名匹配，例如 `gist.github.com` 会匹配到 `github.com` 的规则。

## 安装

```bash
# 激活 SearXNG 的虚拟环境
source /opt/searxng/searxng/venv/bin/activate

# 进入插件目录安装（开发模式，改完代码重启即生效）
cd /path/to/searxng-tech-boost
pip install -e .
```

## 配置

在 SearXNG 的 `settings.yml` 中添加：

```yaml
plugins:
  tech_boost.SXNGPlugin:
    active: true
```

## 生效

```bash
sudo systemctl restart searxng
```

## 自定义

直接编辑 `tech_boost.py` 中的字典即可：

- `TECH_DOMAINS` — 需要加权的高质量站点及其权重系数
- `SOURCE_TYPE_MAP` — 域名到内容类型的映射
- `BLACKLIST` — 直接过滤的站点
- `LOW_PRIORITY_DOMAINS` — 降权但不过滤的站点及降权系数

修改后重启 SearXNG 服务即可生效。

## 文件结构

```
searxng-tech-boost/
├── tech_boost.py   # 插件逻辑
├── setup.py        # 安装配置
└── README.md
```

