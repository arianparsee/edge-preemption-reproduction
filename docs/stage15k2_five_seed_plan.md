# Stage 15-K.2 — طرح اعتبارسنجی محدود پنج-seed

## وضعیت و مرز علمی

- فقط ASSUMP-049 و فقط به‌عنوان `[فرض آزمون کمکی]` اجرا می‌شود.
- چهار seed دوم تا پنجم × دو policy برابر هشت logical pair جدید است؛ هر pair دو
  replay دارد، پس ۱۶ اجرای فیزیکی جدید برنامه‌ریزی شده است.
- seed اول از Run `33663692202` و baselineهای پنج seed از شواهد معتبر قبلی
  reuse می‌شوند و هیچ‌کدام دوباره اجرا نمی‌شوند.
- ASSUMP-050 تا ASSUMP-053، اجرای ۳۰-workload، تغییر Pipeline رسمی و تغییر
  وضعیت Figure 6 مجاز نیستند.

## Instrumentation غیرمداخله‌ای DK-P

مشاهده‌گر نتیجه repacking اتمیک هر `(server, epoch)` را پس از بازگشت policy
می‌خواند و فقط جمع‌ها و شمارنده‌ها را نگه می‌دارد. هیچ Task ID، chromosome یا
trace وظیفه منتشر نمی‌شود. تعداد draw تصادفی افزوده‌شده صفر است.

چون DK-P برخلاف KG-P شرط ۵٪ را به‌عنوان قاعده تصمیم ندارد، نسبت‌های ۵٪ فقط
یک diagnostic counterfactual هستند. در هر batch، تمام زوج‌های وظیفه جدیدِ
پذیرفته‌شده و قربانی همان server/epoch به‌طور aggregate شمرده می‌شوند؛ این
زوج‌ها matching یک‌به‌یک یا منطق مقاله معرفی نمی‌شوند.

Artifact seed اول Stage 15-K.1 این instrumentation جدید را ندارد. مطابق اصل
عدم بازاجرا، مقایسه‌های outcome و Funnel با `n=5` و diagnostic جدید Preemption
با `n=4` گزارش می‌شوند؛ مقدار seed اول تخمین یا بازسازی نمی‌شود.

## گیت‌ها

- دو replay دقیقاً برابر؛
- RNG Option-A با مرز observability ثبت‌شده؛
- seed، workload hash، policy seed و config ثابت؛
- Round 1 و `PRE_ADMISSION_INFEASIBLE` ثابت؛
- capacity/state/partition و Utility conservation موفق؛
- pricing، server selection، lifecycle و preemption rule بدون تغییر؛
- completeness نهایی 10/10 logical pair؛
- checksum مستقل هر pair و checksum artifact نهایی.

## اجرای ابری

Workflow دستی با `max-parallel: 8`، `fail-fast: false`، timeout نود دقیقه و
retention چهارده روز اجرا می‌شود. دسترسی `actions: read` فقط برای دریافت دو
artifact checksum-pinned از Run `33663692202` است و secret جدیدی استفاده
نمی‌شود.
