"""
测试火山方舟 API 调用
"""
import requests
import json

# API 配置
api_key = "056d2839-c0d6-490c-9227-d7acb6a188fd"
base_url = "https://ark.cn-beijing.volces.com/api/v3/responses"

# 请求头
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 测试 1: 使用简单的文本输入
print("测试 1: 简单文本输入")
payload1 = {
    "model": "doubao-seed-2-0-mini-260215",
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "你好，请说一句话"
                }
            ]
        }
    ],
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 100
    }
}

print(f"请求 URL: {base_url}")
print(f"请求头: {headers}")
print(f"请求体: {json.dumps(payload1, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(base_url, headers=headers, json=payload1, timeout=30)
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"错误: {e}")

# 测试 2: 尝试不使用 parameters
print("\n" + "="*70)
print("测试 2: 不使用 parameters")
payload2 = {
    "model": "doubao-seed-2-0-mini-260215",
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "你好，请说一句话"
                }
            ]
        }
    ]
}

try:
    response = requests.post(base_url, headers=headers, json=payload2, timeout=30)
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"错误: {e}")

# 测试 3: 尝试使用 messages 格式
print("\n" + "="*70)
print("测试 3: 使用 messages 格式")
payload3 = {
    "model": "doubao-seed-2-0-mini-260215",
    "messages": [
        {
            "role": "user",
            "content": "你好，请说一句话"
        }
    ]
}

try:
    response = requests.post(base_url, headers=headers, json=payload3, timeout=30)
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"错误: {e}")

# 测试 4: 尝试使用 chat/completions 端点
print("\n" + "="*70)
print("测试 4: 使用 chat/completions 端点")
chat_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
payload4 = {
    "model": "doubao-seed-2-0-mini-260215",
    "messages": [
        {
            "role": "user",
            "content": "你好，请说一句话"
        }
    ]
}

try:
    response = requests.post(chat_url, headers=headers, json=payload4, timeout=30)
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"错误: {e}")
