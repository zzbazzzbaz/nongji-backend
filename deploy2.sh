#!/bin/bash
# 农机检测后端本地部署脚本 - 不从远程拉取代码
# 部署目录: /opt/nongji_app
# 运行端口: 8062

set -e

# 配置变量
APP_DIR="/opt/nongji_app"
VENV_DIR="$APP_DIR/.venv"
GUNICORN_BIND="0.0.0.0:8062"
GUNICORN_WORKERS=4
LOG_FILE="$APP_DIR/gunicorn.log"
PID_FILE="$APP_DIR/gunicorn.pid"

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

# 1. 生成数据库迁移
make_migrations() {
    log_info "生成数据库迁移文件..."
    cd "$APP_DIR"
    uv run python manage.py makemigrations
    log_info "数据库迁移文件生成完成!"
}

# 2. 应用数据库迁移
apply_migrations() {
    log_info "应用数据库迁移..."
    cd "$APP_DIR"
    uv run python manage.py migrate
    log_info "数据库迁移应用完成!"
}

# 3. 杀掉旧进程
kill_old_process() {
    log_info "检查并杀掉旧的Gunicorn进程..."
    
    # 通过PID文件杀进程
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            log_info "杀掉PID为 $OLD_PID 的进程..."
            kill "$OLD_PID" 2>/dev/null || true
            sleep 2
            # 如果还没死，强制杀
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    
    # 通过端口号查找并杀进程
    PIDS=$(lsof -t -i:8062 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        log_info "杀掉占用8062端口的进程: $PIDS"
        echo "$PIDS" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # 杀掉所有gunicorn进程 (与本项目相关的)
    pkill -f "gunicorn.*config.wsgi" 2>/dev/null || true
    
    log_info "旧进程清理完成!"
}

# 4. 重新启动
start_server() {
    log_info "启动Gunicorn服务器..."
    cd "$APP_DIR"
    
    # 收集静态文件
    log_info "收集静态文件..."
    uv run python manage.py collectstatic --noinput
    
    # 启动gunicorn (后台运行)
    nohup uv run gunicorn config.wsgi:application \
        --bind "$GUNICORN_BIND" \
        --workers "$GUNICORN_WORKERS" \
        --timeout 120 \
        --access-logfile "$APP_DIR/access.log" \
        --error-logfile "$LOG_FILE" \
        --pid "$PID_FILE" \
        --daemon \
        2>&1 &
    
    sleep 2
    
    # 检查是否启动成功
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        log_info "Gunicorn启动成功! PID: $(cat $PID_FILE)"
        log_info "服务运行在: http://$GUNICORN_BIND"
    else
        log_error "Gunicorn启动失败，请检查日志: $LOG_FILE"
        return 1
    fi
}

# 主函数
main() {
    log_info "========== 开始本地部署 =========="
    log_info "部署目录: $APP_DIR"
    log_info "运行端口: 8062"
    log_info "注意: 不从远程拉取代码，使用本地代码"
    echo ""
    
    # 执行部署步骤
    make_migrations
    apply_migrations
    kill_old_process
    start_server
    
    echo ""
    log_info "========== 部署完成 =========="
    log_info "访问地址: http://124.222.174.116:8062"
    log_info "日志文件: $LOG_FILE"
    log_info "PID文件: $PID_FILE"
}

# 显示帮助
show_help() {
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  (无参数)    执行完整部署流程"
    echo "  start       仅启动服务"
    echo "  stop        仅停止服务"
    echo "  restart     重启服务"
    echo "  status      查看服务状态"
    echo "  logs        查看日志"
    echo "  help        显示帮助"
}

# 查看状态
show_status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        log_info "Gunicorn正在运行，PID: $(cat $PID_FILE)"
    else
        log_warn "Gunicorn未运行"
    fi
}

# 查看日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        log_error "日志文件不存在: $LOG_FILE"
    fi
}

# 根据参数执行不同操作
case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        kill_old_process
        ;;
    restart)
        kill_old_process
        start_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help)
        show_help
        ;;
    *)
        main
        ;;
esac
