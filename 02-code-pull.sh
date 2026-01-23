#!/bin/bash
# 代码拉取脚本 - 从GitHub更新代码
# 部署目录: /opt/nongji_app

set -e

# 配置变量
APP_DIR="/opt/nongji_app"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 从GitHub更新代码 (最多尝试100次)
update_code() {
    log_info "开始从GitHub更新代码..."
    cd "$APP_DIR"
    
    MAX_ATTEMPTS=100
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        ATTEMPT=$((ATTEMPT + 1))
        log_info "尝试拉取代码 (第 $ATTEMPT/$MAX_ATTEMPTS 次)..."
        
        if git pull origin main 2>/dev/null || git pull origin master 2>/dev/null; then
            log_info "代码更新成功!"
            return 0
        fi
        
        log_warn "拉取失败，等待3秒后重试..."
        sleep 3
    done
    
    log_error "代码更新失败，已尝试 $MAX_ATTEMPTS 次"
    return 1
}

# 主函数
main() {
    log_info "========== 开始拉取代码 =========="
    log_info "部署目录: $APP_DIR"
    echo ""
    
    update_code
    
    echo ""
    log_info "========== 代码拉取完成 =========="
    log_info "下一步: 运行 ./03-deploy.sh 进行部署"
}

main
