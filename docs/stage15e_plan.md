# Stage 15-E — اعتبارسنجی محدود پنج-seed برای repairهای DK

## وضعیت و دامنه

این مرحله فقط یک `[آزمون کمکی]` است. دو variant مؤثر Stage 15-D.1 یعنی
`initial_population_repair` و `offspring_repair` برای DK-R و DK-P بررسی می‌شوند.
`fixed_penalty`، اجرای 30-workload، ترکیب repairها، تغییر pipeline رسمی و بازتولید Figure 6
خارج از دامنه‌اند.

پنج workload نخست فهرست مرتب و مادی‌سازی‌شده ASSUMP-033 عبارت‌اند از:

1. `541501192080118187`
2. `2074092324964443463`
3. `2218754797665862270`
4. `2997476077322633071`
5. `3782887846963969634`

چهار pair variant/policy مربوط به seed نخست از Stage 15-D.1 reuse می‌شوند. برای چهار
seed بعدی، 2 variant × 2 policy و در نتیجه 16 pair جدید اجرا خواهد شد.

## مرز مصوب گزینه A برای RNG

baseline علمی هر پنج seed از Stage 13-H/I/J/K و Stage 15-C reuse می‌شود و هیچ baseline
دوباره اجرا نمی‌شود. Stage 13-I وضعیت نهایی RNG و call-shape baseline چهار seed جدید را
ذخیره نکرده است؛ بنابراین این دو مقایسه با وضعیت
`unknown_not_recorded_in_stage13_baseline` نگهداری می‌شوند و موفقیت آن‌ها ادعا نمی‌شود.

برای هر pair جدید موارد زیر fail-closed کنترل می‌شوند:

- initial RNG state از policy seed مصوب؛
- دو اجرای مستقل و دقیقاً برابر همان variant؛
- outcome، Utility و hash پارتیشن task-ID؛
- funnel، primitive counts، selector call-shape و final RNG همان variant؛
- workload hash، workload seed و policy seed برابر baseline reuseشده؛
- نبود padding draw، reseed و تغییر lifecycle.

## اجرای ابری

- matrix: 16 pair جدید؛
- `max-parallel=8` و `fail-fast=false`؛
- timeout مستقل هر pair: 150 دقیقه؛
- artifact مستقل، پاک‌سازی‌شده و retention هفت روز؛
- retry فقط برای `OSError`های فنی موقت و حداکثر یک بار؛
- `ValueError`، invariant، config mismatch و شکست علمی هرگز retry نمی‌شوند؛
- workflow فقط `contents: read` دارد و همه Actionها به SHA کامل pin شده‌اند.

## تجمیع

پس از تکمیل 16 pair، چهار pair seed نخست reuse می‌شوند تا ماتریس 20 pair تشکیل شود.
paired delta هر variant نسبت به baseline همان seed محاسبه می‌شود. mean، sample standard
deviation و CI 95% با توزیع t و `df=4` فقط با برچسب `[آزمون کمکی]` گزارش می‌شوند.

## منشأ fixtureها

- `tests/fixtures/stage15e_reused_baselines.json`: ده fingerprint علمی و lifecycle
  پاک‌سازی‌شده از artifactهای معتبر؛ baseline اجرا نشده است.
- `tests/fixtures/stage15e_seed_one_reuse.json`: چهار pair معتبر Stage 15-D.1؛ variant
  seed نخست اجرا نشده است.

هیچ fixture شامل task ID، chromosome، workload خام، trace خام یا مسیر شخصی نیست.
