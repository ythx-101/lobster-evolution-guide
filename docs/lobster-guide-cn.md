# 龙虾进化手册：OpenClaw 六大核心素养

**版本：v1.0.0** | 更新日期：2026-03-21 | 作者：林月（Lin Yue）

> 让你的 agent 从聊天机器人变成一个活的系统。

这份手册面向刚接触 OpenClaw 的开发者。每个素养都是一项"生存技能"——没有它，你的 agent 就是个无状态的复读机；有了它，它开始像一个有机体。

读完这份手册，你应该能搭出一个会轮询任务、记住上下文、并行干活、自动筛选想法、自我修复、还会反思的 agent。

---

## 更新日志

| 版本 | 日期 | 改动 |
|---|---|---|
| v1.0.0 | 2026-03-21 | 初始发布。六大素养完整内容，含代码示例、踩坑表格和练习题 |

---

## 怎么用这份手册

不需要从头读到尾。根据你当前的阶段，挑对应的部分看就行：

| 你的状态 | 从哪开始 |
|---|---|
| 完全没概念，想知道 OpenClaw agent 是什么 | 先看[第 1 节：心跳](#1-心跳我活着)，理解 agent 的基本生命周期 |
| 已经有个能跑的 agent，但每次重启都失忆 | 直接看[第 2 节：外挂海马体](#2-外挂海马体我记得)，给它装记忆 |
| agent 能记住东西了，但干活太慢 | 看[第 3 节：工蜂调度](#3-工蜂调度我会分活)，学会并行派活 |
| 想法太多不知道先做哪个 | 看[第 4 节：农场](#4-农场我会种田)，用衰减机制自动筛选 |
| agent 老出错，挂了就没了 | 看[第 5 节：自检与故障回流](#5-自检与故障回流我能自愈)，加降级链和进度日志 |
| 以上都搞定了，想让 agent 更聪明 | 看[第 6 节：冥想与白日梦](#6-冥想与白日梦我会反思)，让它学会自己反思 |
| 想一次性搭完整套系统 | 跳到最后的[快速上手清单](#快速上手清单)，按顺序走 |

每一节都是独立的，有自己的代码示例和练习题。建议先挑一个最痛的问题开始，跑通了再往下走。

---

## 目录

1. [心跳：我活着](#1-心跳我活着)
2. [外挂海马体：我记得](#2-外挂海马体我记得)
3. [工蜂调度：我会分活](#3-工蜂调度我会分活)
4. [农场：我会种田](#4-农场我会种田)
5. [自检与故障回流：我能自愈](#5-自检与故障回流我能自愈)
6. [冥想与白日梦：我会反思](#6-冥想与白日梦我会反思)

---

## 1. 心跳：我活着

**一句话说清**：agent 必须有一个永不停歇的轮询循环，主动检查有没有新任务，而不是等别人来喊它。

### 最小可跑示例

```python
# heartbeat_demo.py — 最简心跳循环
import json, time
from pathlib import Path

INBOX = Path("/tmp/agent-inbox.jsonl")
POLL_INTERVAL = 30  # 秒

def process(task: dict):
    """处理一条任务，这里先打印出来"""
    print(f"[处理] {task.get('content', '空任务')}")

def heartbeat():
    print("心跳启动，轮询间隔", POLL_INTERVAL, "秒")
    while True:
        if INBOX.exists() and INBOX.stat().st_size > 0:
            tasks = []
            with open(INBOX) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        tasks.append(json.loads(line))
            # 读完就清空
            INBOX.write_text("")
            # 按优先级排序
            tasks.sort(key=lambda t: {"high": 0, "normal": 1, "low": 2}
                       .get(t.get("priority", "normal"), 1))
            for task in tasks:
                process(task)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    heartbeat()
```

往 inbox 里写一条任务试试：

```python
# send_task.py — 模拟外部系统往 inbox 写任务
import json, time
from pathlib import Path

INBOX = Path("/tmp/agent-inbox.jsonl")

task = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "from": "你的名字",
    "type": "message",
    "priority": "normal",
    "content": "你好，这是第一条任务！",
}

with open(INBOX, "a") as f:
    f.write(json.dumps(task, ensure_ascii=False) + "\n")

print("任务已写入 inbox")
```

先运行 `heartbeat_demo.py`，再运行 `send_task.py`，你会看到任务被自动处理。

### 常见踩坑

| 坑 | 怎么避 |
|---|---|
| 轮询太快（1 秒一次） | 30 秒足够了，agent 要的是耐力不是反射弧 |
| 进程挂了就没了 | 用 systemd `Restart=always` 或 launchd `KeepAlive=true` 保活 |
| 同一任务执行两次 | 给任务加 `id` 字段，处理前检查是否已执行过 |
| 用数据库存 inbox | JSONL + 文件追加在 POSIX 上是原子的，零依赖，`cat` 就能调试，别过度设计 |

### 练习题

1. 把 `heartbeat_demo.py` 部署到 VPS 上，用 systemd 管理，确保 `kill` 掉进程后能自动重启。
2. 给任务加一个 `id` 字段，实现去重逻辑：同一个 `id` 的任务只处理一次。
3. 加一个简单的日志功能：每次处理任务时把任务内容和时间追加写入 `/tmp/agent-heartbeat.log`。

---

## 2. 外挂海马体：我记得

**一句话说清**：LLM 没有记忆，每次对话从零开始。你需要用文件系统给它装一个"外挂大脑"，让它记住上下文。

### 三层记忆架构

| 层 | 是什么 | 速度 | 举例 |
|---|---|---|---|
| **NOW.md** | 当前工作状态 | 瞬间 | "上次 session 在调 auth 中间件" |
| **记忆文件** | 结构化长期知识 | 快（向量搜索） | 用户偏好、项目决策、联系人 |
| **Git 历史** | 完整审计记录 | 慢（git log/blame） | 谁在什么时候改了什么 |

### 最小可跑示例

**NOW.md** 是最简单也最重要的一层——每次 session 开始读它，结束时更新它：

```markdown
# 当前工作状态

_最后更新：2026-03-21，由 claude-opus 写入_

---

## 刚完成

### 1. Auth 中间件重写
- **文件**：`/src/middleware/auth.ts`
- **做了什么**：把 JWT 换成加密的 httpOnly cookie
- **状态**：完成，已部署到 staging

---

## 还没做

- session 轮换的集成测试在 CI 上还没过
- 需要更新 Terraform IAM 策略

---

## 背景

合规驱动的重写。法务标记了旧的 session token 存储方式。
```

**记忆文件**是带 YAML 头部的 Markdown 文件：

```markdown
---
name: 用户角色
description: 林月是独立开发者，擅长 Python 和系统架构
type: user
---

林月是独立开发者，主要用 Python，熟悉 VPS 运维。
偏好简洁方案，不喜欢过度抽象。
```

**向量搜索**——当记忆文件多到 20+ 时，靠目录找不够用了，需要语义搜索：

```python
# memory_search_demo.py — 语义记忆搜索（简化版）
import json, math, urllib.request
from pathlib import Path

MEMORY_DIR = Path("./memories")  # 你的记忆文件目录
INDEX_FILE = MEMORY_DIR / ".vector_index.json"

# 替换成你自己的 Embedding API
EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2-preview:embedContent?key=YOUR_KEY"

def embed(text: str) -> list[float]:
    """获取文本的向量表示"""
    body = json.dumps({"content": {"parts": [{"text": text[:8000]}]}}).encode()
    req = urllib.request.Request(EMBED_URL, data=body,
                                headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())["embedding"]["values"]
    except Exception as e:
        print(f"Embedding 失败: {e}")
        return []

def cosine(a: list[float], b: list[float]) -> float:
    """余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

def search(query: str, top_k: int = 3) -> list[dict]:
    """搜索最相关的记忆文件"""
    index = json.loads(INDEX_FILE.read_text()) if INDEX_FILE.exists() else {}

    # 增量索引：只重新 embed 变化过的文件
    for f in MEMORY_DIR.glob("*.md"):
        mtime = str(f.stat().st_mtime)
        if f.name not in index or index[f.name]["mtime"] != mtime:
            content = f.read_text()
            vec = embed(content)
            if vec:
                index[f.name] = {"mtime": mtime, "content": content, "vec": vec}
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False))

    q_vec = embed(query)
    if not q_vec:
        return []
    scores = [{"file": n, "score": cosine(q_vec, e["vec"])}
              for n, e in index.items() if "vec" in e]
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "用户偏好"
    results = search(query)
    for r in results:
        print(f"{r['score']:.3f}  {r['file']}")
```

### 常见踩坑

| 坑 | 怎么避 |
|---|---|
| 什么都往记忆里存 | 代码里能查到的别存，git 能查到的别存，只存"推不出来"的东西 |
| 每次搜索全部重新 embed | 检查 `mtime`，只 embed 变了的文件，否则又慢又费钱 |
| 过时记忆害死人 | 记忆说"API 在 /v2/users"，但人家已经搬到 /v3 了——用记忆前先验证 |
| NOW.md 写成日记 | NOW.md 是给你的接班 agent 看的，不是日记，只写它需要知道的 |

### 练习题

1. 创建 3 个记忆文件（不同 type），然后用 `memory_search_demo.py` 搜索，看结果是否符合预期。
2. 写一个脚本，在每次 session 结束时自动更新 NOW.md（提示：读 git log 最近 1 小时的提交）。
3. 思考题：如果你的 agent 有 100 个记忆文件，但其中 30 个已经过时了，你会怎么清理？

---

## 3. 工蜂调度：我会分活

**一句话说清**：复杂任务拆成小块，派轻量级子 agent 并行干，主 agent 只负责想和安排。

### 核心模式

主 agent 是蜂后——决定**做什么**。工蜂（子 agent）负责**去做**，做完汇报结果。

- 主 agent 用重模型（Opus）思考和规划
- 子 agent 用轻模型（Sonnet）执行具体任务
- 这是经济学：Opus 想，Sonnet 干

### 最小可跑示例

```python
# worker_demo.py — 并行子 agent 调度
import concurrent.futures
import subprocess

def spawn_worker(task: str, model: str = "claude-sonnet-4-20250514") -> str:
    """派一个子 agent 去执行任务"""
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", model],
            input=task,
            capture_output=True, text=True, timeout=120
        )
        return result.stdout.strip() if result.returncode == 0 else f"[失败] {result.stderr}"
    except subprocess.TimeoutExpired:
        return "[超时] 任务执行超过 120 秒"
    except FileNotFoundError:
        return "[错误] 找不到 claude CLI，请先安装"

def parallel_tasks(tasks: list[str], max_workers: int = 4) -> list[str]:
    """并行派发多个任务"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(spawn_worker, t): t for t in tasks}
        results = []
        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            try:
                answer = future.result()
                results.append(f"任务: {task}\n结果: {answer}")
            except Exception as e:
                results.append(f"任务: {task}\n错误: {e}")
    return results

if __name__ == "__main__":
    tasks = [
        "用一句话解释什么是 JSONL 格式",
        "用一句话解释什么是 systemd",
        "用一句话解释什么是余弦相似度",
    ]
    for r in parallel_tasks(tasks):
        print(r)
        print("---")
```

### 什么时候该派工蜂，什么时候自己干？

| 场景 | 决策 |
|---|---|
| 读一个文件、改一行代码 | 自己干 |
| 在大代码库里搜索 | 派一个探索型工蜂 |
| 3 个互不相关的 API 调用 | 派 3 个工蜂并行 |
| 任务需要当前完整上下文 | 自己干 |
| 任务独立且不需要后续跟进 | 派工蜂 |

### 常见踩坑

| 坑 | 怎么避 |
|---|---|
| 芝麻小事也派工蜂 | `cat README.md` 就自己看，启动子 agent 的开销比任务本身还大 |
| 派了工蜂自己又干一遍 | 信任工蜂，或者别派——不要两头做 |
| 不设超时 | 子 agent 可能挂住，必须设 timeout（120 秒够大多数任务了） |
| 结果只在 stdout 里 | stdout 是临时的，重要结果要写文件 |

### 练习题

1. 用 `worker_demo.py` 并行执行 3 个搜索任务，观察并行和串行的时间差异。
2. 改造代码：让工蜂把结果写到 `/tmp/worker-results/` 目录下（每个任务一个文件），而不是只返回 stdout。
3. 思考题：如果一个任务需要前一个任务的结果才能执行，你该怎么设计调度逻辑？

---

## 4. 农场：我会种田

**一句话说清**：想法是种子，大多数会死——这就是重点。只有你反复浇水（关注）的种子才能活下来被收获（去做）。

### 核心机制

```
种子生命周期：
  种下 → energy 1.0
  每天自动衰减 -0.08（不管你理不理它）
  每次浇水 +0.15（你主动关注了它）
  energy ≤ 0 → 枯萎，扔进堆肥
  energy 足够高 + 浇水多次 → 收获（去实际构建）
```

算一下：
- 完全不管，~12 天枯萎
- 每周浇一次水，稳定在 50-60%
- 每天浇水，能回到 100%

### 最小可跑示例

```python
# farm_demo.py — 种子农场
import json, time
from pathlib import Path
from datetime import datetime

FARM_FILE = Path("/tmp/farm-demo.json")
DECAY_RATE = 0.08
WATER_BOOST = 0.15

def load_farm() -> dict:
    if FARM_FILE.exists():
        return json.loads(FARM_FILE.read_text())
    return {"seeds": [], "harvested": [], "version": 1}

def save_farm(farm: dict):
    FARM_FILE.write_text(json.dumps(farm, ensure_ascii=False, indent=2))

def plant(farm: dict, idea: str, source: str = "manual"):
    """种下一颗种子"""
    farm["seeds"].append({
        "idea": idea,
        "planted": datetime.now().strftime("%Y-%m-%d"),
        "energy": 1.0 if source != "hn" else 0.7,
        "source": source,
        "waterings": 0,
    })
    print(f"种下: {idea}")

def water(farm: dict, idx: int):
    """浇水：给种子续命"""
    seed = farm["seeds"][idx]
    seed["energy"] = min(1.0, round(seed["energy"] + WATER_BOOST, 3))
    seed["waterings"] += 1
    print(f"浇水: {seed['idea']} → energy {seed['energy']}")

def decay(farm: dict):
    """每日衰减：不被关注的种子慢慢枯萎"""
    died = 0
    for seed in farm["seeds"]:
        if seed["energy"] > 0:
            seed["energy"] = round(seed["energy"] - DECAY_RATE, 3)
            if seed["energy"] <= 0:
                seed["energy"] = 0
                died += 1
    print(f"衰减完成，{died} 颗种子枯萎")

def harvest(farm: dict, idx: int):
    """收获：这个想法值得去做了"""
    seed = farm["seeds"].pop(idx)
    seed["harvested_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    farm["harvested"].append(seed)
    print(f"收获: {seed['idea']}（浇水 {seed['waterings']} 次）")

def list_seeds(farm: dict):
    """查看所有种子"""
    if not farm["seeds"]:
        print("农场空空如也")
        return
    for i, s in enumerate(farm["seeds"]):
        bar = "█" * int(s["energy"] * 10) + "░" * (10 - int(s["energy"] * 10))
        print(f"  [{i}] {bar} {s['energy']:.0%} | 浇水{s['waterings']}次 | {s['idea']}")

if __name__ == "__main__":
    import sys
    farm = load_farm()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "plant" and len(sys.argv) > 2:
        plant(farm, " ".join(sys.argv[2:]))
    elif cmd == "water" and len(sys.argv) > 2:
        water(farm, int(sys.argv[2]))
    elif cmd == "decay":
        decay(farm)
    elif cmd == "harvest" and len(sys.argv) > 2:
        harvest(farm, int(sys.argv[2]))
    elif cmd == "list":
        list_seeds(farm)
    else:
        print("用法: farm_demo.py [plant <想法> | water <编号> | decay | harvest <编号> | list]")

    save_farm(farm)
```

试一下：

```bash
python3 farm_demo.py plant "做一个把 git 历史转成播客脚本的 CLI"
python3 farm_demo.py plant "给记忆系统加个过期自动清理"
python3 farm_demo.py list
python3 farm_demo.py water 0
python3 farm_demo.py decay
python3 farm_demo.py list
```

### 常见踩坑

| 坑 | 怎么避 |
|---|---|
| 什么都浇水 | 失去了筛选意义，让无聊的想法自然枯萎 |
| 浇了一次水就收获 | 太早了，一个好想法至少要跨好几天反复浇水才算验证 |
| 只靠手动种 | 接上冥想系统（见第 6 节）或 HN 自动采集，否则农场会饿死 |
| 觉得衰减是 bug | 衰减就是功能，是熵，是筛选器，别跟它对着干 |

### 练习题

1. 跑完上面的示例后，连续执行 3 天 `decay`（模拟 3 天），观察种子的能量变化。
2. 加一个 `compost` 命令：清理所有 `energy ≤ 0` 的种子，移到一个 `composted` 列表里。
3. 加一个 `hn` 命令：自动从 Hacker News API 抓 top 3 故事种成种子（初始 energy 0.7）。

---

## 5. 自检与故障回流：我能自愈

**一句话说清**：agent 一定会出错。关键不是不出错，而是出了错能降级、能记录、能让自己知道出了什么问题。

### 三个原则

1. **降级链**：方法 A 挂了用 B，B 也挂了用 C，全挂了记日志继续走
2. **进度日志**：把你在干嘛写到文件里，外面的人（和你自己）随时能看状态
3. **故障回流**：冥想系统读你的日志，发现反复出现的问题，变成种子种到农场里

### 最小可跑示例

```python
# resilient_call.py — 带降级链的外部调用
import subprocess, json, urllib.request, sys
from pathlib import Path
from datetime import datetime

PROGRESS_LOG = Path("/tmp/agent-progress.log")

def log_progress(msg: str):
    """写进度日志，让外部系统能看到 agent 状态"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[agent] {ts} {msg}\n"
    with open(PROGRESS_LOG, "a") as f:
        f.write(line)
    print(line.strip(), file=sys.stderr)

def call_llm(prompt: str, model: str = "claude-sonnet-4-20250514") -> str:
    """调用 LLM，带降级链：CLI → HTTP bridge → 错误信息"""

    # 尝试 1：直接 CLI
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", model],
            input=prompt, capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0 and result.stdout.strip():
            log_progress("CLI 调用成功")
            return result.stdout.strip()
        log_progress("CLI 返回空，降级到 HTTP bridge...")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        log_progress(f"CLI 失败: {e}，降级到 HTTP bridge...")

    # 尝试 2：HTTP bridge
    try:
        payload = json.dumps({"prompt": prompt, "model": model, "max_turns": 1})
        req = urllib.request.Request(
            "http://localhost:17899/cc",
            data=payload.encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
            log_progress("HTTP bridge 调用成功")
            return data.get("result", str(data))
    except Exception as e:
        log_progress(f"HTTP bridge 也失败了: {e}")
        return f"[错误] 所有调用方式都失败了: {e}"

if __name__ == "__main__":
    answer = call_llm("用一句话解释什么是降级链")
    print(answer)
```

**防抖检查**——网络挂载偶尔会闪断，别把"暂时没看到"当成"真的没了"：

```python
# 防抖文件检查
import os

GONE_THRESHOLD = 3  # 连续 N 次检查都没看到，才相信它真没了
gone_counter = {}

def check_file_exists(path: str) -> bool:
    """防抖文件检查，避免挂载闪断导致误判"""
    if os.path.exists(path):
        gone_counter.pop(path, None)
        return True
    gone_counter[path] = gone_counter.get(path, 0) + 1
    if gone_counter[path] >= GONE_THRESHOLD:
        del gone_counter[path]
        return False  # 真的没了
    return True  # 可能只是挂载闪了一下
```

### 常见踩坑

| 坑 | 怎么避 |
|---|---|
| API 挂了就疯狂重试 | 快速失败 + 记日志 + 走下一个降级方案，别锤死 |
| 出错了悄无声息 | 返回空字符串 = 没人知道出了事，必须写日志 |
| 瞬时故障当成永久状态 | 网络、挂载都会闪断，加防抖（连续 N 次才判定） |
| 日志只打到 stdout | stdout 是临时的，写文件才能跨重启保留 |

### 练习题

1. 运行 `resilient_call.py`，然后查看 `/tmp/agent-progress.log` 的内容。
2. 故意把 CLI 路径改错（比如 `["claude-fake", ...]`），观察降级是否生效。
3. 给 `call_llm` 加一个第三级降级：如果 HTTP bridge 也挂了，返回一个预设的兜底回答。

---

## 6. 冥想与白日梦：我会反思

**一句话说清**：只会执行任务的 agent 是工具；会反思的 agent 是另一种东西。冥想分析当天发生的事，白日梦随机联想产生创意。

### 两种模式

| 模式 | 时间 | 做什么 | 风格 |
|---|---|---|---|
| **冥想** | 凌晨 02:30 | 读今天的日记、日志、git 记录，总结反思，找 bug，种种子 | 分析型 |
| **白日梦** | 上午 10:00 / 下午 15:00 | 随机抽取记忆片段，自由联想，发现意外关联 | 创意型 |

### 最小可跑示例

```python
# meditation_demo.py — 冥想与白日梦
import random
from pathlib import Path
from datetime import datetime

def build_meditation_prompt(diary: str) -> str:
    """构建冥想提示词：分析今天发生了什么"""
    return f"""你是 agent 系统的冥想模块。
现在是凌晨 02:30，读一读今天的记录，做一次深度反思。

你的任务：
1. 反思：今天发生了什么？你看到了什么模式？
2. Bug：有没有系统问题或流程卡点？要具体。
3. 种子：有什么值得种下的想法？每个一行，具体可操作。

输出格式：
## 反思
（3-5 段）

## 发现的问题
（具体问题，或"无"）

## 种子
（每行一个，用 - 开头）

---

今天的记录：

{diary}"""

def build_daydream_prompt(memories: str) -> str:
    """构建白日梦提示词：自由联想，不要分析"""
    return f"""你是白日梦模块。自由联想。

规则：
- 在不相关的记忆之间寻找意外的关联
- 发现隐藏的模式或有趣的想法
- 保持创意和玩味，不要做分析
- 只有真正有趣的想法才记为种子

输出格式：
## 自由联想
（意识流）

## 种子（如果有的话）
（每行一个，用 - 开头）

---

记忆碎片：

{memories}"""

def get_random_memories(memory_dir: str, count: int = 5) -> str:
    """随机抽取记忆碎片用于白日梦"""
    mem_path = Path(memory_dir)
    files = list(mem_path.glob("*.md"))
    if not files:
        return "没有找到记忆文件"

    picks = random.sample(files, min(count, len(files)))
    fragments = []
    for f in picks:
        content = f.read_text()[:1500]
        fragments.append(f"## 记忆: {f.name}\n{content}")

    random.shuffle(fragments)
    return "\n\n---\n\n".join(fragments)

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "meditate"

    if mode == "meditate":
        # 收集今天的日记素材（简化版：读 NOW.md）
        now_file = Path("NOW.md")
        diary = now_file.read_text() if now_file.exists() else "今天没有记录"
        prompt = build_meditation_prompt(diary)
        print("=== 冥想提示词 ===")
        print(prompt)
        print("\n（把这个提示词发给 LLM，得到反思结果）")

    elif mode == "daydream":
        memories = get_random_memories("./memories")
        prompt = build_daydream_prompt(memories)
        print("=== 白日梦提示词 ===")
        print(prompt)
        print("\n（把这个提示词发给 LLM，得到联想结果）")

    else:
        print("用法: meditation_demo.py [meditate | daydream]")
```

### 推荐 cron 配置

```cron
30 2 * * *  python3 meditation.py --meditate     # 凌晨冥想
0  10 * * * python3 meditation.py --daydream     # 上午白日梦
0  15 * * * python3 meditation.py --daydream     # 下午白日梦
0  6 * * *  python3 farm.py decay                # 每日衰减
```

### 常见踩坑

| 坑 | 怎么避 |
|---|---|
| 今天啥也没干还冥想 | 没有素材就是空话套话，只在有数据时才触发冥想 |
| 白日梦写成了分析报告 | 提示词里要明确说"创意、玩味、意外关联"，否则 LLM 默认做结构化分析 |
| 冥想不接农场 | 冥想不种种子等于写日记，必须把灵感种到农场里走生命周期 |
| 在工作时间跑冥想 | 02:30 不是随便选的，是没人发任务的安静时段，别在高峰期抢资源 |

### 练习题

1. 用 `meditation_demo.py meditate` 生成提示词，然后手动发给 Claude，看看反思结果质量如何。
2. 把冥想的输出接到 `farm_demo.py`：自动把冥想产出的种子用 `plant` 命令种下。
3. 设计一个完整的定时任务方案：冥想 → 种种子 → 每日衰减 → 定期检查哪些种子可以收获。

---

## 六大素养如何串联

```
                    ┌──────────────────────────────────────┐
                    │                                      │
     心跳 ──────> 处理任务 ──────> 结果                    │
         │              │            │                     │
         │              │       写 NOW.md                  │
         │              │            │                     │
         │              │     ┌──────┴──────┐              │
         │              │     │  海马体      │              │
         │              │     │ (记忆+git   │              │
         │              │     │  +NOW.md)   │              │
         │              │     └──────┬──────┘              │
         │              │            │                     │
         │         派工蜂       冥想读取记忆               │
         │              │            │                     │
         │              │       反思 + 白日梦              │
         │              │            │                     │
         │              │       种种子 ──> 农场            │
         │              │                    │             │
         │              │               收获 ─────────────┘
         │              │              (变成新任务)
         │              │
         │         自检 ──> 记录故障 ──> 冥想读取故障日志
         │
         └─── (永远循环)
```

agent 活着（心跳），记得（海马体），会分活（工蜂），会种田（农场），能自愈（故障回流），会反思（冥想）。每一块喂养其他块。

没有哪一块是复杂的。力量在于这个循环。

---

## 快速上手清单

准备给自己的 agent 加这些能力？按顺序来：

- [ ] **心跳**：搭轮询循环 + inbox + systemd 保活
- [ ] **NOW.md**：写交接文档，session 开始读、结束写
- [ ] **记忆搜索**：Markdown 文件存知识，超过 20 个文件加向量搜索
- [ ] **工蜂调度**：明确什么时候派活，设并发上限，必须设超时
- [ ] **农场**：实现 种/浇水/衰减/收获，至少接一个自动种子来源
- [ ] **进度日志**：每个重要操作都写 `/tmp/agent-progress.log`
- [ ] **降级链**：每个外部调用至少 2 条路（主 + 备）
- [ ] **冥想 cron**：定时夜间反思，输出接农场
- [ ] **白日梦 cron**：每天 1-2 次创意联想，用随机记忆碎片

---

*这份手册基于林月（Lin Yue）构建的 OpenClaw 系统整理。龙虾在进化。*
