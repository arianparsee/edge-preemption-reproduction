# Stage 15-G — ممیزی انتشار

## دامنه

این ممیزی فقط مجموعه فایل‌های صریح Stage 15-G را پوشش می‌دهد. تغییر کاربر در
`.gitignore` و دو پوشه pytest قدیمی خارج از دامنه‌اند و stage/commit نمی‌شوند.

فایل PDF خام مقاله، cropهای منبع و renderهای QA در `tmp/` باقی مانده‌اند و در مجموعه
انتشار حضور ندارند. خروجی PDF شکل بازسازی‌شده با PDF مقاله متفاوت است و فقط یک صفحه
برداری تولیدشده توسط اسکریپت پروژه است.

## کنترل‌ها

- الگوهای token، credential، private key، secret expression و مسیر شخصی: یافت نشد.
- `.env`، archive، database، raw data، trace، PDF مقاله و فایل بزرگ‌تر از 500 KB:
  در مجموعه انتشار وجود ندارد.
- PDF تولیدی: header/trailer معتبر، بدون attachment، JavaScript یا OpenAction.
- PNG تولیدی: signature معتبر و اندازه 105755 bytes.
- فایل‌های متنی: UTF-8 و پاک‌سازی‌شده.
- manifest machine-readable: `results/aggregated/stage15g/publication_audit.json`.

## نتیجه

وضعیت ممیزی: **passed**. فقط کد، آزمون، مستندات، inventory/manifest مشتق‌شده و سه
خروجی مجاز Figure 1 برای commit انتخاب می‌شوند. داده خام یا artifact حجیم منتشر نمی‌شود.
