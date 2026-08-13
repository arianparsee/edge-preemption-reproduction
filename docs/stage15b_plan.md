# Stage 15-B - ممیزی غیرمداخله‌ای GA

## وضعیت علمی

- [آزمون کمکی] این مرحله بخشی از نتیجه اصلی مقاله نیست.
- workload نخست فهرست مادی‌سازی‌شده ASSUMP-033 با seed برابر `541501192080118187` است.
- baseline از Run معتبر `31624982369` با fingerprint غیرقابل‌بازگردانی استفاده می‌شود و دوباره اجرا نمی‌شود.
- فقط DK-R و DK-P instrument می‌شوند؛ هیچ فرض، seed، تنظیم GA یا الگوریتمی تغییر نمی‌کند.

## قرارداد عدم مداخله

wrapper ورودی را بدون مرتب‌سازی یا تغییر به selector رسمی می‌دهد و خروجی آن را عیناً
بازمی‌گرداند. مشاهده RNG فقط با `getstate()` و SHA-256 انجام می‌شود. هیچ random draw،
selection، crossover، mutation یا tie choice جدیدی انجام نمی‌شود.

workflow در صورت اختلاف outcome، Utility، hash شناسه‌های outcome، وضعیت علمی کامل run
یا workload hash فوراً fail می‌شود. artifact فقط شمارنده‌های تجمیعی Round 1 و Round 2
را نگه می‌دارد و شامل task ID، trace، مسیر محلی یا داده workload نیست.
