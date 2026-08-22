FROM docker.m.daocloud.io/library/python:3.11-slim

WORKDIR /app

# 安装 Python 依赖（放在最前面，仅 requirements.txt 变更才重新安装）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码 + 迁移脚本
COPY app/ ./app/
# MCP Server（作为包集成，提供 /mcp 端点）
COPY mcp-server/ ./mcp_server/
COPY alembic.ini .

# 复制前端构建产物（变化最频繁，放最后以利用上层缓存）
COPY web/dist/ ./web/dist/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]