## 1. Fix ProductSelector

- [x] 1.1 Remove `is_active: true` from `loadProducts` query params in `ProductSelector.vue`, changing `{ page_size: 100, is_active: true }` to `{ page_size: 100 }`

## 2. Verify

- [x] 2.1 Build frontend: `cd web && npm run build`
- [x] 2.2 Deploy with Podman: `podman compose up -d`
- [x] 2.3 Verify: Open sales order creation page, click "添加产品", confirm product list shows available materials
