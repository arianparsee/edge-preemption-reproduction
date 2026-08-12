# مرحله ۱۳-F — ASSUMP-043 و آماده‌سازی اجرای کامل PIPE-NORMAL

تاریخ: 2026-08-12  
مبنا: `arXiv:2403.15665v2 (2024)`  
وضعیت: **pilot چهارروشی موفق؛ اجرای کامل هنوز شروع نشده است**

## تصمیم علمی

ASSUMP-043 با گزینه A و برچسب `[فرض بازتولید]` تصویب شد. در KG-R و KG-P فقط
هنگامی که حداقل قیمت قابل‌قبول دقیقاً میان چند سرور مساوی است، server IDهای tied
مرتب و انتخاب uniform با همان policy RNG انجام می‌شود. این قاعده به هیچ tie دیگری
تعمیم ندارد. counter هر اجرا در `client.equal_minimum_price_ties` ذخیره می‌شود.

## اجرای واقعی محدود

workload Normal کمکی با seed `15626834761513784926`، سه arrival slot، هشت سرور،
47 وظیفه و maximum absolute deadline برابر 17 میان هر چهار policy مشترک بود.

| Policy | Policy seed | Time (s) | Repairs | Ties | Completed | Rejected | Preempted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| KG-R | 14636373841211474365 | 24.9500 | 74 | 0 | 11 | 36 | 0 |
| KG-P | 10214968163706227246 | 25.5944 | 76 | 1 | 13 | 34 | 0 |
| DK-R | 9334793088729515147 | 49.7616 | 85 | 0 | 10 | 37 | 0 |
| DK-P | 10066703118538082645 | 50.3811 | 77 | 0 | 9 | 38 | 4 |

همه اعداد `[آزمون کمکی]` هستند و Figure 6 یا نتیجه رسمی مقاله نیستند.

## harness اجرای کامل

- config شامل 30 workload seed مرتب و 120 policy seed مادی‌شده است؛
- هر workload میان چهار policy مشترک می‌ماند؛
- هر pair خروجی، workload و manifest مستقل دارد؛
- overwrite ممنوع و resume مبتنی بر hash است؛
- aggregation پیش از تکمیل 120 raw run ممنوع است؛
- aggregation اصلی فقط arithmetic mean است؛
- Figure 6 در این مرحله ساخته نشده است.

Config SHA-256:

```text
AFA7C249911D34CDACEFA4B2B80CDBFC44CDDF47A7F2CFD0E246E7CD70FEE3F0
```

## QA

```text
ruff: passed
mypy: passed on 94 source/test files
pytest: 233 passed in 22.59s
full raw runs at Stage-13F close: 0/120
aggregation guard: correctly failed with missing 120
```

پس از این گزارش، Stage 13-G با مجوز جداگانه کاربر چهار pair نخست را اجرا کرد؛
وضعیت جدید و timingها فقط در `stage_thirteen_g_100_slot_timing_gate.md` ثبت شده‌اند.
