# Stage 15-K — اصلاحات کنترل‌شده پیشنهادی

## اصل جداسازی

در 2026-09-02 فقط ASSUMP-048 و ASSUMP-049 برای Stage 15-K.1 و با برچسب
`[فرض آزمون کمکی]` تأیید شدند. ASSUMP-050 تا ASSUMP-053 پیشنهادی، تأییدنشده
و غیرفعال‌اند. Pipeline رسمی، baselineها، Figure 6 و روش‌های مقاله بدون تغییر
می‌مانند.

معیار پذیرش هر اصلاح:

1. قاعده فعلی در مقاله صریح نباشد یا شواهد معتبری از سخت‌گیری آن وجود داشته باشد.
2. نسخه جایگزین از نظر مدل سیستم قابل دفاع باشد.
3. اثر تک‌عاملی، تکرارپذیر و بدون شکست invariant باشد.

نزدیکی به Figure 6 به‌تنهایی معیار پذیرش نیست و هیچ پارامتری tune نخواهد شد.

## ASSUMP-048 — پروتکل حفاظتی pilot `[فرض آزمون کمکی؛ تأییدشده]`

**متن پیشنهادی:** هر pilot Stage 15-K.1 فقط روی اولین workload seed فهرست مرتب ASSUMP-033 و فقط برای DK-R و DK-P اجرا شود. baseline معتبر reuse شود. هر logical pair دو replay با workload seed، policy seed و config یکسان داشته باشد. برابری outcome، Utility، task partition، Funnel، config، invariantها و RNG طبق Option-A gate کنترل شود. variantها مستقل و تک‌عاملی باشند؛ هیچ tuning، ترکیب اصلاح، padding draw یا reseed مجاز نباشد.

- حفظ قاعده فعلی: عدم اجرای pilot.
- اصلاح حداقلی پیشنهادی: پذیرش متن فوق به‌عنوان چارچوب، بدون تغییر علمی policy.
- گزینه جایگزین: اجرای مستقیم پنج seed؛ رد می‌شود چون pilot کم‌هزینه‌تر هنوز انجام نشده است.
- توصیه: تأیید شود.
- اثر مورد انتظار بر Funnel: ندارد؛ فقط اعتبار آزمایش را تضمین می‌کند.
- ریسک فاصله از مقاله: بسیار کم؛ پروتکل آزمون است، نه الگوریتم.

## ASSUMP-049 — initialization feasibility repair فقط در Round 2 `[فرض آزمون کمکی؛ تأییدشده]`

**متن پیشنهادی:** فقط هنگام ساخت population اولیه GA در Round 2 روش‌های DK، chromosome باینری با همان تعداد draw و همان canonical task-ID order ساخته شود؛ اگر ناممکن بود، بیت‌های منتخب از انتهای ترتیب canonical به‌صورت deterministic حذف شوند تا feasible شود. Round 1، fitness، crossover، mutation، pricing، server choice، lifecycle و ASSUMP-042 تغییر نکنند. repair هیچ draw تصادفی اضافه نکند و با repair دیگری ترکیب نشود.

- حفظ قاعده فعلی: population خام و fitness صفر برای infeasible chromosome.
- اصلاح حداقلی پیشنهادی: R2-only initialization repair.
- گزینه جایگزین: initialization repair در هر دو Round؛ فعلاً رد می‌شود چون تک‌عاملی بودن محل bottleneck را مخدوش می‌کند.
- توصیه: **اولین pilot**؛ قوی‌ترین نسبت شواهد به ریسک.
- اثر مورد انتظار بر Funnel: کاهش Round-2 rejection و `NEVER_ADMITTED_EXPIRED`، افزایش admission/completion؛ `PRE_ADMISSION_INFEASIBLE` نباید تغییر کند.
- فرضیه رد می‌شود اگر: admission/Completed Utility تغییر معنادار تفسیری نکند، feasibility بهتر نشود، یا invariant/RNG gate شکست بخورد.
- ریسک فاصله از مقاله: متوسط؛ repair مقاله منتشر نشده، ولی constraint-preserving و بدون پارامتر جدید است.

## ASSUMP-050 — offspring feasibility repair فقط در Round 2 `[پیشنهادشده و تأییدنشده]`

**متن پیشنهادی:** فقط در GA Round 2، پس از crossover/mutation و پیش از fitness، offspring ناممکن با حذف deterministic بیت‌های منتخب از انتهای canonical order feasible شود. initial population، Round 1 و سایر منطق‌ها تغییر نکنند. تعداد/ترتیب drawهای GA ثابت بماند و این variant با ASSUMP-049 ترکیب نشود.

- حفظ قاعده فعلی: offspring ناممکن با fitness فعلی ارزیابی شود.
- اصلاح حداقلی پیشنهادی: R2-only offspring repair.
- گزینه جایگزین: repair ترکیبی initialization+offspring؛ ممنوع تا اثر مستقل هرکدام روشن شود.
- توصیه: فقط پس از یا موازی با pilot مستقل ASSUMP-049، نه به‌عنوان انتخاب اول.
- اثر مورد انتظار بر Funnel: مشابه ASSUMP-049، با مداخله بیشتر در نسل‌ها.
- فرضیه رد می‌شود اگر: اثر از ASSUMP-049 قابل تفکیک نباشد، replay/RNG gate شکست بخورد، یا repair زیاد بدون افزایش admission باشد.
- ریسک فاصله از مقاله: متوسط رو به بالا؛ تعداد مداخلات بسیار بیشتر است.

## ASSUMP-051 — حذف isolated full-pipeline dry-run از admission `[پیشنهادشده و تأییدنشده]`

**متن پیشنهادی:** canonical resource vector و `compute_per_slot` فعلی حفظ شوند، اما isolated full-pipeline dry-run پیش از Round 1 به‌تنهایی مانع ورود به مزایده نباشد. capacity checks واقعی، progression، deadline inclusive، numerical tolerance و تمام invariantهای runtime حفظ شوند. هیچ نرخ فعالی افزایش نیابد.

- حفظ قاعده فعلی: dry-run باید completion کامل را پیش از admission اثبات کند.
- اصلاح حداقلی پیشنهادی: حذف فقط gate dry-run؛ canonical vector ثابت.
- گزینه جایگزین: کاهش نرخ یا تغییر service-slot formula؛ فعلاً رد می‌شود چون بیش از یک عامل تغییر می‌کند.
- توصیه: اولویت سوم/چهارم؛ نه قبل از pilot Round 2.
- اثر مورد انتظار بر Funnel: کاهش `PRE_ADMISSION_INFEASIBLE` و انتقال آن به Completed یا انواع expiration؛ نباید مستقیماً repair burden را تغییر دهد، جز از راه بزرگ‌شدن candidate pool.
- فرضیه رد می‌شود اگر: Utility فقط از pre-admission به accepted-then-expired منتقل شود یا conservation/invariant شکست بخورد.
- ریسک فاصله از مقاله: متوسط رو به بالا؛ مقاله از minimum resources برای تضمین completion سخن می‌گوید، هرچند فرمول را چاپ نکرده است.

## ASSUMP-052 — bidding در همان epoch ورود `[پیشنهادشده و تأییدنشده]`

**متن پیشنهادی:** task ورودی epoch `e` در همان epoch اجازه bidding داشته باشد، ولی allocation پذیرفته‌شده همچنان از epoch `e+1` فعال شود. ترتیب سایر eventها ثابت بماند.

- حفظ قاعده فعلی: ورود `e`، bidding در `e+1`، processing در `e+2`.
- اصلاح حداقلی پیشنهادی: فقط یک epoch جلوآوردن bidding.
- گزینه جایگزین: activation همان epoch نیز جلو بیفتد؛ رد می‌شود چون دو تغییر هم‌زمان و ناسازگارتر است.
- توصیه: فعلاً **عدم تأیید**؛ مثال Section III صریحاً توالی epoch 2/3/4 را نشان می‌دهد.
- اثر مورد انتظار بر Funnel: فرصت بیشتر و احتمال کاهش pre-admission/retry expiration.
- فرضیه رد می‌شود اگر: فقط call-shape را زیاد کند بدون بهبود completion یا با متن مقاله ناسازگاری عملی نشان دهد.
- ریسک فاصله از مقاله: بالا.

## ASSUMP-053 — کاهش lag مراحل pipeline `[پیشنهادشده و تأییدنشده]`

**متن پیشنهادی جایگزین آزمایشی:** computation از نخستین active slot و download از دومین active slot مجاز شود، در حالی که تقدم نسبتی و ظرفیت‌ها حفظ شوند. `compute_per_slot` باید در یک variant جداگانه و از پیش‌ثبت‌شده بازتعریف شود؛ این گزینه با ASSUMP-051 یا ASSUMP-052 ترکیب نشود.

- حفظ قاعده فعلی: active slot 1 upload، slot 2 computation، slot 3 download.
- اصلاح حداقلی پیشنهادی: یک slot کاهش lag computation/download.
- گزینه جایگزین: pipeline کاملاً هم‌زمان؛ رد می‌شود چون از قیود مقاله فاصله بیشتری دارد.
- توصیه: فعلاً **عدم تأیید**؛ قیود (23)، (25) و (27) از lag فعلی پشتیبانی می‌کنند.
- اثر مورد انتظار بر Funnel: فقط در taskهای نزدیک deadline؛ اگر admission gate مجدداً محاسبه شود ممکن است `PRE_ADMISSION_INFEASIBLE` کاهش یابد.
- فرضیه رد می‌شود اگر: accepted-then-expired قبلاً صفر بماند و تنها canonical gate جابه‌جا شود بدون اثر completion قابل دفاع.
- ریسک فاصله از مقاله: بالا.

## گزینه pricing — ابتدا مشاهده، سپس اصلاح

برای pricing هنوز فرض عددی جدید پیشنهاد نمی‌شود. گام کم‌ریسک‌تر، instrumentation غیرمداخله‌ای و aggregate-only برای ثبت توزیع قیمت منتخب، تعداد price>utility، server-choice entropy و ظرفیت residual هنگام Round 2 است. این مشاهده‌گر باید تصمیم، RNG، task order و artifactهای رسمی را تغییر ندهد. تنها اگر نشان دهد workloadهای یکسان به‌صورت سیستماتیک به سرورهای نامناسب هدایت می‌شوند، یک counterfactual pricing تک‌عاملی باید جداگانه برای تأیید ارائه شود.

## طرح pilot کم‌هزینه

فایل `results/aggregated/stage15k/pilot_plan.csv` برنامه ماشینی را نگه می‌دارد. ترتیب توصیه‌شده:

1. ASSUMP-048 + ASSUMP-049: دو logical pair (DK-R و DK-P)، چهار اجرای فیزیکی.
2. فقط در صورت نیاز به مقایسه مستقل: ASSUMP-050 با دو logical pair و چهار اجرای فیزیکی.
3. اگر Round-2 repair اثر قابل‌تفسیر نداشت: pricing observer؛ سپس تصمیم جداگانه.
4. ASSUMP-051 فقط پس از روشن‌شدن Round 2.
5. ASSUMP-052 و ASSUMP-053 فعلاً اجرا نشوند.

برآوردها از اجرای قبلی همان اندازه workload روی GitHub گرفته شده و صرفاً فنی‌اند: هر variant دو-policy با parallelism مناسب حدود 25 تا 45 دقیقه wall-clock و 50 تا 90 runner-minute. این برآورد تضمین نیست.

## invariantهای مشترک همه pilotها

- partition کامل و بدون overlap Taskها؛
- conservation Utility با tolerance `1e-9`؛
- capacity هیچ منبع منفی یا بیش‌مصرف نشود؛
- task تکمیل‌شده دوباره اجرا نشود؛
- replay دقیق outcome، Utility، Funnel و task partition؛
- seed/config/workload hash ثابت؛
- RNG Option-A gate و ثبت call shape؛
- هر variant مستقل و بدون tuning باشد.

## تصمیم موردنیاز

تصمیم در 2026-09-02 دریافت شد: فقط **ASSUMP-048 و ASSUMP-049** برای
Stage 15-K.1 و به‌عنوان `[فرض آزمون کمکی]` تأیید شدند. ASSUMP-050 تا
ASSUMP-053 همچنان پیشنهادی/غیرفعال‌اند. این انتخاب کم‌هزینه‌ترین آزمایش
تک‌عاملی برای قوی‌ترین مظنون است.
