# گزارش Stage 13-K - تثبیت و اعتبارسنجی اجرای کامل PIPE-NORMAL

## 1. کارهای انجام‌شده

- Run 31644121025 با نتیجه success و بدون اجرای مجدد هیچ policy بررسی شد.
- 108 artifact در مسیر پایدار دانلود شد: 100 pair جدید، 5 validation، prior-20، final و finalizer-status.
- 120/120 pair از روی result/workload/manifest موجود و config دقیق commit اعتبارسنجی شد.
- arithmetic mean سی تکرار مطابق ASSUMP-033 مستقلاً محاسبه و با CSV ابری تطبیق داده شد.
- PDF شکل 6 در 200dpi render و از نظر خوانایی بررسی شد.

## 2. فایل‌های ایجاد یا تغییرکرده

- `inventory_sha256.csv`: نام، اندازه و SHA-256 همه فایل‌های پایدار به‌جز خود inventory.
- `stage13k_verification_report.json`: نتیجه ماشین‌خوان اعتبارسنجی.
- `STAGE13K_REPORT.md`: همین گزارش.
- `assembled_verified_source/`: نمای مونتاژشده 120 pair؛ هیچ داده مبدأ حذف یا بازنویسی نشده است.

## 3. ارتباط هر تغییر با مقاله

- [صریح در مقاله] arXiv v2، شکل 6: مقایسه Utility چهار روش در PIPE-NORMAL.
- [صریح در مقاله] ترتیب ادعاشده Utility تکمیل‌شده: DK-P > KG-P > DK-R > KG-R و اختلاف کلی تقریبا حداکثر 5 درصد.
- [فرض بازتولید] میانگین حسابی 30 workload و seedهای مادی‌سازی‌شده مطابق ASSUMP-033.

## 4. فرمان‌های اجراشده

- `gh run view 31644121025 ...`
- `gh run download 31644121025 ...`
- `python scripts/finalize_stage13j_full_run.py ...` فقط برای validation/aggregation از نتایج موجود.
- `python scripts/stabilize_stage13k_artifacts.py ...` برای inventory و گزارش؛ بدون simulator/policy/workload generation.

## 5. نتایج واقعی اجرا

| Policy | Completed Utility | Rejected Utility | Preempted Utility | Completed Jobs | Rejected Jobs | Preempted Jobs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| KG-R | 9610.652350672544 | 74449.544085019443 | 0.000000000000 | 127.566667 | 1271.733333 | 0.000000 |
| KG-P | 11473.243321756001 | 72586.953113935990 | 1202.908186306399 | 138.433333 | 1260.866667 | 21.566667 |
| DK-R | 1329.509055135900 | 82730.687380556075 | 0.000000000000 | 19.733333 | 1379.566667 | 0.000000 |
| DK-P | 3607.442492263064 | 80452.753943428921 | 787.677255475846 | 43.266667 | 1356.033333 | 11.366667 |

ترتیب بازتولیدشده Completed Utility: `KG-P > KG-R > DK-P > DK-R`.
فاصله نسبی بهترین تا ضعیف‌ترین روش: `88.412090%`.

## 6. آزمون‌های موفق و ناموفق

- موفق: 120/120 result hash، workload hash، config hash، identity و policy seed.
- موفق: 30/30 workload مشترک میان چهار policy.
- موفق: partitionهای Completed/Rejected و زیرمجموعه‌بودن Preempted.
- موفق: برابری معنایی aggregate مستقل و cloud؛ CSVهای raw و Figure 6 byte-identical.
- ناموفق علمی: ترتیب و فاصله Completed Utility با ادعای شکل 6 مقاله سازگار نیست.

## 7. فرض‌های استفاده‌شده

- ASSUMP-033 تا ASSUMP-043 همان config مصوب؛ هیچ فرض، seed یا پارامتر جدیدی اعمال نشد.
- اختلاف line ending و metadata محیطی PDF به‌عنوان اختلاف علمی تلقی نشد.

## 8. ابهامات یا اطلاعات مفقود

- مقاله جدول عددی پشت شکل 6، seedها، repeat count و روش aggregation را منتشر نکرده است.
- بنابراین مقایسه دقیق نقطه‌به‌نقطه با اعداد اصلی ممکن نیست؛ مقایسه با ادعاهای صریح و روند شکل انجام شد.
- علت ضعف شدید DK نسبت به KG باید در Stage بعد با آزمایش‌های کنترل‌شده بررسی شود؛ هنوز به خطای پیاده‌سازی یا مقاله نسبت داده نمی‌شود.

## 9. تصمیم موردنیاز از من

- برای Stage 13-K تصمیم مسدودکننده‌ای باقی نمانده است.

## 10. مرحله بعدی پیشنهادی

- مرحله 15-A: تحلیل کنترل‌شده اختلاف Figure 6، با اولویت رفتار DK، نرخ repair، admission canonicalization و lifecycle retry/preemption؛ هر بار فقط یک عامل تغییر کند.
