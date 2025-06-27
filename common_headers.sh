#!/bin/bash

# 读取 cookie 信息
headers=$(<header.txt)
tokens=$(<token.txt)
# 定义通用的 HTTP 头信息
COMMON_HEADERS=(
	-b "$headers"
	-H "U-CSRF-Token: $tokens"
)

urlencode() {
	local length="${#1}"
	for ((i = 0; i < length; i++)); do
		local c="${1:i:1}"
		case $c in
		[a-zA-Z0-9.~_-]) printf "%s" "$c" ;;
		*) printf "%%%02X" "'"$c"'" ;;
		esac
	done
}
