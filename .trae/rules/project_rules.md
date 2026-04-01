# 项目规则

## 本地修改后重新打包部署命令

每次修改前端代码后，依次执行以下 3 条命令：

```bash
# 1. 构建前端
cd /Users/zhangziyuan/Documents/productdb/web && npm run build

# 2. 复制构建产物到 nginx 容器
podman cp /Users/zhangziyuan/Documents/productdb/web/dist/. productdb-web:/usr/share/nginx/html/

# 3.（可选）如果修改了后端代码，重启 API 容器
cd /Users/zhangziyuan/Documents/productdb && podman-compose restart api
```

## 常用容器操作

```bash
# 查看所有容器状态
podman ps -a

# 重启所有服务（解决 502 网络问题）
cd /Users/zhangziyuan/Documents/productdb && podman-compose down && podman-compose up -d

# 查看容器日志
podman logs productdb-api --tail 50
podman logs productdb-web --tail 50

# 进入 API 容器执行命令
podman exec -it productdb-api bash
```

## 访问地址

- 前端: http://localhost:3001
- API: http://localhost:8001
- 数据库: localhost:5433

## 提示信息规范

所有提示信息统一使用 `showMessage` 函数（基于 Vant Dialog），**禁止使用 `showToast`**。

```typescript
import { showMessage } from '@/utils/request'

showMessage('提示信息内容')
```

特点：
- 点击「确定」才关闭，不会自动消失
- 无动画延迟，文字立即可见
- 标题为「提示」，按钮为「确定」
