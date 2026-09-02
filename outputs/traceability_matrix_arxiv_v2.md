# سند ردیابی مقاله تا کد

## مشخصات سند

- منبع مبنا: *Improved Methods of Task Assignment and Resource Allocation with Preemption in Edge Computing Systems*
- نسخه مبنا: `arXiv:2403.15665v2 [cs.DC]`
- تاریخ نسخه: 29 مارس 2024
- تصمیم کاربر: نسخه نهایی 2025 خارج از محدوده بازتولید است و نباید در استخراج الزامات استفاده شود.
- قاعده تکمیلی کاربر: نسخه IEEE 2025 فقط با برچسب `[منبع تکمیلی خارج از مبنای v2]` برای تحلیل ابهام مجاز است و داده آن نباید به v2 نسبت داده شود.
- وضعیت سند: مرحله 11-B کامل است؛ مرحله 12-A منبع/schema trace Southampton را ممیزی و preprocessing وفادار را تا دریافت raw/schema مسدود ثبت کرده است.
- هش PDF مبنا: `29E51E385E1C15C22B632A95273E83219500A82985B28BCBDE7B8EF3A0E32DBE`

## تاریخچه به‌روزرسانی

- 2026-08-08، مرحله اول: ایجاد ماتریس اولیه با 124 ردیف.
- 2026-08-08، مرحله دوم: افزودن ردیابی lifecycle، stateهای پیشنهادی و انتقال‌ها؛ هیچ فرض بازتولیدی تصویب نشد.
- 2026-08-08، مرحله سوم: افزودن نگاشت مستقل هر 31 رابطه مدل ریاضی به تابع و آزمون آینده؛ ناسازگاری‌های مدل بدون اعمال تفسیر اصلاحی ثبت شد.
- 2026-08-08، مرحله چهارم: تکمیل ردیابی خط‌به‌خط Algorithm 1 و 2، مرزبندی روش‌های KG/DK/Gurobi و ثبت تصمیم‌های مسدودکننده بدون اعمال فرض بازتولید.
- 2026-08-09، ممیزی منابع: هویت و کامل‌بودن فایل‌های ناشر مربوط به مراجع مستقیم [1] و [4] تأیید شد.
- 2026-08-09، مرحله پنجم: استخراج خانواده آزمایش‌ها، پارامترهای Normal/Bimodal/trace، تنظیمات زمانی، مشخصات تمام شکل‌ها و سنجش 55.3 درصدی پوشش وزنی پروتکل.
- 2026-08-09، مرحله ششم: تثبیت معماری `src`-layout، مرزبندی model/algorithm/simulation/data/evaluation، قرارداد fail-fast برای تصمیم‌های حل‌نشده و جداسازی اختیاری Gurobi.
- 2026-08-09، مرحله هفتم: ایجاد scaffold حداقلی و پیاده‌سازی 9 مؤلفه هسته مدل داده با 53 آزمون موفق؛ Gurobi طبق تصمیم کاربر نصب نشد.
- 2026-08-09، مرحله هشتم: پیاده‌سازی objective و validatorهای روابط (2)-(31)، Deadline/Utility/pricing، تخصیص و آزادسازی تراکنشی و invariantها؛ 105 آزمون موفق و هیچ semantics مبهمی default نشد.
- 2026-08-09، مرحله نهم: ثبت دو فرض تأییدشده، ساخت موتور scripted و event schema، اجرای سناریوی 2-server/4-task و تطبیق بدون اختلاف با محاسبه دستی.
- 2026-08-10، مرحله دهم-A: ثبت ASSUMP-003 تا ASSUMP-006 و پیاده‌سازی هسته congestion، شرط ۵٪، انتخاب تک‌قربانی و preemption اتمیک KnapsackGreedy.
- 2026-08-10، مرحله دهم-B: ثبت ASSUMP-007 تا ASSUMP-009، پیاده‌سازی دو دور KG-R، رابط مشترک policy، آزمون چندسروری و مثال دستی/اجرایی.
- 2026-08-10، مرحله دهم-C: ثبت ASSUMP-010 و پیاده‌سازی KG-P با victim snapshot ثابت، زمان منجمد، تک‌قربانی اتمیک و حفاظت پذیرش‌های دور جاری.
- 2026-08-10، مرحله دهم-D: تطبیق مستقیم `4.pdf` (مرجع [4]) با arXiv v2، استخراج Round 1/2 و قیمت‌گذاری Case 3 و ثبت ابهام‌های مسدودکننده؛ هیچ فرض یا کد DK-R افزوده نشد.
- 2026-08-10، مرحله دهم-E: ممیزی هدفمند `1.pdf`، رفع متنی هدف Utility در Round 2 و ثبت پنج شکاف باقی‌مانده و ASSUMP-011 تا ASSUMP-014 به‌صورت پیشنهادی و تأییدنشده؛ هیچ کد DK-R افزوده نشد.
- 2026-08-10، تصمیم مرحله دهم-F: کاربر ASSUMP-011، ASSUMP-012 و ASSUMP-014 را تصویب و ASSUMP-013 را مشروط به ممیزی کامل pyeasyga [28] تصویب کرد؛ Batch DK-R تا یافتن فرمول رسمی blocked شد.
- 2026-08-10، ممیزی مرحله دهم-F: pyeasyga 0.3.1 و تنظیمات source-level استخراج شد؛ تنها population size بین default عمومی 50 و مثال multidimensional با مقدار 200 نامعین ماند و ASSUMP-015 پیشنهاد شد؛ کدنویسی آغاز نشد.
- 2026-08-10، تصمیم مرحله دهم-G: ASSUMP-015 با population 200، tournament 20، generations 50 و seed اجباری تصویب شد؛ population 50 فقط sensitivity کمکی و Exact Solver فقط کمک‌آزمون باقی ماند.
- 2026-08-10، تکمیل مرحله دهم-G: Pipeline DK-R با pyeasyga 0.3.1، دو کوله‌پشتی مستقل، Retention، قیمت‌های Case 3، metadata کامل، آزمون seed ثابت و مقایسه Exact کمکی پیاده‌سازی و اجرا شد.
- 2026-08-10، مرحله دهم-H: متن DK-P در v2 صفحه 8 با صفحات مرتبط [1] و [4] و نسخه نهایی IEEE 2025 تطبیق داده شد؛ چهار شکاف اجرایی ASSUMP-016 تا ASSUMP-019 به‌صورت پیشنهادی و تأییدنشده ثبت شدند و هیچ کد DK-P نوشته نشد.
- 2026-08-10، تصمیم مرحله دهم-I: کاربر ASSUMP-016 تا ASSUMP-019 را دقیقاً با متن پیشنهادی تصویب کرد؛ مجوز پیاده‌سازی Pipeline DK-P صادر شد.
- 2026-08-10، تکمیل مرحله دهم-I: Pipeline DK-P با repack اتمیک، score لفظی، چند preemption، GA رسمی، عدم قیمت R2، آزمون‌های واحد/یکپارچه و artifact واقعی پیاده‌سازی شد.
- 2026-08-11، مرحله دهم-J: schema مشترک policy، سناریوی چهارسیاستی، معیار کمکی after-auction، آزمون عدم mutation و رگرسیون seed ثابت افزوده و اجرا شد؛ هیچ فرض بازتولید تازه‌ای تصویب یا اعمال نشد.
- 2026-08-11، مرحله یازدهم-A: Tables I-II، source package، منابع [1]/[4] و نسخه IEEE 2025 برای قواعد تولید داده ممیزی شدند؛ هشت فرض پیشنهادی ثبت و کدنویسی تا تصمیم کاربر متوقف شد.
- 2026-08-11، تصمیم مرحله یازدهم-B: کاربر ASSUMP-020 تا ASSUMP-027 را دقیقاً مطابق متن پیشنهادی تأیید و مجوز پیاده‌سازی مولدهای مصنوعی را صادر کرد.
- 2026-08-11، مرحله دوازدهم-A: v2، بسته source، مرجع [1]، نسخه نهایی IEEE و منابع رسمی وب برای trace Southampton ممیزی شدند؛ raw/schema عمومی قابل‌تأیید یافت نشد و ناسازگاری Gigabytes/MFlops ثبت شد؛ هیچ preprocessing یا فرض جدیدی اعمال نشد.

## قرارداد برچسب‌ها و مسیرها

- `[صریح در مقاله]`: مستقیماً در PDF نسخه v2 آمده است.
- `[استخراج مستقیم]`: بدون افزودن فرض، از ترکیب بخش‌های PDF نتیجه شده است.
- `[فرض بازتولید]`: مقاله جزئیات کافی نداده و تفسیر فقط پس از تأیید صریح کاربر وارد کد شده است.
- `[پیشنهاد فنی]`: نام فایل یا آزمون پیشنهادی است و بخشی از روش مقاله نیست.
- `[نامشخص]`: منبع v2 برای تعیین آن کافی نیست.
- `[استخراج از مرجع مستقیم مقاله]`: فقط از منبعی که v2 مستقیماً ارجاع داده استخراج شده و به خود v2 نسبت داده نمی‌شود.
- همه مسیرهای ستون «فایل کد آینده» `[پیشنهاد فنی]` و موقت‌اند؛ ساختار قطعی در مرحله ششم تعیین می‌شود.

## A. ردیابی منبع و مدل سیستم

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SRC-001 | صفحه 1؛ سربرگ | `[صریح در مقاله]` هویت منبع: arXiv v2 و عنوان مقاله | PDF مبنا | شناسه منبع و هش | `[پیشنهاد فنی] docs/paper_notes.md` | بررسی عنوان، نسخه، صفحات و SHA-256 | ثبت‌شده |
| SYS-001 | Section III، صفحه 3 | `[صریح در مقاله]` سیستم توزیع‌شده؛ سرورها مستقل‌اند و با یکدیگر ارتباط ندارند | وظایف، سرورها و وضعیت محلی هر سرور | تصمیم‌های محلی تخصیص | `[پیشنهاد فنی] simulation/system.py` | سناریوی دو سرور با وضعیت‌های متفاوت و بدون اشتراک state | استخراج‌شده |
| SYS-002 | Section III، صفحه 3؛ Fig. 1 | `[صریح در مقاله]` دو فاز کلی: bidding و processing | ورود دسته وظایف در epoch | شروع پردازش پس از پایان bidding | `[پیشنهاد فنی] simulation/engine.py` | آزمون ترتیب arrival → bidding → processing | استخراج‌شده |
| SYS-003 | صفحه 3؛ Fig. 1 | `[صریح در مقاله]` تأخیر epoch: وظایف epoch 2 در epoch 3 bidding و در epoch 4 processing را آغاز می‌کنند | arrival epoch | bidding/processing epoch | `[پیشنهاد فنی] simulation/timeline.py` | آزمون نگاشت epoch برای چند ورود متوالی | استخراج‌شده؛ معنای دقیق طول epoch نیازمند مرحله 2 |
| SYS-004 | Section III، صفحه 3 | `[صریح در مقاله]` Round 1: مشتری درخواست را به همه سرورهای در دسترس می‌فرستد | منابع موردنیاز و Utility اعلامی وظیفه | مجموعه قیمت‌های پیشنهادی سرورها | `[پیشنهاد فنی] algorithms/auction.py` | هر وظیفه از تمام سرورهای available پاسخ بگیرد | استخراج‌شده |
| SYS-005 | Section III، صفحه 3 | `[صریح در مقاله]` Round 2: مشتری ارزان‌ترین سرور را انتخاب می‌کند | قیمت‌های Round 1 | یک درخواست بازگشتی به سرور منتخب | `[پیشنهاد فنی] algorithms/client_choice.py` | انتخاب minimum price؛ آزمون قیمت بالاتر از Utility | استخراج‌شده |
| SYS-006 | مثال Fig. 4، صفحه 7 | `[استخراج مستقیم]` در تساوی دو fit-price، Job 532 یکی را به‌صورت تصادفی انتخاب کرده است | چند قیمت حداقل مساوی | یک سرور منتخب | `[پیشنهاد فنی] algorithms/client_choice.py` | آزمون tie با RNG کنترل‌شده | قاعده عمومی tie-breaking `[نامشخص]`؛ مثال تصادفی است |
| SYS-007 | Section III، صفحه 3 | `[صریح در مقاله]` سرور در Round 2 درباره پذیرش درخواست‌های بازگشتی تصمیم می‌گیرد | returning jobs و منابع residual | accepted/rejected jobs | `[پیشنهاد فنی] algorithms/auction.py` | ظرفیت پس از پذیرش و رد بررسی شود | استخراج‌شده |
| SYS-008 | Section III، صفحه 3 | `[صریح در مقاله]` وظیفه ناموفق ممکن است در bidding phase بعد دوباره ارسال شود | job ردشده و deadline باقی‌مانده | resubmitted یا کنارگذاشته‌شده | `[پیشنهاد فنی] simulation/resubmission.py` | آزمون عدم ارسال پس از deadline | سیاست انتخاب «ممکن است» `[نامشخص]` |
| SYS-009 | Section III، صفحه 3 | `[صریح در مقاله]` batch: upload، processing و download سه فاز مجزا هستند | داده ورودی، نیاز پردازشی و نتیجه | پیشرفت ترتیبی سه‌فاز | `[پیشنهاد فنی] simulation/batch_processing.py` | عدم هم‌پوشانی bandwidth و computation یک job | استخراج‌شده |
| SYS-010 | Section III، صفحه 3؛ Section IV | `[صریح در مقاله]` pipeline: upload، computation و download می‌توانند هم‌زمان باشند | تخصیص منابع در slotها | پیشرفت هم‌پوشان متناسب | `[پیشنهاد فنی] simulation/pipeline_processing.py` | قیود تناسب (9) و (10) در هر slot | استخراج‌شده |
| SYS-011 | صفحات 1 و 3-5 | `[صریح در مقاله]` منابع computation و bandwidth کشسان‌اند و در زمان تغییر می‌کنند | ظرفیت سرور و نیاز باقی‌مانده | allocation هر slot | `[پیشنهاد فنی] models/resource_vector.py` | تغییر allocation بدون نقض deadline/capacity | استخراج‌شده |
| SYS-012 | Section III، صفحه 3 | `[صریح در مقاله]` preemption در Round 2 می‌تواند وظیفه قبلی را با وظیفه جدید جایگزین کند | running job، returning job و residual resources | preempted job و admitted job | `[پیشنهاد فنی] algorithms/preemption.py` | آزادسازی کامل منابع وظیفه preempted | استخراج‌شده |
| SYS-013 | Section IV، صفحات 4-5 | `[صریح در مقاله]` Utility به‌صورت all-or-nothing است؛ preempted job utility صفر دارد | completion/preemption state و U_j | Utility earned | `[پیشنهاد فنی] evaluation/utility.py` | completed=U؛ preempted/incomplete=0 | استخراج‌شده |
| SYS-014 | Section III و Section V | `[استخراج مستقیم]` Retention یعنی نسخه بدون preemption که وظایف جاری را نگه می‌دارد | returning jobs و منابع آزاد | پذیرش بدون حذف running jobs | `[پیشنهاد فنی] algorithms/retention.py` | هیچ running job متوقف نشود | نام Retention در شکل‌ها صریح؛ جزئیات کامل Round 2 در v2 نیست |

## B. ردیابی مجموعه‌ها، پارامترها و متغیرها

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SET-001 | Section IV، صفحه 4 | `[صریح در مقاله]` مجموعه سرورها `I` با cardinality برابر `I_size` (نماد مقاله: قدرمطلق I) | تعریف سناریو | اندیس `i` | `[پیشنهاد فنی] models/server.py` | یکتایی شناسه و تعداد سرورها | استخراج‌شده |
| SET-002 | Section IV، صفحه 4 | `[صریح در مقاله]` مجموعه وظایف `J` با cardinality برابر `J_size` (نماد مقاله: قدرمطلق J) | workload | اندیس `j` | `[پیشنهاد فنی] models/task.py` | یکتایی شناسه و تعداد وظایف | استخراج‌شده |
| SET-003 | Section IV، صفحه 4 | `[صریح در مقاله]` مجموعه slotها `N` با افق محدود و cardinality برابر `N_size` | horizon | اندیس `n`/`l_j` | `[پیشنهاد فنی] simulation/clock.py` | slotهای معتبر و محدودیت افق | استخراج‌شده |
| PAR-001 | صفحه 4 | `[صریح در مقاله]` `a_j`: زمان ورود وظیفه بر حسب slot | task trace | arrival slot | `[پیشنهاد فنی] models/task.py` | `a_j` داخل horizon و غیرمنفی | استخراج‌شده |
| PAR-002 | صفحه 4 | `[صریح در مقاله]` `d_j`: deadline نسبی پس از ورود بر حسب slot | task specification | مهلت تکمیل | `[پیشنهاد فنی] models/task.py` | deadline مثبت؛ absolute deadline=`a_j+d_j` نیازمند تأیید مرزی | استخراج‌شده |
| PAR-003 | صفحه 4 | `[صریح در مقاله]` `U_j`: Utility در صورت سرویس تا deadline | task specification | value/profit | `[پیشنهاد فنی] models/task.py` | Utility غیرمنفی و all-or-nothing | استخراج‌شده |
| PAR-004 | صفحه 4 | `[صریح در مقاله]` `s_j`: حجم/نیاز storage داده ورودی؛ متن MB | task specification | upload/storage demand | `[پیشنهاد فنی] models/task.py` | یکسان‌سازی واحد با `S_i` | ناسازگاری MB/GB باید حل شود |
| PAR-005 | روابط (6)-(10)، صفحات 4-5 | `[استخراج مستقیم]` `s'_j`: اندازه نتایج دانلودی وظیفه | task specification | download-result demand | `[پیشنهاد فنی] models/task.py` | مقدار مثبت و تناسب download | تعریف روایی صریح/توزیع آزمایشی `[نامشخص]` |
| PAR-006 | صفحه 4 | `[صریح در مقاله]` `K_j`: کل نیاز محاسباتی بر حسب MFlops | task specification | computation demand | `[پیشنهاد فنی] models/task.py` | مقدار مثبت و مجموع allocation ≤/=`K_j` | استخراج‌شده |
| PAR-007 | صفحه 4 | `[صریح در مقاله]` `S_i`: ظرفیت storage سرور؛ متن GB | server specification | storage capacity | `[پیشنهاد فنی] models/server.py` | ظرفیت غیرمنفی؛ تبدیل واحد | Table I واحد MB دارد؛ ناسازگاری ثبت شد |
| PAR-008 | صفحه 4 | `[صریح در مقاله]` `C_i`: ظرفیت computation در هر slot، MFlops/s | server specification | compute capacity | `[پیشنهاد فنی] models/server.py` | مجموع `κ_j(n)` از ظرفیت بیشتر نشود | رابطه ظرفیت و طول slot `[نامشخص]` |
| PAR-009 | صفحه 4 | `[صریح در مقاله]` `B_{u,i}`: ظرفیت upload سرور در هر slot | server specification و slot duration | upload capacity/slot | `[پیشنهاد فنی] models/server.py` | مجموع upload در slot ≤ ظرفیت | استخراج‌شده |
| PAR-010 | صفحه 4 | `[صریح در مقاله]` `B_{d,i}`: ظرفیت download سرور در هر slot | server specification و slot duration | download capacity/slot | `[پیشنهاد فنی] models/server.py` | مجموع download در slot ≤ ظرفیت | استخراج‌شده |
| VAR-001 | رابطه (1)، صفحه 4 | `[صریح در مقاله]` `x_{i,j}` دودویی؛ تخصیص job j به server i | assignment decision | 0/1 | `[پیشنهاد فنی] optimization/variables.py` | domain و at-most-one-server | استخراج‌شده |
| VAR-002 | روابط (2)-(3)، صفحه 4 | `[صریح در مقاله]` `σ_j(n)`: داده uploadشده در slot | upload allocation | مقدار داده | `[پیشنهاد فنی] optimization/variables.py` | nonnegative فقط در active window | استخراج‌شده |
| VAR-003 | روابط (4)-(5)، صفحه 4 | `[صریح در مقاله]` `κ_j(n)`: computation رزروشده برای job در slot | compute allocation | MFlops/slot | `[پیشنهاد فنی] optimization/variables.py` | nonnegative و capacity-bound | استخراج‌شده |
| VAR-004 | روابط (6)-(10)، صفحات 4-5 | `[صریح در مقاله]` `σ'_j(n)`: داده نتیجه ارسال‌شده به کاربر | download allocation | مقدار result data | `[پیشنهاد فنی] optimization/variables.py` | پس از computation و در active window | استخراج‌شده |
| VAR-005 | صفحه 4؛ روابط (3)، (5)، (7)، (21)، (29)، (30) | `[صریح در مقاله]` `τ_j`: صفر برای preempted و یک برای run-to-end | preemption decision | 0/1 | `[پیشنهاد فنی] optimization/variables.py` | consistency با completion و `d_{j,t}` | متن توضیح رابطه (3) یک بار τ=0 را برای completion می‌نویسد؛ ناسازگار |
| VAR-006 | صفحه 4؛ روابط (11)-(14) | `[صریح در مقاله]` `d_{j,u}`, `d_{j,p}`, `d_{j,d}`: مدت/نقطه پایان upload، processing و download | schedule | intermediate durations | `[پیشنهاد فنی] optimization/variables.py` | `1 ≤ d_ju ≤ d_jp ≤ d_jd ≤ d_j` | معنای دقیق duration در برابر offset در مرحله 3 بررسی شود |
| VAR-007 | صفحه 4؛ روابط (28)-(30) | `[صریح در مقاله]` `d_{j,t}`: تعداد slot تا preemption؛ برابر `d_{j,d}` اگر preempt نشود | execution/preemption plan | stop slot count | `[پیشنهاد فنی] optimization/variables.py` | preempt-before-completion | استخراج‌شده |
| VAR-008 | رابطه (31)، صفحه 5 | `[صریح در مقاله]` `θ_j(n)`: indicator اشغال storage در زمان پردازش | `κ_j` و slot | 0/1 | `[پیشنهاد فنی] optimization/indicators.py` | مرز اولین/آخرین slot پردازش | استخراج‌شده |

## C. ردیابی تابع هدف و قیود ریاضی

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MATH-001 | Eq. (1)، صفحه 4 | `[صریح در مقاله]` بیشینه‌سازی `Σ_i Σ_j U_j τ_j x_{i,j}` | Utility، completion و assignment | total served utility | `[پیشنهاد فنی] optimization/objective.py` | مثال کوچک و مقایسه دستی objective | استخراج‌شده |
| MATH-002 | Eqs. (2)-(3)، صفحه 4 | `[صریح در مقاله]` upload کل از نیاز بیشتر نمی‌شود و برای job تکمیل‌شده باید کامل باشد | `σ`, `s`, `x`, `τ` | feasibility upload | `[پیشنهاد فنی] optimization/constraints.py` | completed/incomplete/preempted cases | استخراج‌شده؛ توضیح τ دارای typo |
| MATH-003 | Eqs. (4)-(5)، صفحه 4 | `[صریح در مقاله]` computation کل از `K_j` بیشتر نمی‌شود و برای completion کامل است | `κ`, `K`, `x`, `τ` | feasibility compute | `[پیشنهاد فنی] optimization/constraints.py` | under/over/exact compute | استخراج‌شده |
| MATH-004 | Eqs. (6)-(8)، صفحه 4 | `[صریح در مقاله]` download نتیجه، completion کامل و preemption پیش از 100% download | `σ'`, `s'`, `x`, `τ` | feasibility download | `[پیشنهاد فنی] optimization/constraints.py` | completed و preempted download | استخراج‌شده؛ strict inequality نیازمند نحوه مدل‌سازی solver |
| MATH-005 | Eq. (9)، صفحه 4 | `[صریح در مقاله]` نسبت computation تجمعی از نسبت upload تجمعی فراتر نمی‌رود | cumulative `κ`, `σ`, `K`, `s` | pipeline precedence | `[پیشنهاد فنی] optimization/pipeline_constraints.py` | 60% upload ⇒ حداکثر 60% compute | استخراج‌شده |
| MATH-006 | Eq. (10)، صفحه 4 | `[صریح در مقاله]` نسبت download تجمعی از نسبت computation فراتر نمی‌رود | cumulative `σ'`, `κ`, `s'`, `K` | pipeline precedence | `[پیشنهاد فنی] optimization/pipeline_constraints.py` | 60% compute ⇒ حداکثر 60% download | استخراج‌شده |
| MATH-007 | Eqs. (11)-(14)، صفحه 4 | `[صریح در مقاله]` ترتیب deadlineهای میانی و حداقل یک slot برای هر فاز | intermediate durations و `d_j` | temporal feasibility | `[پیشنهاد فنی] optimization/time_constraints.py` | برابرشدن فازها در pipeline و حد پایین 1 | استخراج‌شده |
| MATH-008 | Eq. (15)، صفحه 4 | `[صریح در مقاله]` محدودیت storage سرور در هر slot | cumulative upload، `x`, `θ`, `S_i` | storage feasibility | `[پیشنهاد فنی] optimization/capacity_constraints.py` | مجموع اشغال ≤ capacity؛ آزادسازی بعد download | واحدها و فرم ضرب `θ` نیازمند بررسی مرحله 3 |
| MATH-009 | Eq. (16)، صفحه 4 | `[صریح در مقاله]` محدودیت computation هر سرور/slot | `κ`, `x`, `C_i` | compute feasibility | `[پیشنهاد فنی] optimization/capacity_constraints.py` | ظرفیت صفر، برابر ظرفیت، بیش‌ظرفیت | استخراج‌شده |
| MATH-010 | Eq. (17)، صفحه 4 | `[صریح در مقاله]` محدودیت upload هر سرور/slot | `σ`, `x`, `B_u` | upload feasibility | `[پیشنهاد فنی] optimization/capacity_constraints.py` | positive/negative capacity tests | استخراج‌شده |
| MATH-011 | Eq. (18)، صفحه 4 | `[صریح در مقاله]` محدودیت download هر سرور/slot | `σ'`, `x`, `B_d` | download feasibility | `[پیشنهاد فنی] optimization/capacity_constraints.py` | positive/negative capacity tests | استخراج‌شده |
| MATH-012 | Eqs. (19)-(21)، صفحه 4 | `[صریح در مقاله]` تخصیص به حداکثر یک سرور و دامنه دودویی `x`, `τ` | decision variables | assignment/preemption validity | `[پیشنهاد فنی] optimization/domain_constraints.py` | multi-server rejection و binary validation | استخراج‌شده |
| MATH-013 | Eqs. (22)-(23)، صفحه 4 | `[صریح در مقاله]` پنجره فعال upload با `min(d_ju,d_jt)` | arrival، durations و preemption time | مجاز/صفر بودن `σ` | `[پیشنهاد فنی] optimization/activity_windows.py` | slot قبل arrival و بعد stop صفر باشد | استخراج‌شده |
| MATH-014 | Eqs. (24)-(25)، صفحات 4-5 | `[صریح در مقاله]` پنجره فعال computation از slot پس از arrival | arrival، durations و preemption time | مجاز/صفر بودن `κ` | `[پیشنهاد فنی] optimization/activity_windows.py` | off-by-one در آغاز/پایان | استخراج‌شده؛ مرزبندی دقیق نیازمند مرحله 3 |
| MATH-015 | Eqs. (26)-(27)، صفحه 5 | `[صریح در مقاله]` پنجره فعال download از دو slot پس از arrival | arrival، durations و preemption time | مجاز/صفر بودن `σ'` | `[پیشنهاد فنی] optimization/activity_windows.py` | off-by-one و deadline کوتاه | استخراج‌شده |
| MATH-016 | Eqs. (28)-(30)، صفحه 5 | `[صریح در مقاله]` preemption در هر نقطه فعال، اما فقط پیش از completion | `d_jt`, `d_jd`, `τ` | preemption validity | `[پیشنهاد فنی] optimization/preemption_constraints.py` | `τ=1 ⇔ d_jt=d_jd`; preempted has smaller stop | استخراج‌شده؛ strict inequality solver issue |
| MATH-017 | Eq. (31)، صفحه 5 | `[صریح در مقاله]` indicator بازه اشغال storage از اولین تا آخرین computation مثبت | `κ` schedule | `θ_j(n)` | `[پیشنهاد فنی] optimization/indicators.py` | no-compute edge case و بازه پیوسته | حالت مجموعه تهی `[نامشخص]` |
| MATH-018 | پایان Section IV، صفحه 5 | `[صریح در مقاله]` مدل یک MINLP زمان‌دار و مشابه generalized assignment، NP-Hard است | formulation | نیاز به heuristic | `[پیشنهاد فنی] optimization/pipeline_minlp.py` | smoke model و solver capability check | استخراج‌شده |

## D. ردیابی مزایده، قیمت‌گذاری و الگوریتم‌ها

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALG-001 | Section V-A1، صفحه 6؛ Algorithm 1 | `[صریح در مقاله]` اجرای knapsack روی residual resources و requesting jobs در Round 1 | residual resource vector و job pool | `jobsThatFit` | `[پیشنهاد فنی] algorithms/round1_knapsack.py` | مثال چندبعدی با feasible/infeasible jobs | تعریف دقیق knapsack به [4]/pyeasyga وابسته است |
| ALG-002 | Algorithm 1، صفحه 6 | `[صریح در مقاله]` fit job قیمت `0.9 × totalUtility` می‌گیرد و برای Round 2 علامت می‌خورد | fit membership و Utility | price و autoFit mark | `[پیشنهاد فنی] algorithms/pricing.py` | Utility=100 ⇒ price=90 | استخراج‌شده |
| ALG-003 | صفحه 6؛ Algorithm 1 | `[صریح در مقاله]` percentile factor برابر `c1 × percentile(job,currentJobs)` | job و running jobs | percentile discount component | `[پیشنهاد فنی] algorithms/pricing.py` | percentileهای 0، 0.7 و 1 | با ASSUMP-008 پیاده‌سازی و آزمون شد |
| ALG-004 | صفحه 6؛ Algorithm 1 | `[صریح در مقاله]` congestion factor برابر `c2 × (1-congestion(job,residual))` در pseudocode | resource demand و residual vector | congestion discount component | `[پیشنهاد فنی] algorithms/pricing.py` | residual صفر و job بزرگ‌تر از residual | تعریف `congestion()` به بیان/شکل [4] وابسته است |
| ALG-005 | صفحه 6 | `[صریح در مقاله]` `c1=c2=0.025`؛ مجموع preemption discount حداکثر 5% و fit discount برابر 10% | factors | price | `[پیشنهاد فنی] configs/algorithm_defaults.yaml` | property test: preemption discount ≤ 5% | استخراج‌شده |
| ALG-006 | صفحه 6؛ Algorithm 1 | `[صریح در مقاله]` price غیر-fit برابر `U - (percentileFactor+congestionFactor)×U` | U و factors | Round 1 price | `[پیشنهاد فنی] algorithms/pricing.py` | محاسبه دستی و bounds | استخراج‌شده |
| ALG-007 | متن صفحه 6 در برابر Algorithm 1 | `[صریح در مقاله]` job که حتی روی سرور خالی جا نمی‌شود باید price > Utility بگیرد | total capacity و job demand | rejection price | `[پیشنهاد فنی] algorithms/pricing.py` | oversized job هرگز سرور را انتخاب نکند | شاخه در pseudocode نشان داده نشده؛ مقدار دقیق price `[نامشخص]` |
| ALG-008 | صفحه 6 | `[صریح در مقاله]` Round 1 نسخه non-preemptive همان Round 1 اصلی است | requesting jobs | prices/marks | `[پیشنهاد فنی] algorithms/round1_knapsack.py` | equality of Round 1 outputs between modes | استخراج‌شده |
| ALG-009 | Section V-A2، صفحه 7؛ Algorithm 2 | `[صریح در مقاله]` ابتدا همه autoFit jobهای بازگشتی پذیرفته می‌شوند | marked returning jobs | admissions اولیه | `[پیشنهاد فنی] algorithms/knapsack_greedy.py` | autoFitها پیش از سایر jobs پذیرفته شوند | سازگاری simultaneous fit با ظرفیت باید بررسی شود |
| ALG-010 | Algorithm 2، صفحه 7 | `[صریح در مقاله]` remaining returning jobs نزولی بر اساس `utility/time_remaining` مرتب می‌شوند | returning jobs | ordered new jobs | `[پیشنهاد فنی] algorithms/ranking.py` | رتبه‌بندی و tie cases | tie-breaking `[نامشخص]` |
| ALG-011 | Algorithm 2، صفحه 7 | `[صریح در مقاله]` running jobs صعودی بر اساس `utility/time_remaining` مرتب می‌شوند | current server jobs | ordered victim candidates | `[پیشنهاد فنی] algorithms/ranking.py` | کم‌ارزش‌ترین victim ابتدا | tie-breaking `[نامشخص]` |
| ALG-012 | Algorithm 2، صفحه 7 | `[صریح در مقاله]` returning job که روی residual جا می‌شود مستقیماً پذیرفته می‌شود | job demand و residual | admission | `[پیشنهاد فنی] algorithms/knapsack_greedy.py` | exact fit و one-resource failure | استخراج‌شده |
| ALG-013 | Algorithm 2، صفحه 7 | `[صریح در مقاله]` شرط ارزش preemption: `new.utility/new.deadline ×1.05 ≥ running.utility/running.time_remaining` | new/running jobs | eligibility | `[پیشنهاد فنی] algorithms/preemption.py` | زیر، برابر و بالای آستانه 5% | استفاده deadline در pseudocode در برابر time_remaining متن نیازمند بررسی |
| ALG-014 | Algorithm 2، صفحه 7 | `[صریح در مقاله]` شرط فضا: `new.space ≤ victim.space + residual_resources` | resource vectors | fit-after-preemption | `[پیشنهاد فنی] algorithms/preemption.py` | vector-wise feasibility | معنای عملگر ≤ برای چند منبع `[استخراج مستقیم]` component-wise |
| ALG-015 | Algorithm 2، صفحه 7 | `[صریح در مقاله]` در صورت برقرار بودن شروط، victim preempt و new job اضافه می‌شود | eligible pair | updated allocation | `[پیشنهاد فنی] algorithms/preemption.py` | منابع victim آزاد و new یک بار اضافه شود | نبود `break` و امکان تکرار Add `[نامشخص]` |
| ALG-016 | Figs. 3-5، صفحات 7-8 | `[صریح در مقاله]` مثال تشخیصی قیمت‌ها در timestep 43 برای Server 5 و Jobs 532/540 | یک run نرمال pipeline | discount plots و انتخاب‌ها | `[پیشنهاد فنی] tests/regression/test_pricing_examples.py` | بازسازی کیفی دامنه 2%-3.4% و انتخاب‌های گزارش‌شده | داده خام مثال موجود نیست |
| ALG-017 | Section V-A3، صفحات 7-8 | `[صریح در مقاله]` پیچیدگی Round 1 برابر `O(n^g)` با `g≈30` | n و generations | complexity claim | `[پیشنهاد فنی] docs/complexity.md` | benchmark scaling کمکی | ادعای نظری ثبت شد؛ آزمون تجربی اثبات نیست |
| ALG-018 | Section V-A3، صفحه 7 | `[صریح در مقاله]` Round 2 برابر `O(n2×m)` و کل `O(n^g+n2m)=O(n^g)` | returning/current counts | complexity claim | `[پیشنهاد فنی] docs/complexity.md` | benchmark نسبت به n2 و m | استخراج‌شده |
| ALG-019 | Section V-B، صفحه 8 | `[صریح در مقاله]` Double Knapsack Preemption در Round 2 knapsack را روی total capacity و current+returning jobs اجرا می‌کند | all candidate jobs و total resources | knapsack membership | `[پیشنهاد فنی] algorithms/double_knapsack.py` | current/new mixed pool | knapsack implementation پایه در [4] است |
| ALG-020 | Section V-B، صفحه 8 | `[صریح در مقاله]` score عضو knapsack=`1000+U/time_remaining` و غیرعضو=`1+U/time_remaining` | membership و ratio | score | `[پیشنهاد فنی] algorithms/double_knapsack.py` | priority separation ≥ حدود 999 | استخراج‌شده |
| ALG-021 | Section V-B، صفحه 8 | `[صریح در مقاله]` بررسی fit فردی به ترتیب score نزولی؛ هر تعداد job ممکن است preempt شود | scored jobs | final admissions/preemptions | `[پیشنهاد فنی] algorithms/double_knapsack.py` | multi-preemption scenario | جزئیات آزادسازی/توقف از شرح کامل غایب است |
| ALG-022 | Sections V-A/V-B | `[استخراج مستقیم]` رابط مشترک روش‌ها باید job pool، server state و mode را بگیرد و allocation decisions بدهد | simulation state | decisions/events | `[پیشنهاد فنی] algorithms/base.py` | contract tests برای همه روش‌ها | طراحی رابط `[پیشنهاد فنی]` |

## E. ردیابی تولید داده و تنظیمات آزمایش

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-001 | Section VI-A1، صفحه 8 | `[صریح در مقاله]` تلاش oracle: 4 server، 25 job، ورود طی 4 timestep؛ بیش از 10 روز بدون optimality قطعی | توزیع‌های [1] | incumbent/timeout result | `[پیشنهاد فنی] configs/optimal_25_jobs.yaml` | solver smoke و ثبت gap/time | داده نمونه و تنظیم solver `[نامشخص]` |
| EXP-002 | Section VI-A1، صفحه 8 | `[صریح در مقاله]` مقایسه oracle: 18 job طی 3 timestep؛ optimum 17 و زمان ≈5.5h | توزیع‌های [1] | completed jobs per method | `[پیشنهاد فنی] configs/optimal_18_jobs.yaml` | regression با داده دقیق در صورت دسترسی | نمونه تصادفی/seed `[نامشخص]` |
| EXP-003 | Section VI-A1، صفحه 8 | `[صریح در مقاله]` سناریوی 10 job: Double Knapsack=10، KG-P=9، KG-R=8 با زمان‌های تقریبی 15/11/10s | زیرمجموعه سناریوی بالا | counts/runtimes | `[پیشنهاد فنی] configs/optimal_10_jobs.yaml` | regression count و timing report | داده دقیق `[نامشخص]` |
| EXP-004 | Section VI-A2، صفحه 8؛ Table I | `[صریح در مقاله]` Normal server storage `N(540,30)` MB | RNG | server storage | `[پیشنهاد فنی] datasets/synthetic_normal.py` | fixed-seed و mean/std diagnostic | truncation/rounding `[نامشخص]` |
| EXP-005 | Table I، صفحه 8 | `[صریح در مقاله]` Normal server compute `N(80,20)` MFlops/s | RNG | compute capacities | `[پیشنهاد فنی] datasets/synthetic_normal.py` | positivity/statistical diagnostic | truncation `[نامشخص]` |
| EXP-006 | Table I، صفحه 8 | `[صریح در مقاله]` server upload/download هر دو `N(120,30)` MB/s | RNG | bandwidth capacities | `[پیشنهاد فنی] datasets/synthetic_normal.py` | independent/correlated generation decision | هم‌بستگی دو مقدار `[نامشخص]` |
| EXP-007 | Table I، صفحه 8 | `[صریح در مقاله]` job storage `N(200,20)` MB و compute `N(100,20)` MFlops | RNG | job demands | `[پیشنهاد فنی] datasets/synthetic_normal.py` | units/positivity/statistics | truncation/rounding `[نامشخص]` |
| EXP-008 | Table I، صفحه 8 | `[صریح در مقاله]` job upload/download هر دو `N(80,10)` MB/s | RNG | job bandwidth requirements | `[پیشنهاد فنی] datasets/synthetic_normal.py` | statistics و capacity-stress | dependency `[نامشخص]` |
| EXP-009 | Table I، صفحه 8 | `[صریح در مقاله]` deadline `N(10,3)` slot و Utility `N(60,20)` | RNG | job deadline/utility | `[پیشنهاد فنی] datasets/synthetic_normal.py` | integer/positive generation | rounding/truncation `[نامشخص]` |
| EXP-010 | Section VI-A2، صفحه 8 | `[صریح در مقاله]` 8 server و arrival count `N(14,4)` job/slot | RNG و horizon | arrivals per slot | `[پیشنهاد فنی] datasets/arrivals.py` | integer count و fixed-seed repeatability | horizon/rounding `[نامشخص]` |
| EXP-011 | Section VI-A، صفحات 8-10 | `[صریح در مقاله]` pipeline normal با و بدون accounting for auction time | normal workload و چهار روش | utility/job outcomes | `[پیشنهاد فنی] configs/pipeline_normal.yaml` | smoke + aggregation regression | تعداد اجرا/seed `[نامشخص]` |
| EXP-012 | Section VI-A4، صفحه 9 | `[صریح در مقاله]` میانگین زمان auction/server: DK-P≈5s، DK-R≈4s، KG-P≈2s، KG-R≈1s | algorithm mode | deadline adjustment | `[پیشنهاد فنی] configs/auction_time.yaml` | mapping duration→deadline opportunities | نحوه اندازه‌گیری و سخت‌افزار `[نامشخص]` |
| EXP-013 | Section VI-B1، صفحات 9-10 | `[صریح در مقاله]` batch normal و نسخه accounting for auction time | Table I workload و سه روش | utility outcomes | `[پیشنهاد فنی] configs/batch_normal.yaml` | batch phase invariants و regression trend | run count/seed `[نامشخص]` |
| EXP-014 | Section VI-B2، صفحه 10؛ Table II | `[صریح در مقاله]` bimodal job storage `N(160,10)` MB، compute `N(80,20)` MFlops | RNG | demands | `[پیشنهاد فنی] datasets/synthetic_bimodal.py` | statistics/positivity | truncation `[نامشخص]` |
| EXP-015 | Table II، صفحه 10 | `[صریح در مقاله]` bimodal upload/download هر دو `N(70,10)` MB/s و deadline `N(10,3)` slot | RNG | job attributes | `[پیشنهاد فنی] datasets/synthetic_bimodal.py` | statistics و integer deadline | rounding/dependency `[نامشخص]` |
| EXP-016 | Section VI-B2؛ Table II، صفحه 10 | `[صریح در مقاله]` 90% jobs: `U1~N(40,10)`؛ 10%: `U2~N(160,20)` | RNG و class proportion | bimodal utilities | `[پیشنهاد فنی] datasets/synthetic_bimodal.py` | exact class ratio و mode diagnostics | نحوه اعمال دقیق 90/10 در هر run `[نامشخص]` |
| EXP-017 | Section VI-B3، صفحات 10-11 | `[صریح در مقاله]` trace چهار ساله Southampton؛ انتخاب سه روز در آوریل 2021 | raw trace | selected window | `[پیشنهاد فنی] datasets/southampton.py` | row counts و date filter | raw data و exact dates مسدود |
| EXP-018 | Section VI-B3، صفحات 10-11 | `[صریح در مقاله]` auction هر 10 دقیقه | trace timestamps | discrete timestep | `[پیشنهاد فنی] datasets/southampton.py` | boundary timestamps و timezone | alignment origin `[نامشخص]` |
| EXP-019 | Section VI-B3، صفحه 11؛ منبع مستقیم [1] Table III | `[صریح در مقاله]` priority high/medium/low بر اساس user group؛ `[استخراج مستقیم]` منبع [1] Utilityهای `N(100,10)`، `N(40,10)` و `N(20,4)` را می‌دهد | user group | priority/Utility category | `[پیشنهاد فنی] datasets/southampton.py` | mapping coverage | انتقال بدون تغییر از [1] به اجرای v2 نیازمند تأیید |
| EXP-020 | Section VI-B3، صفحه 11 | `[صریح در مقاله]` دو high-memory node با 768GB RAM و سه regular node با 192GB RAM | cluster node sample | 5 simulated servers | `[پیشنهاد فنی] configs/southampton.yaml` | capacities و count | compute capacities دقیق `[نامشخص]` |
| EXP-021 | Section VI-B3، صفحه 11 | `[صریح در مقاله]` `B_d × slot_duration ~ N(10,0.2)` GB | RNG | download capacity/slot | `[پیشنهاد فنی] datasets/southampton.py` | distribution diagnostic | seed/truncation `[نامشخص]` |
| EXP-022 | Section VI-B3، صفحه 11 | `[صریح در مقاله]` capped deadline آزمایش real trace برابر حداکثر 2h | trace deadlines | capped deadlines | `[پیشنهاد فنی] configs/southampton_capped.yaml` | `min(original,2h)` نیازمند تأیید نگاشت | روش cap به‌ظاهر مستقیم؛ unit conversion لازم |
| EXP-023 | کل Section VI | `[نامشخص]` seed، تعداد تکرار، horizon مصنوعی، confidence interval/error bars و aggregation | experiment config | reproducible runs | `[پیشنهاد فنی] configs/reproduction_assumptions.yaml` | deterministic replay | مسدود تا تصمیم کاربر در مرحله 5 |

## F. ردیابی معیارها، شکل‌ها و جدول‌های هدف

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MET-001 | Section VI، صفحات 8-12 | `[صریح در مقاله]` Utility دسته‌های completed، rejected و preempted | event log و U_j | utility totals | `[پیشنهاد فنی] evaluation/metrics.py` | partition و جمع دستی | استخراج‌شده |
| MET-002 | Figs. 7,8,10,14,15 | `[صریح در مقاله]` تعداد high-value/low-value jobs بر حسب outcome | task class و final state | counts | `[پیشنهاد فنی] evaluation/metrics.py` | count partition | آستانه high/low برای normal workload `[نامشخص]` |
| MET-003 | Sections VI-A4/VI-B3 | `[صریح در مقاله]` auction duration و اثر آن بر فرصت‌های allocation/deadline | runtime per method | adjusted outcomes | `[پیشنهاد فنی] evaluation/runtime.py` | deterministic duration injection | hardware measurement unavailable |
| FIG-001 | Fig. 1، صفحه 3 | `[صریح در مقاله]` timeline arrival/bidding/processing | event epochs | system-flow diagram | `scripts/reproduce_figure1.py` و `figures/stage15g/figure1_reconstructed.{svg,pdf,png}` | تطبیق ترتیب رخدادها، topology، SVG editable و QA بصری | کامل در Stage 15-G؛ بازتولید ساختاری/مفهومی، نه pixel copy؛ continuation/dot count `[نامشخص]` |
| FIG-002 | Fig. 2، صفحه 5 | `[صریح در مقاله]` درصد برآورده‌شدن upload/processing/download در زمان | per-slot progress | سه منحنی progression | `[پیشنهاد فنی] visualization/progress.py` | monotonicity و قیود (9)-(10) | داده job واقعی شکل موجود نیست |
| FIG-003 | Fig. 3، صفحه 7 | `[صریح در مقاله]` histogram تخفیف Round 1 سرور 5 در t=43 | pricing log | discount histogram | `[پیشنهاد فنی] visualization/pricing.py` | bins/discount bounds | raw run موجود نیست |
| FIG-004 | Fig. 4، صفحه 7 | `[صریح در مقاله]` تخفیف Job 532 از 8 server | Round 1 bids | per-server bars | `[پیشنهاد فنی] visualization/pricing.py` | two fit discounts و one rejection | raw values فقط از تصویر تقریبی‌اند |
| FIG-005 | Fig. 5، صفحه 8 | `[صریح در مقاله]` تخفیف Job 540 از 8 server | Round 1 bids | per-server bars | `[پیشنهاد فنی] visualization/pricing.py` | chosen lowest server 7 | raw values فقط از تصویر تقریبی‌اند |
| FIG-006 | Fig. 6، صفحه 9 | `[صریح در مقاله]` pipeline normal Utility outcomes برای چهار روش | normal pipeline results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | totals from raw results | داده عددی پشت شکل موجود نیست |
| FIG-007 | Fig. 7، صفحه 9 | `[صریح در مقاله]` pipeline normal high-value job outcomes | classified results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | count aggregation | تعریف high-value `[نامشخص]` |
| FIG-008 | Fig. 8، صفحه 9 | `[صریح در مقاله]` pipeline normal low-value job outcomes | classified results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | count aggregation | تعریف low-value `[نامشخص]` |
| FIG-009 | Fig. 9، صفحه 10 | `[صریح در مقاله]` pipeline normal Utility با accounting for auction time | adjusted deadline results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | recompute from raw logs | adjustment mechanics نیازمند استخراج مرحله 5 |
| FIG-010 | Fig. 10، صفحه 10 | `[صریح در مقاله]` high-value outcomes با auction-time accounting | classified adjusted results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | count aggregation | raw data موجود نیست |
| FIG-011 | Fig. 11، صفحه 10 | `[صریح در مقاله]` batch normal Utility outcomes برای سه روش | batch normal results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | total categories | raw data موجود نیست |
| FIG-012 | Fig. 12، صفحه 10 | `[صریح در مقاله]` batch normal Utility با auction-time accounting | adjusted batch results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | total categories | raw data موجود نیست |
| FIG-013 | Fig. 13، صفحه 11 | `[صریح در مقاله]` batch bimodal Utility breakdown | bimodal results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | utility aggregation | raw data موجود نیست |
| FIG-014 | Fig. 14، صفحه 11 | `[صریح در مقاله]` bimodal high-value job outcomes | high-mode jobs | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | exact 10% class counts | raw data موجود نیست |
| FIG-015 | Fig. 15، صفحه 11 | `[صریح در مقاله]` bimodal low-value job outcomes | low-mode jobs | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | exact 90% class counts | raw data موجود نیست |
| FIG-016 | Fig. 16، صفحه 11 | `[صریح در مقاله]` trace storage distribution بر حسب priority | selected trace | probability histogram | `[پیشنهاد فنی] visualization/trace_diagnostics.py` | histogram normalization | raw trace مسدود |
| FIG-017 | Fig. 17، صفحه 12 | `[صریح در مقاله]` trace computation distribution | selected trace | probability histogram | `[پیشنهاد فنی] visualization/trace_diagnostics.py` | histogram normalization | raw trace مسدود |
| FIG-018 | Fig. 18، صفحه 12 | `[صریح در مقاله]` trace deadline distribution | selected trace | probability histogram | `[پیشنهاد فنی] visualization/trace_diagnostics.py` | hours conversion | raw trace مسدود |
| FIG-019 | Fig. 19، صفحه 12 | `[صریح در مقاله]` trace Utility outcomes برای KG-P/KG-R | trace experiment | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | utility aggregation | raw trace مسدود |
| FIG-020 | Fig. 20، صفحه 12 | `[صریح در مقاله]` Utility completed با deadline cap دو ساعت برای DK و دو KG | capped trace results | grouped bars | `[پیشنهاد فنی] visualization/figures.py` | completed utility only | raw trace مسدود |
| TAB-001 | Table I، صفحه 8 | `[صریح در مقاله]` پارامترهای Normal servers/jobs | paper constants | config table | `[پیشنهاد فنی] configs/synthetic_normal.yaml` | schema و unit validation | مقادیر ثبت شده؛ generation details ناقص |
| TAB-002 | Table II، صفحه 10 | `[صریح در مقاله]` پارامترهای Bimodal jobs | paper constants | config table | `[پیشنهاد فنی] configs/synthetic_bimodal.yaml` | schema و mixture validation | مقادیر ثبت شده؛ generation details ناقص |

## G. به‌روزرسانی مرحله دوم: چرخه عمر و انتقال حالت

نام stateها در این بخش `[پیشنهاد فنی]` است، زیرا مقاله state machine رسمی ندارد. شرط‌ها مطابق منبع برچسب خورده‌اند.

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| STATE-001 | Fig. 1 و Section III، صفحه 3 | `[صریح در مقاله]` arrival در epoch e و bidding در epoch بعد | arrival event | `CREATED → WAITING_FOR_BID` | `[پیشنهاد فنی] simulation/task_state.py` | نگاشت epoch e به e+1 | نام stateها پیشنهادی |
| STATE-002 | Section III، صفحه 3 | `[صریح در مقاله]` ارسال درخواست Round 1 به همه serverهای available | waiting job | `ROUND1_REQUESTED` | `[پیشنهاد فنی] simulation/task_state.py` | broadcast count | استخراج‌شده |
| STATE-003 | Sections III/V-A1، صفحات 3 و 6 | `[صریح در مقاله]` دریافت price و autoFit mark | server responses | `ROUND1_PRICED` | `[پیشنهاد فنی] simulation/task_state.py` | کامل‌بودن price vector | استخراج‌شده |
| STATE-004 | Section III، صفحه 3 | `[صریح در مقاله]` انتخاب cheapest server و بازگشت در Round 2 | prices | `ROUND2_RETURNED` | `[پیشنهاد فنی] simulation/task_state.py` | minimum price selection | tie-breaking نامشخص |
| STATE-005 | Algorithm 2، صفحه 7 | `[صریح در مقاله]` autoFit یا fit روی residual موجب پذیرش است | returning job و server state | `ACCEPTED` | `[پیشنهاد فنی] simulation/task_state.py` | direct/autoFit acceptance | استخراج‌شده |
| STATE-006 | Algorithm 2، صفحه 7 | `[صریح در مقاله]` ratio threshold و fit-after-preemption موجب پذیرش با victim است | new/victim jobs | `ACCEPTED` و victim=`PREEMPTED` | `[پیشنهاد فنی] simulation/task_state.py` | transaction و Utility victim=0 | نبود break نامشخص |
| STATE-007 | Section III، صفحه 3 | `[صریح در مقاله]` job ناموفق در auction rejected است | failed Round 2 | `REJECTED` | `[پیشنهاد فنی] simulation/task_state.py` | no allocation/resources | استخراج‌شده |
| STATE-008 | Section III، صفحه 3 | `[صریح در مقاله]` rejected client ممکن است در bidding phase بعد resubmit کند | rejected job | `WAITING_RETRY → ROUND1_REQUESTED` | `[پیشنهاد فنی] simulation/task_state.py` | retry lifecycle | policy و count نامشخص |
| STATE-009 | Section III، صفحه 3 | `[صریح در مقاله]` پایان bidding باعث آغاز processing accepted jobs می‌شود | accepted job | active processing state | `[پیشنهاد فنی] simulation/task_state.py` | processing starts after bidding | استخراج‌شده |
| STATE-010 | Section III، صفحه 3 | `[صریح در مقاله]` batch شامل upload سپس compute سپس download است | batch job progress | سه state متوالی batch | `[پیشنهاد فنی] simulation/task_state.py` | عدم هم‌پوشانی compute/bandwidth | نام stateها پیشنهادی |
| STATE-011 | Sections III/IV، صفحات 3-5 | `[صریح در مقاله]` pipeline فعالیت‌های هم‌زمان با قیود تناسب دارد | per-slot progress | `PIPELINE_ACTIVE` | `[پیشنهاد فنی] simulation/task_state.py` | Eqs. (9)-(10) | نام state پیشنهادی |
| STATE-012 | Eqs. (2)-(10)، صفحات 4-5 | `[استخراج مستقیم]` completion وقتی upload، compute و download کامل و در deadline باشند | cumulative progress | `COMPLETED` و Utility کامل | `[پیشنهاد فنی] simulation/task_state.py` | exact completion boundary | مرز deadline نیازمند مرحله 3 |
| STATE-013 | Sections III/IV/V، صفحات 3-7 | `[صریح در مقاله]` preemption در upload/compute/download و پیش از completion مجاز است | active victim | `PREEMPTED` و Utility صفر | `[پیشنهاد فنی] simulation/task_state.py` | هر سه فاز victim | retry preempted نامشخص |
| STATE-014 | صفحات 1 و 4-5 | `[استخراج مستقیم]` deadline miss باعث Utility صفر می‌شود | non-completed job و time | `EXPIRED` | `[پیشنهاد فنی] simulation/task_state.py` | deadline boundary و resource release | state/event در مقاله رسمی نیست |
| STATE-015 | Section III و Algorithm 2 | `[استخراج مستقیم]` Retention/Preemption policy هستند نه lifecycle state | server policy | admission behavior | `[پیشنهاد فنی] algorithms/policy.py` | no-preempt invariant برای Retention | Round 2 Retention ناقص |
| STATE-016 | Sections III-IV | `[استخراج مستقیم]` completed، preempted و expired باید terminal باشند مگر retry صریح تعریف شود | final state | terminal lifecycle | `[پیشنهاد فنی] simulation/task_state.py` | منع اجرای مجدد completed | terminal بودن preempted/expired هنوز تصمیم بازتولیدی نشده |

## H. به‌روزرسانی مرحله سوم: نگاشت کامل روابط مدل ریاضی

مسیرهای کد و نام آزمون‌های این بخش همگی `[پیشنهاد فنی]` هستند. خود روابط با نسخه arXiv v2 تطبیق داده شده‌اند؛ هیچ تفسیر اصلاحی در آن‌ها اعمال نشده است.

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EQ-001 | Section IV، رابطه (1)، صفحه 4 | `[صریح در مقاله]` بیشینه‌سازی مجموع `U_j τ_j x_{i,j}` | Utility، completion و assignment | مقدار تابع هدف | `[پیشنهاد فنی] optimization/objective.py` | جمع دستی Utility وظایف تکمیل‌شده و جلوگیری از دوباره‌شماری | استخراج‌شده |
| EQ-002 | Section IV، رابطه (2)، صفحه 4 | `[صریح در مقاله]` کران مجموع upload با `s_j x_{i,j}` برای هر `i,j` | جریان upload، اندازه ورودی و assignment | قید بالای upload | `[پیشنهاد فنی] optimization/constraints.py` | assignment صفر و مثبت در حالت تک‌سروری و چندسروری | ناسازگاری چندسروری ثبت شده |
| EQ-003 | Section IV، رابطه (3)، صفحه 4 | `[صریح در مقاله]` برابری upload هنگام `τ_j=1` | completion و مجموع upload | شرط تکمیل upload | `[پیشنهاد فنی] optimization/constraints.py` | completed و incomplete job | ناسازگاری چندسروری ثبت شده |
| EQ-004 | Section IV، رابطه (4)، صفحه 4 | `[صریح در مقاله]` کران مجموع computation با `K_j x_{i,j}` برای هر `i,j` | جریان compute، نیاز محاسباتی و assignment | قید بالای compute | `[پیشنهاد فنی] optimization/constraints.py` | assignment صفر و مثبت | ناسازگاری چندسروری ثبت شده |
| EQ-005 | Section IV، رابطه (5)، صفحه 4 | `[صریح در مقاله]` برابری computation هنگام `τ_j=1` | completion و مجموع compute | شرط تکمیل computation | `[پیشنهاد فنی] optimization/constraints.py` | completed و incomplete job | ناسازگاری چندسروری ثبت شده |
| EQ-006 | Section IV، رابطه (6)، صفحه 4 | `[صریح در مقاله]` کران مجموع download با `s'_j x_{i,j}` برای هر `i,j` | جریان download، اندازه خروجی و assignment | قید بالای download | `[پیشنهاد فنی] optimization/constraints.py` | assignment صفر و مثبت | ناسازگاری چندسروری و تعریف‌نشدن `s'_j` ثبت شده |
| EQ-007 | Section IV، رابطه (7)، صفحه 4 | `[صریح در مقاله]` برابری download هنگام `τ_j=1` | completion و مجموع download | شرط تکمیل download | `[پیشنهاد فنی] optimization/constraints.py` | completion با دانلود کامل و ناقص | استخراج‌شده؛ وابسته به `s'_j` نامشخص |
| EQ-008 | Section IV، رابطه (8)، صفحه 4 | `[صریح در مقاله]` نسبت download کمتر از `1+τ_j` | cumulative download و output size | جداسازی completion | `[پیشنهاد فنی] optimization/constraints.py` | مرز دقیق نسبت 1 برای `τ=0` | strict inequality نیازمند تصمیم اجرایی |
| EQ-009 | Section IV، رابطه (9)، صفحه 4 | `[صریح در مقاله]` compute تجمعی از upload تجمعی جلو نمی‌زند | cumulative upload و compute | قید تقدم pipeline | `[پیشنهاد فنی] models/progress.py` | چند slot با پیشرفت یکنواخت و جهشی | استخراج‌شده |
| EQ-010 | Section IV، رابطه (10)، صفحه 4 | `[صریح در مقاله]` download تجمعی از compute تجمعی جلو نمی‌زند | cumulative compute و download | قید تقدم pipeline | `[پیشنهاد فنی] models/progress.py` | چند slot و مرز تکمیل | استخراج‌شده |
| EQ-011 | Section IV، رابطه (11)، صفحه 4 | `[صریح در مقاله]` ترتیب `d_ju ≤ d_jp ≤ d_jd ≤ d_j` | چهار پارامتر زمانی | ترتیب پنجره‌ها | `[پیشنهاد فنی] models/task.py` | ترتیب معتبر و هر نقض مجزا | استخراج‌شده |
| EQ-012 | Section IV، رابطه (12)، صفحه 4 | `[صریح در مقاله]` `d_ju ≥ 1` | upload deadline offset | اعتبار offset | `[پیشنهاد فنی] models/task.py` | صفر و یک | استخراج‌شده |
| EQ-013 | Section IV، رابطه (13)، صفحه 4 | `[صریح در مقاله]` `d_jp ≥ 1` | processing deadline offset | اعتبار offset | `[پیشنهاد فنی] models/task.py` | صفر و یک | استخراج‌شده |
| EQ-014 | Section IV، رابطه (14)، صفحه 4 | `[صریح در مقاله]` `d_jd ≥ 1` | download deadline offset | اعتبار offset | `[پیشنهاد فنی] models/task.py` | صفر و یک | استخراج‌شده |
| EQ-015 | Section IV، رابطه (15)، صفحه 4 | `[صریح در مقاله]` ظرفیت storage سرور در هر slot با `θ_j(n)` | upload تجمعی، assignment و storage activity | مصرف storage هر سرور | `[پیشنهاد فنی] models/server.py` | ظرفیت دقیق، اضافه‌ظرفیت و آزادسازی | استخراج‌شده؛ دامنه زمانی متن مبهم |
| EQ-016 | Section IV، رابطه (16)، صفحه 4 | `[صریح در مقاله]` ظرفیت محاسباتی سرور در هر slot | `κ_j(n)` و assignment | مصرف compute هر سرور | `[پیشنهاد فنی] models/server.py` | برابر ظرفیت و بیش‌ظرفیت | استخراج‌شده؛ واحد per-slot نامشخص |
| EQ-017 | Section IV، رابطه (17)، صفحه 4 | `[صریح در مقاله]` ظرفیت upload bandwidth سرور | `σ_j(n)` و assignment | مصرف upload هر سرور | `[پیشنهاد فنی] models/server.py` | برابر ظرفیت و بیش‌ظرفیت | استخراج‌شده؛ واحد per-slot نامشخص |
| EQ-018 | Section IV، رابطه (18)، صفحه 4 | `[صریح در مقاله]` ظرفیت download bandwidth سرور | `σ'_j(n)` و assignment | مصرف download هر سرور | `[پیشنهاد فنی] models/server.py` | برابر ظرفیت و بیش‌ظرفیت | استخراج‌شده؛ واحد per-slot نامشخص |
| EQ-019 | Section IV، رابطه (19)، صفحه 4 | `[صریح در مقاله]` هر job حداکثر روی یک server | assignment matrix | قید یکتایی تخصیص | `[پیشنهاد فنی] optimization/constraints.py` | صفر، یک و دو تخصیص | استخراج‌شده |
| EQ-020 | Section IV، رابطه (20)، صفحه 4 | `[صریح در مقاله]` دودویی بودن `x_{i,j}` | assignment variable | دامنه دودویی | `[پیشنهاد فنی] optimization/variables.py` | رد مقادیر کسری و خارج دامنه | استخراج‌شده |
| EQ-021 | Section IV، رابطه (21)، صفحه 4 | `[صریح در مقاله]` دودویی بودن `τ_j` | completion variable | دامنه دودویی | `[پیشنهاد فنی] optimization/variables.py` | رد مقادیر کسری و خارج دامنه | استخراج‌شده |
| EQ-022 | Section IV، رابطه (22)، صفحه 5 | `[صریح در مقاله]` صفر بودن upload بیرون پنجره مجاز | arrival، `d_ju` و `d_jt` | mask صفر upload | `[پیشنهاد فنی] optimization/time_windows.py` | ابتدا، انتها و slot پس از پنجره | off-by-one محتمل ثبت شده |
| EQ-023 | Section IV، رابطه (23)، صفحه 5 | `[صریح در مقاله]` نامنفی بودن upload داخل پنجره مجاز | arrival، `d_ju` و `d_jt` | دامنه upload فعال | `[پیشنهاد فنی] optimization/time_windows.py` | مقدار صفر و مثبت داخل پنجره | استخراج‌شده |
| EQ-024 | Section IV، رابطه (24)، صفحه 5 | `[صریح در مقاله]` صفر بودن computation بیرون پنجره مجاز | arrival، `d_jp` و `d_jt` | mask صفر compute | `[پیشنهاد فنی] optimization/time_windows.py` | `d_jp=1` و مقادیر بزرگ‌تر | پنجره تهی در مرز ثبت شده |
| EQ-025 | Section IV، رابطه (25)، صفحه 5 | `[صریح در مقاله]` نامنفی بودن computation داخل پنجره مجاز | arrival، `d_jp` و `d_jt` | دامنه compute فعال | `[پیشنهاد فنی] optimization/time_windows.py` | slotهای ابتدا و انتها | off-by-one محتمل ثبت شده |
| EQ-026 | Section IV، رابطه (26)، صفحه 5 | `[صریح در مقاله]` صفر بودن download بیرون پنجره مجاز | arrival، `d_jd` و `d_jt` | mask صفر download | `[پیشنهاد فنی] optimization/time_windows.py` | `d_jd=1,2` و مقادیر بزرگ‌تر | پنجره تهی در مرز ثبت شده |
| EQ-027 | Section IV، رابطه (27)، صفحه 5 | `[صریح در مقاله]` نامنفی بودن download داخل پنجره مجاز | arrival، `d_jd` و `d_jt` | دامنه download فعال | `[پیشنهاد فنی] optimization/time_windows.py` | slotهای ابتدا و انتها | off-by-one محتمل ثبت شده |
| EQ-028 | Section IV، رابطه (28)، صفحه 5 | `[صریح در مقاله]` دامنه `d_jt` از 1 تا `d_jd` | termination offset | دامنه زمان توقف | `[پیشنهاد فنی] optimization/variables.py` | دو مرز و مقدار خارج دامنه | integrality صریح نیست |
| EQ-029 | Section IV، رابطه (29)، صفحه 5 | `[صریح در مقاله]` اگر `τ_j=1` آنگاه `d_jt=d_jd` | completion و termination offset | اتصال completion به deadline | `[پیشنهاد فنی] optimization/constraints.py` | completed در انتها و incomplete زودتر | استخراج‌شده |
| EQ-030 | Section IV، رابطه (30)، صفحه 5 | `[صریح در مقاله]` نسبت `d_jt/d_jd` کمتر از `1+τ_j` | completion و دو offset | اجبار توقف زودهنگام برای ناتمام | `[پیشنهاد فنی] optimization/constraints.py` | مرز `d_jt=d_jd` برای هر دو مقدار `τ` | strict inequality؛ بازنویسی صحیح وابسته به صحیح‌بودن زمان |
| EQ-031 | Section IV، رابطه (31)، صفحه 5 | `[صریح در مقاله]` `θ_j(n)` بین نخستین و آخرین slot محاسبات مثبت برابر 1 است | پروفایل `κ_j` و زمان | indicator فعالیت storage | `[پیشنهاد فنی] models/progress.py` | compute پیوسته، دارای شکاف و کاملاً صفر | حالت مجموعه تهی و سازگاری با متن نامشخص |

## I. به‌روزرسانی مرحله چهارم: جزئیات اجرایی الگوریتم‌ها

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DET-001 | Algorithm 1، خط 2، صفحه 6 | `[صریح در مقاله]` اجرای knapsack روی residual resources و requesting jobs | server residual و requests | `jobsThatFit` | `[پیشنهاد فنی] algorithms/knapsack.py` | feasibility همه ابعاد و عدم تغییر دائمی state | پارامترهای GA نامشخص |
| DET-002 | Algorithm 1، خطوط 4-5، صفحه 6 | `[صریح در مقاله]` قیمت عضو knapsack برابر `0.9U` | membership و Utility | fit price | `[پیشنهاد فنی] algorithms/pricing.py` | مقدار دقیق و Utility صفر | کامل |
| DET-003 | Section V-A1، صفحه 6 | `[صریح در مقاله]` عضو knapsack برای بازگشت Round 2 mark می‌شود | job-server membership | server-specific autoFit mark | `[پیشنهاد فنی] algorithms/pricing.py` | mark فقط برای همان server | در نثر موجود و در شبه‌کد غایب |
| DET-004 | Algorithm 1، خط 7، صفحه 6 | `[صریح در مقاله]` percentile بر مبنای `utility/time_remaining` نسبت به current jobs | incoming و current jobs | percentile factor | `[پیشنهاد فنی] algorithms/pricing.py` | 0، 0.7، 1 و مجموعه تهی | حالت تهی و tie نامشخص |
| DET-005 | Section V-A1 و Algorithm 1 خط 8، صفحه 6 | `[صریح در مقاله]` نثر congestion را نسبت منابع می‌داند ولی شبه‌کد `1-congestion` دارد | demand و residual | congestion factor | `[پیشنهاد فنی] algorithms/pricing.py` | server خلوت/شلوغ و residual صفر | ناسازگاری ثبت شده |
| DET-006 | Algorithm 1، خط 9، صفحه 6 | `[صریح در مقاله]` قیمت preemption برابر Utility منهای مجموع دو factor ضربدر Utility | Utility و factors | preemption price | `[پیشنهاد فنی] algorithms/pricing.py` | سقف 5 درصد و تقدم fit price | وابسته به تعریف congestion |
| DET-007 | Section V-A1، صفحه 6 | `[صریح در مقاله]` job ناممکن باید price بزرگ‌تر از Utility بگیرد | demand و total capacity | rejection price | `[پیشنهاد فنی] algorithms/pricing.py` | demand بیش از یک/چند ظرفیت | مقدار دقیق و شاخه شبه‌کد نامشخص |
| DET-008 | Section V-A1، صفحه 6 | `[صریح در مقاله]` Round 1 نسخه Retention همان Round 1 اصلی است | requests و server state | offers | `[پیشنهاد فنی] algorithms/knapsack_greedy.py` | برابری offers دو mode | کامل، جز ابهام‌های مشترک |
| DET-009 | Algorithm 2، خط 2، صفحه 7 | `[صریح در مقاله]` پذیرش همه autoFitهای بازگشته پیش از بقیه | autoFit returns | allocations | `[پیشنهاد فنی] algorithms/knapsack_greedy.py` | subset feasibility و ترتیب پذیرش | کامل |
| DET-010 | Algorithm 2، خطوط 3-4، صفحه 7 | `[صریح در مقاله]` returningها نزولی و current jobs صعودی بر حسب `U/time_remaining` | دو مجموعه job | دو صف رتبه‌بندی | `[پیشنهاد فنی] algorithms/ranking.py` | ترتیب و tie | tie-breaking نامشخص |
| DET-011 | Algorithm 2، خطوط 5-7، صفحه 7 | `[صریح در مقاله]` fit مستقیم قبل از preemption | job و residual vector | direct accept | `[پیشنهاد فنی] algorithms/knapsack_greedy.py` | fit همه ابعاد و no-preempt invariant | معنای `space≤` باید تثبیت شود |
| DET-012 | Section V-A2 و Algorithm 2 خط 10، صفحه 7 | `[صریح در مقاله]` نثر new ratio را 5 درصد بزرگ‌تر می‌خواهد ولی شبه‌کد `new_ratio*1.05≥old_ratio` دارد | new و victim ratio | eligibility | `[پیشنهاد فنی] algorithms/preemption.py` | مثال `100` در برابر `104` | ناسازگاری بحرانی ثبت شده |
| DET-013 | Algorithm 2، خطوط 10-12، صفحه 7 | `[صریح در مقاله]` fit پس از آزادسازی victim، سپس Preempt و Add | new job، victim و residual | replacement | `[پیشنهاد فنی] algorithms/preemption.py` | transaction و resource invariants | cleanup/state جزئیات ندارد |
| DET-014 | Algorithm 2، صفحه 7 | `[نامشخص]` نبود `break` پس از Preempt و Add | victim loop | کنترل حلقه | `[پیشنهاد فنی] algorithms/preemption.py` | عدم Add تکراری و عدم preemption اضافی | نیازمند تصمیم بازتولید |
| DET-015 | Section V-A1/A2 | `[نامشخص]` Round 2 مستقل KG-R ارائه نشده است | returning jobs | accept/reject | `[پیشنهاد فنی] algorithms/knapsack_greedy.py` | retention و greedy order | بازسازی بدون فرض ممکن نیست |
| DET-016 | Section V-A، صفحه 6 | `[صریح در مقاله]` DK-R در هر دو round knapsack دارد | Round 1/2 job pools | prices و admissions | `[پیشنهاد فنی] algorithms/double_knapsack.py` | دو knapsack مستقل | جزئیات به منبع [4] واگذار شده |
| DET-017 | Section V-B، صفحه 8 | `[صریح در مقاله]` DK-P Round 2 روی total capacity و union current+returning knapsack اجرا می‌کند | total capacity و candidates | preferred membership | `[پیشنهاد فنی] algorithms/double_knapsack.py` | total در برابر residual و union بدون duplicate | کامل در سطح membership |
| DET-018 | Section V-B، صفحه 8 | `[صریح در مقاله]` score عضو `1000+ratio` و غیرعضو `1+ratio` | membership و `U/time_remaining` | score order | `[پیشنهاد فنی] algorithms/double_knapsack.py` | ratio عادی و ratio بیش از 999 | تضمین اولویت بدون کران ratio ناقص |
| DET-019 | Section V-B، صفحه 8 | `[نامشخص]` الگوریتم fit/preemption پس از score برای DK-P تشریح نشده است | ordered candidates و server state | victimها و final allocation | `[پیشنهاد فنی] algorithms/double_knapsack.py` | multi-victim و rollback | مسدودشده |
| DET-020 | Section VI-A1، صفحه 8 | `[صریح در مقاله]` Gurobi oracle با آگاهی کامل و تخصیص slot-level دقیق | کل instance و horizon | upper bound solution | `[پیشنهاد فنی] optimization/gurobi_oracle.py` | status، bound، gap و constraints | وابسته به رفع ابهام‌های مرحله سوم |
| DET-021 | Section V-A3، صفحات 7-8 | `[صریح در مقاله]` پیچیدگی KG: Round 1 برابر `O(n^g)` با `g≈30`، Round 2 برابر `O(n_2m)` و کل `O(n^g)` | pool sizes | complexity claim | `[پیشنهاد فنی] docs/complexity.md` | benchmark scaling | فضا و پارامترهای کامل GA نامشخص |
| DET-022 | Sections III و V | `[نامشخص]` tie-breaking انتخاب server، sortها و knapsack | equal prices/scores | deterministic choice | `[پیشنهاد فنی] algorithms/tie_breaking.py` | fixed-seed replay | فقط مثال انتخاب تصادفی وجود دارد |

## J. به‌روزرسانی مرحله پنجم: منابع مستقیم و پروتکل آزمایش

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REF-001 | مرجع [1] v2 | `[استخراج مستقیم]` `1.pdf` برابر مقاله ICCCN 2022 با DOI `10.1109/ICCCN54977.2022.9868909` است | PDF ناشر | منبع مستقیم 10 صفحه‌ای | `[پیشنهاد فنی] docs/sources.md` | title، authors، DOI، page continuity و SHA-256 | هویت و کامل‌بودن تأیید شد |
| REF-002 | مرجع [4] v2 | `[استخراج مستقیم]` `4.pdf` برابر مقاله MASS 2021 با DOI `10.1109/MASS52906.2021.00038` است | PDF ناشر | منبع مستقیم 9 صفحه‌ای | `[پیشنهاد فنی] docs/sources.md` | صفحات چاپی 225-233، References و SHA-256 | هویت و کامل‌بودن تأیید شد |
| PROT-001 | Section VI-A2؛ Table I، صفحه 8 | `[صریح در مقاله]` Synthetic Normal با 8 server و چهار بعد منبع | RNG و config | server/job samples | `[پیشنهاد فنی] configs/synthetic_normal.yaml` | parameter schema و units | پارامترهای μ/σ کامل؛ generation policy ناقص |
| PROT-002 | Table I، صفحه 8 | `[صریح در مقاله]` serverها: storage `N(540,30)`، compute `N(80,20)`، upload/download `N(120,30)` | RNG | capacities | `[پیشنهاد فنی] datasets/synthetic_normal.py` | distribution diagnostics و positivity | rounding/truncation نامشخص |
| PROT-003 | Table I، صفحه 8 | `[صریح در مقاله]` jobها: storage `N(200,20)`، compute `N(100,20)`، upload/download `N(80,10)`، deadline `N(10,3)` و Utility `N(60,20)` | RNG | task attributes | `[پیشنهاد فنی] datasets/synthetic_normal.py` | statistical و unit tests | `s'_j` و وابستگی‌ها نامشخص |
| PROT-004 | Section VI-A2، صفحه 8 | `[صریح در مقاله]` arrival count برابر `N(14,4)` job/slot | RNG و horizon | arrivals | `[پیشنهاد فنی] datasets/arrivals.py` | integer/positive count | horizon و rounding نامشخص |
| PROT-005 | Section VI-B2؛ Table II، صفحه 10 | `[صریح در مقاله]` Bimodal job distributions و serverهای Table I | RNG | bimodal workload | `[پیشنهاد فنی] configs/synthetic_bimodal.yaml` | mode statistics | arrival/horizon نامشخص |
| PROT-006 | Section VI-B2، صفحه 10 | `[صریح در مقاله]` دقیقاً 90% low با `N(40,10)` و 10% high با `N(160,20)` | class allocation و RNG | Utility classes | `[پیشنهاد فنی] datasets/synthetic_bimodal.py` | exact ratio و per-class distribution | per-run allocation policy نامشخص |
| PROT-007 | Section VI-A1، صفحه 8 | `[صریح در مقاله]` oracle نخست: 4 server، 25 job، 4 arrival slots و بیش از 10 روز بدون optimum اثبات‌شده | instance منبع [1] | incumbent/status | `[پیشنهاد فنی] configs/optimal_25_jobs.yaml` | status، bound، runtime | instance/seed مفقود |
| PROT-008 | Section VI-A1، صفحه 8 | `[صریح در مقاله]` oracle اصلی: 18 job طی 3 slot و optimum 17 در حدود 5.5 ساعت | distributions منبع [1] | completed counts | `[پیشنهاد فنی] configs/optimal_18_jobs.yaml` | regression counts | server count، Utility variant و seed نامشخص |
| PROT-009 | Section VI-A1، صفحه 8 | `[صریح در مقاله]` subset ده-job با DK=10، KG-P=9 و KG-R=8 و runtimeهای تقریبی | subset instance | counts/time | `[پیشنهاد فنی] configs/optimal_10_jobs.yaml` | count regression | subset دقیق مفقود |
| PROT-010 | منبع مستقیم [1]، Table I | `[استخراج مستقیم]` candidate distributions برای آزمایش‌های optimal شامل `S~N(600,30)`، `C~N(92,30)` و سایر پارامترها | source [1] | candidate config | `[پیشنهاد فنی] configs/optimal_source1.yaml` | provenance و no-cross-contamination | Utility variant و upload/download یکتا نیست |
| PROT-011 | Section VI-A4، صفحه 9 | `[صریح در مقاله]` زمان متوسط per-server synthetic: DK-P≈5s، DK-R≈4s، KG-P≈2s، KG-R≈1s | method execution | auction delay | `[پیشنهاد فنی] configs/auction_time.yaml` | method-to-delay mapping | sample size/hardware نامشخص |
| PROT-012 | Sections VI-A4/VI-B1 | `[نامشخص]` mechanics accounting for auction duration | reported durations و deadlines | adjusted timeline | `[پیشنهاد فنی] simulation/clock.py` | clock/deadline controlled tests | نیازمند تصمیم بازتولید |
| PROT-013 | Section VI-B3، صفحات 10-11 | `[صریح در مقاله]` trace چهار ساله Iridis و پنجره سه‌روزه آوریل 2021 با slot ده‌دقیقه‌ای | raw trace | discretized jobs | `[پیشنهاد فنی] datasets/southampton.py` | date filter و slot boundaries | raw data و تاریخ دقیق مفقود |
| PROT-014 | منبع مستقیم [1]، Table III | `[استخراج مستقیم]` Utility priorityها: High `N(100,10)`، Medium `N(40,10)`، Low `N(20,4)` | priority class و RNG | task Utility | `[پیشنهاد فنی] datasets/southampton.py` | mapping coverage و distributions | انتقال بدون تغییر به v2 نیازمند تأیید |
| PROT-015 | Section VI-B3، صفحه 11 | `[صریح در مقاله]` trace servers: دو node با 768GB و سه node با 192GB | node sample | 5 simulated servers | `[پیشنهاد فنی] configs/southampton.yaml` | counts/storage | compute numbers و upload نامشخص |
| PROT-016 | Section VI-B3، صفحه 11 | `[صریح در مقاله]` download capacity×slot برابر `N(10,0.2)` GB | RNG | per-slot download | `[پیشنهاد فنی] datasets/southampton.py` | distribution/units | seed/truncation نامشخص |
| PROT-017 | Section VI-B3، صفحات 11-12 | `[صریح در مقاله]` runtime trace: DK≈10m، KG-P≈3m و KG-R≈2m per auction | method | runtime | `[پیشنهاد فنی] evaluation/runtime.py` | mapping و units | hardware/sample count نامشخص |
| PROT-018 | Section VI-B3؛ Fig. 20 | `[صریح در مقاله]` cap تمام deadlineها به حداکثر 2 ساعت یا 12 slot | trace deadlines | capped deadlines | `[پیشنهاد فنی] configs/southampton_capped.yaml` | cap boundary | exact accounting mechanics نامشخص |
| PROT-019 | Figs. 6-20 | `[صریح در مقاله]` معیارهای Utility/count برای completed، rejected و ever-preempted | event/results | chart aggregates | `[پیشنهاد فنی] evaluation/metrics.py` | overlap و double-count | aggregation/repeats نامشخص |
| PROT-020 | کل Section VI | `[نامشخص]` repeats، seeds، horizon، error bars، Gurobi settings، hardware و OS | experiment config | reproducible protocol | `[پیشنهاد فنی] configs/reproduction_assumptions.yaml` | deterministic replay | پیش از اجرا نیازمند تصمیم کاربر |
| PROT-021 | ممیزی مرحله پنجم | `[استخراج مستقیم]` پوشش وزنی متن v2 برابر 55.3% و پوشش کاملاً مشخص برابر 31.6% است | 19-category rubric | coverage score | `[پیشنهاد فنی] docs/reproduction_report.md` | recount rubric | 6 کامل، 9 جزئی، 4 مفقود |

## K. به‌روزرسانی مرحله ششم: نگاشت معماری آینده

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ARCH-001 | کل مقاله | `[پیشنهاد فنی]` جداسازی مدل دامنه از policy، solver و event engine | مدل و پروتکل استخراج‌شده | package لایه‌بندی‌شده | `src/edge_reproduction/` | import و dependency-boundary | طراحی‌شده؛ هنوز ایجاد نشده |
| ARCH-002 | Section IV، روابط (2)-(6) و (14)-(18) | `[پیشنهاد فنی]` بردار منابع canonical با arithmetic مؤلفه‌ای | ظرفیت و demand | fit/residual/violation | `models/resources.py` | zero/negative/overflow | طراحی‌شده؛ مرحله 7/8 |
| ARCH-003 | Sections III-IV | `[پیشنهاد فنی]` state و تخصیص تراکنشی | task/server/allocation proposal | commit یا rollback | `models/allocation.py`, `simulation/state.py` | atomic preemption | طراحی‌شده؛ مرحله 7/8 |
| ARCH-004 | Sections III و V | `[پیشنهاد فنی]` رابط مشترک `AllocationPolicy` برای KG/DK/R/P | snapshot، jobs و RNG | bids/allocation plan | `algorithms/base.py` | contract همه روش‌ها | طراحی‌شده؛ مرحله 10 |
| ARCH-005 | Section V-A3 | `[صریح در مقاله]` استفاده از `pyeasyga`؛ `[پیشنهاد فنی]` محصورسازی پشت adapter | items، ظرفیت و GA config | membership | `algorithms/knapsack_solver.py` | fixed-seed/feasibility/compatibility | نسخه مقاله نامشخص؛ طراحی‌شده |
| ARCH-006 | Section VI-A1 | `[صریح در مقاله]` oracle از Gurobi؛ `[پیشنهاد فنی]` dependency اختیاری و import تنبل | model data و solver config | status/incumbent/bound/gap | `optimization/gurobi_oracle.py` | بدون package/license و tiny licensed model | طراحی‌شده؛ نسخه مقاله نامشخص |
| ARCH-007 | Section IV، روابط (1)-(31) | `[پیشنهاد فنی]` model builder مستقل از solver | instance و تفسیرهای مصوب | solver-neutral model data | `optimization/model_builder.py` | مثبت/منفی هر قید | مسدود تا رفع ناسازگاری‌ها |
| ARCH-008 | Sections III-IV؛ Figs. 1-2 | `[استخراج مستقیم]` موتورهای batch و pipeline جدا با event engine مشترک | config، dataset و policy | event log و result | `simulation/batch.py`, `pipeline.py`, `engine.py` | مثال دستی و invariants | طراحی‌شده؛ semantics مرزی نامشخص |
| ARCH-009 | Tables I-II | `[پیشنهاد فنی]` مولدهای synthetic جدا و RNG تزریق‌شده | config مصوب و seed | processed dataset و manifest | `datasets/synthetic_normal.py`, `synthetic_bimodal.py` | آمار، replay و positivity | طراحی‌شده؛ rounding/truncation نامشخص |
| ARCH-010 | Section VI-B3 | `[پیشنهاد فنی]` raw immutable و lineage raw→interim→processed | trace و mapping مصوب | dataset canonical و audit counts | `datasets/southampton.py`, `data/*` | SHA-256 و شمارش رکورد | طراحی‌شده؛ raw/mapping مفقود |
| ARCH-011 | Figs. 6-20 | `[پیشنهاد فنی]` محاسبه metric و aggregation فقط از eventهای raw | event logs و run configs | aggregated CSV | `evaluation/metrics.py`, `aggregation.py` | overlap/double-count/lineage | طراحی‌شده؛ repeats/aggregation نامشخص |
| ARCH-012 | Figs. 1-20 | `[پیشنهاد فنی]` تولید نمودار و CSV پشت آن از خروجی تجمیع‌شده | aggregated CSV | PNG+SVG/PDF+CSV | `visualization/figures.py` | axes/series/rebuild | طراحی‌شده؛ مرحله 14 |
| ARCH-013 | کمبودهای مراحل 3-5 | `[پیشنهاد فنی]` gate تصمیم با `status: pending` و بدون default پنهان | decision registry | resolved config یا خطای روشن | `configs/unresolved_decisions.yaml`, `io/config_loader.py` | pending باید fail-fast کند | طراحی‌شده؛ هیچ فرضی تصویب نشده |
| ARCH-014 | کل Section VI | `[پیشنهاد فنی]` run directory مستقل و provenance کامل | config، seed، environment و source hashes | raw events/result/manifest | `io/results.py`, `io/provenance.py`, `results/*` | replay و manifest completeness | طراحی‌شده؛ مرحله 13 |
| ARCH-015 | مراحل 13-18 | `[پیشنهاد فنی]` pipeline سطح‌بالا check→data→tests→runs→aggregate→figures→report | config registry و dependencies | artifacts نهایی | `scripts/reproduce_all.py` | clean-environment smoke/full | طراحی‌شده؛ مرحله 17 |

## L. به‌روزرسانی مرحله هفتم: هسته مدل داده اجراشده

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DATA-001 | Sections III-IV؛ روابط (15)-(18) | `[استخراج مستقیم]` بردار چهاربعدی منابع و fit مؤلفه‌ای | چهار مؤلفه نامنفی | vector/add/subtract/fit | `src/edge_reproduction/models/resources.py` | صفر، NaN/Inf، fit و underflow | پیاده‌سازی‌شده؛ 10 آزمون مرتبط موفق |
| DATA-002 | Section IV، صفحه 4 | `[استخراج مستقیم]` specification وظیفه با `a_j,d_j,U_j,s_j,s'_j,K_j` | record وظیفه | `Task` immutable | `src/edge_reproduction/models/task.py` | زمان، totals، output مفقود و Utility | پیاده‌سازی‌شده؛ boundary deadline هنوز نامشخص |
| DATA-003 | Sections III-IV | `[صریح در مقاله]` server مستقل با ظرفیت چهار منبع | ID و capacity | `Server` immutable | `src/edge_reproduction/models/server.py` | ظرفیت صفر و ID | پیاده‌سازی‌شده |
| DATA-004 | Section III؛ Algorithm 1 | `[استخراج مستقیم]` bid شامل price، autoFit و mark | task/server/round/price | `Bid` | `src/edge_reproduction/models/bid.py` | finite price و metadata | پیاده‌سازی‌شده؛ فرمول price خارج از مرحله 7 |
| DATA-005 | Section III | `[صریح در مقاله]` دو round مزایده | epoch، tasks و bids | `AuctionRound` | `src/edge_reproduction/models/bid.py` | round/membership/duplicate | پیاده‌سازی‌شده |
| DATA-006 | روابط (19)-(20) | `[استخراج مستقیم]` حداکثر یک assignment server برای task | task/server/resources/time | `Allocation` | `src/edge_reproduction/models/allocation.py` | active/end و key uniqueness | پیاده‌سازی‌شده؛ schedule slot-level مرحله 8/9 |
| DATA-007 | مدل lifecycle مرحله 2 | `[پیشنهاد فنی]` 15 نام state بدون transition policy | phase/outcome labels | `TaskState` | `src/edge_reproduction/models/enums.py` | شمارش و serialization values | پیاده‌سازی‌شده؛ transitionها اعمال نشده |
| DATA-008 | Sections III-IV | `[پیشنهاد فنی]` registry ساختاری مجموعه‌های `I`,`J` و assignmentها | Task/Server/Allocation | `SimulationState` | `src/edge_reproduction/simulation/state.py` | key/reference/copy/snapshot | پیاده‌سازی‌شده؛ capacity invariants مرحله 8 |
| DATA-009 | Section VI و کمبودهای پروتکل | `[پیشنهاد فنی]` config typed با gate تصمیم pending | method/mode/horizon/seed/decisions | `ExperimentConfig` | `src/edge_reproduction/models/config.py` | unresolved fail-fast | پیاده‌سازی‌شده |
| DATA-010 | Figs. 6-20 | `[استخراج مستقیم]` outcomeها و ever-preempted غیرpartitionی | task IDs و Utilityها | `ExperimentResult` | `src/edge_reproduction/models/result.py` | overlap/duplicates/finite | پیاده‌سازی‌شده؛ aggregation مرحله 13/14 |
| DATA-011 | ممیزی مرحله 7 | `[پیشنهاد فنی]` Python 3.12.13 و quality gate | source/tests | pytest/Ruff/mypy | `pyproject.toml`, `tests/unit/` | full unit suite و static checks | 53 passed؛ Ruff/mypy موفق |

## M. به‌روزرسانی مرحله هشتم: مدل ریاضی و اعتبارسنجی اجرایی

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IMPL-001 | رابطه (1)، صفحه 4 | `[صریح در مقاله]` Utility all-or-nothing `Uτx` | Task/x/τ/deadline | Utility | `evaluation/utility.py` | completed/preempted/unassigned/late | پیاده‌سازی‌شده؛ موفق |
| IMPL-002 | روابط (2)-(6)، صفحات 4-5 | `[ناسازگاری]` flow bound و completion با quantifier همه serverها | totals/requirements/x/τ/semantics | bool | `optimization/constraints.py` | literal در برابر selected-server | هر دو semantics پیاده؛ بدون default |
| IMPL-003 | روابط (7)-(10)، صفحه 5 | `[صریح در مقاله]` download completion و pipeline proportionality | `TaskSchedule` و requirements | bool | `optimization/constraints.py` | exact/partial و 60٪/61٪ | پیاده‌سازی‌شده؛ موفق |
| IMPL-004 | روابط (11)-(14)، صفحه 5 | `[صریح در مقاله]` stage order و حداقل span | offsets/deadline | bool | `optimization/constraints.py` | equality/reversal و صفر هر stage | پیاده‌سازی‌شده؛ موفق |
| IMPL-005 | روابط (15)-(18)، صفحه 5 | `[صریح در مقاله]` ظرفیت storage/compute/upload/download | per-task allocations/x/θ/capacity | bool | `optimization/constraints.py` | exact/over برای هر منبع | پیاده‌سازی‌شده؛ unit normalization pending |
| IMPL-006 | روابط (19)-(21)، صفحه 5 | `[صریح در مقاله]` تک-server و دامنه دودویی | x/τ | bool | `optimization/constraints.py` | 0/1/0.5 و دو assignment | پیاده‌سازی‌شده؛ موفق |
| IMPL-007 | روابط (22)-(27)، صفحه 5 | `[صریح در فرمول]` پنجره activity با indexing چاپ‌شده | a/end/stop/horizon/activity | allowed slots/bool | `optimization/constraints.py` | داخل/خارج/منفی برای هر activity | literal پیاده؛ off-by-one حل‌نشده |
| IMPL-008 | روابط (28)-(30)، صفحه 5 | `[صریح در مقاله]` دامنه stop و preemption قبل از پایان | τ/d_t/d_d | bool | `optimization/constraints.py` | endpoint و قبل از endpoint | پیاده‌سازی‌شده؛ موفق |
| IMPL-009 | رابطه (31)، صفحه 5 | `[صریح در فرمول]` θ میان اولین/آخرین compute مثبت | computation schedule | binary tuple | `optimization/constraints.py` | positive/noncontiguous/empty | literal پیاده؛ empty unresolved |
| IMPL-010 | Section IV | `[پیشنهاد فنی]` Deadline boundary اجباری | task/completion/boundary | bool/elapsed | `simulation/time.py` | exact endpoint هر دو semantics | پیاده‌سازی‌شده؛ بدون default |
| IMPL-011 | Section V-A1، صفحه 6 | `[صریح در مقاله]` fit price 0.9U و دو congestion reading | utility/factors/semantics | price | `algorithms/pricing.py` | مثال 100 و اختلاف prose/pseudocode | پیاده‌سازی‌شده؛ impossible price unresolved |
| IMPL-012 | Section V-A2، صفحه 7 | `[ناسازگاری]` شرط 5٪ prose در برابر Algorithm 2 | ratios/semantics | bool | `algorithms/feasibility.py` | مثال اختلاف دو تفسیر | هر دو پیاده؛ بدون default |
| IMPL-013 | Sections III-V | `[استخراج مستقیم]` retention fit و preemption resource feasibility | state/task/server/victims | bool/resources | `algorithms/feasibility.py` | residual insufficient/victim sufficient | پیاده‌سازی‌شده؛ موفق |
| IMPL-014 | Sections III-V و روابط ظرفیت | `[پیشنهاد فنی]` allocation/release/preemption تراکنشی | SimulationState و IDs | state جدید | `simulation/accounting.py` | success/failure/original unchanged | پیاده‌سازی‌شده؛ موفق |
| IMPL-015 | روابط (15)-(21) و lifecycle | `[استخراج مستقیم]` invariantهای ظرفیت و state/resource | SimulationState | pass/error | `simulation/invariants.py` | overcapacity/terminal-active/release | پیاده‌سازی‌شده؛ موفق |
| IMPL-016 | ممیزی مرحله 8 | `[پیشنهاد فنی]` quality gate کامل | 37 فایل source/test | pytest/Ruff/mypy/pip | `pyproject.toml`, `tests/unit/` | full suite | 105 passed؛ همه کنترل‌ها موفق |

## N. به‌روزرسانی مرحله نهم: شبیه‌ساز پایه و سناریوی دستی

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEC-001 | رابطه (11)، صفحه 5 | `[فرض بازتولید؛ تأییدشده]` Deadline فراگیر | completion و `a+d` | on-time/late | `simulation/time.py`, `simulation/engine.py` | completion دقیقاً endpoint | تصویب و اعمال شد |
| DEC-002 | روابط (2)-(6)، صفحات 4-5 | `[فرض بازتولید؛ تأییدشده]` فقط server منتخب | flow و assignment | constraint result | `optimization/constraints.py` | selected-server mode | تصویب و در metadata ثبت شد |
| SIM-001 | Section III و نیاز مرحله 9 | `[پیشنهاد فنی]` schema رویداد auditپذیر | transition data | JSON event | `simulation/events.py` | validation/serialization | پیاده‌سازی‌شده |
| SIM-002 | Sections III-V | `[پیشنهاد فنی]` موتور scripted بدون policy الگوریتمی | state/commands/config | SimulationRun | `simulation/engine.py` | outcome/resources/deadline | پیاده‌سازی‌شده |
| SIM-003 | نیاز مرحله 9 | `[آزمون کمکی]` 2 server و 4 task | fixture ثابت | state/commands/config | `simulation/scenarios.py` | محاسبه دستی | پیاده‌سازی‌شده |
| SIM-004 | lifecycle مقاله | `[استخراج مستقیم]` پذیرش، رد، preemption، expiry و completion | command sequence | 11 event | `tests/integration/test_stage_nine_smoke.py` | همه شاخه‌ها | موفق |
| SIM-005 | Utility all-or-nothing | `[استخراج مستقیم]` فقط C Utility می‌گیرد | final state/events | completed utility=30 | `simulation/engine.py` | manual vs program | اختلاف صفر |
| SIM-006 | قیود ظرفیت و release | `[استخراج مستقیم]` ledger منابع در هر event | before/after vectors | full release | `simulation/invariants.py` | هر transition و final capacity | اختلاف صفر |
| SIM-007 | بازتولیدپذیری artifact | `[پیشنهاد فنی]` JSONL و summary از script | smoke scenario | results/raw/stage9_smoke | `scripts/run_smoke_scenario.py` | rerun/hash | اجراشده؛ artifact واقعی |

## O. به‌روزرسانی مرحله دهم: تصمیم‌های Algorithm 1 و Algorithm 2

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEC-003 | Section V-A1؛ Algorithm 1، صفحه 6 | `[فرض بازتولید؛ تأییدشده]` congestion میانگین چهار نسبت بریده‌شده و عامل `0.025(1-congestion)` | demand/residual/total capacity | congestion و factor | `algorithms/pricing.py` | صفر/اشباع/چهار بعد/وظیفه ناممکن | پیاده‌سازی و آزمون شد؛ شاخه ناممکن با ASSUMP-007 تکمیل شد |
| DEC-004 | Section V-A2؛ Algorithm 2، صفحه 7 | `[فرض بازتولید؛ تأییدشده]` `new_ratio >= 1.05*victim_ratio` با پذیرش برابری | utility/deadline/time remaining | eligibility | `algorithms/feasibility.py` | زیر/برابر/بالای ۵٪ | پیاده‌سازی و آزمون مرز شد |
| DEC-005 | Section V-A2؛ Algorithm 2، صفحه 7 | `[فرض بازتولید؛ تأییدشده]` حداکثر یک victim؛ صعودی برحسب نسبت و اولین victim feasible | current jobs/residual/incoming | victim ID یا None | `algorithms/knapsack_greedy.py` | ترتیب، شرط منابع، عدم تعمیم به DK | پیاده‌سازی و آزمون شد؛ tie برابر fail-fast است |
| DEC-006 | Algorithm 2، خطوط 12-14، صفحه 7 | `[فرض بازتولید؛ تأییدشده]` break پس از موفقیت و تراکنش اتمیک | state/incoming/victim | state جدید یا original unchanged | `simulation/accounting.py`, `algorithms/knapsack_greedy.py` | موفقیت/rollback/یک victim | پیاده‌سازی و آزمون rollback شد |
| DEC-007 | Section V-A1، صفحه 6 | `[فرض بازتولید؛ تأییدشده]` sentinel ناممکن `nextafter(U,+inf)` و fail-fast غیرمتناهی | utility/total capacity | finite price > U | `algorithms/pricing.py` | مثبت/منفی/max-float | پیاده‌سازی و آزمون شد |
| DEC-008 | Section V-A1، صفحه 6؛ `[منبع تکمیلی خارج از مبنای v2]` IEEE 2025 | `[فرض بازتولید؛ تأییدشده]` strict empirical percentile؛ empty=0 و tie خارج صورت | new/current ratios | `[0,1]` | `algorithms/pricing.py` | empty/tie/0/1 | پیاده‌سازی و آزمون شد |
| DEC-009 | Section V-A، صفحات 6-7 | `[فرض بازتولید؛ تأییدشده]` KG-R Round 2: autoFit، سپس descending ratio و fit-only | state/returning/marks/times | accepted/rejected/state | `algorithms/knapsack_greedy_retention.py` | no-preemption، update residual، tie fail | پیاده‌سازی و آزمون شد |
| DEC-010 | Section V-A2؛ Algorithm 2، صفحه 7 | `[فرض بازتولید؛ تأییدشده]` victim pool snapshot ثابت پیش از پذیرش‌های Round 2؛ زمان ثابت و حفاظت jobهای جدید | pre-round active jobs/times | ordered fixed victim IDs | `algorithms/knapsack_greedy_preemption.py` | auto/direct protection، removal، tie، frozen time | پیاده‌سازی و آزمون شد |

## P. پیاده‌سازی مرحله دهم-B: KnapsackGreedy Retention

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KGR-001 | Section V-A1؛ Algorithm 1، صفحه 6 | Round 1 روی همه serverها و requestها | state/tasks/times/selector | bids | `algorithms/knapsack_greedy_retention.py` | fit/preemptive/impossible | پیاده‌سازی و آزمون شد |
| KGR-002 | Algorithm 1، صفحه 6 | قیمت `0.9U` و mark سرورمحور autoFit | selected subset | Bid | `algorithms/pricing.py` | mark/price | موفق |
| KGR-003 | Algorithm 1 و ASSUMP-003/007/008 | قیمت non-fit و impossible | demand/residual/current ratios | finite price | `algorithms/pricing.py` | empty/tie/max-float | موفق |
| KGR-004 | Section III، صفحه 3 | انتخاب یکتای کمترین offer و رد price>U | bids همه serverها | server map/rejection | `algorithms/knapsack_greedy_retention.py` | multi-server/equal price/all impossible | موفق؛ tie قابل‌قبول fail-fast |
| KGR-005 | ASSUMP-009 | پذیرش همه autoFitهای همان server | returning/marks/state | updated state | `algorithms/knapsack_greedy_retention.py` | subset/fit/resources | موفق |
| KGR-006 | ASSUMP-009 | remaining نزولی برحسب ratio و fit-only | tasks/times/residual | admissions/rejections | `algorithms/knapsack_greedy_retention.py` | order/continue/tie | موفق |
| KGR-007 | Retention | عدم preemption تحت کمبود منابع | current/incoming | rejected incoming | `algorithms/knapsack_greedy_retention.py` | victim would make fit | موفق؛ victim retained |
| KGR-008 | معماری مرحله 6 | رابط مشترک `AllocationPolicy` | state/requests/times/epoch | policy result | `algorithms/base.py` | runtime protocol | موفق |
| KGR-009 | Round 1 knapsack | selector تزریقی؛ exact فقط `[ابزار کمکی]` | capacity/tasks | selected IDs | `algorithms/knapsack.py` | unique optimum/equal optimum | موفق؛ GA مقاله هنوز نامشخص |
| KGR-010 | آزمون کمکی مرحله 10-B | مثال دستی و artifact واقعی | one server/5 tasks | JSON | `scripts/run_stage_ten_b_kg_retention_example.py` | manual/program/hash | اجرا شد |

## Q. پیاده‌سازی مرحله دهم-C: KnapsackGreedy Preemption

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KGP-001 | Algorithm 2، صفحه 7؛ ASSUMP-010 | capture snapshot پیش از هر پذیرش Round 2 | pre-round active allocations/times | immutable ordered entries | `algorithms/knapsack_greedy_preemption.py` | membership/order/frozen time | موفق |
| KGP-002 | ASSUMP-010 | snapshot صعودی و fail-fast نسبت victim مساوی | utility/time remaining | ordered victim pool | `algorithms/knapsack_greedy_preemption.py` | unique/equal ratios | موفق |
| KGP-003 | Algorithm 2، خطوط 2-3 | پذیرش autoFit و حذف از remaining | returning/marks/residual | updated state | `algorithms/knapsack_greedy_preemption.py` | fit و current-round protection | موفق |
| KGP-004 | Algorithm 2، خطوط 3-7 | ترتیب نزولی returning و پذیرش مستقیم | tasks/times/residual | accepted IDs | `algorithms/knapsack_greedy_preemption.py` | order/tie/direct fit | موفق |
| KGP-005 | متن صفحه 7؛ ASSUMP-004 | شرط `new_ratio >= 1.05*victim_ratio` | deadline/frozen victim time | eligibility | `algorithms/feasibility.py` | زیر/مرز/بالا | موفق |
| KGP-006 | Algorithm 2؛ ASSUMP-005 | اولین victim snapshot که threshold و fit را دارد | incoming/residual/snapshot | victim ID | `algorithms/knapsack_greedy_preemption.py` | skip insufficient/ascending | موفق |
| KGP-007 | ASSUMP-005/006/010 | حداکثر یک victim، break و حذف victim غیرفعال | state/pair | atomic replacement | `simulation/accounting.py`, `algorithms/knapsack_greedy_preemption.py` | one victim/later skip/rollback | موفق |
| KGP-008 | ASSUMP-010 | autoFit و direct admission دور جاری قربانی نمی‌شوند | fixed snapshot/new active jobs | protected admissions | `algorithms/knapsack_greedy_preemption.py` | late incoming after pool exhausted | موفق |
| KGP-009 | Algorithm 1 مشترک | استفاده مجدد از Round 1 KG-R و client choice | state/requests/selector | bids/server map | `algorithms/knapsack_greedy_retention.py` | full integration | موفق |
| KGP-010 | معماری مرحله 6 | policy مشترک KG-P | state/requests/times/epoch | `KGPreemptionAuctionResult` | `algorithms/base.py`, `algorithms/knapsack_greedy_preemption.py` | runtime contract | موفق |
| KGP-011 | آزمون کمکی مرحله 10-C | مثال 2 victim، autoFit و 3 returning | one server/6 tasks | JSON | `scripts/run_stage_ten_c_kg_preemption_example.py` | manual/program/hash | اجرا شد؛ اختلاف صفر |

## R. ممیزی مرحله دهم-D: Double Knapsack Retention و مرجع مستقیم [4]

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DKR-001 | v2 Section V-A، PDF p.6؛ [4] Section IV-A2، PDF p.4 | `[استخراج مستقیم]` اجرای knapsack در هر دو round | submitted/returning jobs و server resources | membershipهای R1/R2 | `[پیشنهاد فنی] algorithms/double_knapsack_retention.py` | دو selector مستقل | استخراج شد؛ کد متوقف |
| DKR-002 | [4] Section IV-C، PDF p.4 | `[استخراج از مرجع مستقیم مقاله]` Case 3 در R1 utility را به‌جای count بیشینه می‌کند | job utility و residual | selected subset | همان | objective/feasibility | R1 روشن؛ R2 نامشخص |
| DKR-003 | [4] Algorithm 1، PDF p.5 | `[استخراج از مرجع مستقیم مقاله]` قیمت عضو R1 برابر `U-αU` | Utility/alpha/membership | bid | `[پیشنهاد فنی] algorithms/double_knapsack_pricing.py` | alpha=0.1 | استخراج شد؛ پیاده‌سازی نشد |
| DKR-004 | [4] Algorithm 1، PDF p.5 | `[استخراج از مرجع مستقیم مقاله]` قیمت nonmember به `Under threshold`، violation، `α` و `β` وابسته است | demand/subset/resources/params | bid | همان | هر سه branch | threshold/beta مسدود |
| DKR-005 | [4] Eq. (11)، PDF p.4؛ v2 Sections III-IV | `[نامشخص]` نگاشت violation سه‌بعدی [4] به چهار منبع v2 | job/subset/total capacities | violation | همان | 4D boundary | مسدود |
| DKR-006 | v2 Sections V-A/V-B، PDF pp.6,8؛ [4] Section IV-A2 | `[استخراج مستقیم]` DK-R current jobs را retain و returningها را روی residual بررسی می‌کند | active allocations/returning | admission/rejection | `[پیشنهاد فنی] algorithms/double_knapsack_retention.py` | no-preemption/current retained | semantics پایه روشن |
| DKR-007 | [4] Algorithm 1، PDF p.5 | `[استخراج از مرجع مستقیم مقاله]` عضو R2 پذیرفته می‌شود و `U-U/violation` می‌پردازد؛ غیرعضو به pool می‌رود | R2 membership/violation | price/state | همان | accepted/rejected | فرمول روشن؛ retry آینده نامشخص |
| DKR-008 | [4] Section IV-C، PDF p.4؛ v2 Section V-A3، PDF p.7 | `[نامشخص]` GA کامل؛ [4] فقط `g≈50` و v2 برای KG فقط `g≈30` و pyeasyga می‌دهد | tasks/capacity/seed/config | subset | `[پیشنهاد فنی] algorithms/knapsack.py` | seeded regression | hyperparameterها مسدود |
| DKR-009 | [4] Section VI-B، PDF p.8 | `[استخراج از مرجع مستقیم مقاله]` batch هر timestep knapsack دارد و price به success count وابسته است | temporal demands/deadlines | memberships/price | `[پیشنهاد فنی] algorithms/double_knapsack_batch.py` | timeline/discount | فرمول price مسدود |
| DKR-010 | [4] Sections II/IV؛ v2 نمونه PDF p.7 | `[نامشخص]` tie-breaking client و subsetهای هم‌ارزش | equal prices/solutions | chosen server/subset | همان | seeded/equal cases | مسدود |
| DKR-011 | ممیزی منبعی مرحله 10-D | `[پیشنهاد فنی]` گزارش تطبیق و تصمیم کفایت | دو PDF | gap register | `outputs/stage_ten_d_double_knapsack_reference4_audit.md` | hash/render/evidence trace | تکمیل شد |

## S. ممیزی مرحله دهم-E: مرجع مستقیم [1] و شکاف‌های DK-R

| شناسه | بخش یا صفحه مقاله | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DKR1-001 | [1] Section II، PDF p.2 | `[استخراج از مرجع مستقیم مقاله]` دو دور، انتخاب کمترین price، تخصیص R2 و امکان resubmit | requests/bids/returning | server choice/pool | `[پیشنهاد فنی] algorithms/double_knapsack_retention.py` | two-round/retry metadata | استخراج شد؛ tie نامشخص |
| DKR1-002 | [1] Section IV، PDF p.4 | `[استخراج از مرجع مستقیم مقاله]` هدف R2 بیشینه‌سازی served utility است | returning jobs/resources | utility-max subset | همان | objective comparison | DK-GAP-01 تا حد زیادی رفع شد |
| DKR1-003 | [1] Section V-A1، PDF p.6 | `[استخراج از مرجع مستقیم مقاله]` baseline در هر round multi-dimensional knapsack دارد و non-preemptive job تا completion می‌ماند | requests/returning/residual | price/final placement | همان | retention/no-preemption | تأیید شد |
| DKR1-004 | [1] Section IV-C، PDF p.5 | `[استخراج از مرجع مستقیم مقاله]` بردار job چهاربعدی storage/computation/upload/download است | utility/four demands | 4D ratios | `[پیشنهاد فنی] algorithms/double_knapsack_pricing.py` | 4D mapping | بعد چهارم تأیید؛ Eq.11 adaptation نامشخص |
| DKR1-005 | [1] Eq. (25)، PDF p.5 | `[استخراج از مرجع مستقیم مقاله]` congestion روش Clustering سه جزء و scaling نامعین دارد | residual/demand/f | price discount | خارج از DK-R | provenance guard | نباید به DK-R نسبت داده شود |
| DKR1-006 | [1] Section IV-D و Algorithm 1، PDF pp.5-6 | `[استخراج از مرجع مستقیم مقاله]` الگوریتم current+returning و preemption متعلق به روش Clustering+Preemption است | total capacity/current/returning | keep/preempt/admit | خارج از DK-R | provenance guard | به DK-R تعمیم داده نشد |
| DKR1-007 | [1] Section IV-D، PDF p.5 | `[استخراج از مرجع مستقیم مقاله]` GA آماده با `g≈50`؛ سایر تنظیمات غایب | candidates/capacity | stochastic subset | `[پیشنهاد فنی] algorithms/knapsack.py` | seed/config/exact oracle | DK-GAP-04 باقی است |
| DKR1-008 | [1] Section II، PDF p.2 | `[استخراج از مرجع مستقیم مقاله]` پردازش batch سه‌مرحله‌ای است؛ فرمول success-count price ندارد | temporal resources | batch allocation | `[پیشنهاد فنی] algorithms/double_knapsack_batch.py` | pricing formula | DK-GAP-05 باقی است |
| DKR1-009 | ممیزی 1.pdf و تصمیم کاربر 2026-08-10 | `[فرض بازتولید]` ASSUMP-011/012/014 تصویب و ASSUMP-013 مشروط تصویب شد | gaps/source evidence | approved decision set | `docs/assumptions.md` | no hidden default | ثبت شد؛ منتظر ممیزی [28] |
| DKR1-010 | تصمیم کاربر 2026-08-10 | `[نامشخص]` Batch DK-R بدون فرمول success-count pricing | batch jobs/timesteps | price | `[پیشنهاد فنی] algorithms/double_knapsack_batch.py` | no fabricated formula | blocked؛ خارج از پیاده‌سازی فعلی |

## T. ممیزی مرحله دهم-F: pyeasyga [28]

| شناسه | منبع | مفهوم/تنظیم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GA28-001 | [28]؛ PyPI و docs 0.3.1 | `[استخراج از مرجع مستقیم مقاله]` نسخه نزدیک به citation سال 2016 برابر 0.3.1 | dependency metadata | pinned version | `pyproject.toml` | import/version | pin و نصب شد؛ import 0.3.1 تأیید شد |
| GA28-002 | API/source 0.3.1 | `[استخراج از مرجع مستقیم مقاله]` defaults: population 50، crossover 0.8، mutation 0.2، elitism/maximise true | constructor | GA config | `[پیشنهاد فنی] algorithms/genetic_knapsack.py` | metadata/default audit | کامل |
| GA28-003 | source 0.3.1 | `[استخراج از مرجع مستقیم مقاله]` tournament selection با size=`population//10` | population | selected parent | همان | size 5/20 | کامل |
| GA28-004 | source 0.3.1 | `[استخراج از مرجع مستقیم مقاله]` one-point crossover و one-bit mutation | parent genes/RNG | children | همان | deterministic seeded operators | کامل |
| GA28-005 | source 0.3.1 | `[استخراج از مرجع مستقیم مقاله]` elitism یک best chromosome را حفظ می‌کند | ranked population | next population | همان | elite retained | کامل |
| GA28-006 | مثال رسمی MKP | `[استخراج از مرجع مستقیم مقاله]` population 200 و fitness صفر برای infeasible | MKP candidates/capacity | feasible-valued fitness | همان | infeasible/optimal helper | population با default عمومی متعارض |
| GA28-007 | ASSUMP-013 | `[فرض بازتولید؛ تأییدشده]` generations=50 و ثبت کامل config/seed؛ Exact فقط کمک‌آزمون | config/tasks | subset/metadata | `algorithms/genetic_knapsack.py` | 50 generations/no exact substitution | پیاده‌سازی و آزمون شد |
| GA28-008 | ممیزی مرحله 10-F و تصمیم کاربر 2026-08-10 | `[فرض بازتولید؛ تأییدشده]` ASSUMP-015: population 200، tournament 20؛ population 50 فقط sensitivity | config | official GA setting | `docs/assumptions.md` | population metadata | تصویب شد؛ مسدودکننده رفع شد |
| GA28-009 | source 0.3.1 و ASSUMP-015 | `[فرض بازتولید؛ تأییدشده]` seed ورودی اجباری؛ RNG خصوصی به module-level random منتقل و state فراخواننده بازیابی شود | caller seed | reproducible RNG stream | `algorithms/genetic_knapsack.py` | rerun equality/global-state preservation | پیاده‌سازی و آزمون شد؛ seed مقاله نامشخص |

## U. مرحله دهم-G: پیاده‌سازی Pipeline Double Knapsack Retention

| شناسه | بخش/منبع | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DKR-IMP-001 | v2 Section V-A؛ [4] Section IV-A2 | `[استخراج مستقیم]` Round 1 یک knapsack بیشینه‌سازی Utility روی residual هر server است | requesting/residual | selected subset | `algorithms/double_knapsack_retention.py` | R1 subset/feasibility | کامل |
| DKR-IMP-002 | [4] Algorithm 1 و Case 3؛ ASSUMP-011/012 | `[استخراج از مرجع مستقیم مقاله]` و `[فرض بازتولید]` قیمت R1 برای selected، feasible non-selected و impossible | utility/subset/f/capacity | server bids | `algorithms/pricing.py` | سه شاخه قیمت | کامل |
| DKR-IMP-003 | v2 مثال صفحه 7؛ ASSUMP-014 | `[فرض بازتولید]` کمینه‌قیمت و انتخاب یکنواخت seeded در تساوی acceptable | bids/seed | selected server | `algorithms/double_knapsack_retention.py` | deterministic RNG/member guard | کامل |
| DKR-IMP-004 | v2 Sections V-A/V-B؛ [1] Eq. (16)؛ [4] Section IV-A2 | `[استخراج مستقیم]` Round 2 کوله‌پشتی Utility روی residual با حفظ current jobs و بدون preemption | returning/residual | accept/reject | `algorithms/double_knapsack_retention.py` | retained/no-preemption/invariants | کامل |
| DKR-IMP-005 | [4] Case 3؛ ASSUMP-012 | `[استخراج از مرجع مستقیم مقاله]` و `[فرض بازتولید]` قیمت پذیرفته‌شده R2 برابر `U-U/violation` با چهار بعد | selected subset/f | final price | `algorithms/pricing.py` | numeric formula | کامل |
| DKR-IMP-006 | [28] pyeasyga 0.3.1؛ ASSUMP-013/015 | `[استخراج از مرجع مستقیم مقاله]` و `[فرض بازتولید]` GA رسمی 200/20/50 با عملگرهای ممیزی‌شده | capacity/tasks/seed | feasible binary subset | `algorithms/genetic_knapsack.py` | exact comparison/fixed seed | کامل |
| DKR-IMP-007 | ASSUMP-012/015 | `[فرض بازتولید]` محاسبه یک‌باره `f` در workload و ثبت تمام تنظیمات | workload/config | run metadata | `configs/stage10g_pipeline_dkr_example.json` | metadata completeness/stale workload | کامل |
| DKR-IMP-008 | تصمیم کاربر | `[ابزار کمکی]` حل دقیق فقط oracle مسئله کوچک است | small candidates | objective/feasibility check | `algorithms/knapsack.py` | GA vs Exact unique optimum | کامل؛ خارج از مسیر رسمی |
| DKR-IMP-009 | تصمیم کاربر | `[نامشخص]` Batch success-count pricing | batch history | batch price | ایجاد نشد | no fabricated formula | blocked |

## V. مرحله دهم-H: ممیزی Pipeline Double Knapsack Preemption

| شناسه | بخش/منبع | مفهوم/فرمول/الگوریتم | ورودی | خروجی | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DKP-001 | v2 Section V-B، PDF p.8 | `[صریح در مقاله]` فقط Round 2 نسبت به Double Knapsack تغییر می‌کند | DK-R R1 | returning jobs/server choices | `algorithms/double_knapsack_preemption.py` | unchanged-R1 regression | کامل |
| DKP-002 | v2 Section V-B، PDF p.8 | `[صریح در مقاله]` knapsack روی total capacity و اجتماع current+returning اجرا می‌شود | active+returning/total capacity | member subset | همان | combined pool/total capacity | کامل |
| DKP-003 | v2 Section V-B، PDF p.8 | `[صریح در مقاله]` member score=`1000+U/time_remaining` و nonmember score=`1+U/time_remaining` | membership/U/time | score | همان | both score branches | کامل |
| DKP-004 | v2 Section V-B، PDF p.8 | `[صریح در مقاله]` بررسی fit به ترتیب نزولی score؛ membership اولویت اول و ratio اولویت دوم | scored jobs | ordered fit decisions | همان | order/resource updates | کنترل‌جریان ناقص |
| DKP-005 | v2 Section V-B، PDF p.8 | `[صریح در مقاله]` هر تعداد job ممکن است preempt شود و مزیت current فقط time_remaining کمتر است | current jobs | zero-to-many preemptions | همان | multi-preemption/no ASSUMP-010 | قاعده کلی کامل |
| DKP-006 | [1] Section IV-D و Algorithm 1، PDF pp.5-6 | `[استخراج از مرجع مستقیم مقاله]` روش متفاوت Clustering+Preemption current و returning را با total capacity بازآرایی و current خارج‌شده را preempt می‌کند | current+returning | retain/preempt/admit | فقط شاهد تفسیری | provenance guard | قابل تعمیم مستقیم نیست |
| DKP-007 | [4] Section IV-A2/Algorithm 1، PDF pp.4-5 | `[استخراج از مرجع مستقیم مقاله]` DK پایه Round-2 membership را به پذیرش و قیمت متصل می‌کند، اما gap-fill پیش‌دستانه ندارد | returning/subset | accept/price | pricing boundary | nonmember accepted price | فرمول DK-P ناکافی |
| DKP-008 | IEEE TPDS 2025 Section V-B، PDF p.8 | `[منبع تکمیلی خارج از مبنای v2]` متن DK-P همان تعریف v2 را تکرار می‌کند و شبه‌کد/قیمت/tie جدیدی نمی‌دهد | ambiguity list | no new resolution | docs only | version provenance | بررسی شد |
| DKP-009 | ASSUMP-016 | `[فرض بازتولید؛ تأییدشده]` repack اتمیک از total capacity و نگاشت fit به retain/admit یا preempt/reject | combined pool | new active set | `algorithms/double_knapsack_preemption.py` | manual state transition | پیاده‌سازی و آزمون شد |
| DKP-010 | ASSUMP-017 | `[فرض بازتولید؛ تأییدشده]` score لفظی، freeze time و fail-fast روی tie/تناقض اولویت | scores | deterministic order/error | همان | equal/cross-tier boundary | پیاده‌سازی و آزمون شد |
| DKP-011 | ASSUMP-018 | `[فرض بازتولید؛ تأییدشده]` تعمیم GA ممیزی‌شده 200/20/50 و seed اجباری به DK-P R2 | GA config/pool | subset/metadata | `algorithms/genetic_knapsack.py` | fixed seed/exact auxiliary | پیاده‌سازی و آزمون شد |
| DKP-012 | ASSUMP-019 | `[فرض بازتولید؛ تأییدشده]` عدم ساخت قیمت اقتصادی R2 بدون فرمول معتبر | decisions/scores | no fabricated price | `PipelineDKPAuctionResult` | absent-price contract | پیاده‌سازی و آزمون شد |
| DKP-013 | مرحله دهم-I | `[پیشنهاد فنی]` current allocation باید پیش از repack با `Task.demand` برابر باشد؛ در غیر این صورت fail-fast | active allocation/task | validated pool | `algorithms/double_knapsack_preemption.py` | mismatched active allocation | کامل؛ از تفسیر پنهان elasticity جلوگیری می‌کند |
| DKP-014 | مرحله دهم-I | `[آزمون کمکی]` مقایسه GA با Exact روی مثال چهاروظیفه‌ای دارای optimum یکتا | total capacity/pool | objective gap | `tests/integration/test_stage_ten_i_pipeline_dkp.py` | membership/objective | کامل؛ جایگزین GA نیست |

## W. مرحله دهم-J: رگرسیون مشترک چهار policy

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل کد | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REG-001 | `[پیشنهاد فنی]` معماری مرحله 6 | قرارداد ساختاری مشترک policy و result با ویژگی‌های فقط‌خواندنی | state/requesting/time | accepted/rejected/final state | `algorithms/base.py` | تطبیق runtime و mypy | کامل |
| REG-002 | `[پیشنهاد فنی]` مرحله 10-J | اجرای مستقل policyها روی snapshot یکسان و جلوگیری از mutation ورودی | policy specs/state | normalized records | `evaluation/policy_comparison.py` | mutating-policy negative test | کامل |
| REG-003 | `[آزمون کمکی]` مثال مشترک | مقایسه KG-R، KG-P، Pipeline DK-R و Pipeline DK-P در یک مزایده | 1 server/4 tasks | accept/reject/retain/preempt | `scripts/run_stage_ten_j_four_policy_regression.py` | manual outcome integration | کامل؛ نتیجه مقاله نیست |
| REG-004 | ASSUMP-015/018 | تنظیم رسمی GA برای دو Pipeline DK برابر 200/20/50 و seed اجباری | config/workload | subset و metadata | `configs/stage10j_four_policy_regression.json` | fixed-seed repeat | کامل |
| REG-005 | `[ابزار کمکی]` | Exact selector برای KG فقط جهت جداسازی آزمون کنترل‌جریان از تنظیم GA نامشخص KG | KG requests/residual | exact small subset | `ExactUtilityKnapsackSelector` | provenance metadata | کامل؛ جایگزین رسمی نیست |
| REG-006 | `[آزمون کمکی]` | `active_utility_after_auction` مجموع Utility تخصیص‌های فعال پس از یک مزایده است | final active set | scalar 22 یا 33 | `evaluation/policy_comparison.py` | warning/schema assertion | کامل؛ completed Utility مقاله نیست |

## X. مرحله یازدهم-A: ممیزی مولد داده مصنوعی

| شناسه | بخش/منبع | مفهوم/پارامتر | ورودی | خروجی آینده | فایل کد آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SYN-001 | v2 Section VI-A2، PDF p.8، Table I | هشت server و توزیع Normal چهار ظرفیت server | seed/config | server records | `datasets/synthetic.py` | sample moments/positivity | پارامترها کامل؛ RNG نامشخص |
| SYN-002 | v2 Table I، PDF p.8 | توزیع Normal پنج ویژگی job و Utility | seed/arrival count | Normal job records | همان | moments/units/deadline | پارامترها کامل؛ conversion نامشخص |
| SYN-003 | v2 Section VI-A2، PDF p.8 | arrival count برابر `N(14,4)` در هر slot | seed/horizon | arrival vector | همان | integer/nonnegative/moments | horizon و rounding مسدود |
| SYN-004 | v2 Section VI-B2 و Table II، PDF p.10 | ویژگی‌های job Bimodal | seed/count | Bimodal job records | همان | component moments | پارامترها کامل |
| SYN-005 | v2 Section VI-B2، PDF p.10 | سهم دقیق 90% low و 10% high | total jobs/seed | class labels | همان | exact quota/repeatability | total غیرمضرب 10 نامشخص |
| SYN-006 | مدل Eqs. (6)-(7) در برابر Tables I-II | output size `s'_j` در جدول‌های داده وجود ندارد | generated job | full pipeline record | ایجاد نمی‌شود | omission guard | مسدود؛ ASSUMP-026 پیشنهادی |
| SYN-007 | v2 کامل/source package | seed، RNG، correlation، truncation و rounding گزارش نشده‌اند | distributions | deterministic draws | `datasets/random.py` | fixed-seed/golden metadata | ASSUMP-020..023 پیشنهادی |
| SYN-008 | [4] PDF p.5 و [1] PDF p.7 | horizonهای 200+20 و 30 متعلق به workloadهای متفاوت‌اند | source comparison | no inherited default | config layer | provenance guard | قابل تعمیم مستقیم به v2 نیست |
| SYN-009 | IEEE TPDS 2025، pp.9,11 | `[منبع تکمیلی خارج از مبنای v2]` جدول‌ها تکرار می‌شوند ولی شکاف‌ها رفع نمی‌شوند | ambiguity list | no new setting | docs only | version provenance | بررسی شد |
| SYN-010 | Stage 11-A | metadata، CSV و نمودار تشخیصی | generated records | reproducible artifacts | `scripts/generate_synthetic.py` | rerun hash/statistical diagnostics | `[پیشنهاد فنی]`؛ اجرا نشده |

## Y. مرحله یازدهم-B: پیاده‌سازی مولدهای داده مصنوعی

| شناسه | بخش/منبع | مفهوم/پارامتر | ورودی | خروجی | فایل کد | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SYNB-001 | v2 Section VI-A2، PDF p.8، Table I؛ ASSUMP-020..024 | مولد Normal هشت سرور و ویژگی‌های وظیفه با marginalهای مستقل و واحدهای لفظی جدول | config و seed اجباری | رکورد سرور/وظیفه/ورود | `datasets/synthetic.py` | ثوابت، مثبت‌بودن، momentها، seed ثابت | کامل؛ `[صریح در مقاله]` برای پارامترها و `[فرض بازتولید]` برای mechanics |
| SYNB-002 | v2 Section VI-B2، PDF p.10، Table II؛ ASSUMP-024..025 | مولد Bimodal با arrival ارث‌بری‌شده و سهم دقیق 90/10 | config و total divisible by 10 | low/high records | `datasets/synthetic.py` | quota، shuffle، guard نامضرب ده | کامل با `[فرض بازتولید]` |
| SYNB-003 | ASSUMP-020 | `SeedSequence.spawn` و PCG64 با ۱۴ stream نام‌دار | seed | RNGهای مستقل | `datasets/synthetic.py` | fixed-seed equality و metadata | کامل |
| SYNB-004 | ASSUMP-022 | rejection sampling، raw draw و nearest-half-up با مرز deadline/arrival | RNG و NormalSpec | مقدار معتبر و rejected count | `datasets/synthetic.py` | مرز نیم، منفی، deadline و arrival | کامل |
| SYNB-005 | ASSUMP-026..027 | رکورد allocation-only، حذف صریح `s'_j` و ID پایدار یک‌مبنا | نمونه‌ها | مدل دامنه و CSV | `datasets/synthetic.py`, `datasets/artifacts.py` | schema، omission، ترتیب ID | کامل |
| SYNB-006 | `[پیشنهاد فنی]` مرحله 11-B | artifactهای deterministic شامل CSV و JSON metadata | dataset | چهار فایل برای هر workload | `datasets/artifacts.py` | بازخوانی و byte repeatability | کامل |
| SYNB-007 | `[آزمون کمکی]` مرحله 11-B | کنترل moment با حدود چهار standard error و نمودارهای تشخیصی | dataset/spec | JSON و PNG/SVG | `datasets/diagnostics.py` | همه checkهای واجد شرایط؛ server n=8 فقط اطلاعاتی | کامل؛ نتیجه مقاله نیست |
| SYNB-008 | ASSUMP-024 | envelope صریح 102 arrival slot و صفر drain slot با seed 20240811 | JSON config | 1410 task در هر workload | `configs/synthetic_*_stage11b_auxiliary.json` | schema و اجرای CLI | کامل؛ envelope کمکی و نه horizon مقاله |
| SYNB-009 | مرحله 11-B | فرمان سطح‌بالای تولید و جداسازی data/result/figure | config path | artifacts و خلاصه اجرا | `scripts/generate_synthetic.py` | integration و اجرای واقعی دو workload | کامل |
| SYNB-010 | مرحله 11-B | تکرارپذیری کل خروجی | دو اجرای متوالی | SHA-256 برابر برای ۲۲ فایل | خروجی‌های Stage 11-B | مقایسه byte-level | کامل؛ ۲۲ از ۲۲ بدون تغییر |

## Z. مرحله دوازدهم-A: ممیزی trace واقعی Southampton

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل آینده | آزمون لازم | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SOT-001 | v2 Section VI-B3، pp.10-12 | trace چهار ساله Southampton و window سه‌روزه April 2021 | raw trace | selected records | `datasets/southampton.py` | checksum/date filter | raw و تاریخ دقیق مسدود |
| SOT-002 | v2 p.10 | auction هر 10 دقیقه | timestamp/timezone/origin | arrival slot | همان | boundary/off-by-one | timezone/origin مسدود |
| SOT-003 | v2 Figs.16-18؛ [1] Figs.7-9 | storage/computation/deadline histogram | selected records | distributions | `visualization/trace_diagnostics.py` | bin/normalization/row count | فقط raster؛ داده پشت شکل مفقود |
| SOT-004 | v2 p.10؛ [1] p.8 | user group → high/medium/low | anonymized group | priority | `datasets/southampton.py` | exhaustive coverage | mapping فقط مثالی و ناقص |
| SOT-005 | `[استخراج از مرجع مستقیم مقاله]` [1] Table III، p.9 | Utilityهای High/Medium/Low برابر N(100,10)/N(40,10)/N(20,4) | priority/RNG | Utility | همان | distribution/seed | انتقال به v2 نیازمند فرض و seed مفقود |
| SOT-006 | v2 p.11 | 2×768GB و 3×192GB node | node config | 5 server storage | `configs/southampton.yaml` | count/capacity | storage تا حد زیادی کامل |
| SOT-007 | v2 p.11 | node statistics برای storage و computation | node specs | `S_i`, `C_i` | همان | units/feasibility | RAM موجود؛ compute capacity عددی مفقود |
| SOT-008 | v2 p.11 | `B_d×slot ~ N(10,0.2)` GB | RNG/seed | download capacity | همان | seed/positivity | توزیع موجود؛ seed مفقود |
| SOT-009 | مدل در برابر Fig.17/[1] Fig.8 | `K_j` مدل MFlops است ولی computation chart بر حسب Gigabytes | raw compute field | `K_j` | `datasets/southampton.py` | unit conversion | ناسازگار و مسدود |
| SOT-010 | v2/[1]/IEEE 2025/source tar/web audit | دسترسی dataset/code | source artifacts | availability decision | docs only | URL/license/schema | dataset عمومی قابل‌تأیید یافت نشد |
| SOT-011 | v2 Fig.20 | cap deadline به 2h=12 slot | deadline | capped deadline | `configs/southampton_capped.yaml` | exact boundary/rounding | تبدیل کلی و semantics cap ناقص |
| SOT-012 | Stage 12-A | ممیزی source/schema و گزینه‌های ادامه | PDF/source/web | gap register | `outputs/stage_twelve_a_southampton_trace_audit.md` | page/hash/visual review | کامل؛ preprocessing متوقف |

## AA. مرحله دوازدهم-B: digitization شکل‌های Southampton

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل کد/سند | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SOTB-001 | v2 Figs.16-18 و source رسمی v2 | استخراج سه PNG رسمی با hash ثابت و نگهداری جدا از raw trace | source tar | published PNG | `data/raw/published_figures/arxiv_v2/` | SHA-256 و ابعاد | کامل؛ `[استخراج مستقیم]` |
| SOTB-002 | `[پیشنهاد فنی؛ آزمون کمکی]` | استخراج مؤلفه‌های رنگی قابل‌مشاهده با RGB دقیق و کالیبراسیون دو نقطه‌ای | published PNG | 33 component | `datasets/histogram_digitization.py` | component count و bounds | کامل؛ bin واقعی ادعا نمی‌شود |
| SOTB-003 | v2 Figs.16-17 | Storage و Computation از pixel row 58 به پایین کاملاً یکسان‌اند | دو PNG | duplication flag | همان | pixel equality | کامل؛ computation مستقل مسدود |
| SOTB-004 | `[پیشنهاد فنی]` | جداسازی published/digitized/generated/results | artifact type | path isolation | `data/*/README.md`, `results/raw/surrogate/README.md` | integration path assertions | کامل |
| SOTB-005 | `[آزمون کمکی]` | overlay تشخیصی bounding box مؤلفه‌ها | PNG و component CSV | 3 PNG | `figures/diagnostics/stage12b/` | بازبینی بصری | کامل؛ نتیجه مقاله نیست |
| SOTB-006 | ASSUMP-028..032 | sampling از visible area، count، independence، schema محدود و RNG | digitized components/config | surrogate محدود | `datasets/southampton_surrogate.py` | distribution/repeatability/omission | تصویب و در Stage 12-C اجرا شد |

## AB. مرحله دوازدهم-C: surrogate کیفی Southampton

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل کد/سند | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SOTC-001 | ASSUMP-028 | وزن normalized `pixel_count` و Uniform روی visible x bounds | digitized components | sampled storage/deadline | `datasets/southampton_surrogate.py` | frequency/mean/bounds | کامل؛ `[فرض بازتولید]` |
| SOTC-002 | ASSUMP-029 | 10000 رکورد صریح برای هر priority | config | 30000 record متوازن | همان | exact count | کامل؛ proportion واقعی ادعا نمی‌شود |
| SOTC-003 | ASSUMP-030 | استقلال storage و deadline مشروط به priority | 12 named RNG streams | paired marginal records | همان | stream metadata/fixed seed | کامل؛ joint trace بازتولید نشده |
| SOTC-004 | ASSUMP-031 | schema چهارفیلدی و omission صریح computation/arrival/Utility/network/output | samples | surrogate CSV | `southampton_surrogate_artifacts.py` | exact schema/omission | کامل؛ ورودی الگوریتم نیست |
| SOTC-005 | ASSUMP-032 | PCG64، seed اجباری و `parameter_tuning_performed=false` | seed 20240812 | deterministic artifacts | config/metadata | two-run byte comparison | کامل؛ seed مقاله نیست |
| SOTC-006 | `[آزمون کمکی]` | شش کنترل visible-area law با مرز 5 standard error | dataset/supports | diagnostics JSON | `southampton_surrogate_diagnostics.py` | 6 pass/0 fail | کامل؛ نتیجه مقاله نیست |
| SOTC-007 | `[آزمون کمکی]` | source raster کنار histogram تولیدشده با 60 bin ثابت | source/generated | PNG/SVG | همان | visual review/file checks | کامل؛ فقط مقایسه کیفی |
| SOTC-008 | `[پیشنهاد فنی]` | fail-fast روی تغییر hash تصاویر و manifest ناسازگار | provenance files | error یا validated dataset | همان | corrupted-source negative test | کامل |

## AC. مرحله سیزدهم-A: specification آزمایش‌ها و readiness audit

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل کد/سند | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXPA-001 | v2 Section VI، pp.8-12 | 12 خانواده آزمایش مستقل | Stage-5 protocol | 12 JSON spec | `configs/experiments/*.json` | registry completeness | کامل؛ non-executable |
| EXPA-002 | v2 Figs.3-20 | نگاشت هر evaluation figure دقیقاً به یک experiment | figure number | unique target | registry/specs | exact cover 3..20 | کامل |
| EXPA-003 | کل Section VI | seed/repeats/horizon/drain/aggregation گزارش‌نشده | paper gaps | `null` run control | experiment specs | no-hidden-default guard | کامل؛ unresolved |
| EXPA-004 | Stages 9-10 | تفکیک single-auction regression از temporal paper experiment | current code | capability status | `docs/experiment_protocol.md` | implementation-boundary assertions | کامل |
| EXPA-005 | Stage 10-G و source [4] | Batch DK-R price مفقود | batch specs | blocked status | batch JSON specs | gap assertion | کامل؛ blocked |
| EXPA-006 | Stage 12-A/C | official trace blocked و surrogate فقط qualitative | trace specs | official/auxiliary split | trace JSON specs | surrogate misuse guard | کامل |
| EXPA-007 | v2 Section III، p.2 | rejected client may resubmit، بدون client policy | temporal runner | decision ID | PIPE/BATCH specs | future state-transition tests | unresolved؛ قبل از اجرا نیازمند تصمیم |
| EXPA-008 | v2 Fig.1 و Section III | arrival→bid→process epoch lag | arrivals | event ordering | future experiment runner | epoch-boundary tests | جزئی؛ ordering کامل نامشخص |
| EXPA-009 | v2 Section VI-A3 | Preempted یعنی ever-preempted overlay | event log | metric overlay | future aggregator | overlap/dedup tests | تعریف اصلی موجود؛ terminal categories نامشخص |
| EXPA-010 | Stage 13-A | harness عمومی با unresolved gating و smoke موجود | specs/policy regression | isolated raw run | future Stage 13-B | byte repeatability | `[پیشنهاد فنی]`؛ هنوز اجرا نشده |

## AD. مرحله سیزدهم-B: harness و smoke experiment کمکی

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل کد/سند | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXPB-001 | `[پیشنهاد فنی]` Stage 13-B | execution config مستقل با label اجباری auxiliary | JSON config | validated config | `experiments/orchestration.py` | missing/extra/type/label | کامل |
| EXPB-002 | اصل وفاداری | Stage-13A paper spec قابل اجرا نیست و decision IDها در خطا حفظ می‌شوند | paper spec | `UnresolvedDecisionError` | همان | PIPE-NORMAL negative CLI/unit | کامل |
| EXPB-003 | `[آزمون کمکی]` REG-003 | runner reusable برای چهار policy روی یک مزایده | Stage-10J scenario | 4 normalized records | `experiments/four_policy_smoke.py` | manual outcome regression | کامل؛ نتیجه مقاله نیست |
| EXPB-004 | `[پیشنهاد فنی]` معماری Stage 6 | raw result و manifest جدا با config/input/result hash | resolved run | isolated run directory | `scripts/run_experiment.py` | hash/provenance/schema | کامل |
| EXPB-005 | `[پیشنهاد فنی]` reproducibility | عدم overwrite؛ resume فقط پس از تطبیق hash | existing artifacts | verified skip/error | `experiments/orchestration.py` | overwrite/corruption/incomplete | کامل |
| EXPB-006 | `[پیشنهاد فنی]` batch orchestration | registry محدود، یکتا و اجرای sequential | execution config list | aggregate summary | `scripts/run_all_experiments.py` | run/verified resume | کامل |
| EXPB-007 | `[آزمون کمکی]` | تکرارپذیری نتیجه و manifest در دو root پاک | same inputs/seed | byte-identical artifacts | Stage-13B tests | SHA-256 equality | کامل |
| EXPB-008 | Stage 13-A readiness | harness هیچ آزمایش رسمی را runnable نمی‌کند | 12 paper specs | unchanged blocked status | docs/configs | scientific-label guards | کامل |

## AE. مرحله سیزدهم-C: ممیزی موتور زمانی PIPE-NORMAL

یادداشت اصلاحی: پیام `Selected model is at capacity` فقط توقف سرویس مدل بود و
هیچ ارتباطی با ظرفیت سرور، `K_j/C_i` یا ASSUMP-036 ندارد. ردیف‌های زیر شکاف‌های
علمی مستقل برای پیاده‌سازی آینده‌اند و از آن پیام استنتاج نشده‌اند.

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل کد/سند | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXPC-001 | v2 Fig.1 و Section III، p.3؛ `[استخراج از مرجع مستقیم مقاله]` [1] Section II، p.2 | arrival `e` → bid `e+1`؛ acceptance `e` → processing `e+1` | arrival/auction epoch | eligibility/activation epoch | future `simulation/temporal_engine.py` | epoch-lag boundary | شواهد کامل؛ engine اجرا نشده |
| EXPC-002 | v2 Section IV، p.4؛ Table I، p.8 | `K_j` total ولی `C_i` per-slot است؛ نگاشت مستقیم فعلی از نظر واحد نادرست است | total computation/deadline | per-slot demand | future admission adapter | typical `K>C` but `K/slots<C` | شکاف شناسایی شد؛ ASSUMP-036 پیشنهادی و غیرفعال |
| EXPC-003 | ASSUMP-033 پیشنهادی | seed list صریح، workload مشترک چهار policy و mean aggregation | seeds/policies | paired raw runs/mean | future experiment config/aggregator | pairing/repeatability/no-default | پیشنهادی؛ غیرفعال |
| EXPC-004 | ASSUMP-034 پیشنهادی؛ ASSUMP-024 | envelope اجباری و drain پوشاننده آخرین deadline inclusive | tasks/config | safe stop/fail-fast | future temporal runner | insufficient drain/early terminal | پیشنهادی؛ غیرفعال |
| EXPC-005 | ASSUMP-035 پیشنهادی؛ ASSUMP-001 | progress→complete/release→expire→arrival→auction→commit | epoch state/events | next state | future temporal engine | deadline/preemption/activation order | پیشنهادی؛ غیرفعال |
| EXPC-006 | ASSUMP-036 پیشنهادی | `compute_per_slot=remaining_K/service_slots` و vector چهاربعدی اصلاح‌شده | task/auction epoch | admission demand | future progress/admission module | unit/capacity/late retry | پیشنهادی؛ غیرفعال |
| EXPC-007 | v2 Eqs.(6)-(10)؛ ASSUMP-037 پیشنهادی | `s'_j=s_j` فقط برای Synthetic Normal temporal | Stage-11 task | complete Task | future dataset adapter | output provenance/no mutation of Stage11 artifacts | پیشنهادی؛ غیرفعال |
| EXPC-008 | v2 Eqs.(9)-(10)؛ ASSUMP-038 پیشنهادی | cumulative pipeline update و storage reservation محافظه‌کارانه | active allocation/progress | updated progress/completion | future `simulation/pipeline_progress.py` | proportional precedence/tolerance/release | پیشنهادی؛ غیرفعال |
| EXPC-009 | v2 p.3؛ `[استخراج از مرجع مستقیم مقاله]` [1] p.2؛ ASSUMP-039 پیشنهادی | rejected retry تا feasibility؛ preempted terminal | rejection/preemption | retry/expired/preempted | future lifecycle module | retry cutoff/no preempt retry | پیشنهادی؛ غیرفعال |
| EXPC-010 | v2 Section VI-A3، p.9؛ ASSUMP-040 پیشنهادی | completed/rejected terminal totals و ever-preempted overlay | event log/final states | Figure-6 metrics | future outcome aggregator | dedup/overlay/temporary rejection | پیشنهادی؛ غیرفعال |
| EXPC-011 | v2 Section V-A3، p.7؛ [28] audit؛ ASSUMP-041 پیشنهادی | KG pyeasyga 0.3.1 با 200/20/30 و seed اجباری | tasks/capacity/seed | Round-1 subset | future KG execution config | metadata/fixed seed/Exact auxiliary | پیشنهادی؛ غیرفعال |
| EXPC-012 | v2 Figs.7-8/10 | Normal high/low threshold گزارش نشده و از raster fit نمی‌شود | continuous Utility | class label | none | unresolved guard | blocked؛ هیچ فرض عددی پیشنهاد نشد |
| EXPC-013 | Stage 13-C | هیچ paper run یا engine ساخته نشد؛ PIPE-NORMAL gated باقی ماند | current repo | audit-only docs | `outputs/stage_thirteen_c_pipe_normal_temporal_gap_audit.md` | doc/source/path checks | کامل |

## AF. Stage 13-D approval registration and consistency gate

The user approved ASSUMP-033 through ASSUMP-041 on 2026-08-12. Every item below
is a `[فرض بازتولید]`, not an explicit arXiv-v2 setting. The service message
`Selected model is at capacity` has no scientific or implementation relation to
these decisions.

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل کد/سند | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXPD-001 | ASSUMP-033 مصوب | 30 run؛ root seed فنی 20240812؛ SeedSequence؛ seed list مرتب و مادی‌شده؛ workload جفت‌شده و policy stream مستقل؛ mean | root seed/workload/policies | raw `(seed,policy)` و aggregate | future temporal config/runner؛ `docs/assumptions.md` | no-default/pairing/metadata/mean | مصوب `[فرض بازتولید]`؛ اجرای 30-run خارج از 13-D |
| EXPD-002 | ASSUMP-034 مصوب؛ ASSUMP-024 | `arrival_slots=100` و drain مشتق‌شده تا بیشینه deadline inclusive | generated tasks | configured last slot/realized drain | future temporal config/engine | no-arrival-after-99/early-stop/nonterminal fail-fast | مصوب `[فرض بازتولید]`؛ full horizon خارج از 13-D |
| EXPD-003 | ASSUMP-035 مصوب | progress→completion/release→expiration→arrival→auction→atomic commit؛ lag یک epoch | epoch state/events | next state | `simulation/temporal_engine.py` | arrival/activation/deadline boundaries | مصوب `[فرض بازتولید]`؛ آماده پیاده‌سازی پس از اصلاح‌های A |
| EXPD-004 | ASSUMP-036 و اصلاح 036-A مصوب | `service_slots=D-e`؛ `compute_eligible_slots=service_slots-1`؛ نرخ `remaining_K/compute_eligible_slots`؛ dry-run کامل pipeline | task/auction epoch | canonical admission demand | `simulation/pipeline.py` | positive-K completion/deadline/retry/dry-run | مصوب `[فرض بازتولید]`؛ گزینه A تأیید 2026-08-12 |
| EXPD-005 | ASSUMP-037 مصوب | `s'_j=s_j` فقط برای temporal Synthetic Normal و provenance صریح | Stage-11 task | temporal task | future dataset adapter | provenance/no Stage-11 mutation | مصوب `[فرض بازتولید]` |
| EXPD-006 | ASSUMP-038 و اصلاح 038-A مصوب | cumulative pipeline؛ آغاز مراحل در active slots 1/2/3؛ تقدم نسبتی؛ tolerance `1e-9`؛ release اتمیک completion/preemption/expiration | active reservation/progress | progress/completion/release | `simulation/pipeline.py` | three-slot start/proportional bounds/tolerance/expiration release | مصوب `[فرض بازتولید]`؛ گزینه A تأیید 2026-08-12 |
| EXPD-007 | ASSUMP-039 مصوب | Round-2 rejection→`WAITING_RETRY`؛ یک retry در هر epoch تا feasibility؛ preemption terminal | rejection/preemption | retry/expired/preempted | future lifecycle module | retry cutoff/no restart | مصوب `[فرض بازتولید]`؛ feasibility وابسته به EXPD-010 |
| EXPD-008 | ASSUMP-040 مصوب | Completed/Rejected partition و ever-preempted overlay؛ raw auction rejection جدا | final states/event log | Figure-6 outcome metrics | future outcome aggregator | partition/dedup/subset invariants | مصوب `[فرض بازتولید]` |
| EXPD-009 | ASSUMP-041 مصوب | KG pyeasyga 0.3.1؛ 200/20/30؛ 0.8/0.2؛ elitism/max؛ audited operators؛ seed اجباری | sorted tasks/capacity/seed | Round-1 subset/metadata | future KG GA selector/config | deterministic seed/settings/Exact auxiliary | مصوب `[فرض بازتولید]`؛ DK 200/20/50 بدون تغییر |
| EXPD-010 | سازگاری ASSUMP-035/036/038 | تعارض نرخ با `compute_eligible_slots=S-1` و dry-run deterministic رفع شد | accepted epoch/deadline/K | executable rate/feasibility | `simulation/pipeline.py`؛ blocker audit | symbolic/numeric/boundary | رفع‌شده با گزینه A مصوب 2026-08-12 |
| EXPD-011 | سازگاری ASSUMP-034/035/038/039 | expiration allocation را اتمیک release می‌کند | active expired allocation | terminal state/free resources | temporal engine/accounting | expiration/resource invariant | رفع‌شده با گزینه A مصوب 2026-08-12 |
| EXPD-012 | v2 Figs.7-8/10 | `NORMAL_HIGH_LOW_THRESHOLDS` تعیین نشده و از barها استخراج/تنظیم نمی‌شود | continuous Utility | unavailable class label | none | unresolved guard | blocked؛ خارج از smoke و Fig.6 total metrics |
| EXPD-013 | ASSUMP-036-A/037/038 | canonical admission، dry-run و cumulative pipeline progress | original task/epoch/reservation | feasible canonical task/progress | `src/edge_reproduction/simulation/pipeline.py` | stage13d unit boundaries | کامل تحت `[فرض بازتولید]` |
| EXPD-014 | ASSUMP-035/038-A/039 | موتور چند-epoch، retry، completion، expiration و preemption terminal | tasks/servers/policy | temporal run/event log | `src/edge_reproduction/simulation/temporal_engine.py` | integration event order/lifecycle | کامل تحت `[فرض بازتولید]` |
| EXPD-015 | ASSUMP-040 | Completed/Rejected partition و preemption overlay | final state/events | TemporalOutcome | `src/edge_reproduction/evaluation/temporal_outcomes.py` | partition/dedup/subset | کامل تحت `[فرض بازتولید]` |
| EXPD-016 | ASSUMP-041 | KG GA 200/20/30 جدا از DK 200/20/50 | mandatory seed/tasks | persistent selector | `algorithms/genetic_knapsack.py` | metadata/invalid config/single-gene compatibility | کامل؛ single-gene adapter `[پیشنهاد فنی]` |
| EXPD-017 | Stage 13-D smoke | چهار policy روی workload مشترک کوچک؛ بدون full run/Fig.6 | smoke JSON | raw JSON | `experiments/temporal_smoke.py`؛ script/config/result | manual outcome/repeatability | کامل `[آزمون کمکی]` |

## AG. Stage 13-E full-run preflight

| شناسه | بخش/منبع | مفهوم | ورودی | خروجی | فایل کد/سند | آزمون | وضعیت |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXPE-001 | ASSUMP-033 مصوب | seedهای 30 workload با `SeedSequence(root_seed=20240812)` به‌صورت uint64 تولید و مرتب شدند؛ چهار child policy seed برای هر workload قابل مشتق‌سازی است | root seed | 30 paired run descriptors | future full config | seed materialization/order/pairing | استخراج مستقیم از فرض مصوب؛ config اجرایی هنوز ساخته نشد |
| EXPE-002 | Stage-13E pilot `[آزمون کمکی]` | Normal با 3 arrival slot، seed `15626834761513784926`، 47 task و max deadline 17 | generator + KG-R | controlled rerun | `outputs/stage_thirteen_e_full_run_preflight_gap_audit.md` | real pilot | rerun پس از ASSUMP-042 موفق: 11 completed، 36 rejected، 74 repair، 24.95s |
| EXPE-003 | pyeasyga 0.3.1 source؛ مثال رسمی MKP | infeasible و empty هر دو fitness صفر؛ rank فقط fitness و tie بدون feasibility preference | final population | possibly infeasible best | audited adapter | reproduce zero tie | شکاف مسدودکننده |
| EXPE-004 | ASSUMP-042 مصوب | repair فقط infeasible best با fitness صفر به all-zero feasible هم‌fitness؛ counter ثبت شود | GA best | feasible subset | `genetic_knapsack.py` | zero/nonzero/no-rerun/metadata | کامل؛ `[فرض بازتولید]`، سه آزمون مرزی و metadata counter |
| EXPE-005 | Stage 13-E/F scope | full 100×30، 120 policy run و Figure 6 اجرا نشدند | full plan | materialized config only | `configs/experiments/pipe_normal_full_stage13f.json` | absence/label check | آماده ولی شروع‌نشده؛ raw result count=0 |
| EXPE-006 | Stage-13E four-policy pilot `[آزمون کمکی]` | همان workload؛ KG-P با policy seed `10214968163706227246` | KG-P + ASSUMP-042 | exact client price tie | `outputs/stage_thirteen_e_full_run_preflight_gap_audit.md` | controlled rerun | epoch 11، job-000032، server-003/server-007؛ fail-fast پس از 76 repair و 25.96s |
| EXPE-007 | ASSUMP-043 مصوب | انتخاب uniform seeded میان minimum-priceهای مساوی KG با همان policy RNG و ثبت counter | tied KG bids | selected server | KG client choice + selector | unique/tie/replay/scope/counter | کامل `[فرض بازتولید]`؛ fixed pilot یک tie و metadata=1 |
| EXPE-008 | Stage-13F pilot `[آزمون کمکی]` | workload مشترک 47-task و چهار policy seed مستقل | چهار policy temporal | چهار outcome کامل | audit report | real bounded execution | KG-R 11/36؛ KG-P 13/34؛ DK-R 10/37؛ DK-P 9/38 و 4 preempted |
| EXPE-009 | ASSUMP-033 full config | 30 workload seed مرتب، 120 policy seed، GA settings و assumptions مادی | root seed 20240812 | immutable JSON | `configs/experiments/pipe_normal_full_stage13f.json` | exact regeneration/tamper | کامل؛ SHA-256 `AFA7C249...EE3F0`، status ready_not_started |
| EXPE-010 | Stage-13F orchestration | اجرای isolated pair، no-overwrite، verified resume و aggregation فقط پس از 120 raw | full config/pair | raw+manifest/mean | `experiments/pipe_normal_full.py` + scripts | resume/missing/tamper | پیاده‌سازی و آزمون شد؛ full execution عمداً اجرا نشد |
| EXPE-011 | Stage-13G timing gate `[آزمون کمکی]` | نخستین workload مادی‌شده، 100 arrival slot، چهار policy ترتیبی | seed `541501192080118187` | 4 raw pair + timing artifact | `results/raw/stage13f/PIPE-NORMAL/seed-541501192080118187/` | hash/resume/partition/time | کامل؛ 1395 task، shared SHA-256، 4/120 raw |
| EXPE-012 | Stage-13G runtime `[آزمون کمکی]` | wall time بیرونی بدون تغییر metadata deterministic | four policy runs | 608.97/619.09/1159.49/1231.16 s | `results/aggregated/stage13g/timing_gate_seed_541501192080118187.json` | serial sum/extrapolation label | مجموع واقعی 60.31 min؛ برون‌یابی خطی 30 seed برابر 30.16h و نتیجه مقاله نیست |
| EXPE-013 | Stage 13-I cloud checkpoint `[آزمون کمکی]` | چهار workload بعدی config مادی‌شده و چهار policy روی workload مشترک | 4 workload seed × 4 policy | 16 raw pair + validated summary | `.github/workflows/stage13i-four-workload-checkpoint.yml`؛ `scripts/record_stage13i_cloud_checkpoint.py` | exact matrix/quoted uint64/hash/partition | کامل؛ run `31629941152` با 17/17 job موفق؛ تجمعی 5/30 workload و 20/120 pair |
| EXPE-014 | Stage 13-I resume/checkpoint integrity `[پیشنهاد فنی]` | دانلود ۱۶ pair و verified resume با config دقیق commit | 16 result/manifest + commit config | 16 × `skipped_existing_verified` | artifacts موقت gitignored؛ `run_full_pair(..., resume=True)` | result/config hash و no-overwrite | کامل؛ mismatch line-ending محلی fail-fast شد و با bytes دقیق commit کنترل شد |
| EXPE-015 | Stage 13-I timing/storage `[آزمون کمکی]` | زمان بیرونی Linux و اندازه artifact، نه runtime مقاله | 16 pair timing files | mean parallel 1189.63s؛ serial equivalent 3.8683h؛ 120,107,828 bytes | `outputs/stage_thirteen_i_four_workload_cloud_checkpoint.md` | recorder محلی/ابر و recursive JSON equality | کامل؛ فقط checkpoint و بدون aggregation علمی |
| EXPE-016 | ASSUMP-033 execution gate | اجرای کامل فقط پس از تصمیم جداگانه؛ checkpoint حق آغاز ۳۰ workload را ندارد | remaining 25 workload / 100 pair | none in Stage 13-I | workflow scope guards | `full_30_repeat_run_completed=false` | اجرای کامل انجام نشده؛ Figure 6 همچنان blocked تا 120/120 raw pair |
| EXPE-017 | Pre-13J protective checkpoint `[پیشنهاد فنی]` | دو کپی پایدار از ۵ workload/۲۰ pair با inventory کامل | Stage 13-H raw + run `31629941152` | 86-file recovery bundle | local `backups/` + central Codex backups؛ protection report | size/SHA-256/manifest/outcome invariants | کامل؛ inventory SHA-256 `28300ed1...e434`؛ raw data gitignored |
| EXPE-018 | Protected recovery/resume `[پیشنهاد فنی]` | resume با config byte-exact هر stage و منع recomputation | 20 result/manifest/workload triples | 20 × `skipped_existing_verified` | `scripts/verify_protected_pipe_normal_checkpoint.py` | before/after payload hashes | کامل از هر دو کپی پایدار؛ payload تغییر نکرد |
| EXPE-019 | Stage 13-J partition `[پیشنهاد فنی]` | 25 workload باقیمانده در پنج batch مستقل 5×4-policy | materialized seeds 6..30 | five gated 20-pair batches | `configs/experiments/stage13j_five_batch_plan.json` | exact partition/no overlap | کامل و آزمون‌شده؛ batchها هنوز اجرا نشده‌اند |
| EXPE-020 | Stage 13-J gated workflow `[پیشنهاد فنی]` | dispatch دستی، confirmation، pair isolation، failed-job rerun، 14-day artifacts و batch validator | selected batch N | 20 pair artifacts + summary/config | `.github/workflows/stage13j-five-workload-batch.yml`؛ `scripts/record_stage13j_batch.py` | manual-only/pins/no-secret/20-pair fixture | آماده ولی اجرا نشده؛ approval جدا پیش از هر batch |
| EXPE-021 | Stage 15-D `[آزمون کمکی]` | سه counterfactual تک‌عاملی برای تفکیک علت repair: penalty ثابت، repair فقط initialization، repair فقط offspring | baseline معتبر Stage 15-C + seed نخست ASSUMP-033 | شش pair DK-R/DK-P، هر pair با دو replay دقیق | `src/edge_reproduction/diagnostics/ga_counterfactual.py`, `scripts/run_stage15d_counterfactual.py`, `scripts/merge_stage15d_counterfactuals.py`, `docs/stage15d_counterfactual_design.md`, `docs/stage15d_rng_gate.md`, `docs/stage15d_report.md` | fixed-shape RNG equality/exact replay/config isolation/feasibility/outcome/public-boundary | کامل؛ Runهای `31716969817` و recovery محدود `31720347641`؛ 6/6 pair پایدار، replay و RNG gate همگی موفق؛ baseline بازاجرا نشد؛ نتیجه فقط تک-seed و کمکی است |
| EXPE-022 | Stage 15-E `[آزمون کمکی]` | اعتبارسنجی محدود پنج-seed برای initialization repair و offspring repair، مستقل و تک‌عاملی | پنج seed نخست ASSUMP-033؛ 10 baseline reuse-only؛ چهار pair seed نخست reuse | 16 pair جدید + 4 pair reuse؛ paired delta و mean/SD/CI کمکی | `scripts/run_stage15e_counterfactual.py`, `scripts/merge_stage15e_validation.py`, `scripts/stabilize_stage15e_artifacts.py`, `.github/workflows/stage15e-limited-multiseed.yml`, `docs/stage15e_report.md` | exact replay/Option-A RNG boundary/20-pair matrix/security/checksum/statistics | کامل؛ Run 31729227438 موفق؛ جهت Utility هر چهار policy/variant در 5/5 seed مثبت؛ final RNG baseline چهار seed جدید `[نامشخص؛ ذخیره‌نشده]` باقی ماند |
| EXPE-023 | Stage 15-F؛ خاتمه تشخیصی Figure 6 | تجمیع شواهد 15-A تا 15-E، تعیین مظنون اصلی و مرز انتساب؛ بدون اجرای محاسباتی | گزارش‌ها و artifactهای اعتبارسنجی‌شده پیشین | گزارش closure، reproduction report جاری و ممیزی اهداف باقی‌مانده | `docs/stage15f_figure6_diagnostic_closure.md`, `docs/reproduction_report.md`, `docs/assumptions.md` | سازگاری وضعیت Figure 6، عدم تغییر pipeline/artifact و پوشش Figs.1–20 | کامل؛ Figure 6 «بازتولید نشد»؛ feasibility chromosome مظنون اصلی ولی علت نهایی `[نامشخص]`؛ Fig.1 نزدیک‌ترین شکل غیرمسدود و R1-DIAG-AUX نزدیک‌ترین هدف ارزیابی‌مانند است |
| EXPE-024 | Stage 15-G؛ Fig.1، PDF p.3، Section III | `[صریح در مقاله]` timeline ورود، bidding، تخصیص/رد، retry و processing؛ `[استخراج مستقیم]` تکرار الگو؛ continuation/dot count `[نامشخص]` | Figure 1، caption و متن ارجاع‌دهنده arXiv v2 | SVG/PDF/PNG، inventory JSON/CSV، manifest و گزارش وفاداری | `scripts/reproduce_figure1.py`, `figures/stage15g/`, `results/aggregated/stage15g/`, `docs/stage15g_figure1.md` | topology و endpoint، evidence labels، SVG editable، PDF/PNG validity، bounds، deterministic hash و QA بصری | کامل؛ بازتولید ساختاری/مفهومی کامل، بدون pixel copy یا اجرای عددی؛ Figure 6 بدون تغییر |

## موارد فاقد اطلاعات کافی

### مسدودکننده‌های وفاداری الگوریتمی

1. `[حل‌شده برای Pipeline DK-R با منبع و فرض]` encoding، fitness و عملگرهای pyeasyga 0.3.1 ممیزی شدند و population/generations/seed با ASSUMP-013/015 تثبیت و پیاده‌سازی شدند. KG و Batch DK همچنان scope جدا دارند.
2. `[حل‌شده با فرض]` percentile با ASSUMP-008 و قیمت ناممکن با ASSUMP-007 پیاده‌سازی شدند.
3. `[حل‌شده برای Pipeline DK-R با فرض]` pricing چهاربعدی/threshold، GA و client tie با ASSUMP-011 تا ASSUMP-015 پیاده‌سازی شدند؛ فقط Batch price مسدود است.
4. `[حل‌شده برای Pipeline DK-R با فرض]` تساوی قیمت client به‌صورت uniform seeded است و تساوی fitness داخلی به pyeasyga واگذار می‌شود؛ tieهای KG و DK-P همچنان scope مستقل‌اند.
5. `[حل‌شده با فرض]` snapshot/live بودن `s.jobs` در KG-P با ASSUMP-010 حل و پیاده‌سازی شد؛ این تصمیم به DK-P تعمیم داده نشده است.

### مسدودکننده‌های مدل و شبیه‌سازی

1. `[نامشخص]` تعریف صریح `s'_j` و توزیع آن در workloadهای مصنوعی وجود ندارد.
2. `[نامشخص]` تبدیل واحد میان MB و GB و تبدیل MFlops/s به مقدار per-slot کامل بیان نشده است.
3. `[نامشخص]` مرز دقیق deadline، ترتیب eventها در یک timestamp و off-by-one پنجره‌های (22)-(27) باید در مرحله سوم تحلیل شود.
4. `[نامشخص]` رفتار resubmission، حداکثر دفعات bidding و وضعیت وظیفه preempted در دورهای بعدی تعیین نشده است.
5. `[نامشخص]` وضعیت storage برای job فاقد computation مثبت، در تعریف `θ_j(n)` مشخص نیست.

### مسدودکننده‌های بازتولید آزمایش

1. `[نامشخص]` seedهای تصادفی، تعداد اجرای مستقل، طول horizon، تعداد کل jobها و روش aggregation گزارش نشده‌اند.
2. `[نامشخص]` truncation توزیع نرمال، گردکردن deadline/arrival count و برخورد با نمونه‌های منفی گزارش نشده‌اند.
3. `[نامشخص]` معیار جداسازی high-value و low-value در workload نرمال مشخص نیست.
4. `[نامشخص]` نسخه/تنظیمات Gurobi، gap، tolerance، threads، time limit، سخت‌افزار و OS گزارش نشده‌اند.
5. `[نامشخص]` داده عددی پشت شکل‌ها در بسته arXiv موجود نیست؛ فقط تصاویر raster وجود دارند.
6. `[نامشخص]` trace خام Southampton، تاریخ دقیق سه روز، schema، mapping اولویت/Utility و ظرفیت computation گره‌ها در دسترس نیست.
7. `[نامشخص]` تصاویر Storage و Computation به‌جز title یکسان‌اند؛ توزیع مستقل computation و تبدیل آن به MFlops قابل بازیابی نیست.

## تصمیم‌های ثبت‌شده

- `[صریح از کاربر]` منبع مبنا فقط arXiv v2 سال 2024 است.
- `[صریح از کاربر]` ASSUMP-001 تا ASSUMP-012 و ASSUMP-014 تصویب شده‌اند؛ ASSUMP-013 مشروط به تکمیل ممیزی [28] و اعلام هر setting مفقود است.
- `[صریح از کاربر]` ASSUMP-015 population رسمی Pipeline DK-R را 200، tournament size را 20، generations را 50 و seed را ورودی اجباری تعیین می‌کند؛ population 50 فقط sensitivity کمکی است.
- `[صریح از کاربر]` Pipeline DK-R تنها scope اجرایی فعلی است؛ Batch DK-R بدون ساخت فرمول دلخواه blocked باقی می‌ماند.
- `[صریح از کاربر]` ASSUMP-020 تا ASSUMP-027 در 2026-08-11 دقیقاً مطابق متن پیشنهادی تصویب و در Stage 11-B پیاده‌سازی شدند؛ envelopeهای نمونه کمکی به horizon مقاله نسبت داده نمی‌شوند.
- `[صریح از کاربر]` preprocessing رسمی Southampton blocked می‌ماند؛ surrogate histogram فقط برای آزمون فنی/کیفی مجاز است، باید از published/digitized/results جدا بماند و نباید با tuning به شکل مقاله نزدیک شود.
- `[صریح از کاربر]` ASSUMP-028 تا ASSUMP-032 در 2026-08-12 مطابق متن پیشنهادی تصویب شدند؛ surrogate فقط آزمون فنی/کیفی است و real trace یا بازتولید عددی مقاله نیست.
- `[Stage 13-A]` هر 12 خانواده آزمایش specification مستقل دارد، اما هیچ paper experiment رسمی هنوز runnable نیست؛ run-controlهای مفقود `null` و executionها gated باقی مانده‌اند.
- مسیرهای کد و نام آزمون‌ها همگی `[پیشنهاد فنی]` و قابل بازنگری در مرحله ششم هستند.
| STAGE15H-AUX | Stage 15-H؛ خارج از روش مقاله | اعتبارسنجی ۳۰-workload دو repair تشخیصی feasibility برای DK-R/DK-P | baselineهای Stage 13-J/13-K؛ repairهای Stage 15-D.1/15-E؛ ۲۵ workload باقی‌مانده | ۱۲۰ repair pair، paired effects، CSV، نمودار و checksum | `scripts/run_stage15h_counterfactual.py`؛ `scripts/finalize_stage15h_validation.py` | reuse 120/120 و 20/20؛ replay/RNG gate؛ completeness؛ security | آماده dispatch؛ `[آزمون کمکی]`؛ Figure 6 بدون تغییر |
| STAGE15K-AUDIT | Stage 15-K؛ arXiv v2 Sections III–VI و شواهد Stage 15-A تا 15-J | ممیزی سخت‌گیری‌های GA، admission، pipeline، pricing و lifecycle؛ تفکیک محل غالب افت از علت قطعی اختلاف | 120/120 baseline، 120/120 repair، Funnel baseline و آمار aggregate repair؛ reuse-only | strictness matrix، candidate corrections و pilot plan | `docs/stage15k_strictness_audit.md`؛ `docs/stage15k_candidate_corrections.md`؛ `results/aggregated/stage15k/` | completeness شواهد، عدم اجرای policy/workload، consistency شمارنده‌ها، اعتبار CSV و security scan | کامل؛ Round-2 feasibility قوی‌ترین مظنون؛ علت قطعی `[نامشخص]`؛ Figure 6 بدون تغییر |
| STAGE15K-PROP-048 | Stage 15-K.1؛ خارج از روش مقاله | پروتکل حفاظتی pilot تک-seed با دو replay و baseline reuse | اولین seed مرتب ASSUMP-033؛ DK-R/DK-P | gate آزمایش مستقل | `scripts/run_stage15k1_pilot.py`؛ workflow Stage 15-K.1 | replay/partition/Utility/Funnel/config/RNG/invariant | تأییدشده فقط به‌عنوان `[فرض آزمون کمکی]` در 2026-09-02؛ خارج از pipeline رسمی |
| STAGE15K-PROP-049 | Stage 15-K.1؛ جزئیات repair در v2 `[نامشخص]` | R2-only initialization feasibility repair با حذف deterministic از canonical tail | candidate pool Round 2، chromosome اولیه | subset feasible بدون draw اضافه | `src/edge_reproduction/diagnostics/ga_counterfactual.py`؛ `scripts/run_stage15k1_pilot.py` | single-factor، draw/call-shape، feasibility، outcome invariant | تأییدشده فقط به‌عنوان `[فرض آزمون کمکی]` در 2026-09-02؛ Figure 6 بدون تغییر |
| STAGE15K-PROP-050 | Stage 15-K.1؛ جزئیات repair در v2 `[نامشخص]` | R2-only offspring feasibility repair | offspring پس از crossover/mutation | offspring feasible بدون draw اضافه | هنوز فایل اجرایی ندارد | مستقل از 049، replay/RNG/feasibility | `[پیشنهادشده و تأییدنشده]`؛ گزینه جایگزین |
| STAGE15K-PROP-051 | Stage 15-K.1؛ minimum-resource formula چاپ نشده | حذف فقط isolated full-pipeline dry-run از gate پیش از Round 1 | canonical vector فعلی | candidate پذیرفتنی برای auction؛ runtime invariant ثابت | هنوز فایل اجرایی ندارد | Funnel shift، expiration، conservation/capacity | `[پیشنهادشده و تأییدنشده]`؛ ریسک متوسط‌بالا |
| STAGE15K-PROP-052 | Stage 15-K.1؛ Section III p.3 | bidding همان epoch ورود | arrival epoch e | bidding epoch e، activation e+1 | هنوز فایل اجرایی ندارد | event order، deadline، RNG call-shape | `[پیشنهادشده و تأییدنشده]`؛ ریسک بالا و خلاف توصیه |
| STAGE15K-PROP-053 | Stage 15-K.1؛ constraints (23),(25),(27) | کاهش lag computation/download | allocation فعال | compute slot1، download slot2 | هنوز فایل اجرایی ندارد | proportional precedence/capacity/deadline | `[پیشنهادشده و تأییدنشده]`؛ ریسک بالا و خلاف توصیه |
