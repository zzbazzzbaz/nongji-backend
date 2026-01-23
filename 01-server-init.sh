#!/bin/bash
# 服务器初始化脚本 - 首次部署时运行
# 在服务器上以root用户运行此脚本

set -e

APP_DIR="/opt/nongji_app"
REPO_URL="https://github.com/zzbazzzbaz/nongji-backend.git"

echo "========== 服务器初始化开始 =========="

# 更新系统
echo "[1/6] 更新系统包..."
apt update && apt upgrade -y

# 安装必要依赖
echo "[2/6] 安装系统依赖..."
apt install -y python3 python3-pip python3-venv git curl lsof

# 安装uv包管理器
echo "[3/6] 安装uv包管理器..."
# 使用国内镜像加速下载
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple/"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/root/.local/bin:$PATH"

# 创建应用目录
echo "[4/6] 创建应用目录..."
mkdir -p "$APP_DIR"
chown -R ubuntu:ubuntu "$APP_DIR"

# 克隆代码仓库
echo "[5/6] 克隆代码仓库..."
if [ -d "$APP_DIR/.git" ]; then
    echo "代码仓库已存在，跳过克隆..."
else
    git clone "$REPO_URL" "$APP_DIR"
fi
chown -R ubuntu:ubuntu "$APP_DIR"

# 创建.env文件
echo "[6/6] 创建环境配置文件..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << 'EOF'
# Django配置
SECRET_KEY=your-production-secret-key-change-this
DEBUG=False

# 阿里云OCR (如需要请填写)
ALIBABA_CLOUD_ACCESS_KEY_ID=
ALIBABA_CLOUD_ACCESS_KEY_SECRET=
EOF
    chown ubuntu:ubuntu "$APP_DIR/.env"
    echo "请编辑 $APP_DIR/.env 文件配置正确的密钥!"
fi

# 设置部署脚本可执行权限
chmod +x "$APP_DIR"/*.sh 2>/dev/null || true

echo ""
echo "========== 服务器初始化完成 =========="
echo ""
echo "下一步操作:"
echo "1. 编辑环境配置: nano $APP_DIR/.env"
echo "2. 切换到ubuntu用户: su - ubuntu"
echo "3. 拉取代码: cd $APP_DIR && ./02-code-pull.sh"
echo "4. 运行部署脚本: ./03-deploy.sh"
echo ""
