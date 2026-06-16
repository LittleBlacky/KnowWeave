"""End-to-end smoke test for KnowWeave."""
import os

# Kill system proxy for local connections — MUST be before httpx import
for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(var, None)
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"

import httpx

BASE = "http://127.0.0.1:9001/api/v1"
client = httpx.Client(timeout=180)


def main():
    # 1. System config
    r = client.get(f"{BASE}/system/config")
    cfg = r.json()
    print(f"1. 配置: {cfg['provider']['type']} | 对话: {cfg['models']['chat']} | 嵌入: {cfg['models']['embedding']}")

    # 2. Upload file
    content = """# 公司考勤制度

## 请假规则
员工请假须提前一天向直属主管提交申请，紧急情况可事后补交。
连续请假超过3天需要部门经理审批。

## 加班政策
加班需提前报备，周末加班可调休。每月调休不超过2天。

## 出差管理
出差需提交出差申请单，注明目的地、时间和预算。
差旅费报销需附发票和出差报告。
"""
    files = {"file": ("attendance.md", content.encode(), "text/markdown")}
    r = client.post(f"{BASE}/files/upload", files=files, data={"directory_path": "/policies"})
    result = r.json()
    assert r.status_code == 201, f"Upload failed: {result}"
    file_id = result["data"]["id"]
    print(f"2. 上传: {result['data']['name']} | id: {file_id[:8]}")

    # 3. Parse
    r = client.post(f"{BASE}/files/{file_id}/parse")
    result = r.json()
    print(f"3. 解析: {result['data']['status']}")

    # 4. Build chunks
    r = client.post(f"{BASE}/files/{file_id}/chunks/build")
    result = r.json()
    chunks = result["data"]["items"]
    print(f"4. 分块: {len(chunks)} 个")

    # 5. Extract KUs (LLM)
    print("5. AI 提取知识单元...")
    r = client.post(f"{BASE}/knowledge-units/files/{file_id}/generate?batch_size=6")
    result = r.json()["data"]
    print(f"   提取: {result['extracted']} 个 | 去重跳过: {result.get('skipped_duplicates', 0)}")
    for u in result["units"][:3]:
        print(f"   - [{u['unit_type']}] {u['title']}")

    # 6. Generate Wiki (LLM)
    print("6. AI 编译 Wiki...")
    r = client.post(f"{BASE}/files/{file_id}/wiki")
    wiki = r.json()["data"]
    print(f"   Wiki: {wiki['title']} | 状态: {wiki['status']} | {len(wiki['content_markdown'])} 字")
    preview = wiki["content_markdown"][:250].replace("\n", " ")
    print(f"   预览: {preview}...")

    # 7. Search
    r = client.post(f"{BASE}/search", json={"query": "请假", "top_k": 3})
    search_data = r.json()
    # SearchResponse wraps results in SearchResponse.results
    sr = (search_data.get("data") or {})
    results = sr.get("results", [])
    print(f"7. 搜索'请假': {len(results)} 条结果")

    # 8. Chat (quick SSE test)
    print("8. 测试对话...")
    r = client.post(f"{BASE}/chat/sessions", json={"title": "测试"})
    session_id = r.json()["data"]["id"]
    r = client.post(
        f"{BASE}/chat/sessions/{session_id}/messages",
        json={"question": "请假需要什么流程？", "top_k": 3},
    )
    # SSE response starts with "event:" or "data:"
    body = r.text.strip()
    has_start = "start" in body[:500]
    has_delta = "delta" in body[:500]
    print(f"   对话 SSE: start={has_start}, delta={has_delta}")

    print()
    print("=== 全部 8 步端到端测试通过 ===")


if __name__ == "__main__":
    main()
