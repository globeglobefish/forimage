<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue.js" />
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License" />
</p>

<h1 align="center">🖼️ Forimage</h1>

<p align="center">
  <strong>现代化的自托管图床系统</strong><br>
  简洁优雅 · 功能完整 · 安全可靠
</p>

<p align="center">
  <a href="https://docs.44img.com">📖 文档</a> •
  <a href="#-预览">预览</a> •
  <a href="#-特性">特性</a> •
  <a href="#-快速开始">快速开始</a>
</p>

---

## 📸 预览

<details>
<summary>点击展开截图</summary>

### 首页上传
![首页](https://44img.com/uploads/dYug0235.png)

### 图片管理
![我的图片](https://44img.com/uploads/QwqIQqh3.png)

### 相册管理
![相册详情](https://44img.com/uploads/7whRigip.png)

### 管理后台
![仪表盘](https://44img.com/uploads/FrtAcW0T.png)
![系统设置](https://44img.com/uploads/IdWYaFTg.png)

### 深色模式
![深色模式](https://44img.com/uploads/zSa9hOl0.png)

</details>

---

## ✨ 特性

### 核心功能
- **多方式上传**：拖拽、点击、Ctrl+V 粘贴，支持批量上传
- **智能压缩**：可调节压缩质量，PNG/WebP/GIF 保留原格式
- **相册管理**：分类整理，支持公开/私有，批量操作
- **多格式链接**：直链、Markdown、HTML、BBCode 一键复制
- **公开画廊**：展示公开相册，支持导出和打包下载

### 用户与安全
- **用户系统**：邮箱注册验证、密码重置、登录保护
- **频率限制**：分钟/小时/天三级限制，游客和用户独立配置
- **自动封禁**：违规达阈值自动封禁，支持申诉
- **审计日志**：完整记录所有操作
- **内容审核**：可接入阿里云/腾讯云/百度审核服务

### 存储与备份
- **多云存储**：本地 / 阿里云 OSS / 腾讯云 COS / S3 兼容
- **多节点备份**：FTP / SFTP / S3 / WebDAV，支持实时/定时同步
- **凭证加密**：AES-256-GCM 加密存储

### 其他
- **国际化**：简体中文、繁体中文、English
- **深色模式**：自动跟随系统
- **响应式设计**：完美适配桌面和移动端
- **后台管理**：可视化配置，无需修改配置文件

---

## 🚀 快速开始

### 环境要求

- Python 3.10+ / Node.js 18+ / MySQL 8.0+
- Linux: `apt install libmagic1`

### 安装

```bash
git clone https://github.com/globeglobefish/forimage.git
cd forimage

# 数据库
mysql -u root -p -e "CREATE DATABASE imgbed CHARACTER SET utf8mb4;"
mysql -u root -p imgbed < database/init.sql

# 后端
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 前端
cd ../frontend && npm install
```

### 配置

```bash
cp .env.example .env
```

编辑 `.env`（仅需 3 项必填）：

```bash
APP_SECRET_KEY=your-random-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/imgbed
```

> 💡 其他配置（站点、存储、邮件、安全等）均可在管理后台设置。

### 运行

```bash
# 后端
cd backend && uvicorn app.main:app --port 8000

# 前端
cd frontend && npm run dev
```

访问 http://localhost:3000，默认管理员：`admin` / `Admin123`

---

## 📦 部署

详细部署指南请参考 **[官方文档](https://docs.44img.com)**

---

## 🛠️ 技术栈

| 后端 | 前端 |
|------|------|
| FastAPI | Vue 3 + Vite |
| SQLAlchemy + MySQL | Pinia + Vue Router |
| Pillow + python-jose | Element Plus + ECharts |

---

## 📁 项目结构

```
forimage/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── models/   # 数据模型
│   │   ├── services/ # 业务逻辑
│   │   └── utils/    # 工具函数
│   └── uploads/      # 本地存储
├── frontend/         # Vue 3 前端
│   └── src/
└── database/         # 数据库脚本
```

---

## 📄 许可证

[MIT License](LICENSE)

---

<p align="center">
  如果这个项目对你有帮助，欢迎 ⭐ Star 支持！
</p>
