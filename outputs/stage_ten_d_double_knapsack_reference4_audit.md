# مرحله دهم-D: تطبیق Double Knapsack با مرجع مستقیم [4]

## 1. کارهای انجام‌شده

- هویت، تمامیت و هش `4.pdf` دوباره کنترل شد.
- صفحات PDF 4 تا 6 و 8 مرجع [4] و صفحات 6 و 8 arXiv v2 هم به‌صورت متنی و هم تصویری بررسی شدند.
- Round 1، Round 2، هدف knapsack، ورودی/خروجی، قیمت‌گذاری، پذیرش، Retention، ترتیب، تنظیمات GA و tie-breaking تطبیق داده شدند.
- اطلاعاتی که فقط در [4] آمده‌اند با برچسب `[استخراج از مرجع مستقیم مقاله]` و صفحه/بخش ثبت شدند.
- کفایت منابع برای پیاده‌سازی وفادار DK-R ارزیابی شد. نتیجه: اطلاعات هنوز کافی نیست و کدنویسی طبق دستور کاربر متوقف شد.

## 2. هویت و تمامیت منبع [4]

| مؤلفه | نتیجه |
| --- | --- |
| عنوان | *Online Resource Allocation in Edge Computing Using Distributed Bidding Approaches* |
| نویسندگان | Caroline Rublein، Fidan Mehmeti، Mark Towers، Sebastian Stein، Thomas F. La Porta |
| محل انتشار | IEEE MASS 2021 |
| DOI | `10.1109/MASS52906.2021.00038` |
| تعداد صفحات فایل | 9 |
| رمزگذاری/خرابی | رمزگذاری نشده؛ هر 9 صفحه قابل استخراج و render است |
| SHA-256 | `C7ACD2298E56B408A9659599F98144FD809B32631EEC94B835B7E5CF4DB2FE7D` |
| تطبیق با فهرست v2 | عنوان و نویسندگان و سال با مرجع [4] arXiv v2 منطبق است |

نتیجه: `4.pdf` نسخه کامل مقاله مرجع مستقیم [4] است، نه فایل تکمیلی arXiv v2. منبع مبنا همچنان `arXiv:2403.15665v2` است.

## 3. تطبیق مؤلفه‌های Double Knapsack

| مؤلفه | arXiv v2 | مرجع [4] | نتیجه ردیابی |
| --- | --- | --- | --- |
| ساختار مزایده | `[صریح در مقاله]` Section V-A، PDF p.6: در روش پیشین، serverها در هر دو round از knapsack استفاده می‌کنند. | `[استخراج از مرجع مستقیم مقاله]` Section II، PDF p.2: jobهای epoch قبل در مزایده دو دور شرکت می‌کنند؛ پس از R1 کمترین قیمت را انتخاب می‌کنند. | سازگار |
| Round 1 pool | `[صریح در مقاله]` Section V-A1، PDF p.6: درخواست‌های هر server در برابر residual space سنجیده می‌شوند. | `[استخراج از مرجع مستقیم مقاله]` Section IV-A2، PDF p.4 (printed p.228): knapsack روی همه jobهای ارسال‌شده به همان server اجرا می‌شود. | سازگار |
| Round 1 objective | `[صریح در مقاله]` Section V-A، PDF p.6 فقط «which jobs could fit» را می‌گوید و تابع هدف DK را چاپ نمی‌کند. | `[استخراج از مرجع مستقیم مقاله]` Section IV-C، PDF p.4 (printed p.228): در Case 3، R1 utility فضای باقی‌مانده را به‌جای تعداد jobها بیشینه می‌کند. | هدف کیفی روشن؛ فرمول اجرایی fitness چاپ نشده است |
| Round 1 pricing | `[صریح در مقاله]` Section V-A، PDF p.6: عضوهای knapsack قیمت پایین می‌گیرند؛ فرمول DK چاپ نشده است. | `[استخراج از مرجع مستقیم مقاله]` Algorithm 1، PDF p.5 (printed p.229): عضو `U-αU`؛ غیرعضوِ «Under threshold» برابر `U-min(1/violation(Eq.11), α/2)U`؛ در غیر این صورت `U+βU`. | فرمول موجود، ولی threshold و چند پارامتر اجرایی نامشخص‌اند |
| انتخاب server | `[صریح در مقاله]` Section III، PDF p.3: job یک offer قابل‌قبول را انتخاب می‌کند؛ نمونه v2 در PDF p.7 برای دو قیمت fit مساوی انتخاب تصادفی نشان می‌دهد. | `[استخراج از مرجع مستقیم مقاله]` Sections II و IV-A1، PDF pp.2 و 4: client کمترین قیمت را انتخاب می‌کند و در Case 2/3 به price بالاتر از Utility پاسخ نمی‌دهد. | قاعده کمینه روشن؛ tie عمومی مشخص نیست |
| Round 2 pool | `[صریح در مقاله]` Section V-A، PDF p.6: jobهایی که در R2 بازگشته‌اند. | `[استخراج از مرجع مستقیم مقاله]` Section IV-A2، PDF p.4: فقط jobهایی که آن server را انتخاب کرده‌اند وارد knapsack دوم می‌شوند. | سازگار |
| Round 2 capacity و Retention | `[استخراج مستقیم]` از Sections V-A و V-B، PDF pp.6 و 8: چون DK-P فقط R2 را به total capacity و current+returning تغییر می‌دهد، DK-R باید current jobs را نگه دارد و returningها را روی residual بررسی کند. | `[استخراج از مرجع مستقیم مقاله]` Section IV-A1/A2، PDF p.4: R2 returning jobs را برای fit می‌سنجد و preemption تعریف نشده است. | Retention و residual قابل استخراج‌اند |
| Round 2 objective | `[نامشخص]` v2 هدف DK-R R2 را چاپ نمی‌کند. | `[نامشخص]` Section IV-C فقط صریحاً می‌گوید **R1** utility را بیشینه می‌کند؛ Section IV-A2 درباره R2 فقط «another knapsack» می‌گوید. | مسدودکننده |
| Round 2 output | `[صریح در مقاله]` Section V-A، PDF p.6: admissionهای server. | `[استخراج از مرجع مستقیم مقاله]` Algorithm 1، PDF p.5: عضو پذیرفته و قیمت `U-U/violation(Eq.11)` می‌گیرد؛ غیرعضو به pool می‌رود. | روشن، جزئیات retry آینده نامشخص |
| ترتیب پردازش | `[نامشخص]` برای DK-R ترتیب sequential چاپ نشده است. | `[استخراج از مرجع مستقیم مقاله]` Section IV-A2 و Algorithm 1: پذیرش تابع membership خروجی knapsack است، نه sort ترتیبی؛ ترتیب داخلی GA ارائه نشده است. | ترتیب بیرونی لازم نیست؛ رفتار subsetهای هم‌ارزش نامشخص است |
| GA | `[صریح در مقاله]` Section V-A3، PDF p.7: برای KG، `pyeasyga` و حدود 30 generation ذکر می‌شود؛ footnote علت کم‌بودن را موقتی‌بودن تصمیم R1 می‌داند. | `[استخراج از مرجع مستقیم مقاله]` Section IV-C، PDF p.4: GA آماده با `g≈50` و پیچیدگی `O(n^g)`؛ نام کتابخانه، population، selection، crossover، mutation، seed و termination دقیق چاپ نشده‌اند. | 50 generation نزدیک‌ترین عدد برای DK است؛ سایر تنظیمات مسدودکننده‌اند |
| Batch DK-R | `[صریح در مقاله]` Section VI-B و شکل‌های 11 تا 15: DK-R در آزمایش‌های batch استفاده شده است. | `[استخراج از مرجع مستقیم مقاله]` Section VI-B، PDF p.8 (printed p.232): knapsack برای هر timestep تا بیشینه deadline اجرا می‌شود و discount بر تعداد timestepهای موفق مبتنی است؛ فرمول discount/normalization چاپ نشده است. | مسدودکننده مستقل |
| Tie-breaking | `[نامشخص]` قاعده عمومی برای قیمت مساوی یا subset هم‌ارزش ندارد. | `[نامشخص]` هیچ tie-breaking برای client یا GA تعریف نشده است. | مسدودکننده بازتولید قطعی |

## 4. قیمت‌گذاری استخراج‌شده از [4]

### Pipeline، Case 3

`[استخراج از مرجع مستقیم مقاله]` Section IV-C و Algorithm 1، PDF pp.4-5 (printed pp.228-229):

```text
R1, selected:      price = U - alpha * U
R1, not selected,
    under threshold:
                   price = U - min(1 / violation(Eq. 11), alpha / 2) * U
R1, otherwise:     price = U + beta * U

R2, selected:      price = U - (1 / violation(Eq. 11)) * U
R2, not selected:  go to pool
```

`[استخراج از مرجع مستقیم مقاله]` Section V-D، PDF p.6 (printed p.230): ارزیابی Case 3 مقدار `α=10%` را انتخاب می‌کند، چون در workload همان مقاله بیشترین utility صادقانه را تکمیل کرده است.

`[نامشخص]` عبارت `Under threshold` در Algorithm 1 تنها بار استفاده شده و هیچ تعریف یا مقدار عددی در [4] ندارد. `β` فقط «هر ثابت مثبت» معرفی شده است. Eq. (11) نیز سه بعد storage، computation و bandwidth دارد، درحالی‌که v2 upload و download را دو بعد جداگانه مدل می‌کند.

### Batch، Case 3

`[استخراج از مرجع مستقیم مقاله]` Section VI-B، PDF p.8: congestion/violation برای discount استفاده نمی‌شود؛ تعداد timestepهایی که job در knapsack موفق است مبنا قرار می‌گیرد. هیچ معادله‌ای برای تبدیل success count به price، مخرج normalization یا قیمت عدم‌موفقیت چاپ نشده است.

## 5. ابهام‌های مسدودکننده و اثر آن‌ها

| شناسه موقت | محل دقیق | اطلاعات مفقود | اثر بر پیاده‌سازی |
| --- | --- | --- | --- |
| DK-GAP-01 | [4] Section IV-C، PDF p.4؛ v2 Section V-A، PDF p.6 | آیا objective کوله‌پشتی R2 در Case 3 تعداد job است یا مجموع Utility؟ | membership، admission، Utility تکمیل‌شده و همه شکل‌های DK-R تغییر می‌کنند. |
| DK-GAP-02 | [4] Algorithm 1، PDF p.5 | تعریف `Under threshold` و مقدار اجرایی `β` | تعیین می‌کند job غیرعضو کدام server را انتخاب کند یا اصلاً بازگردد. |
| DK-GAP-03 | [4] Eq. (11)، PDF p.4 در برابر مدل چهاربعدی v2 Sections III-IV | روش تبدیل violation سه‌بعدی به Storage/Computation/Upload/Download و مقدار `f` در workloadهای v2 | تمام priceهای nonmember و انتخاب server ممکن است عوض شوند. |
| DK-GAP-04 | [4] Section IV-C، PDF p.4؛ v2 Section V-A3، PDF p.7 | GA: فقط 50 generation برای [4] و 30 برای KG-v2؛ سایر hyperparameterها و seed غایب‌اند | subset خروجی، tieها، زمان اجرا و قابلیت تکرار دقیق تعیین‌پذیر نیست. |
| DK-GAP-05 | [4] Section VI-B، PDF p.8 | فرمول قیمت batch برحسب success count | نسخه DK-R مورد استفاده در آزمایش‌های batch قابل بازسازی وفادار نیست. |
| DK-GAP-06 | [4] Sections II/IV و v2 نمونه PDF p.7 | tie-breaking قیمت مساوی و solutionهای هم‌ارزش GA | اجرای تکراری ممکن است server یا subset متفاوتی انتخاب کند. |

## 6. گزینه‌های حل و نزدیک‌ترین مسیر به منابع

### گزینه A — ممیزی هدفمند مرجع مستقیم [1]، سپس تصمیم‌گیری

`[پیشنهاد فنی؛ نزدیک‌ترین گزینه به اصل وفاداری]` پیش از ساخت هر فرض، `1.pdf` فقط برای DK-GAP-01 تا DK-GAP-06 بررسی شود. v2 در Section V-A مستقیماً [1] را به‌عنوان کار بینابینی که Round 2 knapsack را نگه داشته ارجاع می‌دهد و این فایل از قبل در اختیار پروژه است. اگر [1] جزئیات را پر کند، تعداد فرض‌های لازم کم می‌شود.

### گزینه B — پیاده‌سازی pipeline با فرض‌های صریح

`[پیشنهاد فنی؛ نیازمند تأیید کاربر]` اگر [1] شکاف‌ها را پر نکرد:

1. R1 و R2 هر دو `sum(utility)` را روی residual چهاربعدی بیشینه کنند.
2. Case 3 و `α=0.1` استفاده شود.
3. Eq. (11) با افزودن upload و download به‌طور چهاربعدی تعمیم داده شود.
4. `Under threshold` به معنی fit روی total capacity تفسیر و شاخه ناممکن با sentinel تصویب‌شده ASSUMP-007 اجرا شود.
5. پیاده‌سازی GA با 50 generation و تمام تنظیمات/seedهای انتخابی جداگانه به‌عنوان `[فرض بازتولید]` ثبت شود؛ exact selector فقط `[ابزار کمکی]` آزمون باشد.
6. tieهای client به‌صورت random بذرپذیر حل شوند؛ tieهای exact test fail-fast بمانند.
7. batch تا تعیین فرمول قیمت جداگانه مسدود بماند.

این بسته هنوز اعمال یا شماره‌گذاری نهایی نشده است.

### گزینه C — ساخت کنترل‌جریان با exact solver

`[پیشنهاد فنی]` می‌توان فوراً یک نسخه ساختاری deterministic با exact selector ساخت، اما این نسخه جایگزین رسمی GA مقاله نیست و نتیجه آن نباید «DK-R بازتولیدشده» نامیده شود. این گزینه از نظر وفاداری پایین‌تر از A و B است.

## 7. نتیجه کفایت

منابع `arXiv v2 + 4.pdf` برای تعریف معماری دو round، poolها، Retention و بخش عمده قیمت‌گذاری pipeline کافی‌اند، اما برای **پیاده‌سازی وفادار و بازتولیدپذیر کامل DK-R کافی نیستند**. DK-GAP-01 تا DK-GAP-06 مستقیماً بر membership، price، server choice و نتایج عددی اثر می‌گذارند. بنابراین هیچ کد، آزمون واحد/یکپارچه یا مثال اجرایی DK-R در این زیربخش ایجاد نشد.

## 8. فرمان‌های اجراشده و نتایج واقعی

```powershell
pdfinfo.exe tmp\pdfs\stage10d\reference4.pdf
pdfinfo.exe tmp\pdfs\stage10d\arxiv_v2.pdf
pdftoppm.exe -f 4 -l 6 -png -r 150 tmp\pdfs\stage10d\reference4.pdf ...
pdftoppm.exe -f 8 -l 8 -png -r 150 tmp\pdfs\stage10d\reference4.pdf ...
pdftoppm.exe -f 6 -l 6 -png -r 150 tmp\pdfs\stage10d\arxiv_v2.pdf ...
pdftoppm.exe -f 8 -l 8 -png -r 150 tmp\pdfs\stage10d\arxiv_v2.pdf ...
Get-FileHash ... -Algorithm SHA256
```

- `4.pdf`: 9 صفحه، بدون رمزگذاری، همه صفحه‌ها قابل render.
- arXiv v2: 13 صفحه، بدون رمزگذاری، صفحات تطبیقی قابل render.
- هش‌های فایل‌ها با ممیزی قبلی یکسان‌اند.
- render با هشدار فقدان display font برای `Symbol` و `ArialUnicode` پایان یافت؛ بازبینی تصویری نشان داد متن و فرمول‌های موردنیاز خوانا هستند.

## 9. آزمون‌ها و فرض‌ها

- آزمون کد DK-R: اجرا نشد، چون کدی ساخته نشد.
- آزمون رگرسیون موجود پروژه: `146 passed in 0.29s`.
- آزمون ناموفق: صفر.
- فرض جدید: صفر.
- ASSUMP-001 تا ASSUMP-010 تغییر نکردند و هیچ‌یک به DK-R تعمیم داده نشد.

## 10. تصمیم موردنیاز و مرحله بعد

تصمیم پیشنهادی: گزینه A، یعنی ممیزی هدفمند `1.pdf` برای شش شکاف بالا. پس از آن، فقط فرض‌هایی که همچنان لازم‌اند برای تأیید ارائه شوند و سپس پیاده‌سازی pipeline DK-R آغاز شود. قیمت‌گذاری batch باید مستقل ردیابی شود.
