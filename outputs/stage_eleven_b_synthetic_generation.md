# مرحله یازدهم-B — مولدهای Synthetic Normal و Synthetic Bimodal

تاریخ اجرا: 2026-08-11  
منبع مبنا: *Improved Methods of Task Assignment and Resource Allocation with
Preemption in Edge Computing Systems*، arXiv:2403.15665v2 (2024)

## دامنه و مرزبندی علمی

- `[صریح در مقاله]` پارامترهای توزیع هشت سرور، ویژگی‌های Normal و نرخ ورود از
  Section VI-A2 و Table I، PDF p.8 پیاده‌سازی شدند.
- `[صریح در مقاله]` پارامترهای Bimodal و نسبت 90% low / 10% high از Section
  VI-B2 و Table II، PDF p.10 پیاده‌سازی شدند.
- `[فرض بازتولید]` mechanics گزارش‌نشده فقط مطابق ASSUMP-020 تا ASSUMP-027
  مصوب کاربر اجرا شدند. متن کامل و منشأ شکاف‌ها در
  `outputs/stage_eleven_a_synthetic_generator_gap_audit.md` باقی مانده است.
- `[نامشخص]` horizon رسمی، seed مقاله، تعداد اجرای مستقل و `s'_j` در v2 گزارش
  نشده‌اند. بنابراین configهای این مرحله با برچسب
  `auxiliary_envelope_not_paper_horizon` ذخیره شدند.
- `[استخراج مستقیم]` خروجی فقط برای لایه تخصیص قابل استفاده است؛ داده لازم برای
  بازسازی کامل execution/transmission pipeline وجود ندارد.

## نگاشت پارامترهای مقاله

| گروه | فیلد | توزیع پیاده‌سازی‌شده | واحد لفظی جدول | منشأ |
| --- | --- | --- | --- | --- |
| Server | Storage | N(540, 30) | MB | Table I، p.8 |
| Server | Computation | N(80, 20) | MFlops/s | Table I، p.8 |
| Server | Upload/Download | N(120, 30) | MB/s | Table I، p.8 |
| Normal job | Storage | N(200, 20) | MB | Table I، p.8 |
| Normal job | Computation | N(100, 20) | MFlops | Table I، p.8 |
| Normal job | Upload/Download | N(80, 10) | MB/s | Table I، p.8 |
| Normal job | Deadline | N(10, 3) | slot | Table I، p.8 |
| Normal job | Utility | N(60, 20) | utility | Table I، p.8 |
| Bimodal job | Storage | N(160, 10) | MB | Table II، p.10 |
| Bimodal job | Computation | N(80, 20) | MFlops | Table II، p.10 |
| Bimodal job | Upload/Download | N(70, 10) | MB/s | Table II، p.10 |
| Bimodal job | Deadline | N(10, 3) | slot | Table II، p.10 |
| Bimodal utility | Low / High | N(40, 10) / N(160, 20) | utility | Table II، p.10 |
| Arrival | Jobs per slot | N(14, 4) | jobs/slot | Section VI-A2، p.8؛ Bimodal با ASSUMP-024 |

در نماد `N(μ, σ)` پارامتر دوم مطابق خوانش ثبت‌شده در Stage 11-A انحراف معیار
است، نه واریانس.

## طراحی اجرایی

- `SyntheticGenerationConfig` تمام envelopeها و seed را بدون default علمی مخفی
  دریافت و keyهای کم/اضافه را رد می‌کند.
- NumPy `Generator(PCG64)` با یک `SeedSequence` ریشه و ۱۴ child stream نام‌دار
  برای serverها، arrivalها، هر marginal وظیفه و labelهای mixture استفاده می‌شود.
- کمیت‌های پیوسته نامعتبر با rejection sampling جایگزین می‌شوند؛ clipping انجام
  نمی‌شود. deadline و arrival با `floor(raw + 0.5)` گرد می‌شوند.
- سهم Bimodal دقیق است؛ total غیرمضرب ده fail-fast می‌شود و labelها با stream
  مستقل shuffle می‌شوند.
- CSVها با newline و ترتیب ستون ثابت و JSONها با keyهای مرتب نوشته می‌شوند.
- metadata شامل نسخه NumPy، seed، ترتیب streamها، پارامترها، واحدها، raw/rounding
  rule، تعداد resample و فیلدهای مفقود است.

## تنظیم اجرای کمکی این مرحله

| تنظیم | Normal | Bimodal | وضعیت علمی |
| --- | ---: | ---: | --- |
| `server_count` | 8 | 8 | `[صریح در مقاله]` |
| `seed` | 20240811 | 20240811 | `[فرض بازتولید]`؛ seed مقاله نیست |
| `arrival_slots` | 102 | 102 | `[فرض بازتولید]`؛ صرفاً envelope کمکی |
| `drain_slots` | 0 | 0 | `[فرض بازتولید]`؛ صرفاً envelope کمکی |
| task count حاصل | 1410 | 1410 | نتیجه اجرای واقعی |

انتخاب 102 slot فقط برای تولید نمونه تشخیصی با حجم آماری مناسب و total مضرب ده
انجام شده است؛ این مقدار به مقاله نسبت داده نمی‌شود.

## نتایج واقعی کنترل آماری

قاعده `[آزمون کمکی]`: برای `n >= 30`، اختلاف میانگین حداکثر چهار standard error
و خطای نسبی انحراف معیار حداکثر `4/sqrt(2(n-1))` است. چهار فیلد server به دلیل
`n=8` فقط `informational_small_sample` هستند و pass آماری ادعا نمی‌شود.

| Workload | فیلد | n | میانگین مشاهده‌شده | SD مشاهده‌شده | هدف μ/σ | وضعیت |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Normal | storage | 1410 | 200.5070 | 20.3550 | 200/20 | pass |
| Normal | computation | 1410 | 101.4075 | 20.2626 | 100/20 | pass |
| Normal | upload | 1410 | 79.6990 | 9.9293 | 80/10 | pass |
| Normal | download | 1410 | 80.2255 | 10.1733 | 80/10 | pass |
| Normal | deadline | 1410 | 10.0163 | 2.9759 | 10/3 | pass |
| Normal | utility | 1410 | 59.9332 | 19.5140 | 60/20 | pass |
| Bimodal | storage | 1410 | 160.2535 | 10.1775 | 160/10 | pass |
| Bimodal | computation | 1410 | 81.4075 | 20.2626 | 80/20 | pass |
| Bimodal | upload | 1410 | 69.6990 | 9.9293 | 70/10 | pass |
| Bimodal | download | 1410 | 70.2255 | 10.1733 | 70/10 | pass |
| Bimodal | deadline | 1410 | 10.0163 | 2.9759 | 10/3 | pass |
| Bimodal | utility low | 1269 | 39.9529 | 9.9641 | 40/10 | pass |
| Bimodal | utility high | 141 | 162.4894 | 18.9631 | 160/20 | pass |
| Both | arrival count | 102 | 13.8235 | 3.9418 | 14/4 | pass |

نسبت Bimodal دقیقاً 1269 low و 141 high، یعنی 0.9/0.1 است. در هر دو workload
یک deadline خام دوباره نمونه‌گیری شد؛ در Normal دو Utility غیرمثبت نیز دوباره
نمونه‌گیری شدند. هیچ clipping رخ نداد.

## خروجی‌ها و بازبینی بصری

- هر workload چهار فایل `servers.csv`، `tasks.csv`، `arrival_counts.csv` و
  `metadata.json` دارد.
- هر workload سه نمودار tasks، servers و arrivals در هر دو قالب PNG و SVG دارد.
- `[آزمون کمکی]` نمودارها بازبینی بصری شدند: عنوان‌ها، محور/واحدها، legend و
  overlay توزیع هدف خوانا هستند؛ دو مؤلفه Utility در نمودار Bimodal جدا دیده می‌شوند.
- نمودار server صریحاً `n=8` و informational بودن را نمایش می‌دهد.
- این نمودارها نمودار بازتولیدشده مقاله نیستند.

## آزمون و تکرارپذیری

- ۷ آزمون واحد: ثوابت، validation config، rounding/rejection، positivity،
  conversion allocation-only، quota/ID و guard مضرب ده.
- ۳ آزمون یکپارچه: artifactهای byte-stable، moment/quota diagnostics و تولید
  PNG/SVG.
- اجرای هدفمند: `10 passed in 12.12s`.
- اجرای کامل پروژه پس از تغییر: `184 passed in 24.34s`.
- Ruff format/check، mypy روی ۷۱ فایل منبع و `pip check` همگی موفق بودند.
- پس از دو اجرای کامل متوالی Normal و Bimodal، SHA-256 هر ۲۲ فایل بررسی شد:
  `Byte reproducibility: PASS (22 files unchanged)`.

### شکست‌ها و رفع آن‌ها

1. نصب editable نخست در sandbox به دلیل دسترسی شبکه شکست خورد.
2. اجرای escalated اولیه به timeout 124 ثانیه رسید و نصب کامل نشد.
3. `--no-build-isolation` سپس به دلیل نبود `setuptools.build_meta` شکست خورد.
4. با نصب صریح `setuptools==83.0.0`، نصب editable با موفقیت انجام شد.
5. lint اولیه یک `SIM300` در آزمون constantها یافت؛ مقایسه مبهم بازنویسی شد و
   اجرای بعدی Ruff کامل موفق بود.
6. import مستقیم Matplotlib در فرمان گزارش نسخه، به علت غیرقابل‌نوشتن بودن
   AppData یک هشدار cache داد و cache موقت ساخت. مسیر واقعی تولید پیش از import،
   `MPLCONFIGDIR` را به temp قابل‌نوشتن هدایت می‌کند و بدون این هشدار اجرا شد.

## وابستگی‌ها

- Python پروژه: `>=3.11`.
- NumPy `2.5.1`، Matplotlib `3.11.1` و setuptools `83.0.0` پین شدند.
- Matplotlib از backend غیرتعاملی `Agg`، `svg.hashsalt` ثابت و metadata پایدار
  استفاده می‌کند. cache آن خارج از پوشه figures قرار می‌گیرد.
- Gurobi نصب یا استفاده نشد.

## محدودیت‌های باقی‌مانده

1. `[نامشخص]` horizon و seed آزمایش اصلی مقاله هنوز موجود نیست.
2. `[نامشخص]` تعداد تکرار و روش aggregation آزمایش اصلی موجود نیست.
3. `[نامشخص]` `s'_j` برای محاسبه زمان دانلود گزارش نشده است.
4. `[نامشخص]` این رکوردها هنوز به پروتکل کامل مزایده/شبیه‌سازی زمانی متصل نشده‌اند.
5. moment checks و شکل‌های این مرحله فقط آزمون مهندسی مولدند و ادعاهای عددی مقاله
   را بازتولید نمی‌کنند.

## نتیجه زیربخش

مولدهای allocation-layer Synthetic Normal و Synthetic Bimodal مطابق پارامترهای
صریح Tables I-II و هشت فرض مصوب پیاده‌سازی، اجرا و از نظر تکرارپذیری تأیید شدند.
این زیربخش کامل است؛ بازتولید آزمایش‌های مقاله همچنان به envelope رسمی و سایر
اطلاعات مفقود وابسته است.
