# Stage 15-E — گزارش اعتبارسنجی محدود پنج-seed repairهای DK

## جایگاه علمی و دامنه

این مرحله فقط یک `[آزمون کمکی]` counterfactual است. دو variant مستقل
`initial_population_repair` و `offspring_repair` برای Pipeline DK-R و Pipeline DK-P روی پنج
workload نخست فهرست مادی‌سازی‌شده ASSUMP-033 بررسی شدند. هیچ‌یک از این variantها روش مقاله،
اصلاح رسمی DK یا بازتولید جدید Figure 6 نیست.

- چهار pair seed نخست از Stage 15-D.1 بدون محاسبه مجدد reuse شدند.
- baseline هر پنج seed از Stage 13-H/I/J/K و Stage 15-C بدون محاسبه مجدد reuse شد.
- برای چهار seed بعدی، 16 pair جدید در GitHub Actions اجرا شد.
- `fixed_penalty`، ترکیب repairها و اجرای 30 workload انجام نشد.
- policy، seed، GA، pricing، lifecycle، retention و preemption رسمی تغییر نکردند.

## اجرای GitHub

اجرای push اولیه با Run
[`31728542288`](https://github.com/arianparsee/edge-preemption-reproduction/actions/runs/31728542288)
پیش از شروع محاسبه شکست خورد، چون GitHub seedهای بزرگ‌تر از `2^53` را از matrix عددی به
scientific notation تبدیل کرد. این یک شکست صرفاً فنی بود و هیچ pair علمی تولید نشد. seedها با
حفظ دقیق مقدار به رشته YAML تبدیل شدند و retry فنی واحد مجاز انجام شد.

Run نهایی
[`31729227438`](https://github.com/arianparsee/edge-preemption-reproduction/actions/runs/31729227438)
موفق شد. هر 16 job جدید، validator عمومی، upload مستقل و job تجمیع موفق بودند. workflow از
`max-parallel=8`، `fail-fast=false`، `contents: read`، Actionهای pin‌شده به SHA و retention هفت‌روزه
استفاده کرد.

## کنترل تکرارپذیری و RNG

- هر pair جدید دو بار با workload seed و policy seed یکسان اجرا شد.
- outcome، Utility، hash پارتیشن task-ID، funnel، شمارنده‌های GA، call-shape و وضعیت نهایی RNG
  میان دو replay همان variant دقیقاً برابر بود: `all_replays_exact=true`.
- initial RNG state هر variant از policy seed مصوب کنترل شد.
- هیچ padding draw، reseed، workload خام، task ID، chromosome یا trace خام در artifact عمومی نبود.
- برای seed نخست، مقایسه baseline RNG از Stage 15-C در دسترس بود.
- برای چهار seed جدید، final RNG و call-shape baseline در Stage 13 ثبت نشده بود؛ بنابراین وضعیت
  صادقانه `unknown_not_recorded` باقی ماند و موفقیت مقایسه variant با baseline ادعا نشد. این همان
  مرز مصوب گزینه A و `A_partial_observability` است.

## نتایج paired پنج-seed

تمام اعداد جدول زیر `[آزمون کمکی]` هستند. CI با توزیع t، `df=4` و 95% محاسبه شده است.

| Policy | Variant | Δ Completed، mean ± SD | CI95 | Δ Completed Utility، mean ± SD | CI95 | جهت Utility |
|---|---|---:|---:|---:|---:|---:|
| DK-P | initialization repair | 83.8 ± 18.46 | [60.88, 106.72] | 6469.48 ± 1212.69 | [4963.72, 7975.24] | 5/5 مثبت |
| DK-P | offspring repair | 83.0 ± 18.61 | [59.89, 106.11] | 6353.40 ± 1258.03 | [4791.35, 7915.45] | 5/5 مثبت |
| DK-R | initialization repair | 116.8 ± 20.78 | [91.00, 142.60] | 9336.24 ± 1511.38 | [7459.61, 11212.87] | 5/5 مثبت |
| DK-R | offspring repair | 118.2 ± 19.58 | [93.89, 142.51] | 9397.59 ± 1438.37 | [7611.62, 11183.56] | 5/5 مثبت |

جهت اثر completed Utility برای هر دو repair و هر دو policy در هر پنج seed مثبت بود. این پایداری
جهت، شاهد چند-seed قوی‌تری از Stage 15-D.1 است، اما هنوز نتیجه 30-workload یا تغییر رسمی روش نیست.

## repair، admission، retry، expiration و completion

| Policy | Variant | repair / GA call، mean | Accepted، mean | Retry، mean | Expired، mean | Completed، mean | Δ raw rejection، mean |
|---|---|---:|---:|---:|---:|---:|---:|
| DK-P | initialization repair | 184.03 | 174.4 | 5328.6 | 1216.0 | 122.6 | -406.4 |
| DK-P | offspring repair | 1978.21 | 163.4 | 5354.8 | 1227.0 | 121.8 | -369.2 |
| DK-R | initialization repair | 198.53 | 134.6 | 5424.4 | 1255.8 | 134.6 | -325.4 |
| DK-R | offspring repair | 2158.34 | 136.0 | 5429.6 | 1254.4 | 136.0 | -321.6 |

`[استخراج مستقیم از آزمون کمکی]` هر دو repair در همه seedها admission/completion را نسبت به baseline
افزایش و raw rejection را کاهش دادند. repair در offspring تقریباً یک مرتبه بزرگی بیشتر از repair
initialization رخ داد، اما بهبود outcome آن اندکی بهتر یا اندکی ضعیف‌تر بود. بنابراین تعداد repair
به‌تنهایی اندازه بهبود را توضیح نمی‌دهد؛ محل مداخله و اثر downstream بر candidate pool و lifecycle
مهم‌اند.

در DK-R، Accepted و Completed برابرند؛ افت پس از پذیرش مشاهده نشد. در DK-P، بخشی از پذیرش‌ها به
preemption terminal مربوط می‌شوند و Completed از Accepted کمتر است. با وجود بهبود چشمگیر، میانگین
retry و expiration همچنان زیاد است؛ repair گلوگاه شدید Round 2 را کاهش داده، ولی lifecycle پرتراکم
را حذف نکرده است.

## پایدارسازی و checksum

artifactهای خام در مخزن عمومی commit نشده‌اند و در مسیر پایدار محلی زیر نگهداری می‌شوند:

`<LOCAL_BACKUP_ROOT>/edge-reproduction-stage15e-run-31729227438/`

اعتبارسنج مستقل بدون اجرای simulator موارد زیر را تأیید کرد:

- 16/16 pair جدید از مرز عمومی و علمی عبور کردند؛
- با چهار pair reuse، ماتریس 20/20 کامل و بدون تکرار است؛
- summary و دو CSV دانلودشده با merge محلی بدون محاسبه مجدد برابرند؛
- checksumهای inventory ابری صحیح‌اند؛
- 20 فایل دانلودشده، مجموعاً 20,196,727 byte، inventory شده‌اند.

SHA-256های اصلی:

| فایل | SHA-256 |
|---|---|
| manifest پایدار محلی | `9AA050B3F2C7A424BBD2E9DE311B7F8EEA41A8F8F56DBEA5509ED897CD436FC0` |
| summary پنج-seed | `EF6A5E7280B61500E7ACE98A44A7140810838753173B6FA05568D028AE25B64E` |
| CSV per-seed | `80CFD0164BAFCC9F5793711F6C6F7FF8027CFAFFF1C729012E7C68D438ABA697` |
| CSV aggregate | `D060C34F95D6F9A7F599BB7E7D4F28DD32B07058A06D94163C0C0C9EDA51DBAE` |

## محدودیت و تصمیم لازم

- baseline RNG کامل فقط برای seed نخست قابل مقایسه بود؛ برای چهار seed دیگر این metadata در اجرای
  تاریخی موجود نیست.
- پنج seed برای آزمون پایداری محدود مناسب‌اند، اما جایگزین 30 workload نیستند.
- repairها الگوریتم رسمی را تغییر می‌دهند و بدون تأیید جداگانه نباید وارد pipeline رسمی شوند.
- Figure 6 رسمی Stage 14-A بازنویسی نشده است.

مرحله بعدی پیشنهادی **Stage 15-F** است: تصمیم‌گیری درباره توقف تحلیل تشخیصی، یا طراحی یک validation
گسترده‌تر/تغییر رسمی الگوریتم. هر تعمیم به 30 workload، ترکیب repairها یا اصلاح pipeline رسمی نیازمند
تأیید صریح جداگانه است.
