# مرحله دهم-B: پیاده‌سازی KnapsackGreedy Retention

## 1. کارهای انجام‌شده

- صفحات 6 و 7 PDF مبنای arXiv v2 با رندر بصری بازبینی شدند.
- قاعده حاکمیت منبع v2/IEEE 2025 ثبت شد.
- ASSUMP-007 تا ASSUMP-009 در رجیستر و ماتریس ردیابی ثبت شدند.
- sentinel وظیفه ناممکن و strict empirical percentile پیاده‌سازی شدند.
- جریان کامل دو دور KG-R شامل bidding همه سرورها، انتخاب client و Round 2 fit-only پیاده شد.
- رابط مشترک `AllocationPolicy` و قرارداد تزریق `KnapsackSelector` ایجاد شد.
- selector دقیق exhaustive فقط به‌عنوان `[ابزار کمکی]` مثال‌های کوچک ساخته شد.
- آزمون‌های واحد، یکپارچه، چندسروری و مثال دستی/اجرایی تکمیل شدند.

## 2. فایل‌های ایجاد یا تغییرکرده

- `docs/assumptions.md`
- `outputs/traceability_matrix_arxiv_v2.md`
- `outputs/stage_ten_b_manual_calculation.md`
- `outputs/stage_ten_b_knapsack_greedy_retention.md`
- `src/edge_reproduction/algorithms/base.py`
- `src/edge_reproduction/algorithms/knapsack.py`
- `src/edge_reproduction/algorithms/pricing.py`
- `src/edge_reproduction/algorithms/knapsack_greedy_retention.py`
- `tests/unit/test_pricing.py`
- `tests/unit/test_knapsack.py`
- `tests/unit/test_knapsack_greedy_retention.py`
- `tests/integration/test_stage_ten_b_kg_retention.py`
- `scripts/run_stage_ten_b_kg_retention_example.py`
- `results/raw/stage10b/kg_retention_example.json`
- `README.md`

## 3. ارتباط تغییرها با مقاله

- `[صریح در مقاله]` Section V-A1 و Algorithm 1، صفحه 6: knapsack روی residual، قیمت `0.9U`،
  percentile، congestion و قیمت وظیفه ناممکن بزرگ‌تر از Utility.
- `[صریح در مقاله]` Section III، صفحه 3: دو دور bidding و بازگشت به ارزان‌ترین server.
- `[صریح در مقاله]` صفحه 6: Round 1 نسخه non-preemptive همان Round 1 اصلی است.
- `[فرض بازتولید؛ تأییدشده]` ASSUMP-007 قیمت impossible، ASSUMP-008 percentile و
  ASSUMP-009 رفتار Round 2 Retention را اجرایی می‌کنند.
- `[منبع تکمیلی خارج از مبنای v2]` تعریف توصیفی Percentile از نسخه IEEE 2025 فقط برای
  تحلیل ابهام ثبت شده است؛ روش مبنا همچنان arXiv v2 است.
- `[ابزار کمکی]` exact selector جایگزین رسمی pyeasyga مقاله نیست.

## 4. فرمان‌های اجراشده

```powershell
pdftoppm -f 6 -l 7 -png -r 150 <arxiv-v2.pdf> <temporary-prefix>
.\.venv\Scripts\python.exe -m pytest tests\unit\test_pricing.py tests\unit\test_knapsack.py tests\unit\test_knapsack_greedy_retention.py tests\integration\test_stage_ten_b_kg_retention.py -q
.\.venv\Scripts\python.exe scripts\run_stage_ten_b_kg_retention_example.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe format --check src tests scripts
.\.venv\Scripts\ruff.exe check src tests scripts
.\.venv\Scripts\mypy.exe src tests scripts
.\.venv\Scripts\python.exe -m pip check
```

## 5. نتایج واقعی اجرا

```text
Round 1 prices:
auto          = 13.5                  autoFit=True
rejected-high = 9.666666666666666     autoFit=False
rejected-low  = 3.933333333333333     autoFit=False
impossible    = 20.000000000000004    feasible=False

accepted = [auto]
rejected = [impossible, rejected-high, rejected-low]
active final = [current, auto]
preempted = []
residual before = (6,6,6,6)
residual after  = (0,0,0,0)
```

نتیجه برنامه با oracle دستی در priceها، ترتیب، outcomeها و residual اختلاف صفر دارد.

```text
artifact SHA-256 = A77249B28A538BA2D5675CFC44B13091A9309F64BA144770910845F61EB3A299
```

اجرای دوم همان هش را تولید کرد.

## 6. آزمون‌های موفق و ناموفق

```text
137 passed in 0.76s
54 files already formatted
Ruff: All checks passed
mypy: no issues found in 54 source files
pip check: No broken requirements found
```

- آزمون ناموفق نهایی: صفر.
- شکست میانی: پس از 20 آزمون موفق، Ruff یک import نامرتب گزارش کرد؛ با `ruff --fix`
  اصلاح شد و اجرای بعدی کاملاً موفق بود.
- یک خطای منطقی طی آزمون چندسروری کشف و اصلاح شد: رد `price>U` اکنون پیش از Tie-check
  انجام می‌شود تا sentinelهای مساوی سرورهای ناممکن مانع رد نشوند.

## 7. فرض‌های استفاده‌شده

- ASSUMP-001 تا ASSUMP-009 همگی مصوب‌اند.
- در این زیربخش مستقیماً ASSUMP-003، ASSUMP-007، ASSUMP-008 و ASSUMP-009 فعال‌اند.
- Tieهای قیمت قابل‌قبول، نسبت مرتب‌سازی و subset هم‌ارزش fail-fast هستند.
- هیچ Tie-breaking یا retry پنهانی اعمال نشد.

## 8. ابهامات یا اطلاعات مفقود

- `[نامشخص]` نسخه و تنظیمات کامل pyeasyga، population، mutation، crossover و selection.
- `[نامشخص]` Tie-breaking بین subsetهای هم‌ارزش، offerهای مساوی و نسبت‌های مساوی.
- `[نامشخص]` retry وظیفه ردشده در auctionهای آینده.
- `[نامشخص]` در KG-P آیا `s.jobs` پس از پذیرش autoFit یک مجموعه live است یا snapshot وظایف
  جاری پیش از Round 2.

اثر: کنترل‌جریان KG-R قابل‌اجرا و تأییدشده است، ولی اجرای آزمایش کامل مقاله باید selector
ژنتیکی دقیق مقاله را دریافت کند؛ exact selector فقط برای تست کوچک معتبر است.

## 9. تصمیم موردنیاز از کاربر

برای تکمیل مرحله دهم-B تصمیم دیگری لازم نیست. پیش از KG-P باید victim pool مشخص شود:
آیا فقط وظایف جاری پیش از آغاز Round 2 قربانی‌اند، یا autoFitهای تازه‌پذیرفته‌شده نیز وارد
`s.jobs` و قابل Preemption می‌شوند؟

## 10. مرحله بعدی پیشنهادی

مرحله دهم-C: تعیین semantics مجموعه victim و سپس پیاده‌سازی کامل KnapsackGreedy Preemption
با استفاده مجدد از Round 1 حاضر، ASSUMP-004 تا ASSUMP-006 و آزمون اتمیک تک‌قربانی.
