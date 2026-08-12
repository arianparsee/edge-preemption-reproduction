# مرحله دهم-C: پیاده‌سازی KnapsackGreedy Preemption

## 1. کارهای انجام‌شده

- ASSUMP-010 با ده قاعده اجرایی و وضعیت approved ثبت شد.
- تفاوت آن با پیشنهاد اولیه ثبت شد: انتخاب snapshot یکسان است، اما نسخه کاربر membership،
  frozen time، removal، protection و scope را دقیق‌تر می‌کند.
- `VictimSnapshotEntry` immutable و capture پیش از هر admission پیاده‌سازی شد.
- Round 2 پیش‌دستانه با autoFit-first، ترتیب نزولی ورودی‌ها و snapshot صعودی قربانیان ساخته شد.
- شرط ۵٪، fit چهاربعدی، تک‌قربانی، break و replacement اتمیک اعمال شدند.
- autoFitها و direct admissionهای دور جاری از victim pool محافظت شدند.
- Round 1 مشترک، client choice و رابط `AllocationPolicy` به policy کامل KG-P متصل شدند.
- آزمون واحد، یکپارچه، مثال دستی و artifact واقعی اجرا شدند.

## 2. فایل‌های ایجاد یا تغییرکرده

- `docs/assumptions.md`
- `outputs/traceability_matrix_arxiv_v2.md`
- `outputs/stage_ten_c_manual_calculation.md`
- `outputs/stage_ten_c_knapsack_greedy_preemption.md`
- `src/edge_reproduction/algorithms/knapsack_greedy_preemption.py`
- `src/edge_reproduction/algorithms/knapsack_greedy_retention.py`
- `tests/unit/test_knapsack_greedy_preemption.py`
- `tests/unit/test_knapsack_greedy_retention.py`
- `tests/integration/test_stage_ten_c_kg_preemption.py`
- `scripts/run_stage_ten_c_kg_preemption_example.py`
- `results/raw/stage10c/kg_preemption_example.json`
- `README.md`

## 3. ارتباط تغییرها با مقاله

- `[صریح در مقاله]` Algorithm 2، صفحه 7: پذیرش autoFit، نزولی‌کردن returning jobs،
  صعودی‌کردن `s.jobs`، direct fit و سپس بررسی preemption.
- `[صریح در مقاله]` نثر صفحه 7: مقایسه job جدید با currently-running job و شرط منابع
  victim به‌علاوه residual.
- `[فرض بازتولید؛ تأییدشده]` ASSUMP-004 جهت شرط ۵٪، ASSUMP-005 تک‌قربانی، ASSUMP-006
  break/atomicity و ASSUMP-010 victim snapshot را اجرایی می‌کنند.
- `[آزمون کمکی]` اعداد سناریو نتیجه مقاله نیستند.
- `[ابزار کمکی]` exact selector به‌جای GA رسمی مقاله معرفی نمی‌شود.

## 4. فرمان‌های اجراشده

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_knapsack_greedy.py tests\unit\test_knapsack_greedy_retention.py tests\unit\test_knapsack_greedy_preemption.py tests\integration\test_stage_ten_b_kg_retention.py tests\integration\test_stage_ten_c_kg_preemption.py -q
.\.venv\Scripts\python.exe scripts\run_stage_ten_c_kg_preemption_example.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe format --check src tests scripts
.\.venv\Scripts\ruff.exe check src tests scripts
.\.venv\Scripts\mypy.exe src tests scripts
.\.venv\Scripts\python.exe -m pip check
```

## 5. نتایج واقعی اجرا

```text
victim snapshot:
  victim-low  ratio=1  frozen_time=4
  victim-high ratio=3  frozen_time=4

Round 1 prices:
  auto            7.2   autoFit=True
  incoming-first  29.25
  incoming-second 19.5
  rejected        9.875

accepted  = [auto, incoming-first, incoming-second]
preempted = [victim-low, victim-high]
rejected  = [rejected]
residual before = (2,2,2,2)
residual after  = (0,0,0,0)
```

محاسبه دستی و برنامه در snapshot، priceها، ترتیب victims، stateها و residual اختلاف صفر دارند.

```text
artifact SHA-256 = C0D44058B38672FDD69CD01FDDF5B90ECFFF350A40E21330E8241B95B9AD37D8
```

هش اجرای دوم بدون تغییر بود.

## 6. آزمون‌های موفق و ناموفق

```text
146 passed in 0.28s
58 files already formatted
Ruff: All checks passed
mypy: no issues found in 58 source files
pip check: No broken requirements found
```

- آزمون ناموفق نهایی: صفر.
- شکست میانی کد یا آزمون در این زیربخش رخ نداد.
- آزمون‌ها snapshot order، frozen time، victim removal، auto/direct protection، returning tie،
  victim tie، one-victim limit، atomic accounting و full two-round flow را پوشش می‌دهند.

## 7. فرض‌های استفاده‌شده

- ASSUMP-003 و ASSUMP-007/008 برای Round 1.
- ASSUMP-004 برای شرط دقیق ۵٪.
- ASSUMP-005 برای حداکثر یک victim.
- ASSUMP-006 برای break و تراکنش اتمیک.
- ASSUMP-010 برای snapshot ثابت و protection دور جاری.
- هیچ فرض تأییدنشده یا Tie-breaking پنهان استفاده نشده است.

## 8. ابهامات یا اطلاعات مفقود

- `[نامشخص]` تنظیمات کامل pyeasyga و نسخه library.
- `[نامشخص]` Tie-breaking قیمت‌های مساوی، نسبت‌های مساوی و subsetهای هم‌ارزش؛ کد fail-fast است.
- `[نامشخص]` retry وظیفه رد یا preempt‌شده در دورهای آینده.
- `[نامشخص]` جزئیات کامل Double Knapsack پایه و semantics چندقربانی DK-P باید از منبع مستقیم [4]
  و متن v2 در زیربخش بعدی ادغام شوند.

اثر: کنترل‌جریان KG-P کامل و قابل‌اجراست، ولی بازتولید آزمایش اصلی همچنان به selector ژنتیکی
دقیق مقاله و تنظیمات گزارش‌نشده آن وابسته است.

## 9. تصمیم موردنیاز از کاربر

برای پایان مرحله دهم-C تصمیم دیگری لازم نیست. پیش از پیاده‌سازی Double Knapsack باید ابتدا
منبع مستقیم [4] خط‌به‌خط با خلاصه v2 تطبیق داده شود؛ هر ابهام باقی‌مانده پیش از کدنویسی برای
تأیید ارائه خواهد شد.

## 10. مرحله بعدی پیشنهادی

مرحله دهم-D: استخراج اجرایی و پیاده‌سازی Double Knapsack Retention با استفاده از PDF مرجع [4]،
بدون تعمیم ASSUMP-010 به Double Knapsack.
