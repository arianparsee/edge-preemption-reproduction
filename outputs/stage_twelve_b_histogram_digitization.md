# مرحله دوازدهم-B — استخراج قابل‌ردیابی histogramهای Southampton

تاریخ اجرا: 2026-08-11  
منبع مبنا: arXiv:2403.15665v2 (2024)  
وضعیت: **digitization تقریبی کامل؛ تولید surrogate تا تصویب ASSUMP-028..032 متوقف**

## 1. دامنه و مرز علمی

- `[صریح از کاربر]` مسیر preprocessing داده واقعی Southampton به‌دلیل نبود raw
  trace و schema در وضعیت blocked باقی می‌ماند.
- `[صریح از کاربر]` ساخت surrogate از histogramها فقط برای آزمون فنی و
  بازتولید کیفی مجاز است و نباید داده واقعی یا بازتولید عددی مقاله نامیده شود.
- `[صریح از کاربر]` تصاویر منتشرشده، داده digitized، داده تولیدشده و نتایج
  آزمایش‌ها باید جدا بمانند و parameter tuning برای نزدیک‌کردن مصنوعی خروجی به
  شکل مقاله ممنوع است.
- این زیربخش فقط تصویرهای منبع را checksum می‌کند و نواحی رنگی قابل‌مشاهده را
  digitize می‌کند. هیچ رکورد surrogate، arrival، Utility یا ورودی الگوریتمی
  تولید نشده است.

## 2. تصاویر منبع و هویت آن‌ها

سه PNG مستقیماً از بسته source رسمی arXiv v2 استخراج و بدون تغییر در
`data/raw/published_figures/arxiv_v2` نگهداری شدند. این پوشه «تصویر منتشرشده»
است، نه raw trace.

| فایل | اندازه | SHA-256 |
| --- | ---: | --- |
| `trace_storage_distribution.png` | 640×480 | `52de43f031e04d9214a2f2117ced71c04a9ba0aa0148334e725fb299f076c6e6` |
| `trace_computation_distribution.png` | 640×480 | `951b74d895c5cc8a495b99b13de41d66532d03ad54e68e7b178882aaedf38187` |
| `trace_deadline_distribution.png` | 640×480 | `8139f3c85a631cc9e8571e884e80b16e152002fcb87f813caafd37ede5372355` |

## 3. روش digitization

روش با برچسب `[پیشنهاد فنی؛ آزمون کمکی]`:

1. hash و ابعاد هر PNG پیش از پردازش fail-fast کنترل می‌شود.
2. رنگ‌های solid خود Matplotlib به‌طور دقیق انتخاب می‌شوند: Low برابر
   `(44,160,44)`، Medium برابر `(255,127,14)` و High برابر `(214,39,40)`.
3. title، legend و خارج axes ماسک می‌شوند.
4. مؤلفه‌های چهارهمبند رنگی با حداقل هشت پیکسل استخراج می‌شوند.
5. bounding box، تعداد پیکسل و نگاشت خطی تقریبی محور برای هر مؤلفه ثبت می‌شود.
6. overlay تشخیصی ساخته می‌شود تا انتخاب ناحیه‌ها به‌صورت بصری قابل ممیزی باشد.

کالیبراسیون دستی از tickهای همان raster انجام شده است:

| شکل | نگاشت x | تفکیک x در هر pixel | نگاشت y | تفکیک y در هر pixel |
| --- | --- | ---: | --- | ---: |
| Storage/Computation | pixel 103→0 و 518→2500 GB | 6.0241 GB | pixel 427→0 و 78→0.010 | 0.00002865 |
| Deadline | pixel 99→0 و 553→120 h | 0.2643 h | pixel 427→0 و 96→0.12 | 0.00036254 |

این تفکیک فقط خطای quantization یک‌پیکسلی را نشان می‌دهد؛ خطای ناشی از
anti-aliasing، هم‌پوشانی، clipping و نامعلوم‌بودن binها بزرگ‌تر و قابل تعیین نیست.

## 4. یافته مستقیم درباره شکل Computation

مقایسه RGBA دو تصویر Storage و Computation نشان داد:

- تعداد کل پیکسل‌های متفاوت: `2789`
- همه پیکسل‌های متفاوت در سطرهای title یعنی `0..57` هستند.
- از سطر 58 تا انتهای تصویر، دو فایل دقیقاً یکسان‌اند.

بنابراین `[استخراج مستقیم]` plot، محورها، legend و داده رنگی دو شکل یکسان‌اند و
فقط title عوض شده است. همچنین محور Computation در خود شکل «Gigabytes» است، در
حالی‌که مدل `K_j` را MFlops تعریف می‌کند. این می‌تواند خطای شکل یا source باشد،
اما علت آن از منابع موجود `[نامشخص]` است. در نتیجه، توزیع computation مستقل
قابل استخراج نیست و هیچ تبدیل GB→MFlops ساخته نشده است.

## 5. نتایج واقعی digitization

| شکل | مؤلفه قابل‌مشاهده | Low | Medium | High |
| --- | ---: | ---: | ---: | ---: |
| Storage | 10 | 3 | 3 | 4 |
| Computation | 10 | 3 | 3 | 4 |
| Deadline | 13 | 2 | 6 | 5 |
| مجموع | 33 | 8 | 12 | 13 |

ده مؤلفه Computation عیناً هندسه ده مؤلفه Storage را تکرار می‌کنند. خروجی CSV
عمداً هر سطر را `visible_color_component_not_underlying_histogram_bin` می‌نامد.
این سطرها bin، نمونه خام یا probability mass قطعی نیستند.

## 6. Data Dictionary خروجی digitized

| ستون | معنی | واحد/نوع | وضعیت علمی |
| --- | --- | --- | --- |
| `figure` | نام PNG منتشرشده | string | provenance |
| `resource` | storage/computation/deadline | category | برچسب شکل |
| `priority` | low/medium/high | category | رنگ legend |
| `component_id` | شناسه پایدار مؤلفه | string | `[پیشنهاد فنی]` |
| `pixel_count` | تعداد pixelهای solid و متصل | pixel | مشاهده مستقیم raster |
| `pixel_left/right/top/bottom` | bounding box قابل‌مشاهده | pixel | مشاهده مستقیم raster |
| `x_visible_left/right/midpoint_approx` | نگاشت تقریبی bounding box به x | GB یا hour | digitized تقریبی |
| `probability_top/bottom_approx` | نگاشت تقریبی y | probability axis | digitized تقریبی |
| `x_unit_as_published` | واحد لفظی محور | string | بدون اصلاح واحد |
| `scientific_label` | هشدار عدم برابری با bin | string | guard علمی |

## 7. جداسازی artifactها

| نوع | مسیر | وضعیت |
| --- | --- | --- |
| تصاویر رسمی منتشرشده | `data/raw/published_figures/arxiv_v2/` | موجود؛ read-only convention |
| داده digitized | `data/interim/digitized/southampton_histograms_arxiv_v2/` | موجود |
| داده surrogate آینده | `data/processed/surrogates/` | خالی؛ فقط README |
| نتایج آزمایش surrogate آینده | `results/raw/surrogate/` | خالی؛ فقط README |
| نمودارهای QA | `figures/diagnostics/stage12b/` | موجود؛ نتیجه مقاله نیست |

## 8. محدودیت‌های بازسازی از raster

- bin edges، تعداد binها و تنظیمات histogram گزارش نشده‌اند.
- ترتیب رسم باعث پنهان‌شدن بخشی از barهای Low و Medium زیر سری‌های بعدی شده است.
- مؤلفه متصل ممکن است بخشی از یک bar، چند bar متصل یا فقط قسمت قابل‌مشاهده باشد.
- sample count و proportion سه priority معلوم نیست.
- هیچ joint distribution بین storage، computation، deadline، arrival و Utility
  قابل استخراج نیست.
- تصویر computation مستقل نیست و واحد آن با مدل ناسازگار است.
- digitization نمی‌تواند timestamp، user group، schema یا row-level trace بسازد.

## 9. فرض‌های پیشنهادی برای تولید surrogate

این فرض‌ها هنوز **تصویب نشده‌اند** و در این مرحله استفاده نشده‌اند.

### ASSUMP-028 — توزیع تجربی فقط از مساحت قابل‌مشاهده

برای هر `(priority, resource)`، `pixel_count` مؤلفه‌های قابل‌مشاهده به‌عنوان وزن
نسبی normalize شود و پس از انتخاب مؤلفه، مقدار x به‌صورت Uniform روی
`[x_visible_left_approx, x_visible_right_approx]` نمونه‌گیری شود.

- اثر: فقط هندسه رنگی قابل‌مشاهده raster را تقلید می‌کند؛ occluded mass را
  بازیابی نمی‌کند.
- گزینه دیگر: وزن `height×width` کالیبره‌شده یا midpoint گسسته؛ هر دو اطلاعاتی
  بیش از raster وارد می‌کنند یا artefact شدیدتری می‌سازند.
- گزینه پیشنهادی: pixel area، چون مستقیم‌ترین کمیت مشاهده‌شده است.

### ASSUMP-029 — تعداد نمونه صریح و متوازن

`records_per_priority=10000` برای هر یک از Low/Medium/High در config صریح ثبت
شود. این انتخاب برای پایداری نمودار تشخیصی است و تخمینی از proportion واقعی
workload نیست.

- اثر: 30000 ردیف diagnostic ساخته می‌شود؛ class mix مقاله بازسازی نمی‌شود.
- گزینه پیشنهادی: تعداد برابر، چون نسبت واقعی کلاس‌ها مفقود است و از ارتفاع
  histogram قابل استنتاج مطمئن نیست.

### ASSUMP-030 — استقلال شرطی marginalها

Storage و Deadline به‌طور مستقل، مشروط به priority، نمونه‌گیری شوند. هیچ
correlation درون‌کلاس یا بین ردیف‌ها ادعا نشود.

- اثر: فقط marginalهای قابل‌مشاهده قابل مقایسه‌اند؛ workload joint بازتولید
  نمی‌شود.
- گزینه پیشنهادی: استقلال صریح؛ coupling دلخواه مستندپذیر نیست.

### ASSUMP-031 — schema محدود و حذف Computation

خروجی surrogate این مرحله فقط شامل `surrogate_id`, `priority`, `storage_gb` و
`deadline_hours` باشد. Computation، arrival، Utility، upload/download و output
size تولید نشوند. بنابراین این artifact مستقیماً ورودی اجرای الگوریتم‌های مقاله
نیست.

- اثر: استفاده فقط برای smoke test پردازش و بازتولید کیفی دو marginal ممکن است.
- گزینه‌های ردشده: کپی Storage به Computation یا ساخت تبدیل GB→MFlops؛ هر دو
  ادعای بی‌پشتوانه ایجاد می‌کنند.

### ASSUMP-032 — RNG اجباری و بدون tuning

از NumPy PCG64 با seed اجباری و streamهای نام‌دار مستقل برای انتخاب مؤلفه و
نمونه درون بازه استفاده شود. seed و تنظیمات در metadata ذخیره شوند. هیچ seed یا
پارامتری با معیار نزدیکی به شکل انتخاب نشود.

- گزینه پیشنهادی: همان سیاست reproducibility در ASSUMP-020، ولی با scope مستقل
  Southampton surrogate.

## 10. نتیجه زیربخش

digitization تقریبی و checksumدار تصاویر کامل و آزمون شده است. preprocessing
داده واقعی همچنان blocked است. تولید surrogate و بازترسیم آماری تا تصمیم کاربر
درباره ASSUMP-028..032 آغاز نمی‌شود.

## 11. اجرای واقعی و QA

فرمان اصلی:

```powershell
.\.venv\Scripts\python.exe scripts\digitize_southampton_histograms.py
```

خروجی واقعی: `component_count=33`، شمارش Storage=`10`، Computation=`10`،
Deadline=`13` و پرچم pixel identity برابر `true`.

دو اجرای متوالی برای پنج artifact خروجی مقایسه شدند و هر پنج فایل byte-for-byte
یکسان بودند:

| artifact | SHA-256 اجرای نهایی |
| --- | --- |
| `visible_components.csv` | `A3B008C00C601E453894E2A60DB1573C9C3B5966188C25BD6CCFE2B1E3F8D888` |
| `digitization_manifest.json` | `A9CF56BDCE9FCA893E255E26CB94713727119F9D1B946E942FE1930AB4ECF805` |
| Storage overlay | `2B29379A6ED6E274700074B19DB0CB6C4E01EAAAF66F0D36C7FDC1DC83ED41A8` |
| Computation overlay | `47045BDE13D012FA57607FDD904CF45FB5C2E2AA955CA13384E46C7220AC0665` |
| Deadline overlay | `F0CCF0CBA8AE219F30815954CA5CE660DC7707586A16F90D49DE8F6241B76613` |

QA کامل پروژه پس از تغییر:

- Ruff format: 83 فایل، بدون تغییر لازم
- Ruff lint: موفق
- mypy strict: 74 source file، بدون issue
- pytest: `188 passed in 12.56s`
- آزمون جدید Stage 12-B: چهار آزمون موفق، صفر ناموفق
- بازبینی بصری: هر سه overlay با resolution اصلی 640×480 بررسی شدند.
