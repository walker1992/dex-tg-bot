# DEX Trading Telegram Bot

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-development-orange.svg)]()

一个功能完整的Telegram交易机器人，支持在Hyperliquid和Aster交易所进行现货和期货交易。提供用户友好的界面，支持订单管理、仓位监控、资金费率查询以及智能报警功能。

## ✨ 主要功能

### 🔄 多交易所支持
- **Hyperliquid**: 去中心化永续合约交易
- **Aster**: 现货和期货交易
- 统一的交易接口，支持快速扩展

### 📊 交易功能
- **现货交易**: 支持BTC, ETH等主要币种
- **期货交易**: 永续合约和交割合约
- **订单管理**: 限价单、市价单、止损单、止盈单
- **仓位管理**: 开仓、平仓、部分平仓

### 🚨 智能报警
- **价格报警**: 价格突破、区间报警
- **资金费率报警**: 费率异常监控
- **仓位报警**: 盈亏、保证金率监控
- **技术指标报警**: RSI, MACD等指标

### 🛡️ 风险管理
- **仓位限制**: 最大仓位大小控制
- **日损失限制**: 每日最大损失控制
- **紧急停止**: 一键停止所有交易
- **权限管理**: 多用户权限控制

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Telegram Bot Token
- Hyperliquid账户 (可选)
- Aster账户 (可选)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/walker1992/dex-tg-bot.git
cd dex-tg-bot
```

2. **创建conda环境**
```bash
conda create -n dex-tg-bot python=3.10
conda activate dex-tg-bot
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置设置**
```bash
# 复制配置示例文件
cp config/config.example.json config/config.json

# 编辑配置文件
nano config/config.json
```

5. **获取Telegram Bot Token**
   - 在Telegram中搜索 `@BotFather`
   - 发送 `/newbot` 命令
   - 按提示设置机器人名称和用户名
   - 获取Bot Token并配置到config.json

6. **获取Chat ID**
   - 将机器人添加到群组或私聊
   - 发送消息给机器人
   - 访问 `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - 从返回的JSON中找到chat ID

7. **配置交易所API**
在`config/config.json`中配置交易所信息：
- **Hyperliquid**: 需要账户地址和私钥
- **Aster**: 需要API Key和Secret

8. **启动机器人**
```bash
# 确保conda环境已激活
conda activate dex-tg-bot

# 启动机器人
python src/main.py
```

## 📋 配置说明

### 配置文件说明

项目使用单一的`config.json`文件进行配置管理，所有配置信息都集中在一个文件中：

```json
{
  "telegram": {
    "bot_token": "your_bot_token_here",
    "chat_id": "your_chat_id_here"
  },
  "exchanges": {
    "hyperliquid": {
      "account_address": "0x...",
      "secret_key": "0x..."
    },
    "aster": {
      "api_key": "your_api_key",
      "api_secret": "your_api_secret"
    }
  }
}
```

### 配置文件结构

项目使用JSON配置文件，支持以下主要配置：

- **telegram**: Telegram Bot配置
- **exchanges**: 交易所配置
- **trading**: 交易参数配置
  - `default_futures_symbols`: 市场数据菜单默认展示的期货基础币种数组（如 `["BTC","ETH","HYPE","ASTER"]`）
- **risk_management**: 风险管理配置
- **alerts**: 报警配置
- **security**: 安全配置

详细配置说明请参考 [配置指南](docs/configuration.md)

## 🤖 命令列表

### 基础命令
- `/start` - 启动机器人
- `/help` - 显示帮助信息
- `/status` - 显示机器人状态
- `/settings` - 用户设置管理

### 账户管理
- `/connect_hyperliquid` - 连接Hyperliquid账户
- `/connect_aster` - 连接Aster账户
- `/disconnect` - 断开交易所连接
- `/accounts` - 查看已连接的账户

### 交易命令
- `/balance [exchange]` - 查询账户余额
- `/positions [exchange]` - 查询当前仓位
- `/orders [exchange]` - 查询当前订单
- `/buy <symbol> <quantity> [price]` - 买入订单
- `/sell <symbol> <quantity> [price]` - 卖出订单
- `/close <symbol>` - 平仓
- `/cancel <order_id>` - 取消订单

### 市场数据
- `/price <symbol>` - 查询价格
- `/depth <symbol>` - 查询深度
- `/funding <symbol>` - 查询资金费率
- `/24h <symbol>` - 24小时价格变化

#### 市场数据菜单（期货）
- 在主菜单选择 `📈 Market Data`，支持：
  - **Price**: 展示默认期货币种（可配置）的最新价、买一/卖一、点差与百分比
  - **Depth**: 展示默认期货币种的前 5 档买卖盘
  - **Funding Rate**: 展示默认期货币种的当前资金费率
- 默认展示的期货基础币种通过 `trading.default_futures_symbols` 配置，默认值为 `BTC, ETH, HYPE, ASTER`
- 符号规范：
  - **Hyperliquid**: 使用基础名（如 `BTC`, `ETH`）
  - **Aster**: 使用 `BASEUSDT`（如 `BTCUSDT`, `ETHUSDT`）

### 报警管理
- `/alert_price <symbol> <condition> <value>` - 设置价格报警
- `/alert_funding <symbol> <value>` - 设置资金费率报警
- `/alert_position <symbol> <condition> <value>` - 设置仓位报警
- `/alerts` - 查看所有报警
- `/delete_alert <alert_id>` - 删除报警

## 🐳 Docker部署

### 使用Docker Compose

```bash
# 配置config.json文件
cp config/config.example.json config/config.json
# 编辑config/config.json文件

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 单独Docker部署

```bash
# 构建镜像
docker build -t dex-tg-bot .

# 运行容器
docker run -d \
  --name dex-tg-bot \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  dex-tg-bot
```

## 🔧 开发指南

### 项目结构

```
dex-tg-bot/
├── src/                    # 源代码
│   ├── bot/               # Telegram Bot相关
│   ├── services/          # 服务层
│   ├── utils/             # 工具函数
│   └── config/            # 配置管理
├── config/                # 配置文件
├── docs/                  # 文档
├── scripts/               # 脚本文件
└── tests/                 # 测试文件
```

### 开发环境设置

```bash
# 激活conda环境
conda activate dex-tg-bot

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest

# 代码格式化
black src/
isort src/

# 类型检查
mypy src/
```

### 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📚 文档

- [安装指南](docs/installation.md)
- [配置指南](docs/configuration.md)
- [API文档](docs/api.md)
- [故障排除](docs/troubleshooting.md)
- [项目设计](project.md)

## 🛡️ 安全注意事项

- **API密钥安全**: 使用环境变量存储敏感信息
- **权限控制**: 设置适当的用户权限
- **网络安全**: 使用HTTPS和安全的网络连接
- **定期更新**: 保持依赖包和系统更新

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 支持

- **问题报告**: [GitHub Issues](https://github.com/walker1992/dex-tg-bot/issues)
- **功能请求**: [GitHub Discussions](https://github.com/walker1992/dex-tg-bot/discussions)
- **社区交流**: [Discord服务器](https://discord.gg/your-invite)

## ⚠️ 免责声明

本软件仅供学习和研究使用。使用本软件进行实际交易的风险由用户自行承担。开发者不对任何交易损失负责。请在使用前充分了解相关风险。

## 🗺️ 路线图

### 第一阶段 (MVP)
- [x] 基础项目架构
- [x] Telegram Bot集成
- [x] Hyperliquid API集成
- [x] Aster API集成
- [x] 基础交易功能
- [x] 配置管理系统

### 第二阶段
- [ ] 高级订单类型
- [ ] 实时数据流
- [ ] 用户权限管理
- [ ] 交易历史记录
- [ ] Docker容器化

### 第三阶段
- [ ] 多交易所支持
- [ ] 高级策略
- [ ] 移动端优化
- [ ] 社区功能

---

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**
