# مرحله یازدهم-A: ممیزی اجرایی مولدهای داده مصنوعی

## 1. دامنه و منابع

منبع مبنا همچنان `arXiv:2403.15665v2` مورخ 29 مارس 2024 است. این ممیزی فقط
برای تعیین امکان ساخت مولدهای `Synthetic Normal` و `Synthetic Bimodal` انجام شد
و هنوز هیچ generator، config داده، CSV یا نمودار تشخیصی ایجاد نشده است.

منابع بررسی‌شده:

- arXiv v2، Section VI-A2 و Table I، PDF p.8؛
- arXiv v2، Section VI-B2 و Table II، PDF p.10؛
- source package v2 شامل `main.tex` و `main.bbl`؛
- `[استخراج از مرجع مستقیم مقاله]` مرجع [4]، Section V و Table I، PDF p.5؛
- `[استخراج از مرجع مستقیم مقاله]` مرجع [1]، Section VI-B، PDF p.7؛
- `[منبع تکمیلی خارج از مبنای v2]` نسخه IEEE TPDS 2025، PDF pp.9 و 11 متناظر
  با setup و Bimodal؛
- جست‌وجوی هدفمند برای کد رسمی منتشرشده.

بسته source v2 فقط فایل‌های LaTeX/Bibliography دارد و هیچ seed، اسکریپت تولید
داده، فایل config یا داده خامی در آن وجود ندارد. جست‌وجوی هدفمند نیز مخزن رسمی
قابل‌انتساب به نویسندگان پیدا نکرد.

## 2. اطلاعات قطعی قابل تبدیل به config

### Synthetic Normal

| فیلد | توزیع | واحد | محل | برچسب |
| --- | --- | --- | --- | --- |
| تعداد server | ثابت 8 | server | v2 p.8 | `[صریح در مقاله]` |
| server storage | `N(540,30)` | MB | Table I | `[صریح در مقاله]` |
| server computation | `N(80,20)` | MFlops/s | Table I | `[صریح در مقاله]` |
| server upload | `N(120,30)` | MB/s | Table I | `[صریح در مقاله]` |
| server download | `N(120,30)` | MB/s | Table I | `[صریح در مقاله]` |
| job storage | `N(200,20)` | MB | Table I | `[صریح در مقاله]` |
| job computation | `N(100,20)` | MFlops | Table I | `[صریح در مقاله]` |
| job upload | `N(80,10)` | MB/s | Table I | `[صریح در مقاله]` |
| job download | `N(80,10)` | MB/s | Table I | `[صریح در مقاله]` |
| deadline | `N(10,3)` | slot | Table I | `[صریح در مقاله]` |
| Utility | `N(60,20)` | utility | Table I | `[صریح در مقاله]` |
| arrival count | `N(14,4)` | job/slot | Section VI-A2 | `[صریح در مقاله]` |

ستون `σ` در جدول صریح است؛ بنابراین پارامتر دوم standard deviation است، نه
variance. مقاله نوع Normal محدودشده یا گسسته را ذکر نمی‌کند.

### Synthetic Bimodal

| فیلد | توزیع | واحد | محل | برچسب |
| --- | --- | --- | --- | --- |
| serverها | همان Table I | همان بالا | v2 p.10 | `[صریح در مقاله]` |
| job storage | `N(160,10)` | MB | Table II | `[صریح در مقاله]` |
| job computation | `N(80,20)` | MFlops | Table II | `[صریح در مقاله]` |
| job upload | `N(70,10)` | MB/s | Table II | `[صریح در مقاله]` |
| job download | `N(70,10)` | MB/s | Table II | `[صریح در مقاله]` |
| deadline | `N(10,3)` | slot | Table II | `[صریح در مقاله]` |
| low Utility | `N(40,10)` | utility | Table II | `[صریح در مقاله]` |
| high Utility | `N(160,20)` | utility | Table II | `[صریح در مقاله]` |
| low/high share | دقیقاً 90% / 10% | class share | Section VI-B2 | `[صریح در مقاله]` |

چاپ `U_{1,j}` برای Utility 2 در Table II یک خطای نمادگذاری ظاهری است؛ عنوان
`Utility 2` و نثر high-value تفسیر دو مؤلفه را بدون تغییر عددها روشن می‌کند.

## 3. یافته منابع تکمیلی

- `[استخراج از مرجع مستقیم مقاله]` مرجع [4]، PDF p.5، برای workload متفاوت خود
  `200` timestep ورود و `20` timestep خالی گزارش می‌کند.
- `[استخراج از مرجع مستقیم مقاله]` مرجع [1]، PDF p.7، برای آزمایش متفاوت خود
  horizon برابر `30` timestep و arrival rate دیگری گزارش می‌کند.
- این دو مقدار با هم متفاوت‌اند و v2 برای workload اصلی خود هیچ‌یک را ارجاع
  نمی‌دهد. پس انتقال یکی از آن‌ها به Normal/Bimodal v2 قابل استخراج مستقیم نیست.
- `[منبع تکمیلی خارج از مبنای v2]` نسخه IEEE 2025 همان پارامترهای جدول‌ها و
  نسبت 90/10 را تکرار می‌کند، اما seed، horizon، rounding، truncation، dependence
  یا output-size را اضافه نمی‌کند.

## 4. شکاف‌های مسدودکننده

| شکاف | محل بررسی‌شده | اثر | گزینه‌های معقول | گزینه پیشنهادی نزدیک‌تر |
| --- | --- | --- | --- | --- |
| RNG و seed | v2 کامل، source package، IEEE 2025 | داده بایت‌به‌بایت متفاوت | Python random؛ NumPy legacy؛ NumPy Generator | PCG64 با seed اجباری و metadata؛ ASSUMP-020 |
| استقلال متغیرها | Tables I-II و نثر setup | joint workload و feasibility تغییر می‌کند | independent؛ correlation فرضی | independent؛ هیچ correlation منبعی نیست؛ ASSUMP-021 |
| مقادیر منفی Normal | Tables I-II | resource/deadline نامعتبر | clip؛ reject/resample؛ truncate distribution | rejection sampling؛ ASSUMP-022 |
| تبدیل deadline/arrival به integer | Tables I-II و arrival sentence | arrival sequence و deadline تغییر می‌کند | floor؛ ceil؛ nearest؛ stochastic rounding | nearest-half-up با bounds؛ ASSUMP-022 |
| واحد storage | مدل p.3 می‌گوید GB، Table I می‌گوید MB | ظرفیت نسبی 1000 برابر تغییر می‌کند | تبدیل server به GB؛ literal table units | literal MB جدول آزمایش؛ ASSUMP-023 |
| horizon و drain | v2 pp.8-12؛ [4] p.5؛ [1] p.7 | تعداد job و totals نامعلوم | 200+20؛ 30؛ مقدار config اجباری | بدون default و بدون ادعای مقاله؛ ASSUMP-024 |
| arrival در Bimodal | v2 p.10 | تعداد job Bimodal نامعلوم | N(14,4)؛ نرخ جدید؛ total ثابت | reuse صریح‌شده در config از Normal؛ ASSUMP-024 |
| اجرای «دقیقاً 90/10» | v2 p.10 | class count و Utility تغییر می‌کند | Bernoulli؛ quota rounded؛ total divisible by 10 | quota دقیق و fail-fast برای total نامضرب 10؛ ASSUMP-025 |
| output size `s'_j` | model Eqs. (6)-(7)، Tables I-II | full pipeline/batch completion ناقص | برابر input؛ نسبت ثابت؛ omission | omission شفاف؛ allocation-layer only؛ ASSUMP-026 |
| high/low در Normal | captions Figs. 7-8/10 | نمودار class-specific مسدود | threshold؛ quantile؛ latent label | هیچ label ساخته نشود تا منبع/تصمیم؛ ASSUMP-026 |
| ID و ترتیب draw | source package و captions jobs 532/540 | stream و tieها تغییر می‌کند | UUID؛ zero-based؛ one-based sequence | one-based stable arrival order؛ ASSUMP-027 |

## 5. فرض‌های پیشنهادی در پایان ممیزی

### ASSUMP-020 — RNG و seed

- استفاده از `numpy.random.Generator(PCG64)` با نسخه pinشده؛
- seed ورودی اجباری و بدون مقدار پیش‌فرض؛
- child streamهای نام‌دار و مستقل برای server، arrival، job fields و mixture؛
- ثبت seed، bit generator، نسخه NumPy و ترتیب streamها در metadata؛
- seedهای smoke/statistical test فقط `[آزمون کمکی]` باشند.

### ASSUMP-021 — استقلال توزیع‌ها

تمام serverها، jobها و فیلدهای Normal مستقل نمونه‌برداری شوند. هیچ correlation
پنهانی میان storage، computation، bandwidth، deadline و Utility اعمال نشود.

### ASSUMP-022 — positivity و integer conversion

- continuous resource/bandwidth/computation/Utility تا رسیدن به مقدار متناهی و
  strictly-positive دوباره نمونه‌برداری و بدون rounding ذخیره شوند؛
- deadline با `floor(x+0.5)` به نزدیک‌ترین integer تبدیل و تا حصول مقدار `>=1`
  resample شود؛
- arrival count با همان قاعده تبدیل و تا حصول مقدار `>=0` resample شود؛
- raw draw و تعداد resampleها در diagnostics ثبت شوند؛ clipping انجام نشود.

### ASSUMP-023 — واحدهای جدول آزمایش

اعداد Tables I-II عیناً با واحدهای چاپ‌شده جدول استفاده شوند: storage برحسب MB،
computation برحسب MFlops یا MFlops/s، bandwidth برحسب MB/s و deadline برحسب slot.
هیچ تبدیل پنهان MB/GB انجام نشود.

### ASSUMP-024 — envelope و arrival Bimodal

- `arrival_slots`، `drain_slots` و seed ورودی‌های اجباری config و بدون default
  منتسب به مقاله باشند؛
- اجرای smoke مقادیر صریح و برچسب `[آزمون کمکی]` داشته باشد؛
- Bimodal همان arrival count `N(14,4)` را استفاده کند، زیرا متن فقط job-property
  distribution را تغییر می‌دهد؛
- نتیجه full-scale تا تعیین envelope رسمی، نتیجه مقاله معرفی نشود.

### ASSUMP-025 — سهم دقیق Bimodal

پس از تولید arrival counts، total job count باید مضرب 10 باشد؛ در غیر این صورت
generator fail-fast کند. دقیقاً `9N/10` label کم‌ارزش و `N/10` label پرارزش ساخته
و با stream seedدار مستقل shuffle شوند. Bernoulli تقریبی اعمال نشود.

### ASSUMP-026 — مرز داده قابل تولید

فقط ستون‌های گزارش‌شده Tables I-II تولید شوند. `s'_j` یا output size ساخته نشود.
داده می‌تواند برای لایه auction/resource-vector استفاده شود، اما تا تعیین output
mapping، workload کامل pipeline/batch مقاله نامیده نشود. برای Normal نیز هیچ
high/low label بدون threshold منبعی تولید نشود.

### ASSUMP-027 — شناسه و ترتیب پایدار

server و job IDها one-based و zero-padded باشند. jobها ابتدا برحسب arrival slot و
سپس ترتیب تولید در همان slot شماره‌گذاری شوند. این ترتیب در metadata ثبت و برای
tie handling ثابت بماند.

## 6. ابزارهای پیشنهادی

- `[پیشنهاد فنی]` افزودن NumPy برای RNG و آمار؛ نسخه دقیق فقط هنگام پیاده‌سازی
  pin و ثبت شود.
- `[پیشنهاد فنی]` افزودن Matplotlib برای PNG/SVG تشخیصی؛ نمودارها با برچسب
  `[آزمون کمکی]` ذخیره شوند.
- SciPy برای این مرحله ضروری نیست؛ mean، population standard deviation و سهم
  mixture با NumPy قابل کنترل‌اند.
- خروجی پیشنهادی: CSV داده، JSON metadata و JSON summary؛ raw و diagnostic plots
  در مسیرهای جداگانه.

## 7. وضعیت قابلیت پیاده‌سازی

مقادیر marginal distributionها کامل‌اند، اما generator اجرایی و workload کامل
بدون تعیین RNG، rounding، positivity، envelope و mixture semantics یکتا نیست.
بنابراین طبق اصل وفاداری، ASSUMP-020 تا ASSUMP-027 در پایان این ممیزی غیرفعال
بودند و کدنویسی مرحله یازدهم تا تأیید کاربر متوقف شد.

> به‌روزرسانی 2026-08-11: کاربر ASSUMP-020 تا ASSUMP-027 را دقیقاً مطابق متن
> پیشنهادی تصویب کرد. وضعیت پیاده‌سازی آن‌ها در گزارش مرحله 11-B ثبت می‌شود.
