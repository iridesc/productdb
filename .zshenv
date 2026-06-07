export http_proxy="http://127.0.0.1:11001"
export https_proxy="http://127.0.0.1:11001"

# 绕过局域网和本地地址（不走代理）
export no_proxy="localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,127.0.0.1/8,*.local,::1"

# 同时定义大写版本，以防某些挑剔的命令行工具只认大写
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export NO_PROXY="$no_proxy"
