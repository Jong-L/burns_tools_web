# 数据层规格说明（Web 版迁移依据）

> 分析对象：`D:/schoolTour/softwares/burns_tools/services/local_store.py`（SQLite 单用户本地存储）
> 以及 `D:/schoolTour/softwares/burns_tools/tools/` 下 5 个工具：
> `thought_journal.py`（思维日志）、`thought_count.py`（消极思维计数器）、`daily_activity_plan.py`（每日活动计划表）、`anti_procrastination_table.py`（反拖延症表）、`but_rebuttal_tool.py`（反驳"但是"法）。
> 认知扭曲选项来自 `tools/log_editor.py`（日志编辑窗口，被思维日志工具使用）。

第 1、2 节是 Web 后端的权威实现依据；第 3 节业务规则必须与桌面版逐条一致；第 4 节给出老库到新库的字段级迁移映射。

后期迁移到mysql或其他数据库系统。

---

## 1. 数据表结构

### 1.0 通用约定

**连接级设置**（每个连接都必须设置，连接池同理；原版只设了 `foreign_keys`）：

```sql
PRAGMA foreign_keys = ON;      -- 外键与级联删除生效的前提，连接级
PRAGMA busy_timeout = 5000;    -- 写锁竞争时等待 5s 再报错，避免直接抛 database is locked
PRAGMA synchronous = NORMAL;   -- WAL 模式下安全且更快
```

**库级设置**（初始化建表时执行一次即可，持久生效）：

```sql
PRAGMA journal_mode = WAL;     -- 读写不互斥：写事务不再阻塞读
```

**事务**：每个写方法是一个事务。按天工具「先 `DELETE WHERE user_id=? AND day=?` 再批量 INSERT」必须整体成功或整体回滚，禁止出现"删掉旧的、新的没写进去"。异常时显式 `ROLLBACK`，不要依赖连接关闭时的隐式回滚。

**越权防护（强制）**：所有查询与写入都必须带 `user_id` 条件；`user_id` 只能来自服务端会话（JWT），**绝不允许从请求体或查询串接收**。

**文本与空值约定**：

- 文本字段空值统一存 `''`（不用 NULL），写入前 `strip`。与原 `_as_text` 一致。
- 分数/百分比字段"未填写"存 `NULL`，与"填了 0 分"严格区分。与原语义一致。

**日期约定**：`day` 一律 `yyyy-MM-dd`（服务端本地日期，Asia/Shanghai）。数据库用 CHECK 强制，注意 SQLite 的 `date()` 行为：

```
date('2026-09-23') → '2026-09-23'   ✓
date('2026-9-23')  → NULL           （格式不合法）
date('2026-02-30') → '2026-03-02'   （非法日期，归一化后与原值不等）
```

**⚠️ 必须用 `day IS date(day)` 而不是 `day = date(day)`。** SQLite 的 CHECK 只在结果为 FALSE(0) 时拒绝，为 NULL 时放行；而 `date('2026-9-23')` 返回 NULL，`NULL = '2026-9-23'` 结果是 NULL，于是缺前导零的非法日期会被放过去。`IS` 不会产生 NULL，能正确拒绝。（本修订已实测验证。）

**约束分层**：API 层负责给出可读的错误提示（0–5、0–100 的中文报错文案见第 3 节），数据库层负责兜底、保证任何写入路径都无法污染数据。两层都要有，不能只留一层。

**命名**：表名复数、列名 snake_case。`counting` 表保留 `count` 列名（SQLite 允许，且与老库一致），但在代码里不要把它当作聚合函数使用。

---

### 1.1 users — 用户（鉴权表的锚点）

```sql
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

说明：这里只定义业务表需要引用的**最小锚点**，具体鉴权方案（密码哈希、JWT、第三方登录）不在本规格范围内。若实际用户表已存在（如 email 登录、带 salt/hash 字段），保留其定义，只需保证主键是 `INTEGER id`——其余 8 张表都只依赖 `users(id)` 这一个契约，替换用户表无需改业务表。

所有业务表的外键均带 `ON DELETE CASCADE`：注销账号即清空该用户全部数据，不留孤儿行。

---

### 1.2 distortion_options — 认知扭曲选项（参考表，新增）

替代原本硬编码在两个编辑窗口里的 `distortion_data` 字典。前端已支持 zh/en 双语，中文名硬编码无法翻译，且默认描述改一次要动前端代码。

```sql
CREATE TABLE IF NOT EXISTS distortion_options (
    code            TEXT PRIMARY KEY,           -- 稳定标识，前端与数据库的唯一依据
    name_zh         TEXT NOT NULL,
    name_en         TEXT NOT NULL,
    default_note_zh TEXT NOT NULL DEFAULT '',   -- 仅作为「编辑描述」输入框的初始内容
    default_note_en TEXT NOT NULL DEFAULT '',
    sort_order      INTEGER NOT NULL UNIQUE     -- 展示顺序，固定 1–11
);
```

种子数据（11 条，顺序即 `sort_order`；中文默认描述逐字取自 `log_editor.py`，含全角引号，不要改写）：

| code | name_zh | name_en | default_note_zh | default_note_en |
|---|---|---|---|---|
| all_or_nothing | 非此即彼 | All-or-Nothing Thinking | 用非黑即白的极端方式看待事物。如果表现不够完美，就会认为自己彻底失败。 | You see things in black-and-white extremes: if your performance falls short of perfect, you see yourself as a total failure. |
| overgeneralization | 以偏概全 | Overgeneralization | 基于单一事件推断出广泛结论，常使用“总是”、“从不”等绝对化语言。 | You draw broad conclusions from a single event, often using words like "always" or "never". |
| mental_filter | 心理过滤 | Mental Filter | 专注于消极事件而忽略积极方面，只看到负面信息，好像戴上了一副有色眼镜。 | You dwell on the negative and ignore the positive, seeing only the downside as if through tinted lenses. |
| disqualifying_the_positive | 否定正面思考 | Disqualifying the Positive | 拒绝接受正面的经验，找理由告诉自己这些经验不算数。 | You reject positive experiences by insisting that they "don't count". |
| mind_reading | 妄下结论 - 读心术 | Jumping to Conclusions - Mind Reading | 未经证实就认为知道别人在想什么，通常假设他人对自己有负面看法。 | Without evidence you assume you know what others are thinking, usually that they judge you negatively. |
| fortune_telling | 妄下结论 - 先知错误 | Jumping to Conclusions - Fortune Telling | 预测事情会变得很糟糕，并坚信这一预言为事实。 | You predict that things will turn out badly and treat that prediction as an established fact. |
| magnification_minimization | 放大和缩小 | Magnification and Minimization | 夸大自己的错误或他人的成就，同时缩小自己的优点或他人的缺点。 | You exaggerate your mistakes or others' achievements while shrinking your own strengths or others' shortcomings. |
| emotional_reasoning | 情绪化推理 | Emotional Reasoning | 根据感觉来判断现实，“我这么感觉，所以它肯定是真的”。 | You take your feelings as proof of reality: "I feel it, so it must be true." |
| should_statements | ‘应该’句式 | "Should" Statements | 常用“我应该…”、“我不应该…”来要求自己或他人，带来内疚感或愤怒。 | You use "I should…" or "I shouldn't…" to demand things of yourself or others, which breeds guilt or anger. |
| labeling | 乱贴标签 | Labeling | 给自己或他人贴上固定、消极的标签，而不是描述具体的行为。 | You attach a fixed, negative label to yourself or others instead of describing the specific behavior. |
| personalization | 罪责归己 | Personalization | 即使没有直接责任，也会将外界的消极事件归咎于自己。 | You blame yourself for negative external events even when you were not responsible for them. |

注意：

- 三个 `name_zh` 含特殊写法，迁移映射时字符串必须完全一致：`妄下结论 - 读心术`（连字符两侧各一个半角空格）、`妄下结论 - 先知错误`、`‘应该’句式`（全角单引号）。
- 英文列是本修订新增的翻译，上线前需人工校对。
- 前端通过 `GET /api/distortion-options` 获取选项与默认描述（返回中英双语两列，前端按当前语言取用），不再硬编码。

---

### 1.3 journal_logs — 思维日志主表

```sql
CREATE TABLE IF NOT EXISTS journal_logs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type              TEXT NOT NULL CHECK (type IN ('three_column', 'six_column')),
    timestamp         REAL NOT NULL,
    situation         TEXT NOT NULL DEFAULT '',
    emotion           TEXT NOT NULL DEFAULT '',
    automatic_thought TEXT NOT NULL DEFAULT '',
    rational_response TEXT NOT NULL DEFAULT '',
    result            TEXT NOT NULL DEFAULT '',
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, timestamp)
);
```

| 字段 | 说明 |
|---|---|
| id | 内部主键，业务层不直接使用；保留是为了给 `journal_distortions.log_id` 当锚点（比用 `(user_id, timestamp)` 复合外键更省）。AUTOINCREMENT 保证 id 不复用 |
| user_id | 数据归属，见 1.0 越权防护 |
| type | 日志类型。`three_column` / `six_column`。写入时空值兜底 `three_column`（原行为），兜底后必须落在枚举内，否则 CHECK 会拒绝 |
| timestamp | 业务时间戳：Unix 时间戳（秒，可含小数），用于展示与排序。同一用户内唯一（UNIQUE 约束），新建时冲突返回 409，不做静默覆盖。记录身份由自增 id 承担，URL 与编辑/删除均按 id 定位 |
| created_at / updated_at | 非业务字段。`created_at` 首次插入时写入、之后不变；`updated_at` 每次更新时刷新。仅用于审计与将来的多端同步，不参与任何业务判断 |

**timestamp 的三条硬性约定**（原设计在这里最脆弱）：

1. **单位固定为秒**，允许小数。前端必须确认自己的时间戳不是毫秒——毫秒值会直接把唯一键撞坏。
2. **全链路原值透传**：前端生成 → JSON → 存储层，禁止 `round`、`toFixed`、格式化、秒/毫秒换算。Python 的 `float` 与 JS 的 `Number` 同为 IEEE-754 双精度，两边的 JSON 序列化都输出最短可往返表示，因此可以保证逐位一致；若将来有 Java/Go 客户端，需专门验证这一点。
3. **编辑/删除按 id 定位**（id 是记录的唯一身份）；新建时若 `(user_id, timestamp)` 已存在则返回 409，不做 upsert。改 timestamp 走编辑接口显式修改，且不得与其他记录冲突。

### 1.4 journal_distortions — 认知扭曲子表（1 对多挂 journal_logs）

```sql
CREATE TABLE IF NOT EXISTS journal_distortions (
    log_id      INTEGER NOT NULL REFERENCES journal_logs(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL CHECK (position >= 0),
    option_code TEXT REFERENCES distortion_options(code),
    name        TEXT NOT NULL,
    note        TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (log_id, position)
);
```

| 字段 | 说明 |
|---|---|
| log_id | 所属日志，删除日志时级联删除 |
| position | 该条扭曲在日志内的顺序，从 0 起，读出时按它排序。与 log_id 组成主键，因此顺序不可能重复，且自动获得 `(log_id, position)` 索引（原版外键列无索引，删除与级联都是全表扫） |
| option_code | 指向 11 项参考表。老数据能映射到的填对应 code；映射不到的历史/异常值留 NULL |
| name | **快照/兜底**，写入时的规范中文名。展示优先级：`option_code` 非空 → 按当前语言取 `name_zh`/`name_en`；`option_code` 为 NULL → 回退显示本列 |
| note | 用户为该条写的描述，可为空字符串 |

读出的 `name` 取值规则（用于前端渲染与导出）：`option_code` 非空时取参考表当前语言名称，为空时取本列。

### 1.5 thought_counts — 消极思维计数

```sql
CREATE TABLE IF NOT EXISTS thought_counts (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day     TEXT NOT NULL CHECK (day IS date(day)),
    count   INTEGER NOT NULL DEFAULT 0 CHECK (count >= 0),
    PRIMARY KEY (user_id, day)
);
```

- 复合主键 `(user_id, day)` 同时承担唯一约束与按用户查询的索引。
- `count` 不可为负，数据库层强制（原版只有存储层的 `max(0, int(count))`）。
- 一天的记录只有一条，保存是**覆盖**（按 `(user_id, day)` upsert），不是累加。

### 1.6 daily_activity_entries — 每日活动计划表

```sql
CREATE TABLE IF NOT EXISTS daily_activity_entries (
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day            TEXT NOT NULL CHECK (day IS date(day)),
    slot_index     INTEGER NOT NULL CHECK (slot_index BETWEEN 0 AND 13),
    time_slot      TEXT NOT NULL,
    plan           TEXT NOT NULL DEFAULT '',
    actual         TEXT NOT NULL DEFAULT '',
    mastery_score  INTEGER CHECK (mastery_score  IS NULL OR (mastery_score  BETWEEN 0 AND 5)),
    pleasure_score INTEGER CHECK (pleasure_score IS NULL OR (pleasure_score BETWEEN 0 AND 5)),
    PRIMARY KEY (user_id, day, slot_index)
);
```

- 去掉原版从未被引用的自增 `id`，改用 `(user_id, day, slot_index)` 复合主键：一天一个槽位只能一行，且该索引前缀正好覆盖「按用户+日期查一天」的查询。
- `slot_index` 固定 0–13，对应下面 14 个时间段（`TIME_SLOTS`，权威清单）：

| index | 文案 | index | 文案 |
|---|---|---|---|
| 0 | 上午 8-9 | 7 | 下午 3-4 |
| 1 | 上午 9-10 | 8 | 下午 4-5 |
| 2 | 上午 10-11 | 9 | 下午 5-6 |
| 3 | 上午 11-12 | 10 | 下午 6-7 |
| 4 | 下午 12-1 | 11 | 晚上 7-8 |
| 5 | 下午 1-2 | 12 | 晚上 8-9 |
| 6 | 下午 2-3 | 13 | 晚上 9-12 |

- **`time_slot` 的写入规则**：该列是快照（老数据保留原文案），但服务端写入时必须由 `slot_index` 派生规范文案，不采信客户端传来的任意文本。原版直接存 `entry.get("time_slot")`，一旦前端传错，库里就会出现「slot_index=3 却写着晚上 9-12」的数据。
- 一天的数据整体删除重写（先删该用户该天、再批量 INSERT），`slot_index` 取列表枚举序；列表长度固定 14，超出部分由服务端截断（原版不限制，配合新 CHECK 会直接报错，故必须在 API 层挡住）。

### 1.7 anti_procrastination_entries — 反拖延症表

```sql
CREATE TABLE IF NOT EXISTS anti_procrastination_entries (
    user_id                INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day                    TEXT NOT NULL CHECK (day IS date(day)),
    row_index              INTEGER NOT NULL CHECK (row_index >= 0),
    activity               TEXT NOT NULL DEFAULT '',
    predicted_difficulty   INTEGER CHECK (predicted_difficulty   IS NULL OR (predicted_difficulty   BETWEEN 0 AND 100)),
    predicted_satisfaction INTEGER CHECK (predicted_satisfaction IS NULL OR (predicted_satisfaction BETWEEN 0 AND 100)),
    actual_difficulty      INTEGER CHECK (actual_difficulty      IS NULL OR (actual_difficulty      BETWEEN 0 AND 100)),
    actual_satisfaction    INTEGER CHECK (actual_satisfaction    IS NULL OR (actual_satisfaction    BETWEEN 0 AND 100)),
    PRIMARY KEY (user_id, day, row_index)
);
```

- 行可增删，`row_index` 表示显示顺序（0 起），行数不固定。
- 四个百分比：0–100 整数或留空（NULL）。
- 整行丢弃规则：活动名为空且四个百分比全空的行不落库。
- 同样按天整体删除重写。

### 1.8 but_rebuttal_entries — 反驳"但是"法

```sql
CREATE TABLE IF NOT EXISTS but_rebuttal_entries (
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day           TEXT NOT NULL CHECK (day IS date(day)),
    row_index     INTEGER NOT NULL CHECK (row_index >= 0),
    excuse_text   TEXT NOT NULL DEFAULT '',
    rebuttal_text TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (user_id, day, row_index)
);
```

- 轮次序号 `row_index` 从头开始，行序即保存顺序。
- 两列仅做文本清洗，无数值校验。
- 保存时丢弃两列全空的行；末尾始终保留一个空行（见 3.7）。
- 按天整体删除重写。

### 1.9 索引与查询计划

复合主键与 `UNIQUE` 约束会自动生成索引，覆盖主要查询路径，**无需额外建索引**：

| 查询场景 | 走哪个索引 |
|---|---|
| 思维日志按用户读全部 | `UNIQUE(user_id, timestamp)` 自动索引，前缀 `user_id` |
| 认知扭曲按 log 读 / 级联删除 | `PRIMARY KEY(log_id, position)` 自动索引，前缀 `log_id` |
| 按天表「按用户+日期读一天」 | `PRIMARY KEY(user_id, day, row_index/slot_index)` 自动索引，前缀 `(user_id, day)` |

已实测查询计划（`EXPLAIN QUERY PLAN`）确认命中索引：

```
SEARCH daily_activity_entries USING INDEX sqlite_autoindex_daily_activity_entries_1 (user_id=? AND day=?)
```

唯一不走索引的是思维日志列表排序——原版的顺序是「理性回应为空的排前面，同组内按 timestamp 降序（越新越靠前）」，即 `ORDER BY (rational_response = '') DESC, timestamp DESC`，属于表达式排序，只能扫描后排序。个人日志量级（几千条以内）完全可接受，**暂不为它建表达式索引**；若某用户日志超过约 1 万条再考虑：

```sql
CREATE INDEX IF NOT EXISTS idx_journal_logs_unanswered
    ON journal_logs(user_id, (rational_response = ''), timestamp);
```

---

## 2. 各工具使用的读写方法

所有方法都在 `LocalStore` 上，工具通过构造函数注入的 `storage` 实例调用。**v2 的全部方法首参均为 `user_id: int`**（来自会话，不由请求体传入），其余输入输出形态与 v1 保持一致。

### 2.1 thought_journal（思维日志）

| 方法 | 输入 | 输出 / 行为 |
|---|---|---|
| `get_journal_logs(user_id)` | — | `list[dict]`，每项 `{"type": str, "timestamp": float, "data": {...}}`。`data` 键为中文：`情况`、`情绪`、`下意识思维`、`认知扭曲`、`理性回应`、`结果`；文本空值归一为 `""`，认知扭曲缺失归一为 `[]`。排序：`理性回应` 为空的排前面，同组内按 timestamp 降序 |
| `create_journal_log(user_id, log_type, timestamp, data)` | `log_type: str`（空白兜底 `three_column`）；`timestamp: float`；`data: dict` | 新建一条日志；`(user_id, timestamp)` 冲突时报错（HTTP 409），不覆盖；认知扭曲按顺序写入（code 必须在参考表内且不重复，否则报错 HTTP 422；`name` 由服务端按 code 反查规范中文名写入快照） |
| `update_journal_log(user_id, log_id, ...)` | 除 `log_id` 外字段均可选；`distortions` 传入时整删重插 | 按 id 定位更新（不改 id、不改 created_at，刷新 updated_at）；修改 timestamp 时若与该用户其他记录冲突报 409 |
| `delete_journal_log(user_id, log_id)` | `log_id: int` | 按 id 删除该条日志（认知扭曲靠外键级联删除） |

`认知扭曲` 的对外形态（v2 变化点）：

- 读出：`[{"code": "all_or_nothing", "name": "非此即彼", "note": "用户写的描述"}, ...]`，按 position 升序。`code` 为 NULL 的历史数据，`name` 为兜底名称。
- 写入：`[{"code": "all_or_nothing", "note": "..."}, ...]`。服务端按 code 反查规范中文名写入 `name` 快照；code 不在参考表内（或同一请求内重复）则整个请求报错（HTTP 422）——API 场景下前端传错应显式失败，不静默丢弃。前端渲染名称时按当前语言取参考表，不直接用 `name`。

工具侧行为（Web 版需保留）：列表页展示「日期 / 类型 / 未回应徽标（理性回应为空时）/ 下意识思维前 100 字预览」；新增时弹模板选择（三列默认选中）；保存成功弹窗、时间戳重置为 0。

### 2.2 thought_counter（消极思维计数器）

| 方法 | 输入 | 输出 / 行为 |
|---|---|---|
| `get_thought_counts(user_id)` | — | `list[dict]`，每项 `{"day": "yyyy-MM-dd", "count": int}`，按 day 升序读出，**只含该用户**（v2 修订：由原 `{day: count}` 字典改为数组，便于日后扩展字段不破坏契约） |
| `save_thought_count(user_id, day, count)` | `day: str`；`count: int` | 按 `(user_id, day)` upsert；写入前 `max(0, int(count))`，数据库 CHECK 再兜一道 |

工具侧行为：日期默认今天，可切日期（切到非今天按钮显示具体日期）；±按钮本地改计数，点「保存」才落库（保存的是当前所选日期的值，不是累加）；统计窗口用内存里的 `count_data` 画 7/30/90/180/365 天折线图，缺数据的日期补 0（**纯前端计算，不查库**）。

### 2.3 daily_activity_plan（每日活动计划表）

| 方法 | 输入 | 输出 / 行为 |
|---|---|---|
| `get_daily_plan(user_id, day)` | `day: str` | `list[dict]`，每项 `{"time_slot", "plan", "actual", "mastery_score", "pleasure_score"}`，文本空值归一 `""`，分数可空；按 slot_index 升序 |
| `save_daily_plan(user_id, day, entries)` | `day: str`；`entries: list[dict]`，键同上 | 该用户该天先删后插，单事务；`slot_index` = 列表枚举序且不超过 13（超出截断）；`time_slot` 由 `slot_index` 派生规范文案；分数经 `_nullable_score` 校验（空/None → NULL；非 0–5 整数抛 `ValueError`） |

工具侧行为：固定 14 个时间段（见 1.6 表）；读库后按时间段匹配回填，缺的槽位补空行；保存前 UI 校验分数「0–5 整数或留空」，非法则弹窗并中止保存；切换日期前自动保存当前日，失败则回退日期选择；关闭窗口时静默保存。

### 2.4 anti_procrastination_table（反拖延症表）

| 方法 | 输入 | 输出 / 行为 |
|---|---|---|
| `get_anti_procrastination_entries(user_id, day)` | `day: str` | `list[dict]`，每项 `{"activity", "predicted_difficulty", "predicted_satisfaction", "actual_difficulty", "actual_satisfaction"}`，按 row_index 升序，分数可空 |
| `save_anti_procrastination_entries(user_id, day, entries)` | `day: str`；`entries: list[dict]`，键同上 | 该用户该天先删后插；`row_index` = 枚举序；四个百分比经 `_nullable_percent` 校验（空/None → NULL；非 0–100 整数抛 `ValueError`） |

工具侧行为：行可增删（全删空时自动补一行）；UI 校验「0–100 整数或留空」；汇总卡片实时算四个平均值（四舍五入取整显示为 `N%`），并按「实际−预计」差值 ±10 个百分点分档生成提示文案（见 3.6）；切日期自动保存、关窗静默保存。

### 2.5 but_rebuttal_tool（反驳"但是"法）

| 方法 | 输入 | 输出 / 行为 |
|---|---|---|
| `get_but_rebuttal_entries(user_id, day)` | `day: str` | `list[dict]`，每项 `{"excuse_text", "rebuttal_text"}`，按 row_index 升序，文本空值归一 `""` |
| `save_but_rebuttal_entries(user_id, day, entries)` | `day: str`；`entries: list[dict]`，键同上 | 该用户该天先删后插；`row_index` = 枚举序；两列仅 `_as_text` 清洗，无数值校验 |

工具侧行为：链式解锁规则（见 3.7）；末尾始终保留一个空行；保存时丢弃两列全空的行；进度标签显示已完成轮数；切日期自动保存、关窗静默保存。

### 2.6 distortion_options（新增）

| 方法 | 输入 | 输出 / 行为 |
|---|---|---|
| `get_distortion_options()` | — | `list[dict]`，每项 `{"code", "name_zh", "name_en", "default_note_zh", "default_note_en"}`，按 sort_order 升序。公开接口，不要求登录，可缓存 |

---

## 3. 业务规则清单（Web 版需原样保留）

### 3.1 认知扭曲可选项

固定 11 项，名称、默认描述、顺序即 1.2 参考表的种子数据。附加规则：

- 选择对话框里有独立的「编辑描述」输入框；确定后存的是 `(code, 用户输入的描述)`，**note 是用户自定义文本，不自动带默认描述**。
- 同一扭曲不可重复添加（已在列表中则按 code 判重并跳过）。
- 每条可单独删除；条目顺序即 `position`，读出时按此还原。
- 三列/六列编辑窗口使用同一套扭曲数据与添加逻辑。
- 展示名称随界面语言走（zh 用 `name_zh`，en 用 `name_en`）。

### 3.2 三列法 vs 六列法字段差异

| 模板 | type 值 | 出现的字段（data 键） | 数据库实际占用 |
|---|---|---|---|
| 三列 | `three_column` | 下意识思维、认知扭曲、理性回应 | situation / emotion / result 三列存 `''` |
| 六列 | `six_column` | 情况、情绪、下意识思维、认知扭曲、理性回应、结果 | 全部占用 |

- 六列 = 三列的三项 + 情况 + 情绪 + 结果；认知扭曲两类模板都有。
- 列表卡片上理性回应为空 → 显示「未回应」徽标；列表排序把未回应的排最前。
- 新建模板选择框默认选三列；`type` 写库时空白兜底 `three_column`。

### 3.3 0–5 打分（每日活动计划表）

- 适用于 `mastery_score`（掌控型分数 M）、`pleasure_score`（休闲活动分数 P）。
- 取值：0–5 整数，或留空（存 NULL）。越大表示满意度越高。
- 三层校验：UI 层校验「0–5 整数或留空」，报错文案为「<时间段> 的<掌控型分数/休闲活动分数>必须是0到5之间的整数或留空。」；存储层 `_nullable_score` 越界抛 `ValueError`；数据库 CHECK 兜底。
- 读路径宽容：`ActivityEntry.from_dict` 的 `_safe_int` 对越界/非法值静默归 NULL（读宽写严，保持原行为）。

### 3.4 0–100 打分（反拖延症表）

- 适用于四个百分比字段：预计难度、预计满足程度、实际难度、实际满足程度。
- 取值：0–100 整数，或留空（存 NULL）。
- 三层校验同上：UI 层报错「第 N 行的<字段名>必须是 0 到 100 的整数或留空。」；存储层 `_nullable_percent`；数据库 CHECK。读路径 `_safe_percent` 越界归 NULL。
- 整行丢弃规则：活动名与四个百分比全空的行不落库。

### 3.5 计数器规则

- 计数不可为负：UI ±按钮最低到 0；存储层 `max(0, int(count))`；数据库 CHECK。
- 保存是"覆盖当日值"（按 `(user_id, day)` upsert），不是累加。
- 统计图窗口范围固定 7/30/90/180/365 天，缺日补 0，基于内存数据绘制。

### 3.6 反拖延症表摘要洞察（±10 个百分点分档）

有记录时提示文案固定为两段（难度 + 满足感），判定基于「实际均值 − 预计均值」：

- 难度差 ≤ −10：「实际难度明显低于预期，你可能把任务想得比真实体验更难。」
- 难度差 ≥ +10：「实际难度高于预期，下一次可以把步骤拆得更小一些。」
- 否则：「实际难度和预期接近，你对任务的判断已经比较稳定。」
- 满足感差 ≥ +10：「完成后的满足感高于预期，行动本身很可能比拖延更让你轻松。」
- 满足感差 ≤ −10：「完成后的满足感低于预期，也许需要调整任务形式或奖励方式。」
- 否则：「完成后的满足感和预期接近，可以继续保持这种节奏。」
- 无记录时：「开始记录后，这里会自动告诉你：任务是否真的像想象中那样困难。」
- 平均值显示：四舍五入取整 + `%`；无数据显示 `--`。

### 3.7 反驳"但是"法链式解锁

- 第 N 行左列（"但是"）解锁条件：第 1 行恒可写；否则上一行右列（反驳）非空。
- 第 N 行右列解锁条件：本行左列非空。
- 箭头显示：上一行右列非空时本行显示 ↙ 入场箭头；本行左列非空时显示 → 桥接箭头。
- 末尾始终保留一个空行（末行有内容则自动追加新空行）。
- 保存时丢弃两列全空的行；行序即保存顺序。
- 进度文案：完成 N 轮（右列非空的行数）——N=0 提示先写第一个"但是"；1≤N<3 提示继续写；N≥3 提示抓一个反驳马上行动。

### 3.8 时间与日期约定

- 思维日志主键 = 自增 id；`timestamp` 为业务时间戳（秒，REAL），同一用户内唯一，新建冲突返回 409；编辑/删除按 id 定位。跨用户时间戳互不干扰。
- 其余四个工具的身份 = 日期字符串 `yyyy-MM-dd`（服务端本地日期）；一天的数据整体删除重写，行序号表示显示顺序。
- 按天工具切日期时自动保存当前日，保存失败则回退日期选择；窗口关闭时静默保存一次。

### 3.9 多用户隔离（v2 新增）

- 所有业务查询必须带 `user_id`；「按天」类接口不能只按 `day` 查。
- `user_id` 只从会话/JWT 取，请求体或查询串里出现的 `user_id` 一律忽略或直接拒绝。
- 认知扭曲选项接口（2.6）是唯一无需登录的业务接口。

### 3.10 中文键名约定

思维日志的 `data` 字典、日志六字段常量（`情况 / 情绪 / 下意识思维 / 认知扭曲 / 理性回应 / 结果`）在存储层与工具层都以**中文键**流转（LocalStore 的 KEY 常量与 thought_journal 的 LogConstants 各自定义了一份、值相同）。Web 版后端内部若改用英文字段名，需在 API 边界做一次映射；数据库存的是独立列、与键名无关，老数据可直接迁移。API 对外仍沿用中文键，避免前端契约变更。
