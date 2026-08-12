# مرحله دهم-J: رگرسیون مشترک چهار policy

## دامنه علمی

- `[پیشنهاد فنی]` یک schema مشترک برای اجرای مستقل و خلاصه‌سازی KG-R، KG-P،
  Pipeline DK-R و Pipeline DK-P افزوده شد.
- `[آزمون کمکی]` هر چهار policy روی یک state اولیه و یک workload یکسان اجرا شدند.
- `[ابزار کمکی]` KG-R و KG-P فقط در این regression از Exact selector استفاده
  می‌کنند؛ این selector جایگزین GA نامشخص مقاله نیست.
- Pipeline DK-R و DK-P از pyeasyga 0.3.1 و تنظیم رسمی تأییدشده `200/20/50` با
  seed اجباری استفاده می‌کنند.
- معیار `active_utility_after_auction` صرفاً کنترل پس از یک مزایده است و نباید به
  completed Utility یا نتیجه عددی مقاله نسبت داده شود.

## نتیجه واقعی

| روش | Accepted | Rejected | Retained | Preempted | Active Utility | Residual |
| --- | --- | --- | --- | --- | ---: | ---: |
| `knapsack_greedy_retention` | extra | incoming | current-high, current-low | — | 22 | 0 |
| `knapsack_greedy_preemption` | extra, incoming | — | current-high | current-low | 33 | 0 |
| `pipeline_double_knapsack_retention` | extra | incoming | current-high, current-low | — | 22 | 0 |
| `pipeline_double_knapsack_preemption` | incoming, extra | — | current-high | current-low | 33 | 0 |

تمام خروجی‌ها با محاسبه دستی منطبق‌اند، ظرفیت چهار بعد منفی نشده، و state مشترک
ورودی پس از اجرای هر policy بدون تغییر باقی مانده است. برابری دو روش Retention و
دو روش Preemption فقط ویژگی این سناریوی کوچک است و ادعای برابری عمومی الگوریتم‌ها
نیست.

## بازتولید

```powershell
.\.venv\Scripts\python.exe scripts\run_stage_ten_j_four_policy_regression.py
```

پیکربندی در `configs/stage10j_four_policy_regression.json` و artifact خام در
`results/raw/stage10j/four_policy_regression.json` ذخیره می‌شود. metadata هر خروجی
منشأ selector، تنظیمات کامل GA، seed و هشدار معیار کمکی را نگه می‌دارد.

## اعتبارسنجی نهایی

```text
targeted tests: 6 passed in 2.94s
full pytest: 174 passed in 7.01s
Ruff format: 72 files already formatted
Ruff lint: All checks passed
mypy: no issues found in 72 source files
pip check: No broken requirements found
artifact SHA-256 (run 1): DFC45FE9D644941039C64CAF89B1C02D35088275F9340C08A8C1CBB98F2DBF18
artifact SHA-256 (run 2): DFC45FE9D644941039C64CAF89B1C02D35088275F9340C08A8C1CBB98F2DBF18
```

دو اجرای متوالی با seed ثابت artifact بایت‌به‌بایت یکسان ساختند. در نخستین کنترل
ایستا، قرارداد protocol به‌علت writable تلقی‌شدن attributeها با خروجی‌های تخصصی
policy سازگار نبود؛ قرارداد به propertyهای فقط‌خواندنی اصلاح شد. در اجرای هدفمند
بعدی نیز شش آزمون موفق بودند، اما Ruff یک import استفاده‌نشده را گزارش کرد که حذف
شد. QA کامل نهایی هیچ شکست یا هشدار وابستگی ندارد.
