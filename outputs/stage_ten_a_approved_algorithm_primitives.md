# مرحله دهم-A: هسته تصمیم‌گیری تأییدشده Algorithm 1 و Algorithm 2

## 1. کارهای انجام‌شده

- ASSUMP-003 تا ASSUMP-006 با وضعیت approved در رجیستر ثبت شدند.
- congestion چهاربعدی نرمال‌شده، guard ظرفیت کل و عامل Algorithm 1 پیاده‌سازی شدند.
- شرط ۵٪ با تفسیر نثر و مرز inclusive به پیش‌فرض تأییدشده تبدیل شد.
- انتخاب حداکثر یک قربانی KnapsackGreedy با ترتیب صعودی نسبت پیاده‌سازی شد.
- خروج فوری پس از نخستین قربانی و تراکنش اتمیک preempt-and-admit آزمون شدند.
- مثال عددی مستقل اجرا و artifact واقعی JSON تولید شد.
- این زیربخش عمداً یک policy کامل مقاله را ادعا نمی‌کند.

## 2. فایل‌های ایجاد یا تغییرکرده

- `docs/assumptions.md`
- `outputs/traceability_matrix_arxiv_v2.md`
- `src/edge_reproduction/algorithms/pricing.py`
- `src/edge_reproduction/algorithms/feasibility.py`
- `src/edge_reproduction/algorithms/knapsack_greedy.py`
- `src/edge_reproduction/algorithms/__init__.py`
- `src/edge_reproduction/simulation/__init__.py`
- `tests/unit/test_pricing.py`
- `tests/unit/test_feasibility.py`
- `tests/unit/test_knapsack_greedy.py`
- `tests/integration/test_stage_ten_a_approved_primitives.py`
- `scripts/run_stage_ten_a_example.py`
- `results/raw/stage10a/approved_primitives_example.json`
- `README.md`

## 3. ارتباط تغییرها با مقاله

- `[صریح در مقاله]` Algorithm 1 ضرایب 0.9، 0.025 و عبارت
  `congestionFactor = c2 * (1-congestion)` را در صفحه 6 چاپ می‌کند.
- `[صریح در مقاله]` نثر Section V-A2 نسبت‌های Utility/time و بهبود ۵٪ را شرح می‌دهد.
- `[صریح در مقاله]` Algorithm 2 منابع قربانی و residual را برای feasibility ترکیب می‌کند.
- `[فرض بازتولید؛ تأییدشده]` تعریف عددی congestion، جهت شرط ۵٪، تک‌قربانی و break/atomicity
  از ASSUMP-003 تا ASSUMP-006 آمده‌اند.
- `[پیشنهاد فنی]` fail-fast روی نسبت‌های مساوی از ورود tie-breaking گزارش‌نشده جلوگیری می‌کند.
- `[آزمون کمکی]` اعداد مثال اجراشده پارامتر مقاله یا نتیجه بازتولیدشده مقاله نیستند.

## 4. فرمان‌های اجراشده

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_pricing.py tests\unit\test_feasibility.py tests\unit\test_knapsack_greedy.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe format --check src tests scripts
.\.venv\Scripts\ruff.exe check src tests scripts
.\.venv\Scripts\mypy.exe src tests scripts
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\run_stage_ten_a_example.py
```

## 5. نتایج واقعی اجرا

برای مثال کمکی:

```text
residual_before = (4, 6, 8, 8)
congestion shares = (1, 5/6, 1/4, 1/4)
congestion = 0.5833333333333334
congestion_factor = 0.010416666666666666
new_ratio = 30/2 = 15
victim_ratio = 5/4 = 1.25
15 >= 1.05 * 1.25 = True
selected_victim = victim
final states = incoming: accepted, victim: preempted
residual_after = (3, 5, 8, 8)
```

SHA-256 artifact:

```text
F82FE3935CF8C9A787E5A1E4AA591632B27545FF6D7C6646DD02C2D9DA1413C2
```

## 6. آزمون‌های موفق و ناموفق

نتیجه نهایی:

```text
122 passed in 0.22s
47 files already formatted
Ruff: All checks passed
mypy: no issues found in 47 source files
pip check: No broken requirements found
```

شکست‌های میانی پنهان نشده‌اند:

1. اجرای نخست scoped هنگام collection با 3 خطای circular import شکست خورد.
2. پس از حذف re-export الگوریتم، 2 خطای circular import از initializer شبیه‌سازی باقی ماند.
3. پس از اصلاح چرخه، 19 آزمون موفق شدند ولی mypy دو خطای `**dict` در آزمون مرزی گزارش کرد.
4. initializerها import-free و فراخوانی آزمون typed شد؛ سپس همه کنترل‌ها موفق شدند.

## 7. فرض‌های استفاده‌شده

- ASSUMP-003: congestion میانگین چهار نسبت clipped و عامل `0.025*(1-congestion)`.
- ASSUMP-004: `new_ratio >= 1.05*victim_ratio` با پذیرش برابری.
- ASSUMP-005: حداکثر یک قربانی در KG-P و انتخاب اولین قربانی feasible.
- ASSUMP-006: break فوری و تراکنش اتمیک.
- هیچ فرض بازتولید تأییدنشده‌ای استفاده نشده است.

## 8. ابهامات یا اطلاعات مفقود

- `[نامشخص]` مقدار دقیق price برای وظیفه‌ای که از total capacity بزرگ‌تر است؛ کد فقط شاخه را با `None` مشخص می‌کند.
- `[نامشخص]` percentile در مجموعه running خالی و در تساوی‌ها.
- `[نامشخص]` tie-breaking نسبت‌های مساوی قربانیان و ورودی‌ها؛ کد fail-fast می‌کند.
- `[نامشخص]` Round 2 روش KG-R شبه‌کد مستقل ندارد.
- `[نامشخص]` پارامترهای کامل knapsack ژنتیکی مورد استفاده در Round 1.

## 9. تصمیم موردنیاز از کاربر

برای همین زیربخش تصمیم دیگری لازم نیست. برای تکمیل نخستین policy کامل، سه تصمیم زیر مسدودکننده‌اند:

1. sentinel یا فرمول price وظیفه ناممکن؛
2. تعریف percentile برای مجموعه خالی و ties؛
3. تفسیر اجرایی Round 2 در KG-R.

## 10. مرحله بعدی پیشنهادی

مرحله دهم-B: ارائه گزینه‌های کم‌فاصله برای سه ابهام بالا و، پس از تأیید، پیاده‌سازی کامل
KnapsackGreedy Retention به‌عنوان نخستین روش کامل قابل‌اجرا.
