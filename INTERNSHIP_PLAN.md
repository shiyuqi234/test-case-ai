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
| **test-case-ai** | Python | ✅ 已完成 | LLM 驱动的智能测试用例生成工具（CLI + Web） |
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

## 三、test-case-ai（✅ 已完成）

### 定位
**AI Agent × 测试** —— 基于大语言模型的智能测试用例生成工具

### 一句话描述
> 输入 API 描述 / OpenAPI spec → LLM 自动分析接口 → 生成 test-sprint-lite 兼容的 YAML 测试用例；同时支持 CLI 命令行和 Web 可视化界面两种操作方式

### 技术栈
| 层 | 选型 |
|---|---|
| LLM | Claude API / DeepSeek / OpenAI 三 provider 可切换 |
| CLI | argparse（与 tsp 风格一致） + uvicorn |
| Web 后端 | FastAPI |
| Web 前端 | 纯 HTML + CSS + JS（零构建、深色主题、响应式） |
| 输入 | OpenAPI spec URL / 自然语言描述 |
| 输出 | test-sprint-lite 兼容的 YAML |
| 测试 | 74 个 pytest + mock LLM 响应 |
| 打包 | pyproject.toml + CLI entry_point `tai` |

### 实际成果

| 维度 | 数据 |
|---|---|
| 测试 | 74 个 pytest，覆盖率 85% |
| Lint | ruff 零报错 |
| CI/CD | GitHub Actions 4 个 Python 版本矩阵 |
| Provider | Anthropic / DeepSeek / OpenAI |
| Web UI | `tai web` 一键启动，预设场景 + 卡片视图 + 统计面板 + 历史记录 |
| 实测 | DeepSeek 一键生成 21 个覆盖全面的测试用例（正常/边界/异常/类型/认证/特殊字符） |

### 使用方式

```bash
# 命令行模式（CLI）
tai generate --provider deepseek --desc "POST /api/login, body: {username, password}, returns {token}" -o login.yaml
tai generate --openapi https://petstore.swagger.io/v2/swagger.json -o petstore.yaml
tai generate --desc "GET /api/users" | tsp run --file -

# 网页可视化模式（Web UI）
tai web                          # 浏览器打开 http://127.0.0.1:8000
# 功能：自然语言/OpenAPI 双输入、预设场景一键填入、测试用例彩色卡片、
#       统计面板（正常/异常/边界分类）、YAML 源码切换、历史记录回溯
```

### 简历 bullet points
- 基于 Claude/DeepSeek/OpenAI 多 provider 实现 LLM 驱动的测试用例自动生成，覆盖正常/边界/异常/类型校验/认证场景
- 支持自然语言描述和 OpenAPI Spec（Swagger 2.0 / OpenAPI 3.x）两种输入，输出兼容自研 Test Sprint Lite 框架
- 基于 FastAPI 搭建 Web 可视化界面，支持预设场景、用例卡片分类展示、统计面板和历史回溯，提升演示和操作体验
- 打通"AI 生成 → 自动执行 → 报告输出"全链路，74 个 pytest 测试 + ruff 静态检查 + GitHub Actions CI 保证代码质量

---

## 四、做完后简历结构

| 项目 | 定位 | 面试侧重点 |
|---|---|---|
| **test-case-ai** | AI Agent × 测试 | LLM 应用、prompt 工程、FastAPI、全栈 |
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
- [x] **test-case-ai Agent 项目**（CLI + Web UI + 多 provider + 74 test + CI + README）

### 进行中 🔄
- [ ] 投递简历

### 待做 📋
- [ ] 投递简历
- [ ] 刷面试八股
- [ ] 准备项目话术
- [ ] GitHub README 加"找实习中"标识
