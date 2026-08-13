# Stage 15-C - funnel غیرمداخله‌ای تصمیم DK

## دامنه

- [آزمون کمکی] این مرحله نتیجه اصلی مقاله یا تغییر الگوریتم نیست.
- workload نخست فهرست مصوب ASSUMP-033 با seed `541501192080118187` استفاده می‌شود.
- baseline معتبر Run `31624982369` فقط به‌صورت fingerprint استفاده و بازاجرا نمی‌شود.
- فقط DK-R و DK-P instrument می‌شوند.

## قرارداد عدم مداخله

instrumentation پس از دریافت `best_individual()` فقط تعداد بیت‌های یک chromosome برتر،
feasibility و وقوع repair را ثبت می‌کند. خود بیت‌ها و task IDها ثبت نمی‌شوند. hook مشاهده‌ای
هیچ random draw انجام نمی‌دهد و fitness، selection، crossover، mutation، ترتیب candidateها،
seed یا تصمیم نهایی را تغییر نمی‌دهد.

wrapper policy نتیجه رسمی auction را عیناً بازمی‌گرداند و فقط شمارنده‌های aggregate زیر را
از خروجی موجود محاسبه می‌کند:

1. ورودی‌های Round 1؛
2. raw-best و post-repair selector؛
3. انتخاب task روی حداقل یک سرور و server assignment؛
4. pool و knapsack مرحله دوم؛
5. accepted، rejected، retained و preempted؛
6. retry، expiration و completion از event log موجود.

workflow در صورت اختلاف workload hash، outcome، Utility، task-ID hashes، scientific-state
hash یا شمارنده‌های متقاطع funnel فوراً fail می‌شود.

## مرز استنباط

این شمارنده‌ها محل افت را دقیق‌تر می‌کنند، اما counterfactual نیستند و علیت encoding،
fitness یا repair را اثبات نمی‌کنند. هر تغییر الگوریتمی همچنان نیازمند تأیید مستقل است.
