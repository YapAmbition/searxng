# SearXNG 云服务器部署指南（Alibaba Cloud Linux 3 + Nginx）

## 简介

在已有 Nginx + HTTPS 的 Alibaba Cloud Linux 3 云服务器（2C2G）上部署 SearXNG，通过 `https://你的域名/search` 访问搜索界面，同时对接 OpenClaw 实现免费联网搜索。

## 一、安装 Python 3.11

```bash
sudo dnf install python3.11 python3.11-devel python3.11-pip git -y
```

验证：

```bash
python3.11 --version
# 应输出 Python 3.11.x
```

## 二、安装 SearXNG

```bash
# 创建目录
sudo mkdir -p /opt/searxng
sudo chown $(whoami) /opt/searxng

# 克隆仓库
cd /opt/searxng
git clone https://github.com/searxng/searxng.git
cd searxng

# 创建虚拟环境并安装依赖
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 三、配置 SearXNG

先生成随机密钥：

```bash
openssl rand -hex 32
```

然后用以下内容**完整替换** `/opt/searxng/searxng/searx/settings.yml`：

```yaml
general:
  debug: false
  instance_name: "SearXNG"
  enable_metrics: false

brand: {}

search:
  safe_search: 0
  autocomplete: "bing"
  default_lang: "auto"
  ban_time_on_fail: 5
  max_ban_time_on_fail: 120
  formats:
    - html
    - json

server:
  port: 8899
  bind_address: "127.0.0.1"
  limiter: false
  public_instance: false
  secret_key: "替换为你生成的随机密钥"
  base_url: "https://你的域名/search"
  image_proxy: false
  http_protocol_version: "1.0"
  method: "GET"

valkey:
  url: false

ui:
  default_theme: simple
  default_locale: ""
  theme_args:
    simple_style: auto

outgoing:
  request_timeout: 10.0
  pool_connections: 100
  pool_maxsize: 20
  enable_http2: true

categories_as_tabs:
  general:
  images:
  news:
  it:

engines:
  # Bing
  - name: bing
    engine: bing
    shortcut: bi

  - name: bing images
    engine: bing_images
    shortcut: bii

  - name: bing news
    engine: bing_news
    shortcut: bin

  - name: bing videos
    engine: bing_videos
    shortcut: biv

  # Baidu
  - name: baidu
    baidu_category: general
    categories: [general]
    engine: baidu
    shortcut: bd

  - name: baidu images
    baidu_category: images
    categories: [images]
    engine: baidu
    shortcut: bdi

  - name: baidu kaifa
    baidu_category: it
    categories: [it]
    engine: baidu
    shortcut: bdk

doi_resolvers:
  oadoi.org: 'https://oadoi.org/'
  doi.org: 'https://doi.org/'

default_doi_resolver: 'oadoi.org'
```

> 注意：`base_url` 必须设为 `https://你的域名/search`，SearXNG 会据此自动处理子路径下的所有链接和静态资源。记得替换 `secret_key` 和 `你的域名`。

## 四、配置 Nginx 反向代理

编辑你现有的 Nginx HTTPS 配置文件（通常在 `/etc/nginx/conf.d/` 或 `/etc/nginx/sites-available/` 下），在 `server` 块中添加以下 `location`：

```nginx
# SearXNG 反向代理
location /search {
    proxy_pass http://127.0.0.1:8899/search;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Script-Name /search;

    proxy_buffering off;
}
```

测试并重载 Nginx：

```bash
sudo nginx -t
sudo nginx -s reload
```

## 五、配置 systemd 服务

创建 service 文件：

```bash
sudo tee /etc/systemd/system/searxng.service > /dev/null << 'EOF'
[Unit]
Description=SearXNG
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/opt/searxng/searxng
ExecStart=/opt/searxng/searxng/venv/bin/python -m searx.webapp
Restart=on-failure
RestartSec=5
Environment=SEARXNG_SETTINGS_PATH=/opt/searxng/searxng/searx/settings.yml

[Install]
WantedBy=multi-user.target
EOF
```

> 如果你用非 root 用户运行，将 `User=root` 改为你的用户名，并确保该用户对 `/opt/searxng` 有读写权限。

启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable searxng
sudo systemctl start searxng
```

查看状态和日志：

```bash
# 查看运行状态
sudo systemctl status searxng

# 查看实时日志
sudo journalctl -u searxng -f
```

## 六、验证

### 1. 本地验证（在服务器上）

```bash
curl -s 'http://127.0.0.1:8899/search/search?q=test&format=json' | head -c 300
```

> 注意：因为配置了 `base_url`，直接访问 `127.0.0.1:8899` 会被重定向到域名地址，这是正常行为。本地测试需要带上 `/search` 前缀路径。

### 2. 外部验证

浏览器访问：

```
https://你的域名/search
```

应该能看到 SearXNG 的搜索界面，输入关键词能正常返回结果。

### 3. JSON 接口验证

```bash
curl -s 'https://你的域名/search/search?q=test&format=json' | head -c 300
```

## 七、对接 OpenClaw

编辑 `~/.openclaw/openclaw.json`，添加或修改以下配置：

```json
{
  "tools": {
    "web": {
      "search": {
        "provider": "searxng"
      }
    }
  },
  "plugins": {
    "entries": {
      "searxng": {
        "config": {
          "webSearch": {
            "baseUrl": "https://你的域名/search",
            "categories": "general,news",
            "language": "zh-hans"
          }
        }
      }
    }
  }
}
```

> 将 `你的域名` 替换为实际域名。配置完成后重启 OpenClaw 即可。

## 八、常见问题

### Q: 访问 /search 返回 502 Bad Gateway

SearXNG 服务未启动或启动失败。检查：

```bash
sudo systemctl status searxng
sudo journalctl -u searxng --no-pager -n 50
```

### Q: 页面能打开但搜索无结果

确认服务器能访问外网（Bing、Baidu），检查防火墙出站规则。

### Q: 静态资源（CSS/JS）加载失败

确认 `settings.yml` 中 `base_url` 设置正确，必须与 Nginx 的 location 路径一致（都是 `/search`）。

### Q: 报错 `Invalid settings.yml`

配置文件缺少必填字段（如 `brand: {}`），建议直接使用上面提供的完整配置。

