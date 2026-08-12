# مرحله سیزدهم-E: ممیزی پیش‌اجرای PIPE-NORMAL کامل

تاریخ: 2026-08-12

وضعیت: **ASSUMP-042 پیاده‌سازی شد؛ pilot چهارروشی در tie قیمت KG متوقف شد**

این زیربخش هیچ اجرای 100 slot × 30 repeat، هیچ‌یک از 120 اجرای policy و هیچ
نمودار Figure 6 را تولید نکرد.

## 1. ممیزی ورودی اجرای کامل

- مولد Normal موجود از Table I، هشت سرور و `N(14,4)` وظیفه در هر arrival slot
  استفاده می‌کند.
- اجرای کامل 100-slot تقریباً 1400 وظیفه در هر workload خواهد داشت؛ مقدار دقیق
  برای هر seed تصادفی و در raw workload ثبت خواهد شد.
- مطابق ASSUMP-033، از `root_seed=20240812` سی child seed مستقل با
  `NumPy SeedSequence` ساخته و به‌صورت عدد `uint64` مادی شدند؛ فهرست برای config
  نهایی مرتب است.
- هر workload seed چهار child seed مستقل و نام‌دار برای KG-R، KG-P، DK-R و DK-P
  خواهد داشت.
- config/runner full هنوز ساخته نشد، چون pilot پیش از برآورد زمان یک failure
  علمی در GA آشکار کرد.

## 2. pilot واقعی

Pilot عمداً کوچک و با برچسب `[آزمون کمکی]` اجرا شد:

```text
workload_seed = 15626834761513784926
policy = knapsack_greedy_retention
policy_seed = 14636373841211474365
arrival_slots = 3
server_count = 8
generated_tasks = 47
configured_last_slot = 17
```

در epoch 1، بیست وظیفه پس از canonicalization و dry-run pipeline eligible بودند.
هر بیست وظیفه روی `server-001` به‌تنهایی fit می‌شدند. نخستین اجرای GA این خطا را
در guard adapter ایجاد کرد:

```text
StateValidationError: pyeasyga returned an infeasible best chromosome
```

بنابراین pilot پیش از اندازه‌گیری runtime کامل متوقف شد. هیچ نتیجه ناقص به‌عنوان
نتیجه آزمایش ذخیره نشد.

## 3. علت مستقیم

`[استخراج از مرجع مستقیم مقاله]` مثال رسمی multidimensional knapsack در
pyeasyga، fitness chromosome ناممکن را صفر تعیین می‌کند؛ همین رفتار قبلاً در
ممیزی [28] ثبت و در adapter اجرا شده است.

`[استخراج مستقیم از pyeasyga 0.3.1]`:

- initialization آرایه بیتی تصادفی است؛
- population فقط برحسب fitness مرتب می‌شود؛
- sort پایتون در fitness مساوی ترتیب موجود را حفظ می‌کند؛
- chromosome خالی feasible و دارای Utility/fitness صفر است؛
- chromosome ناممکن نیز fitness صفر می‌گیرد؛
- کتابخانه در این tie هیچ اولویت feasibility ندارد.

در فضای چهاربعدی و pool بیست‌عضوی، chromosomeهای تصادفی غالباً ناممکن‌اند. GA
pilot هیچ subset feasible با fitness مثبت را در نسل نهایی به رتبه اول نرساند؛
یک chromosome ناممکن با fitness صفر برگردانده شد. adapter اجازه عبور آن را نداد.

## 4. اثر بر بازتولید

- این failure در workload مصنوعی واقعی رخ داد، نه فقط یک edge case ساختگی.
- KG و DK از همان adapter استفاده می‌کنند، پس هر چهار policy ممکن است متوقف شوند.
- full run و Figure 6 بدون تصمیم صریح قابل اجرا نیستند.
- تغییر penalty یا استفاده از Exact Solver landscape و نتیجه الگوریتم را تغییر
  می‌دهد و نمی‌تواند پنهانی اعمال شود.

## 5. گزینه‌ها

### گزینه A — پیشنهادی: repair هم‌fitness به empty feasible

اگر best ناممکن و fitness آن دقیقاً صفر باشد، subset خالی بازگردانده شود. subset
خالی feasible و دارای همان fitness صفر است. اگر fitness ناممکن غیرصفر بود،
fail-fast باقی بماند. تعداد repairها per-run ثبت شود.

مزیت: fitness، seed، population، selection، crossover، mutation و generations
تغییر نمی‌کنند؛ Exact Solver یا penalty ساخته نمی‌شود. فقط tie نامعتبر خروجی به
نماینده feasible هم‌fitness تبدیل می‌شود.

اثر: membership خالی می‌تواند قیمت‌گذاری و Round 2 را تغییر دهد؛ بنابراین این
رفتار حتماً `[فرض بازتولید]` است.

### گزینه B: penalty منفی درجه‌بندی‌شده

برای chromosome ناممکن fitness منفی متناسب با میزان violation ساخته شود. probe
کمکی نشان داد این روش در همان seed یک subset تک‌عضوی feasible با Utility
`87.49198083114642` یافت.

این گزینه توصیه نمی‌شود، چون fitness landscape مثال رسمی pyeasyga را تغییر و یک
فرمول penalty گزارش‌نشده ایجاد می‌کند.

### گزینه C: fail-fast بدون repair

رفتار فعلی حفظ شود. این وفادارترین رفتار به خروجی خام library است، اما اجرای
PIPE-NORMAL کامل را در pilot موجود مسدود می‌کند.

### گزینه‌های مردود بدون فرض مستقل

- Exact Solver fallback؛
- greedy repair یا حذف تدریجی itemها؛
- تغییر seed یا تکرار GA تا دستیابی به جواب feasible؛
- تزریق chromosome صفر به initial population، چون random binary initialization
  مصوب را تغییر می‌دهد.

## 6. پیشنهاد

ASSUMP-042 با گزینه A نزدیک‌ترین تصمیم به منابع است: objective و تمام operatorهای
ممیزی‌شده ثابت می‌مانند و فقط خروجی tie صفر به یک نماینده feasible با همان fitness
نگاشت می‌شود. این تصمیم باید پیش از تغییر کد تأیید شود.

## 7. وضعیت آزمون و کد

- هیچ فایل source، test، config اجرایی full یا result رسمی در Stage 13-E تغییر
  نکرد.
- فقط ledger فرض‌ها، ماتریس ردیابی و این audit به‌روزرسانی شدند.
- suite موجود پس از تغییر اسناد به‌صورت هدفمند اجرا می‌شود.

## 8. تصمیم موردنیاز

تأیید یا رد ASSUMP-042. پس از تأیید گزینه A، adapter و counter metadata آزمون
می‌شوند، همان pilot دوباره اجرا می‌شود و فقط در صورت موفقیت، config کامل، runner
قابل resume و برآورد هزینه 120 run ساخته خواهد شد.

## 9. تصمیم کاربر

کاربر در 2026-08-12 ASSUMP-042 را مطابق گزینه A تأیید کرد. اجرای Stage 13-E از
همان workload/seed شکست‌خورده ادامه می‌یابد تا اثر repair بدون تغییر سایر عوامل
کنترل شود.

## 10. ادامه کنترل‌شده پس از تصویب ASSUMP-042

ASSUMP-042 در adapter رسمی `PyeasygaUtilityKnapsackSelector` پیاده‌سازی شد. فقط
best ناممکن با fitness دقیقاً برابر infeasible-fitness صفر به subset خالی feasible
هم‌fitness نگاشت می‌شود؛ best ناممکن با fitness غیرصفر همچنان fail-fast است. شمارنده
runtime نیز به metadata اجرای خام متصل شد.

سه آزمون واحد مستقل، شاخه repair صفر، شاخه nonzero fail-fast و عدم repair برای
best feasible صفر را پوشش می‌دهند. smoke قبلی Stage 13-D نیز metadata با counter
صفر را بررسی می‌کند.

همان pilot KG-R، بدون تغییر workload seed یا policy seed، دوباره اجرا و موفق شد:

```text
workload_seed = 15626834761513784926
policy_seed = 14636373841211474365
tasks = 47
configured_last_slot = 17
elapsed_seconds = 24.949999899999966
ga.zero_fitness_feasibility_repairs = 74
completed_jobs = 11
rejected_jobs = 36
completed_utility = 798.0522712338435
rejected_utility = 2060.8384169428086
raw_auction_rejection_count = 201
```

این اعداد `[آزمون کمکی]` هستند و نتیجه Figure 6 یا نتیجه عددی مقاله نیستند.

## 11. شکاف بعدی آشکارشده در pilot چهارروشی

اجرای KG-P روی دقیقاً همان workload و policy seed مستقل مادی‌شده
`10214968163706227246` در epoch 11 متوقف شد. در آن نقطه:

```text
task_id = job-000032
utility = 49.04331194345249
minimum_price = 44.13898074910724
tied_servers = [server-003, server-007]
ga.zero_fitness_feasibility_repairs = 76
elapsed_seconds = 25.95925239999997
exception = UnresolvedDecisionError
message = equal minimum server prices require an unreported client tie-break
```

این تساوی قابل‌قبول است، چون minimum price از Utility کمتر است؛ پس شاخه رد به‌علت
price>Utility نیست. arXiv v2 قاعده عمومی tie را تعیین نمی‌کند، هرچند مثال Fig. 4
در PDF page 7 یکی از دو fit-price مساوی را تصادفی انتخاب می‌کند. ASSUMP-014 همین
شکاف را فقط برای Pipeline DK-R حل کرده بود و عمداً به KG تعمیم داده نشده است.

### ASSUMP-043 پیشنهادی — گزینه A نزدیک‌تر به منبع

برای KG-R و KG-P، در تساوی دقیق چند minimum price قابل‌قبول، server IDهای tied
مرتب و یکی به‌صورت uniform با همان RNG stream اجباری و نام‌دار policy انتخاب شود.
برای minimum یکتا RNG مصرف نشود. شمارنده `client.equal_minimum_price_ties` در raw
metadata ثبت شود. این تصمیم به tieهای sorting، victim، DK-P score یا chromosome
تعمیم داده نشود.

گزینه B انتخاب lexicographic نخست است؛ بازتولیدپذیر اما از انتخاب تصادفی مثال v2
دورتر است. گزینه C حفظ fail-fast است که full experiment را در همین pilot مسدود
نگه می‌دارد. ASSUMP-043 هنوز پیاده‌سازی نشده و نیازمند تأیید صریح کاربر است.

## 12. دامنه‌ای که عمداً اجرا نشد

- DK-R و DK-P pilot پس از شکست KG-P اجرا نشدند؛
- config/runner اجرای کامل ساخته نشد؛
- هیچ‌یک از 120 اجرای 100-slot×30 شروع نشد؛
- Figure 6 تولید نشد.

## 13. Stage 13-F پس از تصویب ASSUMP-043

ASSUMP-043 با گزینه A تصویب و فقط برای client choice مشترک KG-R/KG-P پیاده‌سازی
شد. resolver فقط برای minimum-priceهای دقیقاً مساوی فراخوانی می‌شود؛ شناسه‌های
سرورها ابتدا مرتب و سپس با همان RNG stream موجود policy به‌صورت uniform انتخاب
می‌شوند. minimum یکتا RNG tie را مصرف نمی‌کند و tieهای victim/sort/DK-P/GA خارج
از scope باقی مانده‌اند. شمارنده `client.equal_minimum_price_ties` به metadata
runtime افزوده شد.

همان KG-P شکست‌خورده، بدون تغییر workload یا policy seed، موفق شد:

```text
policy = knapsack_greedy_preemption
policy_seed = 10214968163706227246
elapsed_seconds = 25.594418199998472
zero_fitness_repairs = 76
equal_minimum_price_ties = 1
completed_jobs = 13
rejected_jobs = 34
completed_utility = 950.3178609398235
rejected_utility = 1908.5728272368285
```

دو policy باقی‌مانده نیز روی همان workload موفق شدند:

| Policy | Seed | Time (s) | Repairs | Client ties | Completed | Rejected | Preempted | Completed utility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| KG-R | 14636373841211474365 | 24.9500 | 74 | 0 | 11 | 36 | 0 | 798.0522712338435 |
| KG-P | 10214968163706227246 | 25.5944 | 76 | 1 | 13 | 34 | 0 | 950.3178609398235 |
| Pipeline DK-R | 9334793088729515147 | 49.7616 | 85 | 0 | 10 | 37 | 0 | 729.6781521141075 |
| Pipeline DK-P | 10066703118538082645 | 50.3811 | 77 | 0 | 9 | 38 | 4 | 682.409599271039 |

این جدول فقط `[آزمون کمکی]` است. wall-timeها نتیجه مقاله یا benchmark رسمی نیستند.

config کامل `pipe_normal_full_stage13f.json` پیش از اجرا مادی شد: 30 workload seed
مرتب، 120 policy seed مستقل، تنظیمات کامل GA و ASSUMP-033 تا ASSUMP-043. runner
هر زوج policy/workload را در مسیر مجزا ذخیره می‌کند، overwrite را رد می‌کند و در
resume فقط hashهای موجود را تأیید و skip می‌کند. aggregator تا وجود هر 120 raw
result fail-fast می‌کند و فقط arithmetic mean می‌سازد.

وضعیت واقعی پایان Stage 13-F:

```text
materialized_config_sha256 = AFA7C249911D34CDACEFA4B2B80CDBFC44CDDF47A7F2CFD0E246E7CD70FEE3F0
full_raw_results = 0
full_run_started = false
figure_6_reproduced = false
aggregation_probe = FileNotFoundError: missing 120
```
