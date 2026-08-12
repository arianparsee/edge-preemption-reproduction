# مرحله سیزدهم-B - harness آزمایش و smoke کمکی چهار policy

تاریخ اجرا: 2026-08-12  
منبع مبنا: arXiv:2403.15665v2 (2024)  
وضعیت: **harness کمکی کامل؛ هر 12 آزمایش رسمی Stage 13-A همچنان non-executable**

## 1. دامنه علمی

- `[پیشنهاد فنی]` یک orchestration harness عمومی ساخته شد.
- `[آزمون کمکی]` تنها execution ثبت‌شده، regression تک‌مزایده‌ای Stage 10-J است.
- معیار آن `active_utility_after_auction` است، نه completed Utility مقاله.
- هیچ paper experiment، شکل 3-20 یا Southampton algorithm run اجرا نشده است.
- harness نمی‌تواند configهای Stage 13-A را اجرا کند؛ آن‌ها با decision IDهای
  حل‌نشده fail-fast می‌شوند.

## 2. اجزای پیاده‌سازی‌شده

| جزء | مسئولیت |
| --- | --- |
| `AuxiliaryExecutionConfig` | schema بسته، seed صریح، label اجباری و unresolved gating |
| `run_four_policy_smoke` | اجرای مستقل KG-R/KG-P/Pipeline DK-R/Pipeline DK-P |
| `run_experiment` | اجرای یک config و نوشتن raw result/manifest |
| `run_registry` | اجرای sequential registry و aggregate index |
| `--resume` | تطبیق config/result hash و verified skip |
| manifest | نسخه محیط، وابستگی‌ها، seed، provenance hash و هشدار علمی |

## 3. رفتار ایمنی و reproducibility

- run directory موجود بدون `--resume` بازنویسی نمی‌شود.
- run ناقص، config متفاوت یا result دستکاری‌شده در resume رد می‌شود.
- summary aggregate می‌تواند از raw runهای immutable دوباره ساخته شود.
- wall time در artifact علمی ذخیره نمی‌شود، چون nondeterministic است و مقاله نیز
  runtime این smoke را هدف قرار نداده است.
- result و manifest در دو root پاک، byte-for-byte یکسان آزمون شدند.
- `paper_experiment_claimed=false` در manifest و summary ثبت شده است.

## 4. config اجرای واقعی

| پارامتر | مقدار | وضعیت |
| --- | --- | --- |
| experiment | `stage13b-four-policy-single-auction-smoke` | auxiliary |
| run ID | `seed-20240811` | `[پیشنهاد فنی]` |
| seed | `20240811` | config Stage 10-J؛ seed مقاله نیست |
| runner | `four_policy_single_auction` | `[آزمون کمکی]` |
| scenario | `configs/stage10j_four_policy_regression.json` | مثال دستی چهار وظیفه‌ای |
| unresolved decisions | `[]` | فقط برای همین smoke محدود |

خالی‌بودن decisionها به آزمایش‌های مقاله تعمیم داده نمی‌شود.

## 5. نتایج واقعی smoke

| روش | Accepted | Rejected | Retained | Preempted | Active Utility |
| --- | --- | --- | --- | --- | ---: |
| KG-R | extra | incoming | current-high, current-low | - | 22 |
| KG-P | extra, incoming | - | current-high | current-low | 33 |
| Pipeline DK-R | extra | incoming | current-high, current-low | - | 22 |
| Pipeline DK-P | incoming, extra | - | current-high | current-low | 33 |

این خروجی با مثال دستی Stage 10-J منطبق است. برابری دو Retention و دو Preemption
فقط ویژگی همین مثال کوچک است.

## 6. artifactهای واقعی

- raw result:
  `results/raw/stage13b/stage13b-four-policy-single-auction-smoke/seed-20240811/result.json`
- manifest:
  `results/raw/stage13b/stage13b-four-policy-single-auction-smoke/seed-20240811/manifest.json`
- registry summary:
  `results/aggregated/stage13b/run_summary.json`

SHA-256:

| artifact | SHA-256 |
| --- | --- |
| result | `19066D5D9A4D4CDA576E562E90B5711965FE8EC0A88D07E167E5D8B36C7AFA33` |
| manifest | `30AEAB63F978DA42F9BE264ED5862D5CDB6B05D30524806732B59E38F8C9166A` |
| resumed summary | `EEA48BED10C6908B328C594DCD1781DDDD700A94D52FAC977390AC1E3FD5BD95` |

manifest محیط واقعی را CPython 3.12.13، Windows AMD64، NumPy 2.5.1 و pyeasyga
0.3.1 ثبت کرد.

## 7. آزمون منفی واقعی PIPE-NORMAL

فرمان زیر عمداً اجرا شد:

```powershell
.\.venv\Scripts\python.exe scripts\run_experiment.py --config configs\experiments\pipe_normal.json
```

خروجی مورد انتظار `UnresolvedDecisionError` بود و اجرا متوقف شد. decision IDهای
گزارش‌شده:

`EXPERIMENT_SEEDS`, `EXPERIMENT_REPEATS`, `SYNTHETIC_HORIZON`, `DRAIN_POLICY`,
`OUTPUT_SIZE`, `NORMAL_HIGH_LOW_THRESHOLDS`, `RESUBMISSION`,
`FINAL_REJECTION_SEMANTICS`, `KG_GA_SETTINGS`.

هیچ output directory برای این اجرای مسدود ساخته نشد.

## 8. فرمان‌های اجرای موفق

```powershell
.\.venv\Scripts\python.exe scripts\run_all_experiments.py --registry configs\experiments\auxiliary_stage13b_registry.json
.\.venv\Scripts\python.exe scripts\run_all_experiments.py --registry configs\experiments\auxiliary_stage13b_registry.json --resume
```

اجرای اول: `succeeded_count=1`.  
اجرای دوم: `verified_skip_count=1` و raw artifacts بدون تغییر ماندند.

## 9. آزمون‌ها و QA

آزمون‌های جدید Stage 13-B هفت مورد هستند:

- config label/schema/type guards؛
- unresolved execution config؛
- ممنوعیت اجرای Stage-13A paper spec؛
- isolated raw result و resume-safe؛
- corrupted artifact rejection؛
- registry summary/resume؛
- byte stability در دو root پاک.

همراه با دو regression قبلی Stage 10-J، targeted run برابر `9 passed in 7.90s`
بود.

QA کامل نهایی:

- Ruff format: 97 فایل؛
- Ruff lint: موفق؛
- mypy strict: 85 source file بدون issue؛
- pytest: `208 passed in 20.61s`؛
- آزمون ناموفق: صفر.

## 10. محدودیت‌ها و نتیجه

- harness هنوز runner زمانی چند-epoch ندارد.
- dataset generator به policy-integrated simulator متصل نشده است.
- aggregation paper metrics پیاده نشده است.
- Batch DK-R، Gurobi و official Southampton همچنان blocked هستند.
- runtime واقعی smoke عمداً metric علمی نیست.

نتیجه: زیرساخت اجرای deterministic و resume-safe آماده است و مرز paper/auxiliary
را enforce می‌کند. هیچ ادعای مقاله با این smoke بازتولید نشده است.
