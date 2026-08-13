# Stage 14-A - ثبت رسمی بازتولید Figure 6

## منبع و دامنه

- [صریح در مقاله] مبنا: arXiv:2403.15665v2 (2024)، شکل 6، آزمایش PIPE-NORMAL.
- [فرض بازتولید] مقادیر بازتولیدشده میانگین حسابی 30 workload مشترک مطابق ASSUMP-033 تا ASSUMP-043 هستند.
- هیچ داده خام، policy، شبیه‌ساز یا workload در این مرحله اجرا یا بازتولید نشده است.

## نتیجه

ترتیب گزارش‌شده مقاله `DK-P > KG-P > DK-R > KG-R` است. ترتیب بازتولیدشده
`KG-P > KG-R > DK-P > DK-R` و فاصله بهترین تا ضعیف‌ترین روش `88.412090%`
است. چون ترتیب کیفی منطبق نیست و فاصله با ادعای تقریبی حداکثر 5 درصد سازگار نیست،
وضعیت رسمی Figure 6 **بازتولید نشد** است.

مقاله جدول عددی پشت شکل، seedها، repeat count و روش aggregation را منتشر نکرده است؛
بنابراین اختلاف عددی نقطه‌به‌نقطه قابل محاسبه نیست و هیچ ارتفاعی از تصویر مقاله با
نتایج محاسباتی مخلوط نشده است.

## Artifactهای رسمی

- `results/aggregated/stage14a/figure6_reproduced_data.csv`: جدول داده شکل.
- `results/aggregated/stage14a/raw_run_metrics.csv`: 120 سطر مشتق‌شده از pairهای معتبر.
- `results/aggregated/stage14a/figure6_comparison.csv`: جدول مقایسه با مقاله.
- `figures/stage14a/figure6_reproduced.png` و `.pdf`: نمودارهای نهایی.
- `results/aggregated/stage14a/stage14a_manifest.json`: منشأ و SHA-256 artifactها.
