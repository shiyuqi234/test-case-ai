# 测开实习准备全景图

> 大三下 | 2026 年 7 月 | 目标：测试开发 / 软件测试 / Python Agent 开发实习

---

## 一、当前状态

### 基本情况
- 大三下学期，暑假临近，着急找实习
- 意向方向：测开（SDET）> Python Agent 开发 > 手工测试（保底）
- Python 主力，Java 碰过（Spring Boot）

### GitHub：https://github.com/shiyuqi234

| 仓库 | 语言 | 状态 | 一句话 |
|---|---|---|---|
| **test-sprint-lite** | Python | ✅ 已工程化 | YAML 驱动的 API 自动化测试 CLI 工具 |
| **ecommerce-api-test** | Python | 基础完成 | pytest + Allure 的 FakeStore API 测试套件 |
| **essay-scoring-system** | Java | 课程作业级 | Spring Boot 作文评分 Web 应用（非真 AI） |

---

## 二、已完成的改造（test-sprint-lite）

| 维度 | 改造前 | 改造后 |
|---|---|---|
| 版本控制 | 无 git | 5 个语义化 commit |
| 打包 | 只能 `python x.py` | `pip install` + `tsp run` 命令 |
| 测试 | 0 个 | 44 个 pytest，99% 覆盖率 |
| CI/CD | 无 | GitHub Actions 多 Python 版本矩阵 |
| Lint | 无 | ruff 自动检查 |
| README | 53 行中文 | 中英双语 + badges + 表格文档 |

---

## 三、待做项目：test-case-ai（2-3 天）

### 定位
**AI Agent × 测试** —— 基于 Claude API 的智能测试用例生成工具

### 一句话描述
> 输入 API 描述 / OpenAPI spec → Claude API 自动分析接口 → 生成 test-sprint-lite 兼容的 YAML 测试用例

### 技术栈
| 层 | 选型 |
|---|---|
| LLM | Claude API（anthropic SDK） |
| CLI | argparse（与 tsp 风格一致） |
| 输入 | OpenAPI spec URL / 自然语言描述 |
| 输出 | test-sprint-lite 兼容的 YAML |
| 测试 | pytest + mock Claude API 响应 |
| 打包 | pyproject.toml + CLI entry_point `tai` |

### 工期拆分

| 阶段 | 内容 | 预计 |
|---|---|---|
| Day 1 | CLI 骨架 + Claude API 调用 + 基础 prompt → 生成 YAML | 3-4h |
| Day 2 | 打磨 prompt 质量 + 支持 OpenAPI spec 解析 + 写测试 | 3-4h |
| Day 3 | pyproject.toml + CI + README + 推到 GitHub | 2-3h |

### 使用方式（最终效果）

```bash
# 自然语言生成
tai generate --desc "POST /api/login, body: {username, password}, returns {token}" -o login.yaml

# OpenAPI spec 生成
tai generate --openapi https://petstore.swagger.io/v2/swagger.json -o petstore.yaml

# 与 tsp 联动
tai generate --desc "..." | tsp run --file -
```

### 简历 bullet points
- 基于 Claude API 实现 LLM 驱动的测试用例自动生成，覆盖正常/边界/异常场景
- 支持自然语言描述和 OpenAPI Spec 两种输入，输出兼容自研 Test Sprint Lite 框架
- 打通"AI 生成 → 自动执行 → 报告输出"全链路

---

## 四、做完后简历结构

| 项目 | 定位 | 面试侧重点 |
|---|---|---|
| **test-case-ai** | AI Agent × 测试 | LLM 应用、prompt 工程、API 设计 |
| **test-sprint-lite** | 测试框架开发 | 框架设计、并发、工程化 |
| **ecommerce-api-test** | 测试实践 | pytest 生态、数据驱动、Allure |

覆盖维度：**AI/LLM + 造轮子 + 写测试** = 大厂测开想要的 T 型候选人

---

## 五、投递策略

### 目标分层

| 档位 | 公司举例 | 策略 |
|---|---|---|
| 大厂 | 字节/阿里/腾讯/美团 | 顺手投，面试当练习 |
| **中厂（主攻）** | 滴滴/快手/B站/小红书/SHEIN/得物 | 重点投，项目够用 |
| 小厂/创业公司 | — | 保底，防暑假空窗 |

### 投递渠道

| 渠道 | 优先级 | 用途 |
|---|---|---|
| BOSS 直聘 | 🔥🔥🔥 | 日常实习最多，直接搜"测试实习生""测开实习生""Python 实习生" |
| 实习僧 | 🔥🔥 | 中小厂多，流程快 |
| 牛客网 | 🔥 | 看面经 + 找内推 |
| 公司官网 | 🔥 | 大厂补录 |
| GitHub README | — | 注明"大三在读，寻找测开实习，欢迎联系" |

### 投递话术模板
> 大三在读，计算机相关专业，熟悉 Python 自动化测试。独立开发过 API 测试框架（YAML 驱动 + 并发 + 多格式报告），有 AI Agent 项目经验（LLM 驱动测试用例生成）。可尽快到岗，每周出勤 5 天。

---

## 六、面试准备清单

### Python 基础
- [ ] 装饰器原理与手写
- [ ] 生成器 / 迭代器 / yield
- [ ] 上下文管理器（`__enter__` / `__exit__`）
- [ ] `*args` / `**kwargs`
- [ ] GIL 是什么、影响什么
- [ ] 可变对象 vs 不可变对象
- [ ] 深拷贝 vs 浅拷贝

### pytest
- [ ] fixture scope（function/class/module/session）
- [ ] conftest.py 作用域
- [ ] parametrize 参数化
- [ ] mock / monkeypatch 区别
- [ ] yield fixture（setup/teardown）

### HTTP 协议
- [ ] 常用状态码：200/201/301/302/400/401/403/404/500
- [ ] GET vs POST vs PUT vs PATCH vs DELETE
- [ ] RESTful 设计原则
- [ ] Cookie / Session / Token（JWT）区别
- [ ] HTTP 请求报文结构

### SQL
- [ ] INNER JOIN vs LEFT JOIN
- [ ] GROUP BY + HAVING
- [ ] 子查询
- [ ] 索引概念（什么时候加、什么时候不加）
- [ ] 手写基本 CRUD

### Linux
- [ ] `grep` 查日志
- [ ] `awk` 简单处理
- [ ] `tail -f` 实时看日志
- [ ] `ps aux | grep`
- [ ] `netstat` / `ss` 看端口
- [ ] `chmod` 权限

### 测试理论
- [ ] 测试金字塔
- [ ] 等价类划分 + 边界值分析
- [ ] 黑盒 vs 白盒
- [ ] 冒烟测试 vs 回归测试
- [ ] 如何设计测试用例（给你一个登录页面）

### 项目话术（重点准备）
- [ ] 项目解决了什么问题
- [ ] 你做了哪些技术决策（为什么用 ThreadPoolExecutor 而不是 asyncio）
- [ ] 遇到什么困难、怎么解决的
- [ ] 如果再给你一个月，你会怎么改进

---

## 七、当前进度 & TODO

### 已完成 ✅
- [x] test-sprint-lite 工程化改造（git / pytest / CI / README）
- [x] 推送到 GitHub

### 进行中 🔄
- [ ] **test-case-ai Agent 项目**（下次对话开始）

### 待做 📋
- [ ] 投递简历
- [ ] 刷面试八股
- [ ] 准备项目话术
- [ ] GitHub README 加"找实习中"标识
