# مرحله دوازدهم-C — surrogate کیفی histogramهای Southampton

تاریخ اجرا: 2026-08-12  
منبع مبنا: arXiv:2403.15665v2 (2024)  
وضعیت: **کامل در دامنه آزمون فنی/کیفی؛ مسیر real trace همچنان blocked**

## 1. مرز علمی

- `[صریح از کاربر]` ASSUMP-028 تا ASSUMP-032 مطابق متن پیشنهادی تصویب شدند.
- artifact تولیدشده فقط surrogate تقریبی هندسه قابل‌مشاهده histogramها است.
- این artifact داده واقعی Southampton، reconstruction ردیفی trace یا بازتولید
  عددی نتایج مقاله نیست.
- `algorithm_input_compatible=false` است؛ هیچ اجرای KG/DK یا ادعای Utility از آن
  تولید نشده است.
- هیچ seed، وزن، bin یا پارامتری پس از مشاهده خروجی برای نزدیک‌کردن به شکل مقاله
  تغییر داده نشد.

## 2. نگاشت فرض‌های مصوب به پیاده‌سازی

| فرض | رفتار اجرایی | محل |
| --- | --- | --- |
| ASSUMP-028 | انتخاب component متناسب با normalized visible `pixel_count` و Uniform روی visible x bounds | `southampton_surrogate.py` |
| ASSUMP-029 | دقیقاً 10000 رکورد برای Low، Medium و High | config و validation |
| ASSUMP-030 | Storage و Deadline مستقل، مشروط به priority | PCG64 named streams |
| ASSUMP-031 | فقط ID، priority، storage و deadline؛ حذف computation و سایر فیلدها | record schema/artifact writer |
| ASSUMP-032 | seed اجباری، 12 child stream و metadata کامل؛ no tuning | config/metadata |

## 3. config اجرای واقعی

| پارامتر | مقدار | برچسب |
| --- | --- | --- |
| `dataset_id` | `southampton-visible-histogram-surrogate-stage12c-auxiliary` | `[پیشنهاد فنی]` |
| `seed` | `20240812` | `[پیشنهاد فنی]`؛ seed مقاله نیست |
| `records_per_priority` | 10000 | `[فرض بازتولید؛ ASSUMP-029]` |
| RNG | NumPy 2.5.1 / PCG64 | `[فرض بازتولید؛ ASSUMP-032]` |
| named streams | 12 | 2 operation × 2 resource × 3 priority |
| diagnostic bins | 60 | `[پیشنهاد فنی؛ آزمون کمکی]`؛ ثابت و بدون tuning |

seed پیش از اجرای خروجی انتخاب و فقط به‌عنوان مقدار auxiliary در config ثبت شد.

## 4. schema و artifactهای تولیدشده

CSV دارای دقیقاً چهار ستون است:

| ستون | واحد/نوع | منشأ |
| --- | --- | --- |
| `surrogate_id` | string | شناسه پایدار فنی |
| `priority` | low/medium/high | رنگ شکل منتشرشده |
| `storage_gb` | GB | sample از visible Storage components |
| `deadline_hours` | hour | sample از visible Deadline components |

فیلدهای `computation`, `arrival`, `utility`, `upload`, `download` و `output_size`
صریحاً در metadata به‌عنوان omitted ثبت شده‌اند.

تفکیک مسیرها:

- published raster: `data/raw/published_figures/arxiv_v2/`
- digitized geometry: `data/interim/digitized/southampton_histograms_arxiv_v2/`
- generated rows: `data/processed/surrogates/<dataset_id>/`
- aggregated auxiliary check: `results/aggregated/stage12c/`
- qualitative figures: `figures/diagnostics/stage12c/`
- `results/raw/surrogate/` بدون نتیجه آزمایش الگوریتمی باقی ماند.

## 5. نتیجه واقعی تولید

| Priority | تعداد |
| --- | ---: |
| Low | 10000 |
| Medium | 10000 |
| High | 10000 |
| مجموع | 30000 |

تعداد انتخاب component در metadata ثبت شده و جمع آن برای دو resource برابر
60000 است. PNGهای source پیش از تولید با hashهای digitization manifest مقایسه
می‌شوند؛ هر تغییر باعث fail-fast می‌شود.

## 6. کنترل‌های آماری کمکی

قانون acceptance فقط توزیع sampling مصوب را کنترل می‌کند:

`mean_z <= 5` و `max_component_frequency_z <= 5` و همه مقادیر در envelope
visible support باشند.

| Resource | Priority | mean مورد انتظار visible law | mean مشاهده‌شده | mean z | بیشینه component z | وضعیت |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Storage | Low | 69.6091 | 69.2861 | 0.3553 | 0.9176 | pass |
| Storage | Medium | 210.3400 | 214.3302 | 1.2810 | 1.6683 | pass |
| Storage | High | 458.9563 | 455.8511 | 0.5000 | 2.0645 | pass |
| Deadline | Low | 6.9369 | 6.9404 | 0.1023 | 0.8462 | pass |
| Deadline | Medium | 20.0668 | 20.0127 | 0.5457 | 1.3881 | pass |
| Deadline | High | 58.1949 | 58.0194 | 0.8587 | 1.6207 | pass |

هر شش check موفق‌اند. این میانگین‌ها نتیجه مقاله نیستند؛ صرفاً نتیجه اجرای
surrogate با seed ثبت‌شده‌اند.

## 7. نمودارهای کیفی

برای Storage و Deadline یک comparison دوپنله ساخته شد:

- پنل چپ: raster منتشرشده arXiv v2 بدون تغییر؛
- پنل راست: density histogram surrogate با 60 bin ثابت؛
- محور y سمت راست صریحاً `Density (not paper probability scale)` است؛
- title صریحاً `qualitative auxiliary comparison; not raw trace` است.

هر دو PNG با resolution اصلی بازبینی بصری شدند و نسخه SVG نیز تولید شد.

## 8. تکرارپذیری byte-level

دو اجرای مستقل و متوالی با همان config انجام شد. هر 7 artifact byte-for-byte
یکسان بود:

| artifact | SHA-256 |
| --- | --- |
| `surrogate_records.csv` | `579B2D07E126362FEA31931054D733030048D3A936BB9EC684A0B33859D11CFD` |
| `metadata.json` | `EF7516E199020E13159F172960EC807568489328A29A1CD097D867C4C9CD88AE` |
| diagnostics JSON | `8C4518DC1277CFED8907AD1B41AA84BB04B42F9D1D2B70F0426C45C4D875AC9E` |
| Storage PNG | `7F7FDB74E337865569D51376791577112CF553AA681C4185D9BE0699AA3E9FF5` |
| Storage SVG | `DAC0EAF3F9D71619629DD4DB750DD60D466E91D3E46775D63D062CD53B66D48C` |
| Deadline PNG | `61E025290ED93A3521C5DCE8CFF8E6104705BDFA3A7C5605019EB0AB59B937E2` |
| Deadline SVG | `E4D8EC4972E912E5EBA366F14AF7D2C0691C068FB7077D4650BA800A29C8704C` |

## 9. آزمون‌ها و QA

- آزمون‌های جدید Stage 12-C: 8 موفق، 0 ناموفق
- شامل config guards، حذف computation، seed repeatability، تغییر seed، schema،
  statistical checks، artifact byte repeatability، PNG/SVG و hash mismatch منفی
- Ruff format: 89 فایل، کامل
- Ruff lint: بدون خطا
- mypy strict: 79 source file، بدون issue
- کل pytest: `196 passed in 13.83s`

## 10. محدودیت‌های باقی‌مانده

- raw trace و schema همچنان موجود نیست؛ preprocessing واقعی blocked است.
- hidden/occluded probability mass قابل بازیابی نیست.
- class proportions واقعی معلوم نیست؛ تعداد برابر فقط فرض diagnostic است.
- joint dependence واقعی Storage/Deadline از بین رفته است.
- توزیع Computation به‌دلیل تکرار شکل Storage و ناسازگاری واحد ساخته نشده است.
- arrival، Utility و منابع شبکه وجود ندارند؛ بنابراین اجرای آزمایش‌های مقاله روی
  این artifact مجاز و ممکن نیست.
- نتیجه مرحله فقط «مولد surrogate فنی مطابق فرض‌های مصوب بازتولیدپذیر است»؛
  هیچ ادعای نتایج عددی Southampton مقاله تأیید نشده است.
