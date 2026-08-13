# Stage 15-D — طراحی counterfactual تک‌عاملی علت repair در DK

## وضعیت و مرز مرحله

- ASSUMP-044 تا ASSUMP-047 در 2026-08-13 با برچسب `[فرض آزمون کمکی]`
  تأیید شدند؛ هیچ counterfactual هنوز پیاده‌سازی یا اجرا نشده است.
- نسخه arXiv v2 سال 2024 همچنان منبع مبنای بازتولید است.
- سه variant زیر روش مقاله نیستند و فقط با برچسب `[آزمون کمکی]` مجاز خواهند بود.
- baseline رسمی همان Pipeline DK-R/DK-P مصوب با ASSUMP-042 است و تغییر نمی‌کند.
- نتیجه Stage 15-C نشان داد repair در Round 2 gate مستقیم پذیرش است، اما مشاهده صرف علت
  ریشه‌ای را میان fitness، initialization و offspring operators تفکیک نمی‌کند.

## ممیزی مستقیم pyeasyga 0.3.1

[استخراج از مرجع مستقیم کتابخانه] فایل نصب‌شده `pyeasyga/pyeasyga.py` بررسی شد:

1. `create_individual` برای هر ژن دقیقاً یک `random.randint(0, 1)` اجرا می‌کند؛
2. `rank_population` فقط بر `fitness` مرتب می‌کند؛
3. `tournament_selection` از `random.sample` استفاده می‌کند؛
4. one-point crossover و one-bit mutation هیچ feasibility check ندارند؛
5. elitism فرد رتبه اول را بدون تغییر به نسل بعد می‌برد؛
6. کتابخانه hook داخلی برای repair یا constraint dominance ندارد.

این ممیزی توضیح می‌دهد چرا fitness صفر مشترکِ chromosome ناممکن و مجموعه تهی می‌تواند فرد
ناممکن را در رتبه اول نگه دارد. این توضیح درباره کد کتابخانه است و به arXiv v2 نسبت داده
نمی‌شود.

## اصول مشترک همه آزمایش‌ها

موارد زیر در baseline و هر variant ثابت می‌مانند:

- workload، task order و server order؛
- workload seed و policy seed؛
- `population_size=200`، `tournament_size=20` و `generations=50`؛
- crossover probability برابر 0.8 و mutation probability برابر 0.2؛
- elitism، maximisation، tournament selection، one-point crossover و one-bit mutation؛
- مدل چهارمنبعی، قیمت‌گذاری، Round 1، Round 2، retention، preemption و lifecycle؛
- تعداد اجرای GA و تعداد نسل‌ها؛
- هیچ Exact Solver یا تنظیم برای نزدیک‌کردن نتیجه به شکل مقاله استفاده نمی‌شود.

هر variant در یک policy/RNG stream مستقل اجرا می‌شود. طبق اصلاح حفاظتی کاربر، variant
نباید random draw اضافه کند و تعداد فراخوانی primitiveها و وضعیت نهایی RNG باید با baseline
مقایسه شوند. ممیزی پیش از کدنویسی ثابت کرد مسیر کامل temporal داده‌وابسته است: تغییر subset
می‌تواند pool دورهای بعد، تعداد/طول فراخوانی‌های GA و در نتیجه وضعیت نهایی RNG را تغییر دهد.
گزینه A در 2026-08-13 تأیید شد: برابری دقیق در call shape یکسان و replay همسان الزامی است؛
اختلاف با baseline کامل فقط با تغییر ثبت‌شده در مسیر zero/single/multi، تعداد GA، طول pool
یا فراخوانی انتخاب یکنواخت مجاز است. جزئیات در `docs/stage15d_rng_gate.md` ثبت شده‌اند.

## فرض‌های تأییدشده آزمون کمکی

### ASSUMP-044 — دامنه و ترتیب اجرای counterfactualها

- وضعیت: **تأییدشده `[فرض آزمون کمکی]` در 2026-08-13**.
- ابتدا فقط workload نخست ASSUMP-033 با seed `541501192080118187` اجرا شود.
- هر variant جداگانه برای DK-R و DK-P اجرا شود.
- baseline از artifact معتبر Stage 15-C استفاده شود و دوباره محاسبه نشود.
- ترتیب اجرا: penalty fitness، initial-population repair، سپس offspring repair.
- در هر اجرا فقط یک عامل نسبت به baseline تغییر کند.
- پس از کنترل علمی تک-seed، پیش از تعمیم به 30 workload تأیید جداگانه گرفته شود.
- این نتایج هرگز بازتولید مقاله، Figure 6 یا تنظیم رسمی Pipeline DK معرفی نشوند.

### ASSUMP-045 — variant اول: penalty fitness ثابت

- وضعیت: **تأییدشده `[فرض آزمون کمکی]` در 2026-08-13**.
- initialization و همه operatorهای pyeasyga بدون تغییر بمانند.
- فقط fitness chromosome ناممکن از `0.0` به ثابت دقیق `-1.0` تغییر کند.
- fitness feasible همان مجموع Utility بماند؛ مجموعه تهی fitness صفر دارد.
- دلیل انتخاب `-1.0`: Utilityهای Synthetic Normal در workload رسمی مثبت‌اند، بنابراین این
  مقدار فقط feasible-zero را بر infeasible ترجیح می‌دهد و شدت penalty تنظیم‌شونده نمی‌سازد.
- اگر در workload هدف Utility نامتناهی یا Utility کمتر از صفر وجود داشت، variant fail-fast
  کند و مقدار دیگری پنهانی نسازد.
- ASSUMP-042 همچنان به‌عنوان guard باقی بماند، ولی repair count انتظار می‌رود صفر شود؛ وقوع
  repair یا infeasible best nonnegative یک یافته/خطای تشخیصی ثبت شود.
- این variant آزمون می‌کند آیا **zero-fitness feasibility tie** علت غالب است.

### ASSUMP-046 — variant دوم: پاک‌سازی فقط جمعیت اولیه

- وضعیت: **تأییدشده `[فرض آزمون کمکی]` در 2026-08-13**.
- fitness baseline، selection، crossover، mutation و نسل‌های بعد بدون تغییر بمانند.
- `create_individual` ابتدا دقیقاً همان `n` فراخوانی `random.randint(0,1)` را انجام دهد.
- اگر chromosome اولیه ناممکن بود، بیت‌های 1 از انتهای ترتیب canonical task_id به ابتدای آن
  به صفر تبدیل شوند تا feasible شود؛ random draw اضافه انجام نشود.
- chromosome تهی مجاز است؛ پس از رسیدن به feasibility حذف متوقف شود.
- تعداد chromosomeهای پاک‌سازی‌شده و تعداد بیت‌های حذف‌شده ثبت شود.
- offspringهای crossover/mutation repair نشوند.
- این variant فقط اثر **infeasibility در initialization** را جدا می‌کند.

### ASSUMP-047 — variant سوم: پاک‌سازی فقط offspring

- وضعیت: **تأییدشده `[فرض آزمون کمکی]` در 2026-08-13**.
- جمعیت اولیه، fitness baseline و selection بدون تغییر بمانند.
- پس از crossover و mutation و پیش از fitness evaluation، هر offspring ناممکن با همان قاعده
  deterministic حذف بیت‌های 1 از انتهای task_id-order تا feasibility پاک‌سازی شود.
- هیچ random draw اضافه انجام نشود؛ chromosome تهی مجاز باشد.
- elite کپی‌شده repair نشود، زیرا این variant فقط فرزندان تولیدشده را تغییر می‌دهد.
- تعداد offspringهای پاک‌سازی‌شده و بیت‌های حذف‌شده ثبت شود.
- این variant فقط اثر **infeasibility تولیدشده/حفظ‌شده در evolution** را جدا می‌کند.

## گزینه‌ای که فعلاً پیشنهاد نمی‌شود

یک repair greedy بر اساس utility/resource ratio پیشنهاد نمی‌شود، زیرا انتخاب denominator
چهاربعدی، ترتیب tie و تعریف ratio به فرض‌های عددی جدید نیاز دارد و هم‌زمان جهت بهینه‌سازی را
تغییر می‌دهد. همچنین feasibility-aware rejection sampling پیشنهاد نمی‌شود، چون تعداد RNG
drawها را workload-dependent و نامحدود می‌کند.

## خروجی و معیارها

برای هر `(variant, policy)` موارد زیر ثبت شوند:

- completed/rejected/preempted jobs و Utility؛
- raw auction rejections، retry و expiration؛
- GA call count و repair count به تفکیک Round 1/2؛
- raw-best feasible/infeasible calls؛
- candidate، raw-best و post-repair selected entries؛
- server assignments و Round-2 accepted/rejected؛
- variant-specific repaired chromosomes و removed bits؛
- runtime و RNG primitive draw counts؛
- اختلاف مطلق/نسبی با baseline معتبر همان seed.

artifact عمومی فقط aggregate خواهد بود و task ID، chromosome bits و raw trace ذخیره نمی‌کند.

## invariants و معیار توقف

هر اجرا در موارد زیر fail-fast و متوقف شود:

- تغییر config، workload hash یا task/server order؛
- خروجی chromosome غیردودویی یا subset ناممکن پس از guard نهایی؛
- ظرفیت منفی، allocation ناسازگار یا partition نادرست outcome؛
- فقدان metadata کامل variant یا seed؛
- استفاده از variant بیش از یک عامل در یک run؛
- secret/path/raw-data exposure در artifact؛
- هر اختلاف baseline در اجرای control بدون variant.

موفقیت یک counterfactual به معنی اصلاح مقاله نیست. فقط نشان می‌دهد تغییر تک‌عامل چه اثری بر
repair، admission و Utility همین implementation دارد.

## ماتریس اجرای پیشنهادی

| Run | Policy | تغییر نسبت به baseline | هدف |
| --- | --- | --- | --- |
| C0-R | DK-R | بدون اجرا؛ reuse Stage 15-C | کنترل معتبر |
| C0-P | DK-P | بدون اجرا؛ reuse Stage 15-C | کنترل معتبر |
| C1-R/P | DK-R, DK-P | فقط infeasible fitness = -1 | آزمون tie صفر |
| C2-R/P | DK-R, DK-P | فقط repair جمعیت اولیه | آزمون initialization |
| C3-R/P | DK-R, DK-P | فقط repair offspring | آزمون evolution |

در مجموع شش pair جدید روی یک workload اجرا می‌شوند. هیچ اجرای 30-workload در Stage 15-D
بدون تأیید جداگانه آغاز نخواهد شد.

## تصمیم موردنیاز

فرض‌ها و گزینه A گیت RNG تأیید شده‌اند. اجرای شش pair فقط پس از موفقیت آزمون‌های محلی و
ممیزی امنیتی workflow مجاز است؛ تعمیم به 30 workload همچنان نیازمند تصمیم جداگانه است.
