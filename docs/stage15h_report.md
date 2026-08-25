# Stage 15-H — گزارش اعتبارسنجی ۳۰-workload repairهای تشخیصی DK

## دامنه

این مرحله فقط `[آزمون کمکی]` است. initialization repair و offspring repair روش
مقاله، اصلاح رسمی Pipeline DK یا بازتولید جدید Figure 6 نیستند. baselineهای رسمی
Stage 13-J/13-K reuse شدند و هیچ baseline دوباره اجرا نشد.

## وضعیت اجرا و بازیابی

- source run: `32474360245`؛ ۱۰۲ job شامل ۱۰۱ موفق و یک job تجمیع ناموفق؛
- ۱۰۰/۱۰۰ pair جدید موفق؛ ۲۰/۲۰ repair pair قبلی reuse؛
- ۱۲۰/۱۲۰ repair pair و ۱۲۰/۱۲۰ baseline pair معتبر؛
- ۱۲۰/۱۲۰ same-variant replay دقیق و ۱۲۰/۱۲۰ RNG gate درون variant موفق؛
- baseline-versus-variant RNG comparison: `[نامشخص]`، زیرا Stage 13 آن state را
  ثبت نکرده است؛
- شکست aggregate فقط ناشی از مسیر stale فایل `raw_run_metrics.csv` بود؛
- تجمیع پایدار محلی با همان finalizer و مسیر صحیح، بدون اجرای محاسبات علمی،
  `complete_and_valid` شد.

## Completed Utility روی ۳۰ workload

| Policy | Baseline mean | Initialization mean | Paired effect | Offspring mean | Paired effect | جهت هر repair |
|---|---:|---:|---:|---:|---:|---:|
| DK-R | 1329.51 | 10369.97 | +9040.46 | 10472.30 | +9142.79 | 30+/0/0- |
| DK-P | 3607.44 | 9380.26 | +5772.82 | 9447.00 | +5839.55 | 30+/0/0- |

- DK-R offspring در میانگین `102.33` واحد از initialization بهتر بود و در
  ۱۸/۳۰ seed بر آن غلبه کرد.
- DK-P offspring در میانگین `66.74` واحد بهتر بود و در ۱۸/۳۰ seed بر آن غلبه
  کرد؛ CI اختلاف شامل صفر است.
- هر دو repair نسبت به baseline در تمام ۳۰ workload اثر مثبت داشتند.
- repairهای DK-R از KG-R عبور کردند ولی از KG-P عبور نکردند؛ repairهای DK-P
  اندکی پایین‌تر از KG-R ماندند.

## مرز استنباط

نتیجه، نقش feasibility ضعیف chromosomeهای بازسازی فعلی را به‌عنوان مظنون اصلی
تقویت می‌کند؛ اما به‌دلیل نبود کد نویسندگان، encoding و repair رسمی، علت نهایی
`[نامشخص]` است. Pipeline رسمی و artifactهای Stage 14-A تغییر نکردند و وضعیت رسمی
Figure 6 همچنان **«بازتولید نشد»** است.
