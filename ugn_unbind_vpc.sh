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
	# 提取 UGN 列表
	echo "正在查询 UGN 列表..."
	timestamp=$(date +%s)000	
	offset=0
	limit=100
	all_ugns=""		
	# 执行请求
	response=$(curl -X POST 'https://api.ucloud.cn/?Action=ListUGN' \
			"${COMMON_HEADERS[@]}" \
			-H 'Content-Type: application/json' \
			--data-raw "{\"ProjectId\":\"${PROJECT_ID}\",\"Zone\":\"${ZONE}\",\"Region\":\"${REGION}\",\"Limit\":${limit},\"Offset\":${offset},\"Action\":\"ListUGN\",\"_timestamp\":${timestamp}}")

		if echo "$response" | jq -e 'length == 0' > /dev/null; then
			echo "查询 UGN 列表失败: $response"
			exit 1
		fi

		# Check if UGNs field exists and is not empty
		if ! echo "$response" | jq -e '.UGNs' > /dev/null; then
			echo "UGNs 字段不存在"
			break
		fi

		# Get current batch of UGNs
		current_ugns=$(echo "$response" | jq -r '.UGNs[].UGNID')

		# If no UGNs returned, break the loop
		if [ -z "$current_ugns" ]; then
			break
		fi

		# Append current UGNs to all_ugns with proper newline separation
		all_ugns="${all_ugns}$(echo -e "$current_ugns\n")"
	# Remove empty lines and duplicates
	ugns=$(echo -e "$all_ugns" | grep . | sort -u)

	if [ -z "$ugns" ]; then
		echo "未找到任何 UGN"
		exit 0
	fi

	echo "找到以下 UGN："
	echo "$ugns"

	#   read -p "是否确认解绑这些 UGN？(y/n) " -n 1 -r
	#   echo
	#   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
	#     echo "操作已取消"
	#     exit 1
	#   fi

	# 遍历并执行删除操作
	for ugnid in $ugns; do
		sleep 1
		echo "正在解绑 UGN: $ugnid"
		timestamp=$(date +%s)000

		networksResponse=$(curl -X POST 'https://api.ucloud.cn/?Action=GetUGNNetworks' \
			"${COMMON_HEADERS[@]}" \
			-H 'Content-Type: application/json' \
			--data-raw "{\"ProjectId\":\"${PROJECT_ID}\",\"Zone\":\"${ZONE}\",\"Region\":\"${REGION}\",\"UGNID\":\"${ugnid}\",\"Action\":\"GetUGNNetworks\",\"_timestamp\":${timestamp}}") > /dev/null

		if ! echo "$networksResponse" | jq empty; then
			echo "查询 UGN 绑定网络实例失败: $networksResponse"
			exit 0
		fi

        networks=$(echo "$networksResponse" | jq -r '.Networks[].NetworkID')
		if [ -z "$networks" ]; then
			echo "未找到任何 UGN 绑定网络实例"
			continue
		fi

		network_string=""
        i=0
		for network in $networks; do
			network=${network//\"/} # Remove quotes from the network ID
			encoded_network=$(urlencode "Networks[$i]")
			network_string+="$encoded_network=$network&"
			i=$((i + 1))
		done

		# Remove the trailing '&'
		network_string=${network_string%&}
		if [ -z "$network_string" ]; then
			continue
		fi

		curl 'https://api.ucloud.cn/?Action=DetachUGNNetworks' \
			"${COMMON_HEADERS[@]}" \
			-H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
			--data-raw "ProjectId=${PROJECT_ID}&Region=${REGION}&UGNID=${ugnid}&Action=DetachUGNNetworks&_timestamp=${timestamp}&${network_string}" > /dev/null

		echo -e "\n解绑完成..."
	done

	echo "所有 UGN 解绑 VPC 操作已完成！"
}

start $@
