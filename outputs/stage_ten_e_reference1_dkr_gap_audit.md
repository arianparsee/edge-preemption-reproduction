# مرحله دهم-E: ممیزی هدفمند مرجع مستقیم [1] برای DK-R

## 1. کارهای انجام‌شده

- هویت، تمامیت، تعداد صفحات و SHA-256 فایل `1.pdf` کنترل شد.
- کل ده صفحه برای واژه‌ها و ارجاعات مرتبط با Double Knapsack جست‌وجو شد.
- صفحات PDF 2، 4، 5، 6، 8 و 9 به‌طور کامل متنی خوانده شدند.
- صفحات PDF 4 تا 6، شامل Section IV و Algorithm 1، با رزولوشن 170 DPI render و بصری بازبینی شدند.
- شش شکاف `DK-GAP-01` تا `DK-GAP-06` مرحله قبل، یکی‌یکی ارزیابی شدند.
- به علت باقی‌ماندن ابهام مسدودکننده، هیچ کد، آزمون یا مثال DK-R ایجاد نشد.

## 2. فایل‌های ایجاد یا تغییرکرده

- ایجاد: `outputs/stage_ten_e_reference1_dkr_gap_audit.md`
- تغییر: `outputs/traceability_matrix_arxiv_v2.md`
- موقت: `tmp/pdfs/stage10e/reference1.pdf` و renderهای صفحات 4 تا 6
- بدون تغییر: `docs/assumptions.md`، تمام فایل‌های `src/` و `tests/`

## 3. ارتباط هر تغییر با مقاله

### 3.1 هویت منبع

| مؤلفه | نتیجه |
| --- | --- |
| عنوان | *Scalable Resource Allocation Techniques for Edge Computing Systems* |
| نویسندگان | Caroline Rublein، Fidan Mehmeti، Taha D. Gunes، Sebastian Stein، Thomas F. La Porta |
| محل انتشار | ICCCN 2022 |
| DOI | `10.1109/ICCCN54977.2022.9868909` |
| صفحات | 10 صفحه کامل، بدون رمزگذاری |
| SHA-256 | `D0101C98C7DAB68AA8EB16B78D7277ACD8849B088511BB2C3C4975025EC98564` |
| جایگاه در v2 | مرجع مستقیم [1] arXiv v2 |

`1.pdf` منبع مبنا نیست؛ هر یافته اختصاصی آن در این سند با `[استخراج از مرجع مستقیم مقاله]` ثبت می‌شود.

### 3.2 یافته‌های هدفمند

| مؤلفه | یافته `1.pdf` | اثر بر شکاف |
| --- | --- | --- |
| مزایده | `[استخراج از مرجع مستقیم مقاله]` Section II، PDF p.2: R1 ارسال درخواست و قیمت؛ کاربر کمترین قیمت را انتخاب می‌کند؛ R2 server از returning jobs تخصیص نهایی را می‌سازد؛ ردشده ممکن است در bidding بعدی resubmit شود. | ساختار دو دور تأیید شد؛ tie روشن نشد. |
| هدف R2 | `[استخراج از مرجع مستقیم مقاله]` Section IV، PDF p.4: serverها در R2 مجموعه returning jobs را برای بیشینه‌سازی served utility انتخاب می‌کنند. | `DK-GAP-01` از نظر هدف سطح‌بالا رفع شد. |
| baseline DK-R | `[استخراج از مرجع مستقیم مقاله]` Section V-A1، PDF p.6: baseline Double Knapsack در هر دور multi-dimensional knapsack اجرا می‌کند؛ R1 برای pricing/server choice و R2 برای final placement؛ در نسخه بدون preemption، job پذیرفته‌شده تا completion اجرا می‌شود. | Retention و دو knapsack تأیید شد. |
| چهار بعد | `[استخراج از مرجع مستقیم مقاله]` Section IV-C، PDF p.5: job دارای بردار چهاربعدی `[U/s, U/kappa, U/sigma, U/sigma-prime]` است. | وجود upload/download جدا تأیید شد، ولی pricing DK-R چهاربعدی تعیین نشد. |
| congestion | `[استخراج از مرجع مستقیم مقاله]` Eq. (25)، Section IV-C، PDF p.5: فرمول pricing روش Clustering فقط storage، computation و upload را دارد و `f` را بدون مقدار عددی به توزیع Utility وابسته می‌داند. | `DK-GAP-03` رفع نشد؛ این فرمول متعلق به Clustering است، نه DK-R. |
| Round 2 preemptive | `[استخراج از مرجع مستقیم مقاله]` Section IV-D و Algorithm 1، PDF pp.5-6: current+returning مرتب می‌شوند، subset محدود وارد knapsack total capacity می‌شود و currentهای خارج‌شده preempt می‌شوند. | این الگوریتم نسخه Clustering+Preemption است و نباید به DK-R تعمیم داده شود. |
| GA | `[استخراج از مرجع مستقیم مقاله]` Section IV-D، PDF p.5: off-the-shelf genetic knapsack با `g≈50`؛ `n` شامل pool و jobs درحال‌پردازش است. | تعداد generation تأیید شد؛ library/version و سایر hyperparameterها غایب‌اند. |
| قیمت نهایی روش جدید | `[استخراج از مرجع مستقیم مقاله]` Algorithm 1، PDF p.6: برای روش Clustering+Preemption، `r2Price=max(0.9U,1)`. | متعلق به baseline DK-R نیست؛ جایگزینی قیمت [4] مجاز نیست. |
| batch | `[استخراج از مرجع مستقیم مقاله]` Section II، PDF p.2: مدل پردازش سه‌مرحله‌ای upload/process/download است. | فرمول success-count pricing مرجع [4] باز هم ارائه نشده است. |

### 3.3 وضعیت شش شکاف

| شکاف | وضعیت پس از `1.pdf` | دلیل |
| --- | --- | --- |
| `DK-GAP-01`، objective R2 | تا حد زیادی رفع شد | Section IV p.4 صریحاً maximize served utility را می‌گوید؛ Section V-A1 p.6 knapsack نهایی baseline را تأیید می‌کند. |
| `DK-GAP-02`، `Under threshold` و `beta` | باقی است | این اصطلاح و مقدار در `1.pdf` تعریف نشده‌اند. |
| `DK-GAP-03`، violation چهاربعدی و `f` | باقی است | چهار بعد معرفی شده، اما Eq. (25) روش دیگری است و خود آن فقط سه جزء دارد؛ `f` عدد ندارد. |
| `DK-GAP-04`، تنظیمات GA | باقی است | فقط `g≈50` تکرار شده است. |
| `DK-GAP-05`، batch success-count price | باقی است | هیچ فرمولی برای تبدیل success count به price نیامده است. |
| `DK-GAP-06`، tie-breaking | باقی است | هیچ قاعده‌ای برای bid یا subset مساوی تعریف نشده است. |

## 4. فرمان‌های اجراشده

```powershell
pdfinfo.exe "<local-path-to-reference-1.pdf>"
certutil -hashfile tmp\pdfs\stage10e\reference1.pdf SHA256
python -  # استخراج و جست‌وجوی متن با pypdf bundled runtime
pdftoppm.exe -f 4 -l 6 -png -r 170 tmp\pdfs\stage10e\reference1.pdf ...
python -m pytest -q
```

## 5. نتایج واقعی اجرا

- PDF کامل: 10/10 صفحه قابل‌خواندن و render.
- هش با ممیزی اولیه منبع [1] منطبق است.
- متن Algorithm 1، Eq. (25)، Section IV-D و تعریف baseline در بازبینی تصویری خوانا و منطبق با استخراج متنی بودند.
- Poppler فقط هشدار display font برای `Symbol` و `ArialUnicode` داد؛ محتوای هدف مخدوش نبود.

## 6. آزمون‌های موفق و ناموفق

- آزمون DK-R: اجرا نشد؛ کدی ایجاد نشده است.
- مجموعه رگرسیون موجود پروژه: `146 passed in 0.30s`.
- آزمون ناموفق: صفر.
- شکست استخراج یا render: صفر.

## 7. فرض‌های استفاده‌شده

- فرض جدید اعمال‌شده: صفر.
- ASSUMP-001 تا ASSUMP-010 بدون تغییر باقی ماندند.
- Exact Solver استفاده نشد و همچنان فقط `[ابزار کمکی]` مجاز خواهد بود.
- Algorithm 1 در `1.pdf` به DK-R نسبت داده نشد، زیرا متعلق به ترکیب Clustering+Preemption است.

## 8. ابهامات و فرض‌های پیشنهادی

فرض‌های زیر **پیشنهادی و تأییدنشده** هستند؛ هنوز در `docs/assumptions.md` ثبت نشده و در کد اعمال نشده‌اند.

### ASSUMP-011 — Pipeline DK-R pricing و شاخه feasibility

- Scope فقط pipeline DK-R باشد.
- R1 و R2 از Case 3 مرجع [4] با `alpha=0.1` استفاده کنند.
- `Under threshold` یعنی task به‌تنهایی روی total four-dimensional capacity server قابل‌اجرا باشد.
- task غیرقابل‌اجرا قیمت `math.nextafter(utility, math.inf)` بگیرد؛ این گسترش صریح semantics ASSUMP-007 به DK-R است، نه قیمت اقتصادی.
- در صورت نتیجه غیرمتناهی، fail-fast شود.

دلیل نزدیکی: [1] Section IV-C، PDF p.5 بین fit و not-fit تفکیک می‌کند؛ [4] Algorithm 1 نیز `Under threshold` را پیش از قیمت بالاتر از Utility قرار می‌دهد.

### ASSUMP-012 — تعمیم violation به چهار منبع و scaling factor

- Eq. (11) مرجع [4] برای Storage، Computation، Upload و Download تعمیم یابد.
- برای هر بعد، demand وظیفه جدید و مجموع demand اعضای subset پیشنهادی در صورت کسر قرار گیرد و total capacity همان بعد مخرج باشد.
- `violation = 1 + f * sum(four resource ratios)`.
- `f` یک‌بار برای هر workload از `mean_utility - 1.1 * std_utility` محاسبه و در تمام اجرای آن workload ثابت شود؛ اگر متناهی و مثبت نباشد، fail-fast شود.
- برای داده تجربی، mean/std از workload پردازش‌شده همان experiment و پیش از اجرای auction محاسبه شود، نه از jobهای هر round.

دلیل نزدیکی: [4] Section IV-B/C، PDF p.4 مقدار تقریبی 1.1 انحراف معیار پایین‌تر از میانگین را گزارش می‌کند؛ [1] Section IV-C، PDF p.5 چهار بعد job را تأیید می‌کند. تعمیم چهارم و نحوه محاسبه empirical همچنان `[فرض بازتولید]` است.

### ASSUMP-013 — GA رسمی DK-R

- مسیر رسمی DK-R از یک GA stochastic استفاده کند و Exact Solver فقط oracle آزمون `[ابزار کمکی]` باشد.
- generation count برابر 50 باشد.
- library، نسخه، population، selection، crossover، mutation، elitism و seed باید در config و metadata خروجی ثبت شوند.
- چون منابع این مقادیر را تعیین نکرده‌اند، پیش از کدنویسی یک ممیزی مستقل از مرجع مستقیم pyeasyga [28] انجام و defaultهای همان نسخه پیشنهاد شود؛ هیچ default نصب‌شده‌ای پنهانی پذیرفته نشود.
- آزمون‌های کوچک، feasibility و objective خروجی GA را با Exact Solver مقایسه کنند، اما subset exact جای نتیجه رسمی GA قرار نگیرد.

### ASSUMP-014 — Tie-breaking

- اگر چند server کمترین bid قابل‌قبول مساوی بدهند، با RNG بذرپذیر به‌صورت uniform یکی انتخاب شود؛ seed در نتیجه ثبت شود.
- tieهای داخلی GA به رفتار stochastic همان library و seed ثبت‌شده واگذار شوند و ترتیب task ورودی پیش از GA برحسب ID canonical شود.
- Exact Solver کمکی هنگام چند optimum هم‌ارزش fail-fast کند، مگر آزمون صریحاً مجموعه تمام optimumها را مقایسه کند.

دلیل نزدیکی: v2 در مثال صفحه 7 یک server را میان دو fit price به‌صورت random انتخاب می‌کند، ولی قاعده عمومی یا توزیع را بیان نمی‌کند.

### شکاف batch

برای `DK-GAP-05` فرض عددی پیشنهاد نمی‌شود، زیرا عبارت «discount based on number of successful timesteps» در [4] دامنه بزرگی از فرمول‌های ناسازگار را اجازه می‌دهد. نزدیک‌ترین اقدام وفادارانه این است که:

- ابتدا فقط pipeline DK-R پس از تأیید ASSUMP-011 تا ASSUMP-014 پیاده‌سازی شود؛
- batch DK-R با وضعیت `blocked` باقی بماند؛
- کد رسمی یا توضیح تکمیلی نویسندگان برای فرمول batch جست‌وجو شود؛
- در نبود منبع، گزینه‌های فرمولی بعداً جداگانه برای تأیید ارائه شوند.

## 9. تصمیم موردنیاز از کاربر

برای ادامه پیاده‌سازی pipeline DK-R، تأیید ASSUMP-011 تا ASSUMP-014 و تأیید تعویق batch DK-R لازم است. بدون این تأیید هیچ کدنویسی انجام نمی‌شود.

## 10. مرحله بعدی پیشنهادی

پس از تأیید: ابتدا ممیزی کوتاه مرجع pyeasyga [28] برای تثبیت تنظیمات ASSUMP-013؛ سپس پیاده‌سازی pipeline DK-R، آزمون‌های واحد و یکپارچه و مثال دستی/اجرایی. Batch DK-R تا یافتن فرمول pricing مستقل متوقف می‌ماند.
