import time
import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost:8000/tasks/1"
TOTAL_REQUESTS = 500  # 总请求数
MAX_WORKERS = 10       # 并发数，根据你电脑性能调整

print(f"开始压测：{URL}")
print(f"总请求数：{TOTAL_REQUESTS}，并发数：{MAX_WORKERS}")
print("-" * 50)

success = 0
fail = 0

def make_request():
    global success, fail
    try:
        res = requests.get(URL, timeout=5)
        if res.status_code == 200:
            success += 1
        else:
            fail += 1
    except Exception as e:
        fail += 1

start = time.time()

# 用多线程压测，模拟并发请求
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(make_request) for _ in range(TOTAL_REQUESTS)]
    # 等待所有请求完成
    for i, future in enumerate(futures):
        future.result()
        if (i + 1) % 50 == 0:
            print(f"已完成：{i+1}/{TOTAL_REQUESTS}")

end = time.time()
duration = end - start
qps = success / duration if duration > 0 else 0
avg_latency = (duration / success) * 1000 if success > 0 else 0

print("-" * 50)
print("📊 压测结果：")
print(f"总耗时：{duration:.2f} 秒")
print(f"成功请求：{success}/{TOTAL_REQUESTS}")
print(f"失败请求：{fail}/{TOTAL_REQUESTS}")
print(f"QPS：{qps:.2f} 次/秒")
print(f"平均延迟：{avg_latency:.2f} 毫秒")
print("-" * 50)