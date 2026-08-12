# مرحله ۱۳-I — Checkpoint چهار workload ابری PIPE-NORMAL

تاریخ: 2026-08-12

مبنا: `arXiv:2403.15665v2 (2024)`

برچسب علمی: `[آزمون کمکی؛ checkpoint، نه نتیجه ۳۰ تکراری مقاله]`

وضعیت: **۴ workload و ۱۶ pair کامل؛ تجمعی همراه Stage 13-H برابر 5/30 workload و 20/120 pair**

## دامنه و اجرای ابری

Workflow محدود `Stage 13-I four-workload cloud checkpoint` فقط چهار seed بعدی config
مادی‌شده و چهار policy را اجرا کرد. اجرای ۳۰ workload و تولید Figure 6 در این مرحله
غیرفعال باقی ماندند.

- GitHub Actions run: `31629941152`
- commit: `c9c6677c8ec307452b33b677ca656721277937dd`
- وضعیت نهایی: 17/17 job موفق (16 pair و یک summary validator)
- زمان دیواری workflow: از `18:53:49Z` تا `19:33:17Z`، حدود 39 دقیقه و 28 ثانیه
- artifact نهایی: `stage13i-cloud-checkpoint-summary-31629941152`
- SHA-256 فایل ZIP: `27a9ef5ee11825bf713760e45422dbd4c611f91ddfc11ba15cec6c6091444cf7`
- انقضای artifactها: 2026-08-26

## workloadهای اجراشده

| Workload seed | Tasks | Shared workload SHA-256 | Parallel-policy time (s) |
| ---: | ---: | --- | ---: |
| 2074092324964443463 | 1353 | `1523b0eb04015160adce5ff14b0eb8febbb906ffdd0a6fb9ba58772e01900a55` | 1155.147983435 |
| 2218754797665862270 | 1421 | `b5a75b7ed9a0822f9e91b7eaf68e5b147b3ba27c4582175cc2b4ee7cfd819c1f` | 1210.877173420 |
| 2997476077322633071 | 1345 | `423da189dbc8d62b8d261b9d70c7f56d58ba4e960c54f9e10dfa1087bce2aba7` | 1128.610485172 |
| 3782887846963969634 | 1438 | `5564a0af4e8c8540d6f5058e7b35ef28d692fffdeb903990f0a3ae3a856b1129` | 1263.886449915 |

در هر seed، hash workload هر چهار policy یکسان بود. مجموع taskها 5557 و حجم
artifactهای checkpoint برابر `120,107,828` بایت (حدود 114.54 MiB) بود.

## نتایج واقعی checkpoint

اعداد زیر میانگین **فقط چهار workload checkpoint** هستند و به‌عنوان aggregation
علمی ۳۰ تکراری یا نتیجه مقاله معرفی نمی‌شوند.

| Policy | Completed | Rejected | Preempted | Completed utility | Rejected utility | Repairs | Ties | Wall time (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| KG-R | 136.00 | 1253.25 | 0.00 | 10410.855126 | 73181.042839 | 843.25 | 2.50 | 615.825458 |
| KG-P | 140.25 | 1249.00 | 31.00 | 11537.976091 | 72053.921875 | 846.50 | 2.75 | 573.284109 |
| Pipeline DK-R | 16.25 | 1373.00 | 0.00 | 1198.153816 | 82393.744150 | 967.00 | 0.00 | 1117.391746 |
| Pipeline DK-P | 38.50 | 1350.75 | 13.00 | 3289.268544 | 80302.629422 | 959.50 | 0.00 | 1174.926193 |

ضعف عددی Pipeline DK نسبت به KG و تعداد زیاد repairها در هر چهار seed ادامه دارد؛
این مشاهده تشخیصی است و علت آن در این checkpoint تعیین نشده است.

## timing و برون‌یابی

`[آزمون کمکی]` زمان موازی چهار policy برای هر workload میانگین
`1189.630523 s = 19.8272 min`، انحراف معیار نمونه `60.215871 s` و بازه
`1128.610485` تا `1263.886450 s` داشت. مجموع معادل سری ۱۶ pair برابر
`13925.710020 s = 3.8683 h` بود. زمان workflow شامل صف runner و نصب وابستگی‌ها
است و نباید با runtime الگوریتم مقاله یکی دانسته شود.

## resume و اعتبارسنجی مستقل

- summary job تمام ۱۶ pair، چهار hash مشترک، partition حالت‌ها و قید
  `ever_preempted subset rejected` را کنترل کرد؛
- همه ۱۷ artifact دانلود شدند؛ ۱۶ `result.json` و ۱۶ `manifest.json` موجود بود؛
- resume با config دقیق commit `c9c6677` روی هر ۱۶ pair نتیجه
  `skipped_existing_verified` داد و هیچ pair دوباره اجرا نشد؛
- نخستین resume با config محلی Windows عمداً روی `existing config hash mismatch`
  fail-fast کرد؛ config commit دارای hash ثبت‌شده
  `b0ae2597...1963` بود. اختلاف فقط byte-level/line-ending بود و با بازیابی config
  دقیق commit برطرف شد؛
- recorder محلی summary را دوباره تولید کرد و مقایسه بازگشتی JSON هیچ اختلاف
  ساختاری یا عددی با summary ابری نشان نداد.

## خطای workflow اولیه و اصلاح

Run اولیه `31629252722` پیش از محاسبه شکست خورد، زیرا YAML seedهای بزرگ بدون
quotation را به نمایش علمی/عدد ممیز شناور تبدیل کرد. seedها به رشته‌های quoted
تغییر کردند و آزمون رگرسیون افزوده شد. Run میانی `31629800017` به‌علت guard پیام
commit skipped شد؛ guard حذف و run نهایی موفق اجرا شد. این دو رخداد فنی هیچ
نتیجه علمی تولید نکردند.

## وضعیت علمی

- checkpoint این مرحله: 4/4 workload و 16/16 pair؛
- تجمعی همراه Stage 13-H: 5/30 workload و 20/120 pair؛
- اجرای کامل ASSUMP-033: انجام نشده؛
- arithmetic mean سی‌تکراری: تولید نشده؛
- Figure 6: بازتولید نشده؛
- هیچ پارامتر علمی برای نزدیک‌کردن نتایج به مقاله تغییر نکرده است.
