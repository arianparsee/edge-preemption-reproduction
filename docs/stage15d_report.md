# Stage 15-D.1 — گزارش counterfactual تک‌عاملی Double Knapsack

## دامنه و جایگاه علمی

این مرحله یک `[آزمون کمکی]` تک-seed بر اساس ASSUMP-044 تا ASSUMP-047 و گیت RNG
گزینه A است. منبع baseline، artifact معتبر Stage 15-C از Run `31708325126` است و
baseline در این مرحله دوباره محاسبه نشد. هیچ‌یک از سه variant روش مقاله، اصلاح رسمی
DK یا نتیجه Figure 6 نیست.

- workload seed: `541501192080118187`، نخستین seed مصوب ASSUMP-033؛
- policyها: Pipeline DK-R و Pipeline DK-P؛
- variantها: `fixed_penalty`، `initial_population_repair` و `offspring_repair`؛
- هر pair دو بار با workload seed و policy seed یکسان اجرا شد؛
- اجرای 30-workload انجام نشد و artifactهای رسمی Figure 6 تغییر نکردند.

## اجراهای GitHub

Run اصلی [`31716969817`](https://github.com/arianparsee/edge-preemption-reproduction/actions/runs/31716969817)
چهار pair repair را با موفقیت حفظ کرد. دو pair `fixed_penalty` به‌علت اتصال نادرست
sentinel جدید `-1` به guard نهایی مصوب ASSUMP-042، پیش از تولید نتیجه fail-fast شدند.
اصلاح فقط guard هم‌ارزی fitness را با sentinel همان variant همسو کرد؛ هیچ draw، seed،
operator، lifecycle یا نتیجه موفق قبلی تغییر نکرد.

Run بازیابی محدود [`31720347641`](https://github.com/arianparsee/edge-preemption-reproduction/actions/runs/31720347641)
فقط دو pair شکست‌خورده `fixed_penalty` را اجرا کرد. چهار pair موفق دوباره محاسبه نشدند.

## نتیجه عددی تک-seed

| Policy | Variant | Completed | Δ Completed | Completed Utility | Δ Utility | Raw rejection | Δ Raw rejection | Preempted |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| DK-R | baseline Stage 15-C | 24 | — | 1451.859640 | — | 6759 | — | 0 |
| DK-R | fixed penalty | 24 | 0 | 1451.859640 | 0 | 6761 | +2 | 0 |
| DK-R | initialization repair | 127 | +103 | 10145.404049 | +8693.544409 | 6529 | -230 | 0 |
| DK-R | offspring repair | 128 | +104 | 10282.670285 | +8830.810645 | 6549 | -210 | 0 |
| DK-P | baseline Stage 15-C | 40 | — | 3193.919347 | — | 6727 | — | 6 |
| DK-P | fixed penalty | 40 | 0 | 3193.919347 | 0 | 6727 | 0 | 6 |
| DK-P | initialization repair | 117 | +77 | 9541.426965 | +6347.507618 | 6493 | -234 | 29 |
| DK-P | offspring repair | 114 | +74 | 9295.550461 | +6101.631114 | 6466 | -261 | 28 |

در این workload، penalty ثابت outcome نهایی را بهتر نکرد. repair محدود به initialization
یا offspring، completed Utility را در DK-R به‌ترتیب حدود 6.99 و 7.08 برابر baseline و
در DK-P حدود 2.99 و 2.91 برابر baseline کرد. این نسبت‌ها فقط مشاهده تک-seed هستند و
قابل تعمیم به 30 workload نیستند.

## تشخیص repair و RNG

| Policy | Variant | repaired chromosomes | removed bits | final RNG برابر baseline | call shape برابر baseline | RNG gate |
|---|---|---:|---:|---|---|---|
| DK-R | fixed penalty | 0 | 0 | خیر | خیر | موفق؛ اختلاف با تغییر ثبت‌شده call shape توضیح داده شد |
| DK-R | initialization repair | 197874 | 5947088 | خیر | خیر | موفق؛ اختلاف توضیح‌پذیر |
| DK-R | offspring repair | 2151019 | 9048163 | خیر | خیر | موفق؛ اختلاف توضیح‌پذیر |
| DK-P | fixed penalty | 0 | 0 | بله | بله | موفق؛ برابری دقیق |
| DK-P | initialization repair | 197348 | 5922912 | خیر | خیر | موفق؛ اختلاف توضیح‌پذیر |
| DK-P | offspring repair | 2151364 | 8853670 | خیر | خیر | موفق؛ اختلاف توضیح‌پذیر |

برای ورودی، candidate order و call shape یکسان، آزمون selector برابری دقیق شمار primitiveها
و وضعیت نهایی RNG با baseline را تأیید کرد. در اجرای کامل، هر اختلاف RNG فقط با تغییرهای
ثبت‌شده در GA calls، مسیرهای empty/single/multi، candidate entries یا uniform-choice calls
پذیرفته شد. هیچ padding draw، reseed یا ثابت‌سازی candidate pool وجود ندارد.

هر دو اجرای مستقل هر variant در outcome، Utility، hash پارتیشن task-ID، funnel، شمارنده‌های
GA، trace تجمیعی primitiveها و وضعیت نهایی RNG byte-for-byte برابر بودند. artifact عمومی
شامل task ID، chromosome، workload خام یا trace خام نیست.

## تفسیر کنترل‌شده

`[استخراج مستقیم از آزمون کمکی]` اثر بزرگ دو repair و بی‌اثری outcome-level penalty ثابت
در این seed نشان می‌دهد bottleneck مشاهده‌شده صرفاً مقدار penalty fitness نیست؛ حضور فراوان
chromosomeهای infeasible در initialization/offspring و نحوه ورود آن‌ها به انتخاب نهایی عامل
قوی‌تری است. بااین‌حال، چون repair خود مسیر پذیرش‌های بعدی و در نتیجه call shape را تغییر
می‌دهد، این آزمایش سهم علّی initialization را از offspring به‌طور کامل جدا نمی‌کند و شاهد
تک-seed برای تغییر پیاده‌سازی رسمی کافی نیست.

## پایداری و checksum

شش ZIP و شش JSON استخراج‌شده در مسیر محلی gitignored زیر نگهداری می‌شوند:

`backups/stage15d-run-31716969817/`

این مسیر در مخزن عمومی commit نشده است. inventory کامل اندازه و SHA-256 در
`manifest.json` همان مسیر ثبت شده؛ SHA-256 فایل manifest پس از اعتبارسنجی نهایی در گزارش
اجرایی پایان مرحله ثبت می‌شود. CSV و JSON تجمیعی پاک‌سازی‌شده از همین شش artifact و بدون
اجرای مجدد علمی تولید می‌شوند.

## محدودیت و تصمیم بعدی

- نتیجه فقط برای یک workload است؛
- baseline شمار primitiveهای RNG را در Stage 15-C ذخیره نکرده بود، بنابراین مقایسه
  primitive-count با baseline فقط در آزمون selector هم‌شکل ممکن بود؛ مقایسه اجرای کامل
  بر hash وضعیت RNG و call-shape ثبت‌شده تکیه دارد؛
- هیچ variant برای pipeline رسمی DK پذیرفته نشده است؛
- تعمیم چند-seed یا اصلاح روش رسمی نیازمند تأیید جداگانه است.
