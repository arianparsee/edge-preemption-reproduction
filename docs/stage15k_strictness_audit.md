# Stage 15-K — ممیزی سخت‌گیری‌های بازتولید

## دامنه و وضعیت

- منبع مبنا: نسخه arXiv v2 سال 2024 مقاله.
- این سند فقط شواهد معتبر Stage 15-A تا Stage 15-J را تجمیع می‌کند؛ هیچ workload، policy، simulator یا workflow ابری اجرا نشده است.
- Pipeline رسمی و artifactهای Figure 6 دست‌نخورده‌اند؛ وضعیت رسمی Figure 6 همچنان **«بازتولید نشد»** است.
- initialization repair و offspring repair فقط `[آزمون کمکی]` هستند و به روش مقاله نسبت داده نمی‌شوند.

## کفایت و اعتبار شواهد موجود

| مؤلفه | وضعیت ممیزی | نتیجه |
| --- | --- | --- |
| baseline رسمی | 120/120 pair؛ checksum/config/workload/policy identity قبلاً اعتبارسنجی شده | کامل و reuse-only |
| repair تشخیصی | 120/120 pair؛ 100 جدید + 20 reuse؛ دو replay و checksum معتبر | کامل و reuse-only |
| Funnel baseline | Task ID، Utility map، event و final state موجود | طبقه‌بندی Task-level کامل ممکن است |
| Funnel repair | artifact عمومی عمداً فاقد Task ID، workload خام، event trace و final state است | شمارنده‌های lifecycle ممکن؛ تفکیک Utility علل نهایی ناممکن |
| Figure 6 | baseline رسمی حفظ شده است | «بازتولید نشد» |

نتیجه مهم محدودیت داده: برای repairها تعدادهای lifecycle و رابطه
`accepted = completed + preempted` قابل کنترل است، اما Utility ردشده را نمی‌توان بدون Task ID و Utility map به‌طور دقیق میان
`PRE_ADMISSION_INFEASIBLE` و `NEVER_ADMITTED_EXPIRED` تقسیم کرد. هیچ مقدار تخمینی جایگزین نشده است.

## Funnel معتبر baseline در ۳۰ workload

مقادیر زیر میانگین حسابی ۳۰ workload هستند. سهم Utility نسبت به کل Utility تولیدشده محاسبه شده است.

| Policy | Completed jobs | Completed Utility | Completed share | Preempted jobs | Preempted Utility | Pre-admission infeasible jobs | Pre-admission infeasible Utility | Never-admitted expired jobs | Never-admitted expired Utility | Never-admitted share | Accepted-then-expired |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| KG-R | 127.57 | 9,610.65 | 11.43% | 0.00 | 0.00 | 98.50 | 5,930.70 | 1,173.23 | 68,518.84 | 81.51% | 0 |
| KG-P | 138.43 | 11,473.24 | 13.65% | 21.57 | 1,202.91 | 98.50 | 5,930.70 | 1,140.80 | 65,453.34 | 77.86% | 0 |
| DK-R | 19.73 | 1,329.51 | 1.58% | 0.00 | 0.00 | 98.50 | 5,930.70 | 1,281.07 | 76,799.98 | 91.36% | 0 |
| DK-P | 43.27 | 3,607.44 | 4.29% | 11.37 | 787.68 | 98.50 | 5,930.70 | 1,246.17 | 73,734.37 | 87.72% | 0 |

میانگین Utility کل تولیدشده تقریباً `84,060.20` است. مقدار `PRE_ADMISSION_INFEASIBLE` در هر چهار baseline دقیقاً یکسان است: میانگین 98.5 وظیفه و 7.0553% Utility کل. بنابراین این gate بخشی از افت مطلق را توضیح می‌دهد، اما شکاف نسبی DK با KG را توضیح نمی‌دهد.

در baseline، DK-R پس از پذیرش completion/admission برابر 1 دارد و `ACCEPTED_THEN_EXPIRED = 0` است. برای DK-P نیز همه پذیرش‌ها یا completion شده‌اند یا مطابق lifecycle به preemption terminal رسیده‌اند. پس محدودیت‌های پس از پذیرش، مظنون اصلی شکاف DK نیستند.

## شواهد Round 1 و Round 2

| Policy | Round-1 no-server rejection | Round-2 rejection | Retry | Accepted | Completed | Preempted | Completion/admission | GA repair burden | Completed Utility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| KG-R | 0.00 | 6,678.00 | 5,507.20 | 127.57 | 127.57 | 0.00 | 1.0000 | 844.97 | 9,610.65 |
| KG-P | 0.00 | 6,638.67 | 5,500.30 | 160.00 | 138.43 | 21.57 | 0.8652 | 860.00 | 11,473.24 |
| DK-R | 0.00 | 6,918.03 | 5,639.40 | 19.73 | 19.73 | 0.00 | 1.0000 | 964.37 | 1,329.51 |
| DK-P | 0.00 | 6,851.77 | 5,608.03 | 54.63 | 43.27 | 11.37 | 0.7919 | 947.90 | 3,607.44 |

در single-seed instrumentation معتبر Stage 15-B/15-C:

- DK-R Round 2: مجموع 3,389 بیت منتخب در بهترین chromosomeهای خام به 24 بیت پس از کنترل feasibility کاهش یافت؛ 24 پذیرش/تکمیل و 6,759 rejection ثبت شد.
- DK-P Round 2: 3,620 بیت خام به 168 بیت پس از feasibility رسید؛ 46 پذیرش، 40 completion و 6 preemption ثبت شد.
- نرخ فراخوانی‌های نیازمند repair در نمونه Stage 15-B برای DK-R Round 2 برابر 95.50% و برای DK-P Round 2 برابر 81.25% بود.

این شواهد ثابت می‌کنند bottleneck مشاهده‌شده در پیاده‌سازی فعلی در مسیر selection/feasibility پیش از پذیرش قرار دارد؛ اما بدون کد نویسندگان، encoding واقعی و روش constraint handling نمی‌توان ثابت کرد که این تفاوت علت قطعی اختلاف با مقاله است.

## نتیجه repairهای تشخیصی ۳۰-seed

| مقایسه paired | میانگین افزایش Completed Utility | 95% CI `[آزمون کمکی]` | جهت اثر |
| --- | ---: | ---: | --- |
| DK-R initialization − baseline | +9,040.46 | [8,645.02, 9,435.91] | 30 مثبت / 0 صفر / 0 منفی |
| DK-R offspring − baseline | +9,142.79 | [8,756.93, 9,528.65] | 30 / 0 / 0 |
| DK-P initialization − baseline | +5,772.82 | [5,417.91, 6,127.72] | 30 / 0 / 0 |
| DK-P offspring − baseline | +5,839.55 | [5,479.19, 6,199.92] | 30 / 0 / 0 |

هر دو repair در ۳۰/۳۰ seed اثر مثبت داشتند. این نتیجه فقط `[آزمون کمکی]` است. offspring نسبت به initialization برای DK-R به‌طور میانگین `+102.33` و برای DK-P `+66.74` Utility داشت، اما جهت این برتری فقط در 18/30 seed مثبت بود و CI اختلاف DK-P صفر را قطع می‌کند؛ پس برتری offspring پایدار تلقی نمی‌شود.

میانگین Completed Utility repaired:

- DK-R initialization: 10,369.97؛ DK-R offspring: 10,472.30.
- DK-P initialization: 9,380.26؛ DK-P offspring: 9,447.00.
- برای مقایسه reuse-only: KG-R برابر 9,610.65 و KG-P برابر 11,473.24 است.

repairها DK-R را از KG-R بالاتر، ولی از KG-P پایین‌تر بردند؛ DK-P repaired همچنان از هر دو KG baseline پایین‌تر ماند.

## ممیزی منشأ قواعد

ماتریس کامل قابل‌ماشین‌خواندن در `results/aggregated/stage15k/strictness_matrix.csv` است. جمع‌بندی مهم:

1. **GA encoding/constraint handling:** جزئیات دقیق DK در arXiv v2 چاپ نشده است `[نامشخص]`. رفتار fitness صفر برای chromosome ناممکن و guard نهایی ASSUMP-042 `[فرض بازتولید]` است. این قوی‌ترین مظنون سخت‌گیری است.
2. **delete-only repair:** فقط ابزار تشخیصی `[پیشنهاد فنی]` است؛ در pipeline رسمی وجود ندارد. اثر مثبت پایدار آن نشان می‌دهد feasibility گلوگاه است، نه اینکه repair واقعی مقاله همین بوده است.
3. **canonical admission و dry-run:** فرمول minimum resource در v2 چاپ نشده؛ پیاده‌سازی دقیق `[فرض بازتولید]` است. بااین‌حال gate آن میان policyها یکسان و فقط 7.06% Utility کل است، بنابراین اولویت آن از Round-2 پایین‌تر است.
4. **activation delay:** مثال صریح Section III می‌گوید ورود در epoch 2، bidding در epoch 3 و processing در epoch 4 رخ می‌دهد. قاعده فعلی با این مثال سازگار است و شواهدی از سخت‌گیری اضافه نداریم.
5. **شروع سه‌مرحله‌ای و تقدم نسبتی:** از قیود (23)، (25)، (27) و روابط تقدم نسبتی استخراج می‌شوند؛ تغییرشان ریسک فاصله‌گرفتن از مدل مقاله دارد.
6. **`output_size = input_storage`:** در مقاله مقدار `s'_j` تعریف عددی/توزیعی کافی ندارد؛ این قاعده `[فرض بازتولید]` و نامطمئن است، اما Funnel فعلی آن را علت اصلی نشان نمی‌دهد.
7. **retry و preemption terminal:** تصمیم‌های lifecycle `[فرض بازتولید]` هستند؛ شواهد موجود نشان می‌دهد افت غالب قبل از پذیرش رخ داده است.
8. **pricing/server selection:** اصل min-price و رد قیمت بالاتر از Utility صریح است، ولی scaling دقیق pricing در DK تا حدی فرضی است. چون سرور منتخب ظرفیت Round 2 را تعیین می‌کند، این مسیر مظنون درجه دوم است؛ قبل از counterfactual بهتر است instrumentation غیرمداخله‌ای قیمت انجام شود.

## نگاشت محل افت Utility

| محل | قواعد مؤثر | وضعیت علت‌یابی |
| --- | --- | --- |
| پیش از Round 1 | canonicalization و isolated dry-run | افت مطلق ثابت 7.06% Utility؛ علت شکاف DK/KG نیست |
| Round 1 | encoding/fitness/constraint handling GA | مظنون؛ R1 no-server rejection صفر است، اما انتخاب قیمت و سرور را شکل می‌دهد |
| Pricing/server choice | threshold، violation scaling، min-price | مظنون درجه دوم؛ causal evidence مستقیم کافی نیست |
| Round 2 | GA feasibility، membership/repack semantics، final guard | قوی‌ترین محل اثبات‌شده گلوگاه در پیاده‌سازی فعلی |
| پس از Admission | activation، pipeline stages، proportional precedence، output size | علت اصلی پشتیبانی نمی‌شود؛ accepted-then-expired صفر است |
| Retry/Expiration | یک retry در epoch، feasibility-to-deadline | اتلاف را زمان‌بندی می‌کند؛ غالب وظایف نهایتاً never-admitted expired می‌شوند |
| Preemption | terminal/no retry | فقط DK-P/KG-P؛ سهم کوچک‌تر از never-admitted loss |

## تفکیک «محل» از «علت قطعی»

- **محل غالب اتلاف در پیاده‌سازی بازتولید شناسایی شد:** مسیر Round 2 و عدم پذیرش؛ DK-R و DK-P به‌ترتیب 91.36% و 87.72% Utility کل را در `NEVER_ADMITTED_EXPIRED` از دست می‌دهند.
- **علت قطعی اختلاف با مقاله اثبات نشد:** کد رسمی نویسندگان، encoding واقعی DK، روش constraint handling/repair، و جزئیات GA منتشر نشده‌اند.

## اولویت اصلاحات کنترل‌شده

1. R2-only initialization feasibility repair؛ کم‌هزینه‌ترین pilot تک‌عاملی و توصیه اصلی.
2. R2-only offspring repair؛ جایگزین مستقل، نه ترکیبی؛ intervention بسیار بیشتری دارد.
3. مشاهده‌گر غیرمداخله‌ای pricing/server steering؛ پیش‌نیاز بهتر برای هر اصلاح قیمت.
4. حذف فقط isolated dry-run gate؛ ریسک متوسط/بالا و شواهد ضعیف‌تر.
5. same-epoch bidding یا کاهش stage lag؛ ریسک بالا، چون با مثال/قیود مقاله در تنش است.
6. تغییر output size؛ تا یافتن منبع یا sensitivity از پیش‌ثبت‌شده، blocked.

جزئیات گزینه‌ها، معیار رد فرضیه و هزینه pilot در `docs/stage15k_candidate_corrections.md` و `results/aggregated/stage15k/pilot_plan.csv` آمده است.

## نتیجه ممیزی

محتمل‌ترین محل افت نتایج، feasibility و constraint handling کوله‌پشتی DK در Round 2 است. سخت‌گیری exact GA behavior، final feasibility guard و canonical dry-run از متن مقاله صریح نیستند؛ اما فقط دو مورد اول شواهد قوی برای توضیح شکاف DK/KG دارند. activation delay و pipeline precedence با متن/فرمول‌های v2 پشتیبانی می‌شوند و فعلاً نباید به‌عنوان علت اصلی دستکاری شوند.
