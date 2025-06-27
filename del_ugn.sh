#!/bin/bash

# 引入通用头信息
source "$(dirname "$0")/common_headers.sh"

usage() {
	echo "Usage: $0 <ProjectId> <Region> <Zone>"
	echo "Example: $0 org-xxxxx cn-bj2 cn-bj2-01"
	exit 1
}

# Check if all parameters are provided
if [ $# -ne 3 ]; then
	usage
fi

PROJECT_ID=$1
REGION=$2
ZONE=$3

start() {
	# 提取 UGNID 列表
	echo "正在查询 UGN 列表..."
	timestamp=$(date +%s)000

	# 执行请求
	response=$(curl -X POST 'https://api.ucloud.cn/?Action=ListUGN' \
		"${COMMON_HEADERS[@]}" \
		-H 'Content-Type: application/json' \
		--data-raw "{\"ProjectId\":\"${PROJECT_ID}\",\"Zone\":\"${ZONE}\",\"Region\":\"${REGION}\",\"Limit\":2000,\"Offset\":0,\"Action\":\"ListUGN\",\"_timestamp\":${timestamp}}")

	if ! echo "$response" | jq empty; then
		echo "查询 UGN 失败: $response"
		exit 0
	fi

	if ! echo "$response" | jq -e '.UGNs' > /dev/null; then
		echo "未找到任何 UGN"
		exit 0
	fi

	# Parse the UGN IDs
	ugns=$(echo "$response" | jq -r '.UGNs[].UGNID')

	if [ -z "$ugns" ]; then
		echo "未找到任何 UGN"
		exit 0
	fi

    echo "找到以下 UGN："
	echo "$ugns"

	# read -p "是否确认删除这些 UGN？(y/n) " -n 1 -r
	# echo
	# if [[ ! $REPLY =~ ^[Yy]$ ]]; then
	#   echo "操作已取消"
	#   exit 1
	# fi

	# 遍历并执行删除操作
	for ugnid in $ugns; do
		echo "正在删除 UGN: $ugnid"
		delete_timestamp=$(date +%s)000

		curl -X POST 'https://api.ucloud.cn/?Action=DelUGN' \
			"${COMMON_HEADERS[@]}" \
			-H 'Content-Type: application/json' \
			--data-raw "{\"ProjectId\":\"${PROJECT_ID}\",\"Zone\":\"${ZONE}\",\"Region\":\"${REGION}\",\"UGNID\":\"${ugnid}\",\"Action\":\"DelUGN\",\"_timestamp\":${delete_timestamp}}" > /dev/null

		echo -e "\n删除完成，等待 1 秒..."
		sleep 1
	done

	echo "所有 UGN 删除操作已完成！"
}

start $@
