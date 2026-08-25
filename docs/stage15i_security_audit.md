# Stage 15-I — ممیزی امنیتی پیش از dispatch aggregation-only

## دامنه فنی

- فقط ۱۰۰ pair موفق Run `32474360245`، بسته reuse معتبر ۲۰ pair و baselineهای
  Run `31644121025` دانلود می‌شوند.
- job محافظت‌شدهٔ `aggregate-only` در workflow ثبت‌شدهٔ Stage 15-H هیچ matrix،
  repair-pair، simulator، workload generator یا counterfactual runner ندارد.
- وقتی `resume_run_id=32474360245` باشد، jobهای `prepare`، `repair-pair` و
  `aggregate` عادی با شرط صریح skip می‌شوند و فقط `aggregate-only` فعال است.
- finalizer فقط completeness، checksum، paired aggregation، CSV و نمودار را از
  نتایج موجود می‌سازد.
- اصلاح workflow اصلی فقط مسیر baseline را با شرط «دقیقاً یک فایل» کشف می‌کند.
- برای رفع نبود lifecycle روی runner پاک، ۱۲۰ نتیجهٔ baseline موجود از Run
  `31644121025` به‌طور موقت دانلود می‌شوند؛ هیچ‌کدام اجرا یا در مخزن commit
  نمی‌شوند و در artifact نهایی نیز منتشر نمی‌شوند.
- بستهٔ ۲۰ pair نخست به archive SHA-256
  `e17e18cd10760a6f004424905e9dcfd617b950aa334d0498f11dfe722cfad179`
  pin شده است. پنج گروه بیست‌تایی دیگر ابتدا با digest رسمی GitHub و سپس تمام
  ۱۲۰ نتیجه با manifest علمی checksum-pinned کنترل می‌شوند.
- lifecycle مشتق‌شده فقط در صورت برابری دقیق با SHA-256 معتبر Stage 15-A یعنی
  `fac98f37a6faf23bdb91387498ed11008611adef29b383d24f1c866f8504610a`
  پذیرفته می‌شود؛ هر اختلاف fail-fast است.

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
- Run ناموفق `32829531291` هیچ artifact نهایی نساخت؛ علت دوم از log job به‌صورت
  `FileNotFoundError` برای lifecycle gitignored تأیید شد و خطای علمی نبود.
- PDF منبع، داده خام، workload، task trace، chromosome، archive حجیم، مسیر محلی،
  `.env`، token و metadata حساس در commit قرار نمی‌گیرند.
- تغییر قبلی `.gitignore` و پوشه‌های pytest محلی خارج از staging باقی می‌مانند.
- workflow مستقل Stage 15-I تا زمانی که روی شاخه پیش‌فرض ثبت نشود قابل dispatch
  نیست؛ بازیابی فعلی از حالت محافظت‌شدهٔ workflow ازقبل‌ثبت‌شده استفاده می‌کند و
  نیازی به merge یا تغییر `main` ندارد.

## کنترل پیش از انتشار اصلاح دوم

- ۱۵ آزمون هدفمند materializer، downloader، Stage 15-H و گزارش Stage 15-A موفق
  شدند.
- Ruff و mypy برای materializer جدید موفق شدند و `git diff --check` خطایی نداشت.
- بازسازی مستقل محلی از ۱۲۰ baseline موجود دقیقاً checksum معتبر
  `fac98f37…4610a` را تولید کرد.
- ممیزی هشت فایل قابل‌انتشار هیچ secret، credential، token، مسیر شخصی، PDF،
  archive، داده خام یا metadata حساس پیدا نکرد؛ ۱۹ ارجاع Action همگی SHA چهل‌رقمی
  کامل دارند.

## نتیجه پس از اجرا

- Run `32831698843` موفق شد و فقط job `aggregate-only` اجرا شد؛ سه مسیر محاسباتی
  دیگر skip شدند.
- artifact نهایی با digest رسمی GitHub
  `ab3b29120ee3b32ead53cc25a0d6f2bde1e21e753562ee1e09ff37146d8ae623`
  دریافت شد.
- داده‌های دانلودشده فقط در مسیر پشتیبان محلی پایدار نگهداری شدند و وارد staging
  یا مخزن عمومی نشدند.
- ابزار پایدارسازی فقط checksum، provenance، completeness و schema را می‌سنجد و
  simulator یا policy را فراخوانی نمی‌کند.
