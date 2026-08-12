# مرحله هفتم: ساخت هسته مدل داده

## 1. دامنه و نتیجه

- منبع مبنا: *Improved Methods of Task Assignment and Resource Allocation with Preemption in Edge Computing Systems*، `arXiv:2403.15665v2`.
- معماری مرحله ششم در 9 اوت 2026 توسط کاربر تأیید شد.
- تصمیم صریح کاربر: Gurobi فعلاً نصب نشود؛ این تصمیم رعایت شد.
- یک scaffold حداقلی Python با layout نوع `src/` ایجاد شد.
- 9 مؤلفه اصلی داده‌ای پیاده‌سازی شد: `ResourceVector`, `Task`, `Server`, `Bid`, `AuctionRound`, `Allocation`, `SimulationState`, `ExperimentConfig`, `ExperimentResult`.
- enumهای فنی `TaskState`, `ProcessingMode`, `AuctionRoundNumber`, `ResultStatus` نیز اضافه شدند.
- هیچ الگوریتم KG/DK، قیمت‌گذاری، transition policy، تخصیص منابع پویا یا شبیه‌سازی رویدادگسسته پیاده‌سازی نشد.

## 2. scaffold ایجادشده

| مسیر | نقش | وضعیت شواهد |
| --- | --- | --- |
| `.python-version` | تثبیت CPython 3.12.13 | `[پیشنهاد فنی]`؛ نسخه مقاله `[نامشخص]` |
| `pyproject.toml` | metadata، Python constraint و ابزارهای آزمون/کیفیت | `[پیشنهاد فنی]` |
| `.gitignore` | حذف محیط و cacheها از version control آینده | `[پیشنهاد فنی]` |
| `README.md` | معرفی منبع و وضعیت مرحله‌ای | `[پیشنهاد فنی]` |
| `src/edge_reproduction/` | package اصلی | `[پیشنهاد فنی]` |
| `tests/unit/` | آزمون‌های واحد مرحله هفتم | `[پیشنهاد فنی]` |
| `.venv/` | محیط محلی Python 3.12.13؛ artifact اجرایی و ignoreشده | `[پیشنهاد فنی]` |

## 3. نگاشت کلاس‌ها به مقاله

| کلاس | پشتوانه مقاله | مسئولیت فعلی | عمداً خارج از این مرحله |
| --- | --- | --- | --- |
| `ResourceVector` | storage، computation، upload، download در Sections III-IV | نگه‌داری چهار مؤلفه، جمع، تفریق امن و fit مؤلفه‌ای | تبدیل MB/GB و rate×slot |
| `Task` | `a_j`, `d_j`, `U_j`, `s_j`, `s'_j`, `K_j` | specification تغییرناپذیر task | progress، state transition و retry |
| `Server` | `S_i`, `C_i`, `B_{u,i}`, `B_{d,i}` | ظرفیت تغییرناپذیر server مستقل | residual capacity و current jobs |
| `Bid` | مزایده دو دور و metadata Algorithm 1 | price، feasibility، auto-fit و markها | فرمول قیمت و impossible sentinel |
| `AuctionRound` | Section III | snapshot یک round و کنترل سازگاری bidها | orchestration مزایده |
| `Allocation` | assignment دودویی `x_{i,j}` | رکورد admission-level یک task روی یک server | schedule پیوسته `σ`, `κ`, `σ'` |
| `SimulationState` | مجموعه‌های `I`,`J` و وضعیت local server | registry ساختاری task/server/state/allocation/round | invariantهای کامل روابط (1)-(31) |
| `ExperimentConfig` | دو دور مزایده و protocol Section VI | config typed و gate تصمیم حل‌نشده | YAML loading و configهای واقعی مقاله |
| `ExperimentResult` | معیارهای Figs. 6-20 | task IDs و Utilityهای outcomeها | aggregation چند run و plot |

## 4. ویژگی‌ها، نوع و واحد

### 4.1 `ResourceVector`

| ویژگی | نوع | معنی | واحد |
| --- | --- | --- | --- |
| `storage` | `float` | task `s_j` یا server `S_i` | paper: MB/GB ناسازگار؛ canonical experiment unit هنوز تعیین نشده |
| `computation` | `float` | task demand یا server `C_i` | MFlops یا MFlops/s؛ تبدیل slot نامشخص |
| `upload` | `float` | upload demand/capacity | MB/s یا data/slot؛ تبدیل نامشخص |
| `download` | `float` | download demand/capacity | MB/s یا data/slot؛ تبدیل نامشخص |

`[پیشنهاد فنی]` تمام مؤلفه‌ها finite و نامنفی‌اند. هیچ tolerance ضمنی وجود ندارد؛ tolerance پیش‌فرض دقیقاً صفر است.

### 4.2 `Task`

| ویژگی | نوع | نماد/منشأ | اعتبارسنجی |
| --- | --- | --- | --- |
| `task_id` | `str` | اندیس `j` | non-empty/trimmed |
| `arrival_slot` | `int` | `a_j` | نامنفی |
| `deadline_slots` | `int` | `d_j` نسبی | مثبت |
| `utility` | `float` | `U_j` | finite؛ منفی در model layer ممنوع نشده چون دامنه مقاله `[نامشخص]` است |
| `demand` | `ResourceVector` | `s_j`,`K_j` و demands heuristic | storage و computation مثبت؛ upload/download می‌توانند صفر باشند |
| `output_size` | `float | None` | `s'_j` | اگر موجود باشد مثبت؛ `None` کمبود مقاله را بدون حدس نمایش می‌دهد |

`absolute_deadline_slot` فقط مقدار عددی `a_j+d_j` را برمی‌گرداند و inclusive/exclusive بودن boundary را تعیین نمی‌کند.

### 4.3 `Server`

| ویژگی | نوع | نماد/منشأ | اعتبارسنجی |
| --- | --- | --- | --- |
| `server_id` | `str` | اندیس `i` | non-empty/trimmed |
| `capacity` | `ResourceVector` | `S_i,C_i,B_{u,i},B_{d,i}` | ظرفیت صفر مجاز است |

### 4.4 `Bid` و `AuctionRound`

| ویژگی | نوع | معنی |
| --- | --- | --- |
| `task_id`, `server_id` | `str` | دو طرف bid |
| `round_number` | `AuctionRoundNumber` | فقط 1 یا 2 |
| `price` | `float` | قیمت server؛ فقط finite، چون کران رسمی `[نامشخص]` است |
| `feasible`, `auto_fit` | `bool` | feasibility و mark auto-fit |
| `marked_task_ids` | `tuple[str,...]` | markهای Algorithm 1 بدون تکرار |
| `epoch` | `int` | epoch نامنفی round |
| `task_ids`, `bids` | tupleهای immutable | membership snapshot |

`AuctionRound` round یکسان bidها، membership task و یکتایی `(task,server)` را کنترل می‌کند.

### 4.5 `Allocation`

| ویژگی | نوع | معنی |
| --- | --- | --- |
| `task_id`, `server_id` | `str` | assignment یک task به یک server |
| `resources` | `ResourceVector` | reservation admission-level |
| `start_slot` | `int` | slot آغاز، نامنفی |
| `end_slot` | `int | None` | slot پایان ثبت‌شده؛ نباید قبل از آغاز باشد |

`is_active=True` فقط یعنی `end_slot` ثبت نشده است؛ مفهوم completion/preemption را استنتاج نمی‌کند.

### 4.6 `SimulationState`

| ویژگی | نوع | نقش |
| --- | --- | --- |
| `current_slot` | `int` | ساعت ساختاری فعلی |
| `tasks` | `dict[str,Task]` | registry مجموعه `J` |
| `servers` | `dict[str,Server]` | registry مجموعه `I` |
| `task_states` | `dict[str,TaskState]` | state فنی هر task |
| `allocations` | `dict[str,Allocation]` | حداکثر یک allocation record برای هر task |
| `auction_rounds` | `tuple[AuctionRound,...]` | تاریخچه snapshotهای round |

کلید mapping باید با ID شیء برابر باشد. allocation فقط می‌تواند task/server شناخته‌شده را ارجاع دهد. capacity invariant و سازگاری task state/resource عمداً به مرحله هشتم واگذار شد.

### 4.7 `ExperimentConfig`

- دو auction round را مطابق Section III الزام می‌کند.
- seed می‌تواند `None` باشد، زیرا seed مقاله گزارش نشده است.
- `unresolved_decisions` حاوی شناسه تصمیم‌های علمی pending است.
- `ensure_resolved()` در صورت وجود حتی یک تصمیم pending، `UnresolvedDecisionError` ایجاد می‌کند.
- mappingهای parameters/provenance کپی و read-only می‌شوند.

### 4.8 `ExperimentResult`

- task IDs و Utilityهای completed، rejected و ever-preempted را ثبت می‌کند.
- `[استخراج مستقیم]` فهرست ever-preempted مجاز است با outcome نهایی overlap داشته باشد، زیرا مرحله پنجم نشان داد ستون Preempted یک partition قطعی نیست.
- duplicate درون هر category ممنوع است، اما overlap میان categoryها ممنوع نشده است.
- Utilityها باید finite و event count نامنفی باشد.

## 5. stateها و مرزبندی علمی

`TaskState` شامل 15 state ثبت‌شده در مرحله دوم است. underlying phaseها/outcomeها در مقاله آمده‌اند، اما بیشتر نام stateها `[پیشنهاد فنی]` هستند. این مرحله هیچ transition table اجرایی اضافه نکرد، به‌ویژه:

- `PREEMPTED` terminal فرض نشده است؛
- resubmission policy پیاده نشده است؛
- زمان دقیق `EXPIRED` تعیین نشده است؛
- `ACCEPTED → batch/pipeline` هنوز توسط engine انجام نمی‌شود.

## 6. آزمون‌ها و شرایط مرزی

| گروه | نمونه پوشش |
| --- | --- |
| enum | دو processing mode، دقیقاً دو round و 15 task state |
| ResourceVector | صفر، منفی، NaN/Inf، fit یک‌بعد ناموفق، underflow و tolerance صریح |
| Task | deadline نسبی، output مفقود، زمان نامعتبر، totals صفر و Utility نامتناهی |
| Server | ظرفیت صفر و ID نامعتبر |
| Bid/AuctionRound | metadata mark، price نامتناهی، auto-fit ناسازگار، round اشتباه و duplicate bid |
| Allocation | active/ended و end-before-start |
| Config | pending gate، auction count و mapping read-only |
| Result | overlap ever-preempted، duplicate category و Utility نامتناهی |
| SimulationState | state اولیه، copy isolation، key mismatch، allocation ناشناخته و snapshot مستقل |

نتیجه نهایی: **53 passed, 0 failed**. همچنین Ruff و mypy strict بدون خطا اجرا شدند.

## 7. محیط و وابستگی‌های نصب‌شده

- محیط: `.venv` با CPython `3.12.13`.
- package پروژه به‌صورت editable نصب شد.
- فقط ابزارهای توسعه مرحله هفتم نصب شدند: `pytest==9.1.1`, `ruff==0.15.22`, `mypy==2.3.0` و dependencyهای transitive آن‌ها.
- `numpy`, `pandas`, `scipy`, `matplotlib`, `PyYAML`, `pyeasyga` و `gurobipy` در این مرحله نصب نشدند.
- درخواست نصب اول به علت محدودیت شبکه sandbox شکست خورد؛ اجرای تأییدشده با دسترسی شبکه موفق شد.

## 8. فایل‌های ایجاد یا تغییرکرده

### ریشه

- `.gitignore`
- `.python-version`
- `README.md`
- `pyproject.toml`

### package

- `src/edge_reproduction/__init__.py`
- `src/edge_reproduction/exceptions.py`
- `src/edge_reproduction/models/__init__.py`
- `src/edge_reproduction/models/_validation.py`
- `src/edge_reproduction/models/enums.py`
- `src/edge_reproduction/models/resources.py`
- `src/edge_reproduction/models/task.py`
- `src/edge_reproduction/models/server.py`
- `src/edge_reproduction/models/bid.py`
- `src/edge_reproduction/models/allocation.py`
- `src/edge_reproduction/models/config.py`
- `src/edge_reproduction/models/result.py`
- `src/edge_reproduction/simulation/__init__.py`
- `src/edge_reproduction/simulation/state.py`

### آزمون

- `tests/unit/test_enums.py`
- `tests/unit/test_resources.py`
- `tests/unit/test_task_and_server.py`
- `tests/unit/test_bid_and_allocation.py`
- `tests/unit/test_config_and_result.py`
- `tests/unit/test_simulation_state.py`

### اسناد

- `outputs/stage_seven_core_data_model.md`
- `outputs/traceability_matrix_arxiv_v2.md`

## 9. فرض‌ها، ابهام‌ها و محدودیت‌ها

### فرض‌های استفاده‌شده

هیچ `[فرض بازتولید]` علمی اعمال نشد.

### پیشنهادهای فنی اعمال‌شده

- validation شناسه‌ها و finite بودن اعداد؛
- immutable specification برای Task/Server/Bid/Allocation؛
- mapping read-only برای config/result metadata؛
- fail-fast تصمیم pending؛
- پذیرش Utility و price منفی finite در لایه مدل تا وقتی دامنه مقاله تعیین/تصویب شود؛
- `None` برای `s'_j` مفقود؛
- عدم tolerance عددی ضمنی.

### ابهام‌های باقی‌مانده

ابهام‌های مراحل 3-5 بدون تغییر باقی‌اند: واحدها، boundary deadline، transitionهای retry/preempted، مدل دقیق allocation slot-level، domains Utility/price، فرمول impossible price، و تمام تصمیم‌های الگوریتم/داده/آزمایش.

## 10. نتیجه و gate مرحله بعد

هسته مدل داده برای ورود به مرحله هشتم از نظر ساختاری و آزمون واحد آماده است. مرحله هشتم باید توابع تخصیص/آزادسازی، deadline، Utility و invariantهای روابط مقاله را اضافه کند؛ اما هر بخش وابسته به تفسیر حل‌نشده باید پیش از پیاده‌سازی متوقف و برای تصمیم کاربر ارائه شود.

