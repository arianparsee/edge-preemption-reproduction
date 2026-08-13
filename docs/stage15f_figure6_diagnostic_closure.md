# Stage 15-F — جمع‌بندی و خاتمه تحلیل تشخیصی Figure 6

## 1. دامنه و تصمیم خاتمه

- منبع مبنا همچنان arXiv:2403.15665v2 (2024) است.
- در Stage 15-F هیچ workload، baseline، repair یا policy اجرا نشد.
- pipeline رسمی DK، artifactهای Stage 14-A و نتیجه رسمی Figure 6 تغییر نکردند.
- وضعیت نهایی Figure 6 همچنان **«بازتولید نشد»** است.
- اجرای 30-workload repair، ترکیب repairها و پذیرش repair به‌عنوان روش اصلاح‌شده انجام نشد.
- initialization repair و offspring repair فقط `[آزمون کمکی]` هستند و روش مقاله محسوب نمی‌شوند.

کنترل SHA-256 نشان داد پنج artifact علمی Stage 14-A شامل CSV/PNG/PDF دقیقاً byte-identical
باقی مانده‌اند. hash تاریخی `docs/stage14a_figure6.md` پیش از commit با CRLF ثبت شده بود، درحالی‌که
`.gitattributes` مخزن نسخه LF را نگهداری می‌کند؛ ممیزی این فایل فقط با normalization شفاف line-ending
انجام شد و محتوا با نسخه ثبت‌شده یکسان است. این استثنا به داده یا شکل علمی تعمیم داده نشد.

## 2. زنجیره شواهد Stage 15-A تا Stage 15-E

| مرحله | نوع شاهد | یافته اصلی | مرز استنباط |
|---|---|---|---|
| 15-A | تحلیل observational روی 30 workload معتبر Figure 6 | افت DK پیش از activation و عمدتاً در انتخاب/پذیرش Round 2 متمرکز است؛ canonicalization میان policyها خنثی و completion پس از پذیرش DK-R کامل بود | محل افت را نشان می‌دهد، نه علت الگوریتمی آن را |
| 15-B | instrumentation غیرمداخله‌ای GA، تک-seed | repair/GA-call برای DK-R در R1 برابر 97.90% و در R2 برابر 95.50%؛ برای DK-P به‌ترتیب 97.57% و 81.25% بود | فشار feasibility/repair را کمی می‌کند، اما encoding، fitness و repair را از هم جدا نمی‌کند |
| 15-C | funnel غیرمداخله‌ای chromosome تا lifecycle، تک-seed | raw-best تقریباً نیمی از candidate-entryها را انتخاب می‌کرد، ولی پس از repair در R1 فقط 16 ورودی DK-R و 22 ورودی DK-P باقی ماند؛ در R2، DK-R از 3389 انتخاب خام به 24 خروجی رسید | فروپاشی خروجی در مرز feasibility/repair را نشان می‌دهد؛ repair فعلی یک بازسازی است، نه کد نویسندگان |
| 15-D | counterfactualهای مستقل، تک-seed | fixed penalty اثر outcome-level نداشت؛ initialization repair و offspring repair completed Utility را برای هر دو DK به‌شدت افزایش دادند | تغییر رفتار الگوریتمی و فقط `[آزمون کمکی]`؛ رابطه علی کامل میان initialization و offspring جدا نشده است |
| 15-E | paired validation روی پنج seed | جهت اثر completed Utility هر دو repair برای DK-R و DK-P در 5/5 seed مثبت بود | پایداری جهت را تقویت می‌کند، ولی 30-workload نیست و روش مقاله را اصلاح نمی‌کند |

### شواهد lifecycle

- `[استخراج مستقیم]` در Stage 15-A، میانگین پذیرش DK-R برابر 19.733 و DK-P برابر 54.633 بود، درحالی‌که رد Round 2 به‌ترتیب 6918.033 و 6851.767 بود.
- `[استخراج مستقیم]` retry و expiration پیامد نزدیکِ عدم پذیرش مکرر بودند؛ آن‌ها مظنون ریشه‌ای مستقل نیستند.
- `[استخراج مستقیم]` برای DK-R نسبت completion/admission برابر یک بود؛ بنابراین pipeline progress پس از activation علت افت DK-R نیست.
- `[استخراج مستقیم]` برای DK-P فاصله admission تا completion با preemption terminal توضیح داده می‌شود، اما admission پایین‌تر همچنان گلوگاه غالب است.

### شواهد counterfactual پنج-seed

| Policy | Repair | میانگین Δ Completed | میانگین Δ Completed Utility | جهت Utility |
|---|---|---:|---:|---:|
| DK-R | initialization | +116.8 | +9336.24 | مثبت در 5/5 seed |
| DK-R | offspring | +118.2 | +9397.59 | مثبت در 5/5 seed |
| DK-P | initialization | +83.8 | +6469.48 | مثبت در 5/5 seed |
| DK-P | offspring | +83.0 | +6353.40 | مثبت در 5/5 seed |

این اعداد `[آزمون کمکی]` هستند. نه artifact رسمی Figure 6 را تغییر می‌دهند و نه به‌عنوان نتیجه روش مقاله گزارش می‌شوند.

## 3. نتیجه علت‌یابی

`[استخراج مستقیم از مجموعه آزمون‌های کمکی]` قوی‌ترین مظنون اختلاف، **feasibility ضعیف chromosomeهای GA در بازسازی فعلی Pipeline DK و فروپاشی شدید خروجی در مرز repair** است. ترتیب شواهد عبارت است از:

1. افت قبل از activation رخ می‌دهد؛
2. فشار repair در هر دو round بسیار بالاست؛
3. raw-best پرعضو به subset بسیار کوچک یا تهی تبدیل می‌شود؛
4. تغییر penalty به‌تنهایی outcome را بهبود نمی‌دهد؛
5. دو repair feasibility-aware مستقل در پنج seed اثر مثبت پایدار دارند.

بااین‌حال، وضعیت علت نهایی **`[نامشخص]`** باقی می‌ماند. این شواهد نمی‌توانند مشخص کنند که اختلاف ناشی از نبود repair رسمی، تفاوت encoding، تفاوت fitness/penalty، customization نویسندگان روی pyeasyga، یا خطای بازسازی ما در جزئیات گزارش‌نشده است. بنابراین این نتیجه نباید به‌عنوان خطا در مقاله یا اثبات repair خاصی نسبت داده شود.

## 4. اطلاعات مفقود برای حل قطعی اختلاف

موارد زیر از منابع مبنای موجود قابل تعیین نیستند:

- کد رسمی نویسندگان و commit/tag دقیق اجرای Figure 6؛
- تعریف دقیق chromosome و ترتیب نگاشت بیت‌ها به taskها در Round 1 و Round 2؛
- روش رسمی برخورد با chromosome ناممکن و repair واقعی، در صورت وجود؛
- fitness دقیق برای حالت feasible، infeasible و empty و هر penalty یا constraint handling؛
- initialization واقعی population و هر preprocessing روی candidate pool؛
- نسخه دقیق pyeasyga یا fork/custom patch نویسندگان؛
- تنظیم کامل population، tournament، selection، crossover، mutation و elitism؛
- tie-breaking داخلی GA و tie-breaking بین serverها؛
- نحوه تبدیل خروجی GA به membership، price و پذیرش نهایی؛
- seedهای workload و policy/GA، ترتیب task/server و state دقیق RNG؛
- raw workloadهای 30 اجرا و جدول عددی پشت Figure 6؛
- تعداد تکرار و aggregation واقعی مقاله؛
- logging میانی author run برای candidate count، feasibility، repair و Round-2 admission.

دسترسی به کد نویسندگان همراه با حداقل یک workload و seed Figure 6 نزدیک‌ترین مسیر برای تشخیص قطعی است. بدون آن، هر repair انتخابی یک روش جدید/کمکی خواهد بود.

## 5. ممیزی شکل‌ها و آزمایش‌های باقی‌مانده

| هدف | وضعیت رسمی | مسدودکننده اصلی | نزدیک‌ترین قابلیت موجود |
|---|---|---|---|
| Figs.1–2 | شکل مفهومی؛ آزمایش نیست | trace نمونه و layout دقیق شکل 2 کامل نیست | مدل حالت و pipeline پیاده‌سازی و آزمون شده‌اند؛ بازطراحی فنی ممکن است |
| Figs.3–5 / R1-DIAG | رسمی مسدود | seed و horizon اصلی، workload دقیق و تطبیق Job 532/540 مفقود | Fig.3 به‌صورت `[آزمون کمکی]` روی workload مصوب موجود قابل instrumentation است |
| Fig.6 / PIPE-NORMAL | اجرا و ثبت شد؛ **بازتولید نشد** | جزئیات رسمی DK/GA و داده پشت شکل | تحلیل تشخیصی 15-A تا 15-F خاتمه یافت |
| Figs.7–8 | مسدود | `NORMAL_HIGH_LOW_THRESHOLDS` گزارش نشده است | raw outcomeهای 30 workload موجودند، ولی تقسیم high/low مجاز نیست |
| Figs.9–10 | مسدود | auction-time clock semantics، slot duration و threshold high-value نامشخص | موتور بدون auction-time موجود است |
| Figs.11–12 | مسدود | Batch DK-R success-count pricing و batch/time simulator مفقود | مولد Normal و Pipeline DK-R موجودند، اما جایگزین Batch نیستند |
| Figs.13–15 | مسدود | Batch DK-R، batch lifecycle و run control مفقود | مولد Bimodal کمکی مصوب و آزمون‌شده است |
| Figs.16–18 | مسیر رسمی مسدود | raw Southampton trace، schema، سه تاریخ دقیق، priority mapping و bins مفقود | surrogate raster فقط بازتولید کیفی/فنی است |
| Figs.19–20 | مسدود | raw trace، preprocessing رسمی، batch semantics و در Fig.20 DK-R | surrogate نباید برای نتیجه عددی استفاده شود |
| OPT-10/18/25 | مسدود | instanceهای دقیق، subsetها، Gurobi settings و داده ورودی مفقود؛ Gurobi فعلاً نصب نشده | مدل ریاضی و کنترل‌های feasibility موجودند؛ exact solver فقط ابزار کمکی آزمون است |

### نتیجه ممیزی

هیچ آزمایش ارزیابی رسمی باقی‌مانده در وضعیت «کاملاً غیرمسدود» نیست. بااین‌حال، نزدیک‌ترین
**شکل مقاله که واقعاً غیرمسدود است Figure 1**، یعنی نمودار مفهومی epoch/job-set و گردش
arrival/bidding/processing است. این شکل داده تجربی، workload یا seed نمی‌خواهد و مدل لازم آن در
Stage 2 و موتور زمانی Stage 13-D بازسازی شده است. نزدیک‌ترین هدف **ارزیابی‌مانند** قابل‌اجرا نیز
R1-DIAG-AUX برای بخش histogram شکل 3 است؛ اما باید صریحاً `[آزمون کمکی]` بماند و بازتولید Fig.3
معرفی نشود.

## 6. پیشنهاد مرحله بعد، بدون اجرا

### گزینه A پیشنهادی: Stage 15-G — بازسازی مفهومی Figure 1

دامنه پیشنهادی:

- بازطراحی وفادار نمودار epoch/job-set از خود arXiv v2؛
- نگاشت اجزا و transitionها به مدل سیستم تأییدشده؛
- خروجی SVG/PDF/PNG و specification متنی؛
- بدون workload، seed، اجرای policy یا نتیجه عددی؛
- مقایسه ساختاری با شکل مقاله، نه ادعای بازتولید آزمایشی.

داده و اطلاعات موردنیاز:

1. تصویر و caption Figure 1 از arXiv v2 که هم‌اکنون در منابع پروژه موجود است؛
2. مدل epoch و حالت‌های task استخراج‌شده در Stage 2؛
3. convention بصری برای رنگ/فونت در صورتی که از raster مقاله دقیقاً قابل تعیین نباشد؛ این بخش
   `[پیشنهاد فنی]` خواهد بود.

این گزینه نزدیک‌ترین هدف واقعاً غیرمسدود و پیشنهاد اصلی است.

### گزینه B بعدی: R1-DIAG-AUX نزدیک Figure 3

دامنه پیشنهادی:

- فقط KG-P و فقط یک workload موجود از فهرست مصوب ASSUMP-033؛
- ترجیحاً reuse workload ذخیره‌شده، بدون تولید مجدد؛
- مشاهده غیرمداخله‌ای تمام قیمت‌ها/discountهای Round 1 برای Server 5 در epoch 43؛
- تولید histogram، CSV پشت شکل و fingerprint عدم مداخله؛
- عدم ادعای تطبیق Job 532/540 یا بازتولید رسمی Figs.3–5؛
- عدم تغییر seed، GA، pricing، lifecycle یا policy.

داده و تصمیم لازم پیش از اجرا:

1. تأیید اینکه هدف فقط `[آزمون کمکی]` نزدیک Fig.3 است؛
2. تأیید reuse اولین workload مصوب ASSUMP-033 و عدم ادعای seed مقاله؛
3. تعیین اینکه discount به‌صورت `utility - price`، نسبت آن به Utility، یا هر دو ذخیره شود؛ مقاله محور شکل را باید مبنای انتخاب نهایی قرار دهد؛
4. تأیید عدم تعمیم Job IDهای محلی به Job 532/540 مقاله؛
5. تعیین تعداد/لبه binها از خود شکل یا ثبت آن‌ها به‌عنوان `[مقادیر تقریبی خوانده‌شده از شکل]`، جدا از داده شبیه‌سازی.

تا دریافت تصمیم کاربر میان گزینه A و B، Stage 15-G اجرا نمی‌شود.
