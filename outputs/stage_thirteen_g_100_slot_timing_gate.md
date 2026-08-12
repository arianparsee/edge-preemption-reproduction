# مرحله ۱۳-G — Timing gate صد-slotی PIPE-NORMAL

تاریخ: 2026-08-12  
مبنا: `arXiv:2403.15665v2 (2024)`  
وضعیت: **یک workload کامل روی هر چهار policy اجرا شد؛ 4/120 raw pair موجود است**

## دامنه اجرا

نخستین workload seed از config مرتب و مادی‌شده انتخاب شد:

```text
workload_seed = 541501192080118187
arrival_slots = 100
last_arrival_slot = 99
configured_last_slot = 115
drain_slots = 16
generated_tasks = 1395
shared_workload_sha256 = e571940d01f46f5251d62d89453099c7f466fda7e22ccd350f4aa05d3c4a1200
```

چهار policy به‌صورت ترتیبی اجرا شدند تا اندازه‌گیری wall-time با رقابت هم‌زمان CPU
مخدوش نشود. wall-timeها `[آزمون کمکی]` هستند، در raw scientific result تزریق
نشده‌اند و runtime گزارش‌شده مقاله محسوب نمی‌شوند.

## نتایج واقعی

| Policy | Wall time (s) | Completed | Rejected | Preempted | Completed utility | Rejected utility | Repairs | KG client ties |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| KG-R | 608.9653 | 123 | 1272 | 0 | 9109.31351279173 | 74892.12223005593 | 857 | 4 |
| KG-P | 619.0946 | 144 | 1251 | 22 | 11771.752459885452 | 72229.68328296221 | 860 | 3 |
| Pipeline DK-R | 1159.4936 | 24 | 1371 | 0 | 1451.859640016816 | 82549.57610283085 | 944 | 0 |
| Pipeline DK-P | 1231.1643 | 40 | 1355 | 6 | 3193.9193472199277 | 80807.51639562774 | 947 | 0 |

مجموع زمان سری واقعی یک workload برابر `3618.7178222 s = 60.3119637 min` است.

## اعتبارسنجی

- هر چهار workload SHA-256 یکسان دارند؛
- result و workload hash هر چهار manifest معتبر است؛
- برای هر policy، Completed و Rejected افراز تمام 1395 task هستند؛
- Preempted زیرمجموعه Rejected است؛
- چهار اجرای `--resume` همگی `skipped_existing_verified` شدند؛
- حجم چهار result به‌ترتیب حدود 7.22، 7.32، 6.69 و 6.78 MB است؛
- artifactهای چهار pair با workloadهای تکراری مجموعاً `30,527,578` بایت هستند.

## برآورد هزینه اجرای کامل

`[آزمون کمکی؛ برون‌یابی، نه اندازه‌گیری]` اگر هر 30 workload دقیقاً زمان seed اول
را بگیرند، اجرای سری 120 pair حدود `30.15598 ساعت` و 29 workload باقی‌مانده حدود
`29.15078 ساعت` طول می‌کشد. این برآورد عدم‌قطعیت بین seedها را اندازه‌گیری نمی‌کند
و ادعای runtime مقاله نیست.

## وضعیت تجمیع و Figure 6

Aggregator دوباره اجرا و عمداً متوقف شد:

```text
FileNotFoundError: full aggregation requires all 120 raw runs; missing 116
```

بنابراین arithmetic mean سی‌تکراری و Figure 6 هنوز تولید نشده‌اند. هیچ میانگین
چهار اجرای موجود به‌عنوان نتیجه مقاله گزارش نشده است.

## QA نهایی

```text
ruff: passed
mypy: passed on 94 source/test files
pytest: 233 passed in 20.27s
raw full-run pairs: 4/120
aggregation: blocked (missing 116)
figure_6_reproduced: false
```
