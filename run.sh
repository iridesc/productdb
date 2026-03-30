#!/bin/bash
set -e

# PostgreSQL
echo "Starting PostgreSQL..."
podman run -d \
  --name erp-postgres \
  -e POSTGRES_USER=erp_user \
  -e POSTGRES_PASSWORD=erp_password \
  -e POSTGRES_DB=erp_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  registry.cn-hangzhou.aliyuncs.com/library/postgres:15-alpine

echo "PostgreSQL started!"
podman ps
