# مرحله پنجم: استخراج پروتکل آزمایش نسخه arXiv v2

## 1. دامنه و منشأ اطلاعات

- منبع مبنا: *Improved Methods of Task Assignment and Resource Allocation with Preemption in Edge Computing Systems*، `arXiv:2403.15665v2`، 29 مارس 2024.
- بخش‌های اصلی: Section V، صفحات 6 تا 8 و Section VI، صفحات 8 تا 12.
- جدول‌های هدف: Table I در صفحه 8 و Table II در صفحه 10.
- شکل‌های هدف: Figs. 1 تا 20.
- منابع مستقیم تکمیلی تأییدشده:
  - `[استخراج مستقیم]` مرجع [1]: *Scalable Resource Allocation Techniques for Edge Computing Systems*، ICCCN 2022، فایل `1.pdf`.
  - `[استخراج مستقیم]` مرجع [4]: *Online Resource Allocation in Edge Computing Using Distributed Bidding Approaches*، MASS 2021، فایل `4.pdf`.
- اطلاعات منابع [1] و [4] فقط در مواردی وارد این سند شده‌اند که v2 مستقیماً workload یا روش آن‌ها را فراخوانده است؛ این اطلاعات با متن صریح v2 مخلوط نشده‌اند.
- نسخه نهایی 2025 استفاده نشده است.
- در این مرحله هیچ کد، config یا داده مصنوعی تولید نشده است.

## 2. خانواده آزمایش‌های مقاله

| شناسه پیشنهادی | پرسش آزمایش | paradigm | workload | روش‌ها | خروجی هدف | وضعیت |
| --- | --- | --- | --- | --- | --- | --- |
| `OPT-25` | آیا Gurobi برای سناریوی منبع [1] optimum می‌دهد؟ | pipeline oracle | synthetic از [1] | Gurobi | incumbent/optimality پس از بیش از 10 روز | `[صریح در مقاله]`؛ instance دقیق مفقود |
| `OPT-18` | فاصله heuristicها از optimum چقدر است؟ | pipeline | synthetic از [1] | Gurobi، DK-P، DK-R، KG-P، KG-R | تعداد job تکمیل‌شده و runtime | `[صریح در مقاله]`؛ seed و نمونه دقیق مفقود |
| `OPT-10` | در بار کوچک‌تر، کیفیت و runtime چگونه‌اند؟ | pipeline | subset سناریوی 18-job | DK-P/DK-R، KG-P، KG-R | تعداد تکمیل و runtime | `[صریح در مقاله]`؛ subset دقیق مفقود |
| `R1-DIAG` | قیمت‌گذاری Round 1 چگونه jobها را هدایت می‌کند؟ | pipeline | Normal | KG-P | Figs. 3-5 | `[صریح در مقاله]`؛ raw run مفقود |
| `PIPE-NORMAL` | کیفیت چهار روش بدون هزینه auction | pipeline | Synthetic Normal | DK-P، DK-R، KG-P، KG-R | Figs. 6-8 | `[صریح در مقاله]`؛ horizon/repeats مفقود |
| `PIPE-NORMAL-TIME` | اثر زمان auction بر deadline | pipeline | همان Normal | چهار روش | Figs. 9-10 | `[صریح در مقاله]`؛ mechanics زمان نامشخص |
| `BATCH-NORMAL` | کیفیت روش‌ها در پردازش سه‌مرحله‌ای | batch | Synthetic Normal | DK-R، KG-P، KG-R | Fig. 11 | `[صریح در مقاله]`؛ علت حذف DK-P بیان نشده |
| `BATCH-NORMAL-TIME` | اثر auction time در batch | batch | همان Normal | DK-R، KG-P، KG-R | Fig. 12 | `[صریح در مقاله]`؛ mechanics زمان نامشخص |
| `BATCH-BIMODAL` | آیا preemption high-valueها را ترجیح می‌دهد؟ | batch | Synthetic Bimodal | DK-R، KG-P، KG-R | Figs. 13-15 | `[صریح در مقاله]`؛ horizon/repeats مفقود |
| `TRACE-DIAG` | توزیع ویژگی‌های trace چیست؟ | batch | Southampton Iridis trace | ندارد | Figs. 16-18 | `[صریح در مقاله]`؛ raw trace مفقود |
| `TRACE-BASE` | KG-P نسبت به KG-R روی trace چگونه است؟ | batch | Southampton trace | KG-P، KG-R؛ DK-R فقط مقایسه متنی | Fig. 19 | `[صریح در مقاله]` |
| `TRACE-CAP-2H` | با deadline حداکثر 2 ساعت، trade-off سرعت/کیفیت چیست؟ | batch | trace اصلاح‌شده | DK-R، KG-P، KG-R | Fig. 20 | `[صریح در مقاله]` |

## 3. جدول جامع پارامترها

### 3.1 پارامترهای مشترک سیستم و الگوریتم

| پارامتر | مقدار مقاله | واحد | توزیع/دامنه | ثابت یا متغیر | محل ذکر | وضعیت بازتولید |
| --- | ---: | --- | --- | --- | --- | --- |
| تعداد ابعاد منابع | 4 | نوع منبع | storage، computation، upload، download | ثابت | Sections III-IV | `[استخراج مستقیم]` کامل در مدل pipeline |
| Utility accrual | all-or-nothing | - | Utility کامل در completion، صفر در preemption | ثابت | Sections IV-V | `[صریح در مقاله]` |
| fit discount | 10 | درصد Utility | `price=0.9U` | ثابت | Section V-A1 | `[صریح در مقاله]` |
| `percentile_weight=c1` | 0.025 | نسبت | ثابت | ثابت | Section V-A1 | `[صریح در مقاله]` |
| `congestion_weight=c2` | 0.025 | نسبت | ثابت | ثابت | Section V-A1 | `[صریح در مقاله]`؛ تابع congestion ناسازگار |
| سقف preemption discount | 5 | درصد Utility | `c1+c2` | ثابت | Section V-A1 | `[صریح در مقاله]`؛ وابسته به normalization |
| آستانه preemption KG-P | 5 | درصد ratio | متن: new حداقل 5% بهتر | ثابت | Section V-A2 | `[صریح در مقاله]`؛ شبه‌کد جهت متفاوت دارد |
| نسل‌های GA در KG Round 1 | تقریباً 30 | generation | pyeasyga | ثابت | Section V-A3 | `[صریح در مقاله]`؛ سایر تنظیمات GA نامشخص |
| DK-P score عضو knapsack | `1000+U/time_remaining` | score | حقیقی | متغیر | Section V-B | `[صریح در مقاله]` |
| DK-P score غیرعضو | `1+U/time_remaining` | score | حقیقی | متغیر | Section V-B | `[صریح در مقاله]` |
| تعداد کاربران مستقل | `[نامشخص]` | client | - | - | کل مقاله | هر job مانند client رفتار می‌کند؛ ownership تعریف نشده |
| تعداد تکرار | `[نامشخص]` | run | - | - | Section VI، صفحات 8-12 | مسدودکننده تجمیع |
| Random seed | `[نامشخص]` | - | - | - | کل v2 | مسدودکننده تکرار دقیق |

### 3.2 Synthetic Normal

همه نمادهای `N(μ,σ)` در این جدول با پارامتر دوم به‌عنوان standard deviation گزارش شده‌اند، زیرا عنوان ستون Table I برابر `σ` است.

| پارامتر | مقدار مقاله | واحد | توزیع/دامنه | ثابت یا متغیر | محل ذکر | وضعیت بازتولید |
| --- | ---: | --- | --- | --- | --- | --- |
| تعداد server | 8 | server | ثابت | ثابت | Section VI-A2، صفحه 8 | `[صریح در مقاله]` |
| server storage `S_i` | `N(540,30)` | MB در Table I | Normal | متغیر | Table I، صفحه 8 | `[صریح در مقاله]`؛ متن مدل GB می‌گوید |
| server computation `C_i` | `N(80,20)` | MFlops/s | Normal | متغیر | Table I | `[صریح در مقاله]` |
| server upload `B_u,i` | `N(120,30)` | MB/s | Normal | متغیر | Table I | `[صریح در مقاله]` |
| server download `B_d,i` | `N(120,30)` | MB/s | Normal | متغیر | Table I | `[صریح در مقاله]` |
| job storage/input `s_j` | `N(200,20)` | MB | Normal | متغیر | Table I | `[صریح در مقاله]` |
| job computation `K_j` | `N(100,20)` | MFlops | Normal | متغیر | Table I | `[صریح در مقاله]` |
| job upload bandwidth `b_u,j` | `N(80,10)` | MB/s | Normal | متغیر | Table I | `[صریح در مقاله]`؛ ارتباط با `σ_j(n)` نامشخص |
| job download bandwidth `b_d,j` | `N(80,10)` | MB/s | Normal | متغیر | Table I | `[صریح در مقاله]`؛ `s'_j` را تعیین نمی‌کند |
| deadline `d_j` | `N(10,3)` | slot | Normal | متغیر | Table I | `[صریح در مقاله]`؛ integer conversion نامشخص |
| Utility `U_j` | `N(60,20)` | utility unit | Normal | متغیر | Table I | `[صریح در مقاله]` |
| arrival count per slot | `N(14,4)` | job/slot | Normal | متغیر | Section VI-A2 | `[صریح در مقاله]`؛ integer conversion نامشخص |
| horizon | `[نامشخص]` | slot | - | - | Section VI-A2/A3 | تعداد کل job قابل تعیین نیست |
| drain/empty slots | `[نامشخص]` | slot | - | - | Section VI | پایان شبیه‌سازی نامشخص |
| result/output size `s'_j` | `[نامشخص]` | MB | - | - | Table I ندارد | مدل pipeline بدون آن کامل نیست |
| high-value threshold | `[نامشخص]` | utility | - | - | Figs. 7، 10 | تعداد high/low قابل بازسازی دقیق نیست |
| low-value threshold | `[نامشخص]` | utility | - | - | Figs. 8 و متن | تعداد high/low قابل بازسازی دقیق نیست |
| truncation نمونه منفی | `[نامشخص]` | - | - | - | Table I | همه توزیع‌ها بالقوه مقدار فیزیکی نامعتبر می‌دهند |
| rounding | `[نامشخص]` | - | deadline/arrival integer | - | Table I | مسدودکننده sequence دقیق |
| هم‌بستگی پارامترها | `[نامشخص]` | - | independent یا correlated | - | Table I | joint workload قابل تعیین نیست |

### 3.3 Synthetic Bimodal

`[صریح در مقاله]` serverها همان توزیع Table I را دارند؛ Table II فقط jobها را تغییر می‌دهد.

| پارامتر | مقدار مقاله | واحد | توزیع/دامنه | ثابت یا متغیر | محل ذکر | وضعیت بازتولید |
| --- | ---: | --- | --- | --- | --- | --- |
| job storage `s_j` | `N(160,10)` | MB | Normal | متغیر | Table II، صفحه 10 | `[صریح در مقاله]` |
| job computation `K_j` | `N(80,20)` | MFlops | Normal | متغیر | Table II | `[صریح در مقاله]` |
| upload `b_u,j` | `N(70,10)` | MB/s | Normal | متغیر | Table II | `[صریح در مقاله]` |
| download `b_d,j` | `N(70,10)` | MB/s | Normal | متغیر | Table II | `[صریح در مقاله]` |
| deadline `d_j` | `N(10,3)` | slot | Normal | متغیر | Table II | `[صریح در مقاله]`؛ rounding نامشخص |
| Utility 1، low | `N(40,10)` | utility unit | Normal | متغیر | Table II | `[صریح در مقاله]` |
| Utility 2، high | `N(160,20)` | utility unit | Normal | متغیر | Table II | `[صریح در مقاله]`؛ جدول نماد را دوباره `U_1,j` چاپ کرده است |
| سهم low-value | دقیقاً 90 | درصد jobها | mixture class | ثابت در workload | Section VI-B2 | `[صریح در مقاله]` |
| سهم high-value | دقیقاً 10 | درصد jobها | mixture class | ثابت در workload | Section VI-B2 | `[صریح در مقاله]` |
| نحوه اعمال 90/10 | `[نامشخص]` | - | exact per run یا probabilistic | - | Section VI-B2 | عبارت exactly فقط نسبت نهایی را روشن می‌کند |
| arrival count/horizon | `[نامشخص]` | job/slot، slot | - | - | Section VI-B2 | انتقال تنظیمات Normal صریح نیست |
| output size `s'_j` | `[نامشخص]` | MB | - | - | Table II ندارد | مسدودکننده pipeline؛ آزمایش bimodal batch است ولی download همچنان لازم است |

### 3.4 زمان auction و accounting

| پارامتر | مقدار مقاله | واحد | توزیع/دامنه | ثابت یا متغیر | محل ذکر | وضعیت بازتولید |
| --- | ---: | --- | --- | --- | --- | --- |
| DK-P synthetic auction | تقریباً 5 | s/server/auction | average | روش‌وابسته | Section VI-A4 | `[صریح در مقاله]` |
| DK-R synthetic auction | تقریباً 4 | s/server/auction | average | روش‌وابسته | Section VI-A4 | `[صریح در مقاله]` |
| KG-P synthetic auction | تقریباً 2 | s/server/auction | average | روش‌وابسته | Section VI-A4 | `[صریح در مقاله]` |
| KG-R synthetic auction | تقریباً 1 | s/server/auction | average | روش‌وابسته | Section VI-A4 | `[صریح در مقاله]` |
| batch auction times | همان pipeline | s/server/auction | average | روش‌وابسته | Section VI-B1 | `[صریح در مقاله]` |
| DK trace auction | تقریباً 10 | minute/auction | average | روش‌وابسته | Section VI-B3 | `[صریح در مقاله]`؛ per-server بودن صریح نیست |
| KG-P trace auction | تقریباً 3 | minute/auction | average | روش‌وابسته | Section VI-B3 | `[صریح در مقاله]` |
| KG-R trace auction | تقریباً 2 | minute/auction | average | روش‌وابسته | Section VI-B3 | `[صریح در مقاله]` |
| نحوه کسر زمان auction | `[نامشخص]` | - | clock advance، deadline reduction یا missed auction | - | Sections VI-A4/VI-B1/B3 | فقط اثر توصیف شده است |
| تعداد اندازه‌گیری runtime | `[نامشخص]` | auction | - | - | Section VI | confidence/variance ناموجود |

### 3.5 Gurobi/Optimal

| پارامتر | مقدار مقاله | واحد | توزیع/دامنه | ثابت یا متغیر | محل ذکر | وضعیت بازتولید |
| --- | ---: | --- | --- | --- | --- | --- |
| سناریوی اول | 4 server، 25 job، ورود طی 4 timestep | count | distributions منبع [1] | ثابت | Section VI-A1 | `[صریح در مقاله]` |
| زمان حل سناریوی اول | بیش از 10 روز | wall time | optimum اثبات نشد | - | Section VI-A1 | `[صریح در مقاله]` |
| سناریوی قابل حل | 18 job، ورود طی 3 timestep | count | distributions منبع [1] | ثابت | Section VI-A1 | `[صریح در مقاله]`؛ server count صریح نیست |
| زمان optimum 18-job | تقریباً 5.5 | hour | - | - | Section VI-A1 | `[صریح در مقاله]` |
| optimum 18-job | 17 | completed jobs | - | - | Section VI-A1 | `[صریح در مقاله]` |
| DK-P و DK-R در 18-job | هرکدام 10 | completed jobs | 59% optimum | - | Section VI-A1 | `[صریح در مقاله]` |
| KG-P در 18-job | 9 | completed jobs | 53% optimum | - | Section VI-A1 | `[صریح در مقاله]` |
| KG-R در 18-job | 8 | completed jobs | 47% optimum | - | Section VI-A1 | `[صریح در مقاله]` |
| سناریوی 10-job | کاهش همان سناریو از 18 به 10 job | count | subset نامشخص | ثابت | Section VI-A1 | `[صریح در مقاله]` |
| DK در 10-job | 10 job، تقریباً 15 s | count/time | هر دو نسخه به‌طور جمعی ذکر شده‌اند | - | Section VI-A1 | `[صریح در مقاله]` |
| KG-P در 10-job | 9 job، تقریباً 11 s | count/time | - | - | Section VI-A1 | `[صریح در مقاله]` |
| KG-R در 10-job | 8 job، تقریباً 10 s | count/time | - | - | Section VI-A1 | `[صریح در مقاله]` |
| Gurobi version | `[نامشخص]` | version | reference manual 2022 تنها سرنخ است | - | bibliography و Section VI | قابل نسبت‌دادن به نسخه اجرا نیست |
| MIP gap/tolerances | `[نامشخص]` | - | - | - | Section VI | مسدودکننده تطبیق solver |
| threads | `[نامشخص]` | thread | - | - | Section VI | runtime قابل مقایسه نیست |
| time limit | `[نامشخص]` | time | اجرای 10 روزه گزارش شده، limit رسمی نه | - | Section VI | status حل مبهم |
| hardware/OS | `[نامشخص]` | - | - | - | کل v2 | runtime قابل بازتولید سخت‌افزاری نیست |

### 3.6 توزیع‌های واردشده از منبع مستقیم [1] برای آزمایش Optimal

v2 می‌گوید سناریوهای optimal از «همان job و server distributions منبع [1]» استفاده می‌کنند. Table I منبع [1] مقادیر زیر را می‌دهد:

| پارامتر | مقدار منبع [1] | واحد | وضعیت برای v2 |
| --- | ---: | --- | --- |
| server storage | `N(600,30)` | MB | `[استخراج مستقیم]` candidate برای `OPT-*`، نه آزمایش Normal اصلی v2 |
| server computation | `N(92,30)` | MFlops/s | `[استخراج مستقیم]` candidate |
| server bandwidth | `N(320,60)` | MB/s | `[استخراج مستقیم]` [1] upload/download را جدا نمی‌کند |
| job storage | `N(50,10)` | MB | `[استخراج مستقیم]` candidate |
| job computation | `N(90,25)` | MFlops | `[استخراج مستقیم]` candidate |
| job bandwidth | `N(70,10)` | MB/s | `[استخراج مستقیم]` candidate |
| deadline | `N(10,4)` | slot | `[استخراج مستقیم]` candidate |
| Utility در بخش all-or-nothing | `N(40,10)` | utility | `[استخراج مستقیم]` |
| Utility در workload scalability | Pareto، mode=20، `α=3` | utility | `[استخراج مستقیم]`؛ معلوم نیست سناریوی v2 کدام Utility را به ارث می‌برد |

در نتیجه، عبارت «same distributions as [1]» هنوز برای Utility و تفکیک upload/download یکتا نیست و قبل از ساخت `OPT-*` نیازمند تصمیم است.

## 4. پروتکل داده واقعی Southampton

### 4.1 اطلاعات صریح v2

| پارامتر | مقدار | محل ذکر | وضعیت |
| --- | --- | --- | --- |
| منبع | University of Southampton HPC/Iridis workload trace | Section VI-B3 | `[صریح در مقاله]` |
| طول trace اصلی | چهار سال | Section VI-B3 | `[صریح در مقاله]` |
| پنجره منتخب | سه روز در آوریل 2021 | Section VI-B3 | `[صریح در مقاله]`؛ تاریخ دقیق نامشخص |
| علت انتخاب | workload پایدار در semester | Section VI-B3 | `[صریح در مقاله]` |
| slot/auction interval | هر 10 دقیقه | Section VI-B3 | `[صریح در مقاله]` |
| priority classes | high، medium، low براساس user group | Section VI-B3 | `[صریح در مقاله]` |
| job attributes | arrival، storage، computation، deadline | v2 و منبع [1] | `[استخراج مستقیم]` |
| server count | 5 | Section VI-B3 | `[استخراج مستقیم]` دو high-memory + سه regular |
| high-memory node | 2 × 768 GB RAM | Section VI-B3 | `[صریح در مقاله]` |
| regular node | 3 × 192 GB RAM | Section VI-B3 | `[صریح در مقاله]` |
| server computation | براساس همان nodeهای واقعی | Section VI-B3 | `[صریح در مقاله]`؛ عدد دقیق گزارش نشده |
| download per slot | `N(10,0.2)` GB | Section VI-B3 | `[صریح در مقاله]` |
| upload capacity | `[نامشخص]` | Section VI-B3 | گزارش نشده |
| deadline cap | حداکثر 2 ساعت | Section VI-B3 | `[صریح در مقاله]`؛ 12 slot در مقیاس 10 دقیقه |

### 4.2 نگاشت priority از منبع مستقیم [1]

| priority | گروه‌ها | Utility distribution | وضعیت برای v2 |
| --- | --- | --- | --- |
| High | WorldPop/data-processing research، research staff و سایر research groups | `N(100,10)` | `[استخراج مستقیم]` از Table III [1]؛ v2 عدد را تکرار نکرده است |
| Medium | PhD students و ML/GPU-heavy jobs | `N(40,10)` | `[استخراج مستقیم]` از [1] |
| Low | undergraduate، serial/batch و کاربران بدون برچسب staff/student | `N(20,4)` | `[استخراج مستقیم]` از [1] |

نزدیک‌ترین نگاشت برای بازتولید v2 همین Table III منبع [1] است، زیرا v2 صریحاً می‌گوید همان trace در آن کار استفاده شده است. با این حال، ثابت‌ماندن این نگاشت در اجرای v2 صریحاً تأیید نشده و استفاده از آن یک `[فرض بازتولید]` نیازمند تأیید کاربر خواهد بود.

### 4.3 اطلاعات مفقود trace

- URL یا شناسه dataset خام
- سه تاریخ دقیق آوریل 2021 و timezone
- schema و نام ستون‌ها
- تعداد jobهای پنجره منتخب
- قواعد پاک‌سازی و رکوردهای حذف‌شده
- تبدیل CPU/core/runtime به `K_j`
- عدد computation capacity هر node
- upload capacity
- نگاشت دقیق output size و download demand
- seed توزیع download server و Utility priority
- محدودکردن/گردکردن نمونه‌های Normal

تا زمان دریافت raw trace و تأیید mapping، پردازش داده واقعی مسدود است.

## 5. روش‌های مقایسه‌شده

| روش | pipeline Normal | batch Normal | batch Bimodal | trace base | trace cap | optimal small |
| --- | --- | --- | --- | --- | --- | --- |
| Gurobi | فقط آزمایش متنی کوچک | خیر | خیر | خیر | خیر | بله |
| Double Knapsack Preemption | بله | خیر | خیر | خیر | خیر | بله |
| Double Knapsack Retention | بله | بله | بله | مقایسه متنی | بله | بله |
| KnapsackGreedy Preemption | بله | بله | بله | بله | بله | بله |
| KnapsackGreedy Retention | بله | بله | بله | بله | بله | بله |

`[نامشخص]` مقاله توضیح نمی‌دهد چرا DK-P از آزمایش‌های batch و trace حذف شده است.

## 6. معیارهای ارزیابی و تجمیع

| معیار | تعریف قابل استخراج | محل | ابهام |
| --- | --- | --- | --- |
| Completed Utility | مجموع Utility jobهای completed | Figs. 6،9،11-13،19-20 | تعداد run و aggregation نامشخص |
| Rejected Utility | مجموع Utility jobهای rejected | همان شکل‌ها | زمان نهایی تعیین rejection نامشخص |
| Preempted Utility | Utility jobهایی که حداقل یک بار preempt شده‌اند | Section VI-A3 | ممکن است با rejected/completed هم‌پوشانی مفهومی داشته باشد |
| Completed job count | تعداد job تکمیل‌شده | Figs. 7،8،10،14،15 و optimal | threshold high/low Normal نامشخص |
| Rejected job count | تعداد job ردشده | همان | resubmission می‌تواند double-count ایجاد کند؛ تعریف نشده |
| Preempted job count | تعداد jobهایی که حداقل یک بار preempt شده‌اند | Section VI-A3 | preemption تکراری یک job یک‌بار شمرده می‌شود |
| Auction runtime | average duration | Sections VI-A4/B3 | sample count/hardware نامشخص |
| Relative-to-optimal jobs | completed / 17 | Section VI-A1 | فقط سناریوی 18-job |

`[صریح در مقاله]` ستون Preempted در شکل‌های pipeline، «کل Utility یا تعداد jobهایی که حداقل یک‌بار preempt شده‌اند» را نشان می‌دهد. این دسته الزاماً یک partition ساده از state نهایی نیست؛ یک job می‌تواند preempt شود و بنا بر policy نامشخص بعداً دوباره bid کند. نحوه جلوگیری از double-count گزارش نشده است.

## 7. مشخصات بازتولید تمام شکل‌ها و جدول‌ها

| شکل/جدول | ورودی متغیر | مقادیر متغیر | معیار خروجی | روش‌ها | تعداد اجرا | فایل خروجی آینده |
| --- | --- | --- | --- | --- | --- | --- |
| Fig. 1 | epoch و job-set | نمونه مفهومی epochs 0–2 و ادامه timeline | arrival/bidding/processing timeline | پروتکل مشترک | ندارد | `[نتیجه اجرای واقعی] figures/stage15g/figure1_reconstructed.svg`؛ بازتولید ساختاری/مفهومی کامل |
| Fig. 2 | progress slot-level یک trace job | upload، compute، download درصدی | درصد پیشرفت در زمان | مدل pipeline | `[نامشخص]` یک job | `[پیشنهاد فنی] figures/fig02_pipeline_progress.svg` |
| Fig. 3 | discountهای Server 5 در `t=43` | bins تخفیف | تعداد job در هر bin | KG-P، Normal pipeline | یک run صریح؛ seed نامشخص | `[پیشنهاد فنی] figures/fig03_discount_histogram.svg` |
| Fig. 4 | priceهای Job 532 از 8 server | server 1-8 | R1 discount | KG-P | همان run Fig. 3 | `[پیشنهاد فنی] figures/fig04_job532_prices.svg` |
| Fig. 5 | priceهای Job 540 از 8 server | server 1-8 | R1 discount | KG-P | همان run | `[پیشنهاد فنی] figures/fig05_job540_prices.svg` |
| Fig. 6 | outcome category | completed، rejected، preempted | Utility | DK-P، DK-R، KG-P، KG-R | `[نامشخص]` | `[پیشنهاد فنی] figures/fig06_pipeline_normal_utility.svg` |
| Fig. 7 | high-value outcome | سه category | تعداد job | چهار روش | `[نامشخص]` | `[پیشنهاد فنی] figures/fig07_pipeline_high_jobs.svg` |
| Fig. 8 | low-value outcome | سه category | تعداد job | چهار روش | `[نامشخص]` | `[پیشنهاد فنی] figures/fig08_pipeline_low_jobs.svg` |
| Fig. 9 | outcome با auction time | سه category | Utility | چهار روش | `[نامشخص]` | `[پیشنهاد فنی] figures/fig09_pipeline_time_utility.svg` |
| Fig. 10 | high-value با auction time | سه category | تعداد job | چهار روش | `[نامشخص]` | `[پیشنهاد فنی] figures/fig10_pipeline_time_high_jobs.svg` |
| Fig. 11 | batch Normal outcome | سه category | Utility | DK-R، KG-P، KG-R | `[نامشخص]` | `[پیشنهاد فنی] figures/fig11_batch_normal_utility.svg` |
| Fig. 12 | batch Normal با auction time | سه category | Utility | DK-R، KG-P، KG-R | `[نامشخص]` | `[پیشنهاد فنی] figures/fig12_batch_time_utility.svg` |
| Fig. 13 | Bimodal outcome | سه category | Utility | DK-R، KG-P، KG-R | `[نامشخص]` | `[پیشنهاد فنی] figures/fig13_bimodal_utility.svg` |
| Fig. 14 | high-mode outcome | سه category | تعداد job | DK-R، KG-P، KG-R | `[نامشخص]` | `[پیشنهاد فنی] figures/fig14_bimodal_high_jobs.svg` |
| Fig. 15 | low-mode outcome | سه category | تعداد job | DK-R، KG-P، KG-R | `[نامشخص]` | `[پیشنهاد فنی] figures/fig15_bimodal_low_jobs.svg` |
| Fig. 16 | trace storage و priority | GB bins؛ Low/Med/High | probability | data diagnostic | یک trace window | `[پیشنهاد فنی] figures/fig16_trace_storage.svg` |
| Fig. 17 | trace computation و priority | chart label Gigabytes، با ناسازگاری معنایی | probability | data diagnostic | یک trace window | `[پیشنهاد فنی] figures/fig17_trace_computation.svg` |
| Fig. 18 | trace deadline و priority | hours bins | probability | data diagnostic | یک trace window | `[پیشنهاد فنی] figures/fig18_trace_deadline.svg` |
| Fig. 19 | trace outcome | completed، rejected، preempted | Utility | KG-P، KG-R | `[نامشخص]` | `[پیشنهاد فنی] figures/fig19_trace_outcomes.svg` |
| Fig. 20 | capped trace outcome | سه category؛ deadline≤2h | Utility | DK-R، KG-P، KG-R | `[نامشخص]` | `[پیشنهاد فنی] figures/fig20_trace_cap_2h.svg` |
| Table I | Normal resource variables | `μ,σ` | config specification | synthetic normal | ندارد | `[پیشنهاد فنی] results/tables/table01_normal.csv` |
| Table II | Bimodal job variables | `μ,σ` و 90/10 | config specification | synthetic bimodal | ندارد | `[پیشنهاد فنی] results/tables/table02_bimodal.csv` |

### نکات شکل‌ها

- `[نامشخص]` داده عددی پشت نمودارها در بسته arXiv وجود ندارد؛ تصاویر raster هستند.
- `[نامشخص]` error bar یا confidence interval رسم نشده و تعداد run ذکر نشده است.
- `[نامشخص]` bin edges شکل‌های 16-18 از متن قابل تعیین نیستند و فقط از تصویر قابل تقریب‌اند.
- Fig. 17 محور افقی را Gigabytes می‌نامد، درحالی‌که caption آن computation distribution است؛ mapping واحد نامشخص است.
- برای شکل‌های 3-5، شناسه‌های server/job/timestep صریح‌اند ولی instance و seed کامل نیستند.
- مقادیر خوانده‌شده از تصویر باید بعداً با برچسب `[مقادیر تقریبی خوانده‌شده از شکل]` جدا از نتایج شبیه‌سازی ذخیره شوند.

## 8. نرم‌افزار و سخت‌افزار

| مؤلفه | اطلاعات موجود | وضعیت |
| --- | --- | --- |
| Gurobi | نام solver و reference manual سال 2022 | `[صریح در مقاله]`؛ نسخه اجرایی نامشخص |
| pyeasyga | implementation off-the-shelf و `g≈30` | `[صریح در مقاله]`؛ نسخه package و تنظیمات نامشخص |
| زبان پیاده‌سازی | `[نامشخص]` | v2 صریحاً Python را اعلام نمی‌کند |
| OS | `[نامشخص]` | گزارش نشده |
| CPU/RAM اجرای آزمایش | `[نامشخص]` | گزارش نشده؛ RAM nodeهای trace ظرفیت شبیه‌سازی‌اند، نه سخت‌افزار اجرای برنامه |
| parallelism/threads | `[نامشخص]` | گزارش نشده |
| plotting software | `[نامشخص]` | سبک تصویر به‌تنهایی اثبات ابزار نیست |

## 9. اطلاعات مفقود، اثر و گزینه‌های بازتولید

تمام Section VI صفحات 8-12، Tables I-II، captions شکل‌های 3-20، بسته source arXiv و منابع مستقیم [1]/[4] بررسی شدند.

| اطلاعات مفقود | اثر | گزینه‌های معقول | نزدیک‌ترین گزینه؛ هنوز اعمال نشده |
| --- | --- | --- | --- |
| horizon و تعداد کل jobهای synthetic | scale و مجموع Utility نامعلوم | دریافت از نویسنده؛ استفاده از horizon منبع پیشین؛ تعریف sweep مستقل | دریافت از نویسنده؛ انتقال horizon مقالات پیشین بی‌دلیل است |
| repeats و seeds | میانگین و variance بازتولید نمی‌شود | درخواست از نویسنده؛ تک‌run؛ مجموعه seed ثابت چندتایی | seedهای ثابت چندتایی برای robustness، فقط `[فرض بازتولید]` |
| rounding/truncation Normal | deadline/arrival/resource نامعتبر | rejection sampling؛ clipping؛ resampling؛ round/floor/ceil | resampling تا مثبت و round-to-nearest برای integerها، نیازمند تأیید |
| `s'_j` و output mapping | مدل pipeline ناقص | برابر input؛ مشتق از download demand؛ نسبت ثابت؛ دریافت نویسنده | دریافت نویسنده؛ هیچ نسبت متن‌محوری وجود ندارد |
| high/low threshold Normal | Figs. 7،8،10 بازتولید نمی‌شوند | threshold ثابت؛ quantile؛ برچسب از generation | دریافت تعریف نویسنده؛ تصویر threshold را تعیین نمی‌کند |
| mechanics auction time | Figs. 9،10،12،20 تغییر می‌کنند | کسر average از deadline؛ advance clock؛ استفاده actual runtime | advance clock با duration گزارش‌شده محتمل‌تر است، ولی تأیید لازم است |
| raw trace و سه تاریخ دقیق | Figs. 16-20 مسدود | دریافت dataset؛ digitize histogram؛ synthetic surrogate | دریافت trace رسمی؛ surrogate بازتولید واقعی نیست |
| trace Utility mapping v2 | Utility outcomes تغییر می‌کند | Table III منبع [1]؛ mapping جدید؛ inference از شکل | Table III منبع [1] نزدیک‌ترین است، نیازمند تأیید |
| compute/upload ظرفیت trace | feasibility تغییر می‌کند | اطلاعات node؛ scaling از RAM؛ parameter sweep | دریافت مشخصات node؛ scaling از RAM توجیه نشده است |
| Gurobi settings/hardware | runtime و solution status قابل مقایسه نیست | درخواست تنظیمات؛ defaults ثبت‌شده؛ solver کمکی | defaults نسخه منتخب فقط `[فرض بازتولید]` و نه تنظیم مقاله |
| aggregation و overlap outcomeها | totals ممکن است double-count شوند | terminal partition؛ ever-preempted overlay؛ event-level | ever-preempted overlay با عبارت مقاله سازگارتر است؛ تأیید لازم |
| batch minimum resource allocation | fit و completion متفاوت می‌شود | استخراج بیشتر از [1]/[4]؛ تعریف فرمول جدید | تحلیل منابع مستقیم در ادامه ردیابی، بدون فرض پنهان |

هیچ‌یک از گزینه‌های ستون آخر در این مرحله استفاده نشده‌اند.

## 10. درصد قابلیت استخراج پروتکل

برای جلوگیری از درصد سلیقه‌ای، 19 مؤلفه پروتکل امتیازدهی شد:

- `کامل = 1`
- `جزئی = 0.5`
- `مفقود = 0`

| دسته | تعداد | مؤلفه‌ها |
| --- | ---: | --- |
| کامل | 6 | خانواده workloadها، روش‌ها، ابعاد منابع، پارامترهای Normal، پارامترهای Bimodal، ثابت‌های اصلی pricing/preemption |
| جزئی | 9 | server counts، job counts/horizon، trace window، trace mapping، deadline generation، Utility generation، load، metrics/aggregation، plotting |
| مفقود | 4 | repeats، seeds، Gurobi settings/time limit، hardware/software environment |

```text
weighted_coverage = (6 + 0.5*9) / 19 = 55.3%
strict_full_coverage = 6 / 19 = 31.6%
```

نتیجه:

- **حدود 55٪ پروتکل آزمایش از متن v2 با احتساب اطلاعات جزئی قابل استخراج است.**
- فقط **حدود 32٪ کاملاً مشخص** است و بدون تصمیم اضافی قابل تبدیل مستقیم به config است.
- منابع [1] و [4] بخشی از trace و workload optimal را روشن می‌کنند، اما repeats، seeds، raw data، محیط اجرا و تنظیمات solver را تکمیل نمی‌کنند.

## 11. نتیجه مرحله پنجم

- پارامترهای اصلی Normal و Bimodal استخراج شده‌اند.
- خانواده آزمایش‌ها و نگاشت کامل Figs. 1-20 و Tables I-II مشخص شده‌اند.
- روش‌ها و معیارهای هر آزمایش مشخص‌اند.
- trace واقعی و آزمایش‌های full-scale synthetic هنوز برای بازتولید عددی دقیق اطلاعات کافی ندارند.
- هیچ `[فرض بازتولید]` اعمال نشده است.
- کدنویسی فقط پس از طراحی معماری و تأیید تصمیم‌های بازتولید آغاز خواهد شد.
