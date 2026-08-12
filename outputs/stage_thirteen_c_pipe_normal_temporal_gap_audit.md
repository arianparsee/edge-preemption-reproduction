# مرحله سیزدهم-C: ممیزی زمان، ظرفیت و پیشرفت PIPE-NORMAL

تاریخ ممیزی: 2026-08-12  
منبع مبنا: arXiv:2403.15665v2 (2024)  
وضعیت: **ممیزی کامل؛ ASSUMP-033 تا ASSUMP-041 پیشنهادی، غیرفعال و نیازمند تأیید**

## 0. وضعیت واقعی workspace هنگام ادامه

- repository در این workspace پوشه `.git` ندارد؛ بنابراین تعیین نقطه توقف از
  commit history ممکن نیست و بر timestamp/hash فایل‌ها و اجرای آزمون تکیه شد.
- آخرین زیربخش اجرایی کامل، Stage 13-B است: فایل‌های source/test آن در
  2026-08-12 حدود 12:14 و گزارش آن در 12:18 ثبت شده‌اند.
- پیش از اصلاح حاضر، تغییرهای Stage 13-C فقط چهار سند audit/traceability بودند؛
  هیچ فایل `src/`، `tests/` یا config رسمی PIPE-NORMAL در Stage 13-C تغییر نکرد.
- `configs/experiments/pipe_normal.json` همچنان `execution_status=blocked`، دارای
  9 تصمیم حل‌نشده و run-controlهای `null` است.
- اجرای مستقل کل suite پس از ازسرگیری: `208 passed in 18.56s`؛ failure صفر.
- نتیجه: توقف سرویس در جریان ممیزی Stage 13-C رخ داده بود، نه در اجرای کد. Stage
  13-B آخرین implementation کامل و Stage 13-C یک audit-only زیربخش است.

در این زیربخش هیچ شبیه‌ساز چند-epoch، config اجرایی PIPE-NORMAL یا نتیجه مقاله
ساخته نشد. هدف، جداکردن شواهد منبع از تصمیم‌هایی است که برای اتصال policyهای
تک‌مزایده‌ای به یک مدل زمانی لازم‌اند.

یادداشت اصلاحی: توقف پاسخ پیشین ناشی از پیام سرویس
`Selected model is at capacity. Please try a different model.` بود. این پیام فقط
به ظرفیت سرویس مدل مربوط است و هیچ ارتباطی با ظرفیت سرورهای مقاله، `K_j`، `C_i`
یا ASSUMP-036 ندارد. بررسی total/per-slot زیر یک شکاف علمی مستقل در طراحی موتور
زمانی است و علت توقف پاسخ یا یک خطای مشاهده‌شده در اجرای پروژه نبوده است.

## 1. منابع و محدوده بررسی

- arXiv v2، Section III و Fig.1، PDF p.3: توالی ورود، مزایده و پردازش؛
- arXiv v2، Section IV، PDF pp.4-5: `K_j` کل محاسبه، `C_i` ظرفیت per-slot،
  `s'_j`، روابط pipeline و آزادسازی storage؛
- arXiv v2، Section V-A3، PDF p.7: pyeasyga و `g≈30` برای KG Round 1؛
- arXiv v2، Section VI-A2-A3، PDF pp.8-9: workload نرمال، معیارهای outcome و
  تعریف ستون Preempted؛
- `[استخراج از مرجع مستقیم مقاله]` مرجع [1]، Section II، PDF p.2 و Fig.1:
  توالی epoch و resubmit اختیاری؛
- `[استخراج از مرجع مستقیم مقاله]` مرجع [1]، Section III، PDF pp.2-3:
  مدل batch، `s'_j` بدون توزیع workload و terminal نبودن تعریف retry؛
- `[استخراج از مرجع مستقیم مقاله]` مرجع [1]، Section V-B، PDF pp.7-8:
  نمونه‌های horizon مختص workloadهای متفاوت؛ این مقادیر به PIPE-NORMAL v2
  تعمیم داده نشدند.

مرجع [1] مدل batch را شرح می‌دهد. بنابراین از آن فقط برای تأیید semantics مشترک
مزایده/زمان استفاده شد و هیچ قاعده batch به پیشرفت pipeline نسبت داده نشد.

## 2. شواهد قطعی

| موضوع | یافته | محل | برچسب |
| --- | --- | --- | --- |
| lag زمانی | job پذیرفته‌شده در bid epoch `e` در epoch `e+1` پردازش را آغاز می‌کند | v2 Fig.1 و Section III، p.3 | `[صریح در مقاله]` |
| lag ورود | job واردشده در epoch `e` در `e+1` bid و در صورت پذیرش در `e+2` process می‌شود | همان | `[صریح در مقاله]` |
| retry | job ردشده «ممکن است» در bidding بعدی دوباره ارسال شود | v2 p.3؛ [1] p.2 | `[صریح در مقاله]` / `[استخراج از مرجع مستقیم مقاله]` |
| pipeline | upload، computation و download می‌توانند هم‌زمان پیش بروند | v2 p.3 | `[صریح در مقاله]` |
| تقدم نسبی | fraction computation از fraction upload و fraction download از fraction computation جلو نمی‌زند | v2 روابط (9)-(10)، pp.4-5 | `[صریح در مقاله]` |
| ظرفیت محاسبه | `K_j` total MFlops است، ولی `C_i` ظرفیت سرور در هر slot است | v2 p.4 | `[صریح در مقاله]` |
| ظرفیت شبکه | ظرفیت upload/download سرور برابر rate ضرب‌در slot duration است | v2 p.4، footnote 3 | `[صریح در مقاله]` |
| خروجی | completion به ارسال کامل `s'_j` وابسته است | v2 روابط (6)-(10) | `[صریح در مقاله]` |
| utility | all-or-nothing؛ preemption پیش از completion utility صفر می‌دهد | v2 p.4 و objective | `[صریح در مقاله]` |
| Preempted bar | taskهایی را می‌شمارد که حداقل یک‌بار preempt شده‌اند | v2 Section VI-A3، p.9 | `[صریح در مقاله]` |
| KG GA | Round-1 knapsack با pyeasyga و حدود 30 generation اجرا می‌شود | v2 Section V-A3، p.7 | `[صریح در مقاله]` |

## 3. شکاف مستقل نگاشت total/per-slot در موتور زمانی

`SyntheticTaskRecord.to_domain()` در وضعیت فعلی و برای دامنه allocation-layer،
مقدار total computation یعنی
`K_j≈N(100,20)` MFlops را مستقیماً در بعد computation از `ResourceVector` قرار
می‌دهد، در حالی که ظرفیت متناظر server برابر `C_i≈N(80,20)` MFlops/s در هر slot
است. مقایسه مستقیم این دو:

```text
task_total_computation <= server_per_slot_computation
```

هم از نظر واحد نادرست است و هم بسیاری از jobهای معمولی را به‌اشتباه «بزرگ‌تر از
ظرفیت کل سرور» نشان می‌دهد. arXiv v2 نیز در p.8 می‌گوید heuristic از حداقل منابع
per-timestep برای تضمین completion استفاده می‌کند، اما فرمول این حداقل را چاپ
نمی‌کند.

این وضعیت در کد فعلی یک failure نیست، زیرا Stage 11-B صریحاً allocation-layer-only
است و هنوز به موتور زمانی متصل نشده است. اثر احتمالی در پیاده‌سازی آینده این است
که اجرای temporal با همین نگاشت می‌تواند نرخ rejection، congestion، price،
preemption و Utility را به‌شدت منحرف کند. بنابراین اتصال generator به policy تا
تأیید ASSUMP-036 مجاز نیست.

## 4. شکاف‌ها، گزینه‌ها و گزینه نزدیک‌تر

| شکاف | محل‌های بررسی‌شده | اثر | گزینه‌ها | گزینه پیشنهادی |
| --- | --- | --- | --- | --- |
| seed/repeat/aggregation | v2 Section VI کامل | bars و واریانس تکرارپذیر نیست | یک run؛ چند seed؛ fit به شکل | seed list صریح، raw مستقل و mean؛ ASSUMP-033 |
| horizon/drain | v2 pp.8-12؛ [1] pp.7-8 | total jobs و terminal totals تغییر می‌کند | عدد قرض‌گرفته‌شده؛ stop فوری؛ deadline-derived drain | envelope اجباری و drain تا آخرین deadline؛ ASSUMP-034 |
| ordering در epoch | v2 Fig.1 و روابط (22)-(27) | off-by-one و victim progress تغییر می‌کند | auction-first؛ progress-first؛ event microsteps | progress/completion/deadline سپس auction commit؛ ASSUMP-035 |
| total/per-slot computation | v2 pp.4 و 8 | feasibility نادرست | `K_j` مستقیم؛ `K_j/d_j` ثابت؛ remaining-work/remaining-slots | نرخ ثابت در admission؛ ASSUMP-036 |
| output size | v2 روابط (6)-(10)، Tables I-II؛ [1] pp.2-3 | completion pipeline قابل تعیین نیست | omission؛ input=output؛ نسبت ثابت/توزیع جدید | `s'_j=s_j` فقط با برچسب فرض؛ ASSUMP-037 |
| پیشرفت pipeline | v2 روابط (9)-(10) | زمان completion و resource release نامعلوم | مدل مرحله‌ای؛ جریان آزاد solver؛ گام حریصانه محدودشده | update upload→compute→download در هر slot؛ ASSUMP-038 |
| retry/preempted | v2 p.3، p.9؛ [1] p.2 | pool size و utility عوض می‌شود | no retry؛ always retry؛ probability | retry ردشده تا feasible deadline؛ preempted terminal؛ ASSUMP-039 |
| rejected metric | v2 Figs.6-8 و تعریف Preempted | جمع ستون‌ها ambiguous است | auction rejection؛ final non-completion؛ disjoint states | complement نهایی completed با overlay preempted؛ ASSUMP-040 |
| KG GA کامل | v2 p.7 و ممیزی [28] قبلی | subset stochastic و price تغییر می‌کند | Exact؛ default 50؛ config audited با 30 generation | pyeasyga 0.3.1، 200/20/30؛ ASSUMP-041 |
| Normal high/low | v2 captions Figs.7-8 و Table I | Figs.7-8 قابل ساخت نیست | mean threshold؛ quantile؛ fit از bar | همچنان blocked؛ هیچ threshold پیشنهاد عددی نمی‌شود |

## 5. ASSUMP-033 — seedها، تکرارها و aggregation صریح

- وضعیت: **پیشنهادی؛ غیرفعال**.
- هر run باید یک seed صریح و یکتا داشته باشد؛ فهرست مرتب seedها و تعداد runها
  ورودی اجباری config باشند و هیچ مقدار پیش‌فرضی نداشته باشند.
- برای هر seed دقیقاً یک workload تولید و همان workload میان چهار policy به اشتراک
  گذاشته شود؛ هر policy RNG stream مستقل و نام‌دار داشته باشد.
- raw result هر `(seed, policy)` جدا حفظ شود. مقدار تجمیعی، arithmetic mean روی
  runهای مستقل باشد؛ standard deviation/CI فقط `[آزمون کمکی]` است و به bars مقاله
  نسبت داده نمی‌شود.
- تا زمانی که seed list و repeat count عددی انتخاب نشده‌اند، نتیجه صرفاً
  reproduction-under-assumptions است، نه بازتولید دقیق instance مقاله.

## 6. ASSUMP-034 — افق ورود و drain مبتنی بر deadline

- وضعیت: **پیشنهادی؛ غیرفعال**.
- `arrival_slots` و `drain_slots` مطابق ASSUMP-024 ورودی اجباری و بدون default
  باقی بمانند؛ مقادیر 102/0 موجود فقط artifact کمکی Stage 11-B هستند.
- پیش از اجرا باید برقرار باشد:

  `configured_last_slot >= max(task.absolute_deadline_slot)`.

- پس از آخرین slot ورود، arrival جدید ساخته نشود؛ simulation تا terminal شدن همه
  taskها ادامه یابد و اگر زودتر terminal شدند زود متوقف شود.
- اگر drain پیش از آخرین deadline تمام شود، run fail-fast کند و taskها را پنهانی
  rejected/expired نکند.
- هیچ عدد horizon از [1] یا ارتفاع شکل‌های v2 به PIPE-NORMAL منتقل نشود.

## 7. ASSUMP-035 — ترتیب canonical رویدادهای هر epoch

- وضعیت: **پیشنهادی؛ غیرفعال**.
- در epoch `e`، به ترتیب زیر عمل شود:
  1. allocationهای فعالِ پذیرفته‌شده در epochهای قبلی یک slot پیشرفت کنند؛
  2. completionها ثبت و منابعشان آزاد شود؛
  3. با رعایت ASSUMP-001، task ناقص فقط پس از فرصت completion روی مرز inclusive
     منقضی شود؛
  4. arrivalهای epoch `e` ثبت شوند، ولی تا `e+1` وارد bidding نشوند؛
  5. jobهای eligible مزایده دو-round را اجرا کنند؛
  6. تصمیم Round 2 اتمیک commit شود و پذیرش‌های epoch `e` از ابتدای `e+1`
     `PIPELINE_ACTIVE` شوند.
- auction درون یک epoch زمان شبیه‌سازی را جلو نبرد؛ آزمایش‌های auction-time scope
  جدا و همچنان blocked هستند.

## 8. ASSUMP-036 — canonicalization ظرفیت محاسباتی per-slot

- وضعیت: **پیشنهادی؛ غیرفعال**.
- برای PIPE-NORMAL بدون auction-time، یک slot واحد ظرفیت گزارش‌شده در Table I است؛
  تبدیل ثانیه‌ای اضافی انجام نشود و این normalization در metadata ثبت شود.
- هنگام پذیرش در auction epoch `e`، اولین slot پردازش `e+1` است. تعداد فرصت‌های
  inclusive برابر است با:

  `service_slots = absolute_deadline_slot - e`.

- اگر `service_slots <= 0`، job برای پذیرش غیرقابل‌اجرا است.
- تقاضای computation رزروشده در کل عمر allocation ثابت باشد:

  `compute_per_slot = remaining_computation / service_slots`.

- ابعاد admission vector عبارت‌اند از: storage=`s_j`، computation مقدار بالا،
  upload=`b_u,j` و download=`b_d,j`؛ مقایسه مستقیم total `K_j` با `C_i` ممنوع است.
- در retry، `remaining_computation` حفظ و نرخ بر مبنای فرصت‌های باقی‌مانده دوباره
  محاسبه شود. allocation فعال نرخ پذیرفته‌شده خود را تا completion/preemption
  حفظ کند؛ افزایش پنهانی نرخ مجاز نیست.
- اثر: این تفسیر محافظه‌کارانه و اجرایی است، اما چون فرمول minimum resource در v2
  چاپ نشده، نتیجه دقیق paper-code ادعا نمی‌شود.

## 9. ASSUMP-037 — اندازه خروجی مصنوعی

- وضعیت: **پیشنهادی؛ غیرفعال**.
- برای Synthetic Normal در temporal PIPE-NORMAL قرار داده شود:

  `output_size_mb = storage_mb`، یعنی `s'_j = s_j`.

- دلیل توصیه: تنها انتخاب بدون پارامتر عددی تازه است و upload/download job در Table I
  توزیع یکسان دارند؛ با این حال، مقاله این برابری را بیان نکرده است.
- این فرض دامنه ASSUMP-026 را فقط برای workload temporal تصویب‌شده آینده گسترش
  می‌دهد؛ artifactهای Stage 11-B تغییر نمی‌کنند و allocation-layer-only می‌مانند.
- alternative `s'_j` مستقل یا نسبت ثابت ناشناخته رد می‌شود، چون پارامتر تازه و
  بدون منبع می‌سازد.

## 10. ASSUMP-038 — گام پیشرفت deterministic pipeline

- وضعیت: **پیشنهادی؛ غیرفعال**.
- در هر slot فعال، سه cumulative quantity نگهداری شود: uploaded، computed و
  downloaded.
- update درون slot به ترتیب upload، computation و download انجام شود؛ مقدار همان
  slot در constraintهای cumulative قابل استفاده است، چون روابط (9)-(10) مجموع را
  تا slot `n` می‌سنجند.
- هر update به reservation همان بعد، کار باقی‌مانده و تقدم نسبتی محدود شود:
  - `computed / K_j <= uploaded / s_j`؛
  - `downloaded / s'_j <= computed / K_j`.
- storage `s_j` از زمان activation به‌صورت محافظه‌کارانه reserve شود و فقط پس از
  completion یا preemption اتمیک آزاد شود. این با فضای ثابت مورد استفاده auction
  سازگار است، هرچند formulation مرکزی cumulative storage را دقیق‌تر مدل می‌کند.
- completion فقط وقتی ثبت شود که هر سه مقدار با tolerance عددی ثبت‌شده به totals
  خود برسند؛ completion در مرز ASSUMP-001 معتبر است.
- tolerance باید config/metadata صریح داشته باشد و برای تغییر outcome استفاده نشود.

## 11. ASSUMP-039 — retry ردشده و terminal بودن preemption

- وضعیت: **پیشنهادی؛ غیرفعال**.
- rejection در یک Round 2 حالت نهایی فوری نیست؛ task به `WAITING_RETRY` برود و در
  bidding phase بعدی دوباره submit شود، مشروط به اینکه ASSUMP-036 نشان دهد هنوز
  حداقل یک برنامه completion feasible پیش از deadline دارد.
- حداکثر یک تلاش در هر bidding epoch انجام شود؛ counter و علت هر شکست ثبت شود.
- jobی که دیگر feasible نیست به `EXPIRED` برود و دیگر submit نشود.
- job preempted برای همان task instance terminal است، utility صفر می‌گیرد و retry
  نمی‌شود؛ در غیر این صورت all-or-nothing preemption به بازشروع نامحدود تبدیل
  می‌شود که مقاله تعریف نکرده است.

## 12. ASSUMP-040 — semantics معیارهای outcome

- وضعیت: **پیشنهادی؛ غیرفعال**.
- `completed_utility`: جمع Utility taskهای `COMPLETED` تا deadline inclusive.
- `rejected_utility`: جمع Utility تمام taskهای نهایی که completed نشده‌اند؛ شامل
  never-admitted/expired/preempted، دقیقاً یک‌بار برحسب task ID.
- rejection موقتِ taskی که بعداً complete می‌شود در rejected نهایی مشارکت نکند.
- `ever_preempted_utility` و `ever_preempted_jobs` overlay مستقل بر task ID باشند؛
  با completed/rejected یک partition جدا نسازند. برای preemption terminal، این
  overlay زیرمجموعه rejected است.
- raw event counts از terminal metrics جدا ذخیره شوند تا تعداد auction rejection
  با تعداد jobهای نهایی اشتباه نشود.

## 13. ASSUMP-041 — GA رسمی KG Round 1

- وضعیت: **پیشنهادی؛ غیرفعال**.
- pyeasyga `0.3.1` ممیزی‌شده استفاده شود با:
  - `population_size=200`؛
  - `tournament_size=20`؛
  - `generations=30` مطابق `g≈30` در v2؛
  - crossover probability `0.8`، mutation probability `0.2`، elitism و
    maximisation فعال؛
  - tournament selection، one-point crossover، one-bit mutation و random binary
    initialization همان source ممیزی‌شده.
- seed ورودی اجباری، ورودی taskها canonical برحسب task ID و تمام settings در
  config/metadata ثبت شوند.
- population 200 از مثال multidimensional رسمی pyeasyga می‌آید، نه از v2؛ پس
  `[فرض بازتولید]` باقی می‌ماند. Exact Solver فقط `[ابزار کمکی]` آزمون است.
- این فرض به تنظیم 200/20/50 Pipeline DK در ASSUMP-015/018 دست نمی‌زند.

## 14. تصمیمی که عمداً پیشنهاد عددی نگرفت

`NORMAL_HIGH_LOW_THRESHOLDS` همچنان blocked است. v2 فقط captions high/low را دارد
و Table I یک Normal پیوسته برای Utility می‌دهد؛ threshold، quantile یا latent label
را بیان نمی‌کند. استخراج threshold از ارتفاع barها tuning معکوس است. بنابراین:

- Fig.6 پس از تصویب و پیاده‌سازی فرض‌های بالا می‌تواند به‌صورت
  reproduction-under-assumptions هدف قرار گیرد؛
- Figs.7-8 و بخش high-value از Fig.10 تا دریافت source/code یا تصویب یک فرض مستقل
  همچنان non-executable می‌مانند.

## 15. نتیجه readiness

پس از این ممیزی، شکاف مستقل نگاشت total/per-slot و گزینه اجرایی نزدیک‌تر تعریف
شد، اما هیچ فرضی فعال نشده است. این یافته علت توقف سرویس نبوده و از یک failure
پروژه نیز استخراج نشده است. PIPE-NORMAL همچنان blocked است. برای شروع پیاده‌سازی موتور
چند-epoch باید ASSUMP-033 تا ASSUMP-041 تأیید یا اصلاح شوند. حتی پس از تأیید، seed
list، repeat count و arrival/drain عددی paper گزارش نشده‌اند و خروجی باید با برچسب
`[بازتولید تحت فرض]` نگهداری شود؛ Figs.7-8 نیز جداگانه blocked می‌مانند.
