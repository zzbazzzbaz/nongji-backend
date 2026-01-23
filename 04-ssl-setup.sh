#!/bin/bash
# SSL证书配置脚本 - 使用Certbot自动获取和续签Let's Encrypt证书
# 域名: www.zbhtdz.top
# 后端代理: 127.0.0.1:8062

set -e

# 配置变量
DOMAIN="www.zbhtdz.top"
BACKEND_PORT="8062"
EMAIL="3217233537@qq.com"  # 用于证书通知，可修改

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 安装Certbot
install_certbot() {
    log_info "安装Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
    log_info "Certbot安装完成"
}

# 创建Nginx配置
create_nginx_config() {
    log_info "创建Nginx配置..."
    
    # 先创建HTTP配置用于证书验证
    cat > /etc/nginx/sites-available/$DOMAIN << 'EOF'
server {
    listen 80;
    server_name www.zbhtdz.top;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    
    # 测试并启动/重载Nginx
    nginx -t
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
    else
        systemctl start nginx
        systemctl enable nginx
    fi
    log_info "Nginx HTTP配置完成"
}

# 获取SSL证书
obtain_certificate() {
    log_info "获取SSL证书..."
    
    # 使用Certbot获取证书
    certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL
    
    log_info "SSL证书获取成功"
}

# 配置HTTPS
configure_https() {
    log_info "配置HTTPS..."
    
    cat > /etc/nginx/sites-available/$DOMAIN << EOF
# HTTP - 重定向到HTTPS
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL证书
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 客户端请求大小限制（用于文件上传）
    client_max_body_size 50M;

    # 代理到后端
    location / {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件
    location /static/ {
        alias /opt/nongji_app/static_collected/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media/ {
        alias /opt/nongji_app/media/;
        expires 7d;
    }
}
EOF

    # 测试并启动/重载Nginx
    nginx -t
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
    else
        systemctl start nginx
    fi
    log_info "HTTPS配置完成"
}

# 配置自动续签
setup_auto_renewal() {
    log_info "配置证书自动续签..."
    
    # Certbot会自动创建定时任务，检查是否存在
    if systemctl is-enabled certbot.timer &>/dev/null; then
        log_info "Certbot定时任务已启用"
    else
        systemctl enable certbot.timer
        systemctl start certbot.timer
    fi
    
    # 测试续签
    certbot renew --dry-run
    
    log_info "自动续签配置完成"
}

# 主函数
main() {
    log_info "========== SSL证书配置开始 =========="
    log_info "域名: $DOMAIN"
    log_info "后端端口: $BACKEND_PORT"
    echo ""
    
    # 检查是否为root用户
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root用户运行此脚本"
        exit 1
    fi
    
    install_certbot
    create_nginx_config
    obtain_certificate
    configure_https
    setup_auto_renewal
    
    echo ""
    log_info "========== SSL证书配置完成 =========="
    log_info "网站地址: https://$DOMAIN"
    log_info "证书位置: /etc/letsencrypt/live/$DOMAIN/"
    log_info "证书将自动续签"
}

main
