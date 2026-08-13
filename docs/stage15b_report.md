# Stage 15-B - گزارش instrumentation غیرمداخله‌ای GA

## 1. کارهای انجام‌شده

- [آزمون کمکی] wrapper مشاهده‌ای برای selector رسمی `pyeasyga 0.3.1` پیاده‌سازی شد.
- wrapper ورودی و خروجی selector را تغییر نمی‌دهد، random draw انجام نمی‌دهد و فقط وضعیت
  RNG داخلی را با `getstate()` و SHA-256 مشاهده می‌کند.
- baseline معتبر Run `31624982369` به fingerprint غیرقابل‌بازگردانی تبدیل و بدون اجرای
  مجدد policy استفاده شد.
- workload نخست فهرست مادی‌سازی‌شده ASSUMP-033 با seed
  `541501192080118187` برای DK-R و DK-P در GitHub Actions اجرا شد.
- Run `31700739166` روی commit
  `9b12a5a4de8a171a889f94e8bbc2c5a166fb05f7` با نتیجه `success` کامل شد.
- سه artifact پاک‌سازی‌شده با retention هفت‌روزه دریافت، در backup محلی پایدار نگهداری و
  SHA-256 آن‌ها با digest اعلام‌شده GitHub تطبیق داده شد.

## 2. عدم مداخله و برابری baseline

برای هر دو policy همه کنترل‌های زیر موفق بودند:

- workload seed و workload SHA-256 یکسان؛
- policy seed یکسان؛
- outcome و Utilityها یکسان؛
- hash مجموعه task IDهای completed، rejected و preempted یکسان؛
- hash وضعیت علمی کامل شامل eventها، final state، progress، retry و rejection reason یکسان؛
- تنظیم GA بدون تغییر؛
- مشاهده RNG بدون random draw جدید؛
- baseline دوباره محاسبه نشد.

نتیجه علمی تک-seed دقیقاً همان نتیجه معتبر قبلی باقی ماند:

| Policy | Completed | Rejected | Preempted | Completed Utility | Rejected Utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| DK-R | 24 | 1371 | 0 | 1451.859640016816 | 82549.57610283085 |
| DK-P | 40 | 1355 | 6 | 3193.9193472199277 | 80807.51639562774 |

## 3. یافته‌های Round 1 و Round 2

`candidate_entries` و `selected_entries` تعداد ورودها در همه فراخوانی‌های selector هستند،
نه تعداد task ID یکتا. بنابراین نسبت‌ها فشار انتخاب را نشان می‌دهند و نباید به‌عنوان نرخ
پذیرش یکتای وظیفه تفسیر شوند.

| Policy/Round | Calls | GA calls | Empty calls | Candidate entries | Selected entries | Selection fraction | Repairs / GA calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DK-R / R1 | 872 | 856 | 0 | 54264 | 16 | 0.0295% | 838/856 = 97.90% |
| DK-R / R2 | 872 | 111 | 721 | 6783 | 24 | 0.3538% | 106/111 = 95.50% |
| DK-P / R1 | 872 | 864 | 0 | 54184 | 22 | 0.0406% | 843/864 = 97.57% |
| DK-P / R2 | 872 | 128 | 600 | 7005 | 168 | 2.3983% | 104/128 = 81.25% |

### گلوگاه Round 1

- در 109 مزایده و هشت سرور، Round 1 برای هر policy دقیقاً 872 بار selector را فراخواند.
- GA در 98.17% فراخوانی‌های DK-R و 99.08% فراخوانی‌های DK-P واقعاً اجرا شد.
- repair در 97.90% و 97.57% فراخوانی‌های واقعی GA رخ داد.
- فقط 0.0295% و 0.0406% candidate-entryها در خروجی selector باقی ماندند.

[استخراج مستقیم] این اعداد نشان می‌دهند نخستین گلوگاه قابل‌اندازه‌گیری، فشار بسیار شدید
feasibility/repair و فروپاشی مجموعه انتخاب‌شده در Round 1 است. این مشاهده هم‌بستگی و محل
حذف را مشخص می‌کند، اما به‌تنهایی ثابت نمی‌کند کدام جزء encoding، fitness یا repair علت
ریشه‌ای است.

### گلوگاه Round 2

- 82.68% فراخوانی‌های سرور در DK-R و 68.81% در DK-P مجموعه candidate خالی داشتند.
- در فراخوانی‌های واقعی GA، repair برای DK-R همچنان 95.50% و برای DK-P برابر 81.25% بود.
- فشار انتخاب در Round 2 از Round 1 کمتر است، ولی هنوز شدید است.
- در DK-R تعداد 24 selected-entry در Round 2 با 24 completion این seed هم‌اندازه است.
- در DK-P تعداد 168 selected-entry به 46 پذیرش یکتا، 40 completion و 6 preemption منتهی
  شد. چون candidateها می‌توانند میان epochها تکرار شوند، این فاصله نباید بدون instrumentation
  مسیر تصمیم به یک علت خاص نسبت داده شود.

[استخراج مستقیم] Stage 15-A گلوگاه کلان را در admission/Round 2 نشان داده بود؛ Stage 15-B
اکنون نشان می‌دهد فشار GA از Round 1 آغاز می‌شود و در Round 2 نیز repair و تبدیل خروجی
selector به پذیرش نهایی محدودکننده باقی می‌ماند. completion پس از پذیرش برای DK-R همچنان
کامل است، پس ضعف DK-R ناشی از pipeline completion پس از activation نیست.

## 4. artifact و پایدارسازی

| Artifact | اندازه | SHA-256 | تطبیق digest GitHub |
| --- | ---: | --- | --- |
| merged diagnostic | 1182 B | `3f9d1f42c1b02e6a0862a7b6f4ca54f4a1ae0fbd670b4c5a653a06cd7abac049` | موفق |
| DK-P diagnostic | 1376 B | `6e4c04e674abbad589b9c534232f68c01a0cadf7300c449f91fdb3b8c404502e` | موفق |
| DK-R diagnostic | 1361 B | `a17690baeef0475606a70c3b62d31c681b178b5338ec5b4ea178a42d6e24d0a4` | موفق |

manifest پایدار محلی SHA-256 برابر
`564a41d189eaf86f5321e8bf81b6f31ac26d16a17458445abfa7aa12d096af33`
دارد. artifactها، JSONهای استخراج‌شده و manifest در مخزن عمومی commit نشده‌اند.

## 5. اجرای واقعی و آزمون‌ها

- Ruff: موفق.
- mypy: موفق.
- آزمون‌های محلی مرتبط پیش از push: `39 passed in 2.32s`؛ آخرین بازاجرا پس از گزارش:
  `39 passed in 2.40s`.
- آزمون قرارداد RNG در هر دو job ابری: موفق.
- اجرای رسمی instrumented DK-R: 19 دقیقه و 5 ثانیه برای گام policy.
- اجرای رسمی instrumented DK-P: 19 دقیقه و 17 ثانیه برای گام policy.
- کل workflow از `12:35:10Z` تا `12:55:16Z`: حدود 20 دقیقه و 6 ثانیه.
- validator محتوای artifact و job تجمیع: موفق.

یک فرمان محلی inventory پس از استخراج به‌علت نبود متد `Path.GetRelativePath` در runtime
PowerShell خطا داد. استخراج کامل بود؛ inventory با روش سازگار مبتنی بر substring دوباره
اجرا و موفق شد. هیچ artifact حذف یا بازنویسی نشد.

نخستین فرمان بازاجرای نهایی pytest نیز به‌دلیل سه نام مسیر قدیمی پیش از collection متوقف
شد و `no tests ran` گزارش کرد. مسیرها با `rg --files` از مخزن استخراج شدند و فرمان اصلاح‌شده
همه 39 آزمون مرتبط را با موفقیت اجرا کرد؛ شکست آزمون علمی وجود نداشت.

## 6. ممیزی امنیتی و فایل‌های انتشار

- ممیزی پیش از push روی 20 فایل قابل‌انتشار موفق بود.
- هیچ secret، credential، token، `.env`، مسیر شخصی، PDF، raw data، artifact، فایل binary
  یا فایل بزرگ‌تر از 500000 بایت منتشر نشد.
- workflow فقط `contents: read` دارد، هیچ secret مصرف نمی‌کند و Actionها به SHA کامل pin هستند.
- دو commit منتشرشده: `2f68028` و `9b12a5a`.
- داده‌های تشخیصی تفصیلی task و raw workload در artifact و log عمومی وجود ندارند.

## 7. فرض‌ها و محدودیت‌ها

- هیچ فرض بازتولید جدیدی اضافه نشد.
- هیچ seed، الگوریتم، ترتیب پردازش، پارامتر GA یا RNG stream تغییر نکرد.
- این تحلیل فقط یک workload مصوب است و `[آزمون کمکی]` محسوب می‌شود؛ میانگین 30 تکرار
  Figure 6 را جایگزین نمی‌کند.
- شمارنده‌های selector ورودی‌های تکرارشونده میان سرورها و epochها را شامل می‌شوند؛ تحلیل
  علت ریشه‌ای encoding/fitness/repair به instrumentation غیرمداخله‌ای دقیق‌تری نیاز دارد.

## 8. مرحله بعدی پیشنهادی

**Stage 15-C**: instrumentation غیرمداخله‌ای funnel تصمیم DK از chromosome خام تا repair،
خروجی selector، انتخاب سرور، commit پذیرش، retry و expiration؛ بدون تغییر رفتار و ابتدا روی
همین workload مصوب. هر counterfactual یا تغییر الگوریتمی نیازمند تأیید جداگانه است.
