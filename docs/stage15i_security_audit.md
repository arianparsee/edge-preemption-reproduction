# Stage 15-I — ممیزی امنیتی پیش از dispatch aggregation-only

## دامنه فنی

- فقط ۱۰۰ pair موفق Run `32474360245`، بسته reuse معتبر ۲۰ pair و baselineهای
  Run `31644121025` دانلود می‌شوند.
- workflow هیچ matrix، repair-pair job، simulator، workload generator یا
  counterfactual runner ندارد.
- finalizer فقط completeness، checksum، paired aggregation، CSV و نمودار را از
  نتایج موجود می‌سازد.
- اصلاح workflow اصلی فقط مسیر baseline را با شرط «دقیقاً یک فایل» کشف می‌کند.

## مرز علمی

- هیچ seed، workload، policy، GA setting، repair، lifecycle یا aggregation rule
  تغییر نمی‌کند.
- baseline و repair pair دوباره اجرا نمی‌شوند.
- Figure 6 رسمی و Pipeline DK تغییر نمی‌کنند.
- خروجی همچنان `[آزمون کمکی]` است.

## امنیت انتشار

- مجوز workflow فقط `contents: read` و `actions: read` است.
- هیچ secret یا credential جدیدی استفاده نمی‌شود؛ فقط token موقت داخلی GitHub
  برای خواندن artifactهای همان مخزن به کار می‌رود.
- Actionها به SHA کامل pin شده‌اند و retention برابر ۱۴ روز است.
- reuse bundle با SHA-256 آرشیو pin شده است.
- PDF منبع، داده خام، workload، task trace، chromosome، archive حجیم، مسیر محلی،
  `.env`، token و metadata حساس در commit قرار نمی‌گیرند.
- تغییر قبلی `.gitignore` و پوشه‌های pytest محلی خارج از staging باقی می‌مانند.
