# مرحله چهارم: استخراج الگوریتم‌ها و شبه‌کد اجرایی

## 1. محدوده و منابع

- منبع مبنا: *Improved Methods of Task Assignment and Resource Allocation with Preemption in Edge Computing Systems*، نسخه `arXiv:2403.15665v2`، 29 مارس 2024.
- بخش اصلی بررسی‌شده: Section V، صفحات 6 تا 8؛ همراه با Sections III، IV و VI برای ورودی، خروجی و روش‌های مقایسه.
- Algorithm 1 و Algorithm 2 از `main.tex` رسمی arXiv استخراج و با رندر صفحات 6 و 7 PDF تطبیق داده شدند.
- `[استخراج مستقیم]` مقاله برای تعریف پایه Double Knapsack، قیمت‌گذاری congestion و روش clustering به منابع مستقیم [4] و [1] ارجاع می‌دهد. در 9 اوت 2026، کاربر نسخه‌های کامل ناشر را با نام‌های `4.pdf` و `1.pdf` فراهم کرد؛ هویت، DOI، تعداد صفحات و کامل‌بودن هر دو تأیید شد. این دسترسی مانع منبع را رفع می‌کند، ولی ادغام خط‌به‌خط جزئیات آن‌ها در الگوریتم‌ها باید جداگانه و با حفظ منشأ انجام شود.
- نسخه نهایی 2025 طبق تصمیم کاربر خارج از محدوده است و برای رفع هیچ ابهامی استفاده نشده است.
- در این مرحله هیچ کد Python نوشته یا اجرا نشده است.

## 2. فهرست روش‌ها و سطح تعریف

| روش | نقش | Round 1 | Round 2 | Preemption | سطح اطلاعات در v2 |
| --- | --- | --- | --- | --- | --- |
| KnapsackGreedy Retention یا `KG-R` | روش پیشنهادی بدون preemption | Algorithm 1؛ همان Round 1 نسخه preemptive | نسخه greedy بدون شاخه preemption | خیر | Round 1 کامل‌تر؛ Round 2 Retention صریح و مستقل ارائه نشده |
| KnapsackGreedy Preemption یا `KG-P` | روش پیشنهادی اصلی | Algorithm 1 | Algorithm 2 | یک victim در توصیف متنی؛ حلقه شبه‌کد مبهم | تا حد زیادی تعریف‌شده، با چند ناسازگاری بحرانی |
| Double Knapsack Retention یا `DK-R` | روش مبنای [4] | knapsack برای قیمت‌گذاری | knapsack برای پذیرش | خیر | فقط خلاصه؛ تعریف کامل به [4] واگذار شده |
| Double Knapsack Preemption یا `DK-P` | توسعه ارائه‌شده در v2 | همان Round 1 پایه Double Knapsack | knapsack روی ظرفیت کل و current+returning، سپس score | بله؛ هر تعداد victim ممکن است | ایده روشن، اما عملیات اجرایی preemption ناقص |
| مدل متمرکز Gurobi | oracle آفلاین و کران بالا | ندارد | ندارد | در مدل ریاضی مجاز | روابط موجود؛ تنظیمات حل و رفع ناسازگاری‌ها نامشخص |
| Clustering + Round 2 Knapsack | روش پیشین [1] | clustering | knapsack | در متن پیشینه مطرح شده | الگوریتم کامل در v2 وجود ندارد و روش اصلی مقایسه شکل‌های v2 نیست |

## 3. قرارداد داده‌ای لازم برای تبدیل آینده به Python

این نام‌ها `[پیشنهاد فنی]` هستند و ساختار قطعی پروژه نیستند.

| ساختار | فیلدهای لازم | منشأ |
| --- | --- | --- |
| `Task` | `task_id`, `utility`, `deadline`, `time_remaining`, `resource_demand`, `state` | `[صریح در مقاله]` Sections III-V |
| `Server` | `server_id`, `total_capacity`, `residual_capacity`, `current_jobs` | `[صریح در مقاله]` Sections III و V |
| `ResourceVector` | storage، computation، upload و download | `[استخراج مستقیم]` Sections III-IV و جدول‌های آزمایش |
| `RoundOneOffer` | `server_id`, `task_id`, `price`, `auto_fit` | `[استخراج مستقیم]` متن Algorithm 1؛ mark در نثر صریح ولی در شبه‌کد غایب است |
| `KnapsackResult` | مجموعه jobهای منتخب و بردار مصرف | `[استخراج مستقیم]` Algorithms و توضیحات |
| `AllocationDecision` | accept، reject، retain یا preempt و دلیل | `[پیشنهاد فنی]` برای ثبت اجرای قابل آزمون |
| `PreemptionTransaction` | victimها، منابع قبل/بعد و job جایگزین | `[پیشنهاد فنی]` برای اعمال اتمی آزادسازی و تخصیص |

`resource_demand` یا `job.space` باید برداری چندبعدی باشد. `[نامشخص]` مقاله مشخص نمی‌کند مقایسه `≤` در Algorithm 2 دقیقاً component-wise است یا از یک تابع fit دیگر استفاده می‌کند؛ سازگاری با مدل ظرفیت، مقایسه مؤلفه‌به‌مؤلفه را محتمل می‌کند، اما این تفسیر هنوز اعمال نشده است.

## 4. گردش مشترک مزایده

### هدف

`[صریح در مقاله]` تخصیص jobها به serverهای مستقل برای بیشینه‌سازی Utility تکمیل‌شده در مدل all-or-nothing، با اولویت دادن به تخصیص بدون preemption و استفاده از preemption فقط برای gain مناسب.

### ورودی و خروجی

- ورودی: jobهای درخواست‌کننده، serverهای available، وضعیت جاری و ظرفیت باقیمانده هر server.
- خروجی Round 1: یک price و در صورت fit، یک mark برای هر جفت job-server.
- خروجی انتخاب client: حداکثر یک server با کمترین price.
- خروجی Round 2: پذیرش، رد، retention یا preemption.
- خروجی processing: پیشرفت منابع و در نهایت Utility کامل یا صفر.

### شبه‌کد مستقل مشترک

```text
FOR each bidding epoch:
    requesting_jobs <- jobs eligible to bid in this epoch

    FOR each requesting job:
        broadcast requirements and stated utility to all available servers

    FOR each server independently:
        offers[server] <- ROUND_ONE(server, requesting_jobs)

    FOR each requesting job:
        eligible_offers <- offers received by the job
        chosen_server <- server with minimum offered price
        IF no acceptable offer exists:
            reject job for this auction
        ELSE:
            return job to chosen_server for Round 2

    FOR each server independently:
        decisions <- ROUND_TWO(server, jobs_returned_to_server)

    start or continue processing accepted jobs
```

- شرط آغاز: `[صریح در مقاله]` ورود jobها و شروع bidding phase.
- شرط پایان مزایده: `[استخراج مستقیم]` همه jobهای بازگشته در Round 2 پذیرفته یا رد شده‌اند.
- `[نامشخص]` «قیمت قابل قبول» فقط برای server غیرممکن «بیشتر از Utility» توصیف شده است؛ قاعده رسمی client برای رد همه قیمت‌های بیشتر از Utility در v2 تکرار نشده، هرچند منطق قیمت‌گذاری آن را مفروض می‌گیرد.
- `[نامشخص]` tie-breaking ارزان‌ترین قیمت. تنها در مثال Job 532 انتخاب تصادفی از دو fit price گزارش شده است.
- `[نامشخص]` ترتیب اجرای serverها و jobها در تساوی و اثر آن بر RNG.

## 5. Algorithm 1: Round 1 در KnapsackGreedy

### هدف

`[صریح در مقاله]` هدایت jobها به serverهایی که بدون preemption جا می‌شوند و در مرتبه دوم، جذب محتاطانه jobهای مناسب preemption؛ قیمت کمتر جذاب‌تر است.

### ورودی‌ها

- `servers`
- `requesting_jobs`
- `s.residual_resc`
- `currentJobs`
- `job.totalUtility`
- `c1 = percentile_weight = 0.025`
- `c2 = congestion_weight = 0.025`
- `fit_discount = 0.10`

### خروجی‌ها

- price برای هر job-server
- mark موسوم به `autoFit` برای اعضای knapsack
- قیمت بیشتر از Utility برای job ناممکن، با مقدار دقیق نامشخص

### تحلیل خط‌به‌خط Algorithm 1

| خط مقاله | دستور | توضیح | وضعیت پیش از اجرا | تغییر ایجادشده | تابع کد آینده |
| ---: | --- | --- | --- | --- | --- |
| 1 | `For Server s` | اجرای مستقل روی هر server | فهرست serverها موجود است | server جاری انتخاب می‌شود | `[پیشنهاد فنی] round_one_all_servers` |
| 2 | `jobsThatFit = Knapsack(s.residual_resc, requesting_jobs)` | انتخاب زیرمجموعه feasible روی residual capacity | current jobs منابع خود را اشغال کرده‌اند | مجموعه fit موقت ساخته می‌شود | `[پیشنهاد فنی] solve_multidimensional_knapsack` |
| 3 | `For job in requesting_jobs` | قیمت‌گذاری همه درخواست‌ها | نتیجه knapsack موجود است | job جاری انتخاب می‌شود | `[پیشنهاد فنی] price_round_one_jobs` |
| 4 | `if job in jobsThatFit` | عضویت در زیرمجموعه fit | job ممکن است عضو یا غیرعضو باشد | شاخه fit انتخاب می‌شود | `[پیشنهاد فنی] is_auto_fit` |
| 5 | `price = utility * 0.9` | تخفیف 10 درصد | Utility مثبت | قیمت fit ساخته می‌شود | `[پیشنهاد فنی] fit_price` |
| 5a | mark job for future reference | این دستور در نثر صریح است ولی در Algorithm 1 نوشته نشده | job عضو knapsack است | mark وابسته به server ثبت می‌شود | `[پیشنهاد فنی] mark_auto_fit` |
| 6 | `else` | job عضو knapsack نیست | شاخه fit ناموفق است | ورود به قیمت preemption | `[پیشنهاد فنی] preemption_price` |
| 7 | `percentileFactor = c1 * percentile(job,currentJobs)` | رتبه job نسبت به current jobs با معیار Utility/time_remaining | current jobs موجودند | عامل رتبه محاسبه می‌شود | `[پیشنهاد فنی] utility_time_percentile` |
| 8 | `congestionFactor = c2 * (1-congestion(job,residual))` | عامل تراکم طبق شبه‌کد | residual vector موجود است | عامل congestion محاسبه می‌شود | `[پیشنهاد فنی] congestion_discount_component` |
| 9 | `price = U - (percentileFactor + congestionFactor) * U` | اعمال تخفیف preemption | دو عامل محاسبه شده‌اند | price تولید می‌شود | `[پیشنهاد فنی] preemption_price` |
| 10 | پایان if | پایان شاخه قیمت | price موجود است | هیچ | - |
| 11 | پایان حلقه job | حرکت به job بعدی | offer جاری موجود است | offer ذخیره می‌شود | `[پیشنهاد فنی] append_offer` |
| 12 | پایان حلقه server | حرکت به server بعدی | همه jobها قیمت گرفته‌اند | price matrix کامل‌تر می‌شود | - |

### فرمول‌های قیمت‌گذاری

#### fit price

```text
price_fit(j) = 0.9 * U_j
```

`[صریح در مقاله]` تخفیف 10 درصدی از منبع [4] به‌عنوان بهترین محافظت گزارش‌شده در برابر overstatement گرفته شده است.

#### preemption price طبق خود شبه‌کد

```text
p_j = percentile(j, current_jobs)
q_j = congestion(j, residual_resources)
percentile_factor = 0.025 * p_j
congestion_factor = 0.025 * (1 - q_j)
price_preempt(j) = U_j * (1 - percentile_factor - congestion_factor)
```

#### مثال عددی کمکی

`[آزمون کمکی]` اگر `U=100`، percentile برابر `0.7` و congestion برابر `0.4` باشد، طبق Algorithm 1:

```text
percentile_factor = 0.025 * 0.7 = 0.0175
congestion_factor = 0.025 * 0.6 = 0.015
price = 100 * (1 - 0.0325) = 96.75
```

این مقدار نتیجه مقاله نیست و فقط test oracle آینده است.

### شرایط مرزی

- current jobs تهی: percentile تعریف نشده است.
- residual resource صفر: نسبت demand/residual تقسیم بر صفر می‌شود.
- demand بزرگ‌تر از total capacity: متن price بزرگ‌تر از Utility می‌خواهد، اما مقدار/فرمول ندارد.
- Utility صفر یا منفی: دامنه Utility در الگوریتم اعلام نشده؛ داده‌های نرمال نیز ممکن است بدون truncation نمونه منفی بسازند.
- percentile یا congestion خارج `[0,1]`: تضمین سقف 5 درصد از بین می‌رود.
- `c1+c2 > 0.1`: مقاله می‌گوید تضمین اولویت fit discount از بین می‌رود.

### آزمون‌های لازم

1. عضو knapsack دقیقاً `0.9U` بگیرد.
2. عضو knapsack، mark وابسته به همان server دریافت کند.
3. job خارج knapsack با دو مؤلفه صفر، price برابر `U` بگیرد.
4. سقف تخفیف preemption با عوامل نرمال‌شده 5 درصد باشد.
5. price preemption از price fit کمتر نشود.
6. job ناممکن price بزرگ‌تر از Utility بگیرد؛ مقدار فقط پس از تصمیم بازتولید.
7. current-jobs-empty و residual-zero بدون رفتار پنهان بررسی شوند.

## 6. Algorithm 2: Preemptive Round 2 در KnapsackGreedy

### هدف

`[صریح در مقاله]` پذیرش سریع jobهای fit و در صورت نیاز، جایگزینی یک job جاری کم‌ارزش‌تر با job جدیدی که هم ارزش نسبی کافی دارد و هم با منابع آزادشده جا می‌شود.

### ورودی‌ها و خروجی‌ها

- ورودی: returning jobs، autoFit marks همان server، residual resources و current jobs.
- خروجی: accepted، rejected، retained و preempted jobs؛ residual resources جدید.

### تحلیل خط‌به‌خط Algorithm 2

| خط مقاله | دستور | توضیح | وضعیت پیش از اجرا | تغییر ایجادشده | تابع کد آینده |
| ---: | --- | --- | --- | --- | --- |
| 1 | `For Server s` | اجرای Round 2 مستقل برای هر server | jobهای بازگشته partition شده‌اند | server جاری انتخاب می‌شود | `[پیشنهاد فنی] round_two_all_servers` |
| 2 | `Admit all autoFit jobs` | پذیرش jobهای markشده در R1 | residual همان مبنای R1 است | jobها افزوده و منابع رزرو می‌شوند | `[پیشنهاد فنی] admit_auto_fit_jobs` |
| 3 | sort returning descending `utility/time_remaining` | اولویت jobهای جدید | autoFitها باید از remainder حذف شوند | صف ورودی مرتب می‌شود | `[پیشنهاد فنی] rank_returning_jobs` |
| 4 | sort `s.jobs` ascending `utility/time_remaining` | ضعیف‌ترین victim ابتدا | current jobs موجودند | صف victim مرتب می‌شود | `[پیشنهاد فنی] rank_victims` |
| 5 | `For job in remaining returning_jobs` | بررسی jobهای باقی‌مانده | دو صف آماده‌اند | job جدید انتخاب می‌شود | `[پیشنهاد فنی] evaluate_returning_job` |
| 6 | `if job fits residual` | پذیرش بدون preemption | residual جاری معلوم است | شاخه مستقیم انتخاب می‌شود | `[پیشنهاد فنی] fits` |
| 7 | `Add job to server` | تخصیص مستقیم | fit برقرار است | منابع مصرف و job پذیرفته می‌شود | `[پیشنهاد فنی] allocate` |
| 8 | `else` | نیاز به بررسی preemption | fit مستقیم برقرار نیست | ورود به حلقه victim | - |
| 9 | `For sJob in s.jobs` | victimها از ratio کم به زیاد | فهرست مرتب است | victim جاری انتخاب می‌شود | `[پیشنهاد فنی] iterate_victims` |
| 10 | شرط ratio و fit-after-release | سنجش ارزش و امکان جاگیری | job و victim و residual معلوم‌اند | شاخه preemption ممکن می‌شود | `[پیشنهاد فنی] can_preempt` |
| 11 | `Preempt sJob` | توقف job جاری | victim فعال است | Utility victim صفر و منابعش آزاد می‌شود | `[پیشنهاد فنی] preempt` |
| 12 | `Add job to server` | جایگزینی job جدید | منابع victim آزاد شده‌اند | job جدید پذیرفته می‌شود | `[پیشنهاد فنی] allocate` |
| 13-17 | پایان شرط‌ها و حلقه‌ها | Algorithm 2 هیچ `break` بعد از Add ندارد | job ممکن است قبلاً اضافه شده باشد | رفتار تکرار بعدی نامشخص است | `[پیشنهاد فنی] transactional_preemption` |

### ترتیب پردازش

1. autoFitها پیش از همه پذیرفته می‌شوند.
2. returning jobهای باقی‌مانده بر حسب `U/time_remaining` نزولی‌اند.
3. current jobها بر حسب `U/time_remaining` صعودی‌اند.
4. fit مستقیم پیش از preemption آزمایش می‌شود.
5. victimهای ضعیف‌تر زودتر بررسی می‌شوند.

### شرط preemption چاپ‌شده در Algorithm 2

```text
(new.utility / new.deadline) * 1.05 >=
    current.utility / current.time_remaining
AND
new.space <= current.space + server.residual_resources
```

### شرطی که نثر همان صفحه بیان می‌کند

```text
new.utility / new.deadline >=
    1.05 * (current.utility / current.time_remaining)
```

این دو معادل نیستند. شرط شبه‌کد اجازه می‌دهد ratio جدید تا حدود `95.24%` ratio victim کاهش یابد، ولی نثر ratio جدید را حداقل `105%` ratio victim می‌خواهد.

### مثال عددی کمکی ناسازگاری 5 درصد

`[آزمون کمکی]` اگر ratio جدید `100` و ratio victim برابر `104` باشد:

- شرط Algorithm 2: `100*1.05 = 105 ≥ 104`، پس preemption مجاز است.
- شرط نثر: `100 ≥ 1.05*104 = 109.2`، پس preemption مجاز نیست.

### شرایط مرزی و ابهام‌ها

- deadline یا time_remaining صفر باعث تقسیم بر صفر می‌شود.
- `[نامشخص]` برای job بازگشتی پس از retry، چرا شرط از `deadline` استفاده می‌کند ولی مرتب‌سازی از `time_remaining`؟
- `[نامشخص]` `s.jobs` پس از پذیرش autoFit و jobهای جدید، snapshot است یا live collection؟
- `[نامشخص]` نبود `break` ممکن است victimهای متعدد را برای یک job preempt کند یا یک job را چند بار Add کند.
- `[نامشخص]` اگر یک victim کافی نباشد، KG-P اجازه ترکیب چند victim را می‌دهد یا job رد می‌شود؟ نثر از «another job» مفرد استفاده می‌کند.
- `[نامشخص]` tie-breaking ratioهای برابر.
- `[نامشخص]` وضعیت job preempted در auctionهای بعدی.

### آزمون‌های لازم

1. autoFitها پیش از صف greedy تخصیص یابند.
2. fit مستقیم هیچ victimی را متوقف نکند.
3. victim دارای کمترین ratio نخست بررسی شود.
4. هر دو تفسیر شرط 5 درصد با مثال مرزی جدا آزمون شوند.
5. fit-after-release برای تمام ابعاد منابع برقرار باشد.
6. هر job حداکثر یک بار Add شود.
7. پس از preemption منابع victim دقیقاً آزاد شوند.
8. در نسخه مورد تأیید، حلقه پس از موفقیت متوقف شود یا رفتار چند-victim دقیقاً آزمون شود.

## 7. KnapsackGreedy Retention

`[صریح در مقاله]` Round 1 نسخه non-preemptive همان Algorithm 1 است، زیرا هدف هدایت jobهای مطلوب به server تغییر نمی‌کند.

`[نامشخص]` v2 برای Round 2 Retention شبه‌کد مستقل ارائه نمی‌کند. نزدیک‌ترین اسکلت قابل استنتاج، پذیرش autoFitها و سپس بررسی greedy jobهای باقی‌مانده بدون ورود به شاخه preemption است؛ اما استفاده از این اسکلت در کد یک `[فرض بازتولید]` خواهد بود و هنوز تصویب نشده است.

```text
ROUND_TWO_KG_RETENTION_UNRESOLVED(server, returning_jobs):
    admit autoFit returning jobs
    sort remaining returning jobs by descending utility/time_remaining
    FOR each remaining job:
        IF job fits residual resources:
            add job
        ELSE:
            reject job
```

آزمون‌های لازم: عدم preemption تحت هر بار، ترتیب نزولی ratio، تخصیص فقط در fit و سازگاری منابع.

## 8. Double Knapsack Retention

### آنچه v2 صریحاً می‌گوید

- `[صریح در مقاله]` server در هر دو round یک knapsack اجرا می‌کند.
- `[صریح در مقاله]` Round 1 تعیین می‌کند کدام jobها fit هستند و به آن‌ها قیمت پایین می‌دهد.
- `[صریح در مقاله]` Round 2 تعیین می‌کند کدام returning jobها پذیرفته شوند.
- `[صریح در مقاله]` اشکال اصلی، زمان محاسباتی طولانی است.

### اطلاعاتی که در v2 وجود ندارد

- encoding مسئله چندبعدی برای pyeasyga
- fitness و value دقیق هر job
- population size، crossover، mutation، selection و seed
- فرمول کامل قیمت اعضا و غیرعضوها برای DK-R مورد آزمایش
- نحوه تخصیص منابع پس از انتخاب زیرمجموعه
- tie-breaking و رفتار solver stochastic

### شبه‌کد مستقل با نقاط حل‌نشده

```text
ROUND_ONE_DK_RETENTION(server, requesting_jobs):
    selected <- MULTIDIMENSIONAL_KNAPSACK(
        capacity = server.residual_resources,
        items = requesting_jobs,
        fitness = UNRESOLVED,
        genetic_parameters = UNRESOLVED
    )
    FOR each requesting job:
        price <- UNRESOLVED_BASELINE_PRICING(selected, job, server)
    RETURN offers

ROUND_TWO_DK_RETENTION(server, returning_jobs):
    selected <- MULTIDIMENSIONAL_KNAPSACK(
        capacity = server.residual_resources,
        items = returning_jobs,
        fitness = UNRESOLVED,
        genetic_parameters = UNRESOLVED
    )
    admit selected jobs
    reject non-selected jobs
```

این شبه‌کد فقط مرز دانسته/ندانسته را نشان می‌دهد و هنوز قابل تبدیل وفادارانه به Python نیست.

## 9. Double Knapsack Preemption

### هدف و داده‌ها

`[صریح در مقاله]` فقط Round 2 پایه Double Knapsack تغییر می‌کند. knapsack روی total capacity هر server و unionِ current jobs و returning jobs اجرا می‌شود.

### رتبه‌بندی

```text
IF job is selected by knapsack:
    score = 1000 + utility/time_remaining
ELSE:
    score = 1 + utility/time_remaining
```

سپس jobها بر حسب score نزولی برای fit بررسی می‌شوند.

### شبه‌کد مستقل با نقاط حل‌نشده

```text
ROUND_TWO_DK_PREEMPTION(server, returning_jobs):
    candidates <- union(server.current_jobs, returning_jobs)
    preferred <- MULTIDIMENSIONAL_KNAPSACK(
        capacity = server.total_capacity,
        items = candidates,
        fitness = UNRESOLVED,
        genetic_parameters = UNRESOLVED
    )

    FOR each job in candidates:
        IF job in preferred:
            score[job] <- 1000 + utility[job] / time_remaining[job]
        ELSE:
            score[job] <- 1 + utility[job] / time_remaining[job]

    ordered <- sort candidates by descending score

    FOR each job in ordered:
        CHECK_INDIVIDUAL_FIT_AND_UPDATE_STATE(
            job,
            preemption_policy = UNRESOLVED,
            victim_selection = UNRESOLVED
        )
```

### ابهام‌های اجرایی

- `[نامشخص]` وضعیت server پیش از حلقه fit reset می‌شود یا current jobs در جای خود باقی می‌مانند؟
- `[نامشخص]` چگونه job منتخب knapsack که فعلاً جا نمی‌شود victimهای لازم را آزاد می‌کند؟
- `[نامشخص]` ترتیب آزادسازی چند victim و rollback در failure.
- `[نامشخص]` current job غیرمنتخب فوراً preempt می‌شود یا فقط هنگام نیاز؟
- `[نامشخص]` score ثابت 1000 فقط وقتی اولویت عضویت را تضمین می‌کند که دامنه `utility/time_remaining` اختلافی کمتر از 999 داشته باشد؛ چنین کرانی گزارش نشده است.
- `[صریح در مقاله]` هر تعداد job ممکن است preempt شود.
- `[صریح در مقاله]` تنها مزیت current jobs، time_remaining کمتر و در نتیجه ratio معمولاً بالاتر است.

### آزمون‌های لازم

1. union شامل current و returning باشد و duplicate نداشته باشد.
2. knapsack از total capacity استفاده کند، نه residual.
3. score دقیق عضو و غیرعضو محاسبه شود.
4. membership priority با نمونه‌ای که ratio غیرعضو بیش از 999 است بررسی شود.
5. چند-victim preemption، آزادسازی و عدم منفی‌شدن منابع آزمون شود.
6. current job منتخب بدون حذف غیرضروری retained شود.

## 10. مدل متمرکز Gurobi

### هدف

`[صریح در مقاله]` حل مدل Section IV با آگاهی کامل از تمام سناریو و ورودهای آینده برای تولید upper bound.

### ورودی و خروجی

- ورودی: کل serverها، jobها، horizon، arrivalها، ظرفیت‌ها، deadlineها، Utilityها و تمام پارامترهای مدل.
- خروجی: `x_{i,j}`، `τ_j`، جریان‌های slot-level و objective.

### شبه‌کد سطح‌بالا

```text
BUILD_OFFLINE_ORACLE(instance):
    create all variables from Section IV
    add constraints (2) through (31)
    set objective (1)
    configure Gurobi using REPORTED_SETTINGS_OR_UNRESOLVED
    optimize
    return status, incumbent, bound, gap, runtime, assignments, flows
```

### موانع

- ناسازگاری indexing روابط (2)-(6)
- strict inequalityهای (8) و (30)
- integrality نامشخص offsetهای زمانی
- تنظیمات و نسخه Gurobi نامشخص
- مدل شامل حاصل‌ضرب متغیرهای تصمیم است؛ نحوه linearization یا تنظیم nonconvex گزارش نشده است

این oracle هنوز شبه‌کد قابل اجرا نیست و پیش از کدنویسی به تصمیم‌های مرحله سوم وابسته است.

## 11. پیچیدگی زمانی و فضایی

| مؤلفه | زمان | فضا | وضعیت |
| --- | --- | --- | --- |
| KG Round 1 knapsack | `O(n^g)` با `g≈30` | `[نامشخص]` | `[صریح در مقاله]`؛ این همان ادعای مقاله است، نه تحلیل مستقل |
| KG Round 1 pricing | در متن جداگانه گزارش نشده؛ حلقه روی jobها دارد | `[نامشخص]` | `[استخراج مستقیم]` حداقل پیمایش jobها لازم است |
| KG-P Round 2 | `O(n_2 m)` | `[نامشخص]` | `[صریح در مقاله]` |
| KG کل | `O(n^g+n_2m)=O(n^g)` | `[نامشخص]` | `[صریح در مقاله]` |
| DK-R | `[نامشخص]` در v2 | `[نامشخص]` | فقط کندتر بودن صریح است |
| DK-P | `[نامشخص]` در v2 | `[نامشخص]` | knapsack و سپس sort/fit دارد، ولی bound رسمی ارائه نشده |
| Gurobi oracle | رشد نمایی با اندازه مسئله | `[نامشخص]` | `[صریح در مقاله]` به‌صورت توصیفی؛ bound رسمی ارائه نشده |

نکته: `[صریح در مقاله]` `g` تعداد نسل‌های GA و تقریباً 30 است. population size و هزینه fitness مشخص نیست؛ بنابراین ادعای `O(n^g)` بدون بازسازی تنظیمات GA قابل راستی‌آزمایی نیست.

## 12. ناسازگاری‌های متن، شبه‌کد و ادعاها

### 12.1 جهت شرط 5 درصد

- محل اول: Section V-A2، صفحه 7، نثر «new job حداقل 5 درصد ارزشمندتر».
- محل دوم: Algorithm 2، شرط `new_ratio*1.05 >= old_ratio`.
- نوع: نامساوی غیرمعادل و جهت ضریب متفاوت.
- اثر: victimهایی ممکن است preempt شوند که ratio آن‌ها از job جدید بیشتر است.
- گزینه‌ها:
  1. literal pseudocode؛
  2. literal prose یعنی `new_ratio >= 1.05*old_ratio`؛
  3. حذف ضریب در صورت خطای نگارشی.
- نزدیک‌ترین تفسیر پیشنهادی: گزینه 2، چون با عبارت «at least 5% greater» و هدف gain سازگار است. هنوز اعمال نشده است.

### 12.2 تعریف congestion

- محل اول: نثر صفحه 6، congestion برابر مجموع نسبت demand به residual معرفی می‌شود.
- محل دوم: Algorithm 1 از `1-congestion(...)` استفاده می‌کند.
- محل سوم: همان نثر ادعا می‌کند مؤلفه‌ها در `[0,1]` و تخفیف کل حداکثر 5 درصد است، درحالی‌که مجموع چند نسبت می‌تواند از 1 بیشتر شود.
- اثر: server خلوت یا شلوغ ممکن است تخفیف معکوس دریافت کند و قیمت‌ها جهت نادرست پیدا کنند.
- گزینه‌ها:
  1. تابع congestion نسبت «fit quality» بازگرداند و `1-q` درست باشد؛
  2. تابع مقدار congestion بازگرداند و `c2*q` درست باشد؛
  3. میانگین/نرمال‌سازی نسبت‌ها پیش از استفاده.
- نزدیک‌ترین تفسیر قابل تعیین نیست؛ منبع مستقیم [4] برای تعریف پایه لازم است.

### 12.3 job ناممکن

- محل اول: نثر می‌گوید price باید بیشتر از Utility باشد.
- محل دوم: Algorithm 1 هیچ شاخه‌ای برای impossible-fit ندارد و فرمول آن price را حداکثر Utility می‌سازد، اگر عوامل نامنفی باشند.
- اثر: job غیرقابل‌اجرا ممکن است همان server را انتخاب کند.
- مقدار sentinel یا فرمول price `[نامشخص]` است.

### 12.4 نبود break در Algorithm 2

- محل اول: نثر از preempt کردن «another» job مفرد سخن می‌گوید.
- محل دوم: حلقه victim پس از `Preempt` و `Add` ادامه دارد.
- اثر: چند preemption غیرضروری، چند Add، corruption منابع یا وابستگی به semantics مجموعه.
- نزدیک‌ترین تفسیر پیشنهادی: توقف حلقه پس از اولین جایگزینی موفق، ولی هنوز اعمال نشده است.

### 12.5 تضمین score ثابت 1000

- محل اول: DK-P score عضو `1000+ratio` و غیرعضو `1+ratio`.
- محل دوم: متن اولویت اعضا را تضمین‌شده معرفی می‌کند.
- ناسازگاری: بدون upper bound روی ratio، تضمین ریاضی وجود ندارد.
- گزینه نزدیک‌تر: sort با کلید tuple عضویت و سپس ratio؛ این تغییر معادل ادعای اولویت است اما فرمول score چاپ‌شده را عوض می‌کند و نیازمند تأیید است.

### 12.6 mark و impossible branch غایب از شبه‌کد

- mark کردن autoFit و price بیش از Utility در نثر آمده‌اند ولی خطوط Algorithm 1 آن‌ها را اجرا نمی‌کنند.
- پیاده‌سازی وفادار باید مشخص کند نثر تکمیل‌کننده شبه‌کد است یا فقط توضیح غیرالزام‌آور؛ پیشنهاد فعلی، تکمیل شبه‌کد با mark است و توقف درباره sentinel price.

## 13. فهرست تصمیم‌های لازم پیش از پیاده‌سازی

1. انتخاب تفسیر شرط 5 درصد Algorithm 2.
2. تعریف دقیق و نرمال‌شده `congestion(job,residual_resources)`.
3. رفتار percentile وقتی current jobs تهی است.
4. مقدار price برای job غیرقابل‌اجرا روی total capacity.
5. tie-breaking در client choice، knapsack و sort.
6. افزودن یا عدم افزودن `break` پس از preemption موفق KG-P.
7. snapshot یا live بودن `s.jobs` در Algorithm 2.
8. تعریف دقیق Round 2 برای KG-R.
9. استخراج و ادغام کنترل‌شده تعریف کامل DK-R از منبع [4] که اکنون در دسترس است؛ تنظیمات گزارش‌نشده همچنان نباید حدس زده شوند.
10. تعریف دقیق state transition و victim selection برای DK-P.
11. تنظیمات pyeasyga شامل population، generations، mutation، crossover و seed.
12. تفسیر score ثابت 1000 در ratioهای خارج دامنه معمول آزمایش.
13. رفع موانع مدل Gurobi ثبت‌شده در مرحله سوم.

## 14. جمع‌بندی قابلیت تبدیل به Python

| روش | قابلیت تبدیل مستقیم | علت |
| --- | --- | --- |
| KG Round 1 | مشروط | فرمول اصلی موجود است؛ congestion، impossible price و حالت تهی نامشخص‌اند |
| KG-P Round 2 | مشروط | ترتیب و حلقه‌ها موجودند؛ شرط 5 درصد و break ناسازگارند |
| KG-R Round 2 | خیر، بدون فرض | الگوریتم مستقل در v2 ارائه نشده است |
| DK-R | خیر، مستقیماً از v2 | تعریف عمده در منبع [4] است؛ فایل کامل منبع اکنون در دسترس و نیازمند ردیابی مستقل است |
| DK-P | خیر، به‌صورت کامل | score روشن است؛ عملیات fit/preemption و state update غایب‌اند |
| Gurobi oracle | خیر، پیش از تصمیم مدل | روابط وجود دارند ولی ناسازگاری‌های مرحله سوم مانع‌اند |

هیچ `[فرض بازتولید]` در این مرحله انتخاب یا اعمال نشده است. شبه‌کدهای دارای `UNRESOLVED` عمداً غیرقابل‌اجرا نگه داشته شده‌اند تا ابهام به رفتار پنهان تبدیل نشود.
