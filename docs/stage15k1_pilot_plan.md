# Stage 15-K.1 — طرح اجرای Pilot

## وضعیت

- ASSUMP-048 و ASSUMP-049 فقط با برچسب `[فرض آزمون کمکی]` تأیید شده‌اند.
- ASSUMP-050 تا ASSUMP-053 غیرفعال‌اند.
- Pipeline رسمی DK، 120 baseline معتبر، repairهای قبلی و Figure 6 تغییر نمی‌کنند.
- workload رسمی فقط در GitHub Actions اجرا می‌شود.

## دامنه ثابت

- workload seed: نخستین seed مرتب ASSUMP-033، برابر `541501192080118187`؛
- policyها: Pipeline DK-R و Pipeline DK-P؛
- logical pair: دو؛
- replay: دو برای هر logical pair؛
- اجرای فیزیکی: چهار؛
- baseline: reuse از Stage 13-H/13-K؛
- repair قبلی: reuse از بسته checksum-validated Stage 15-D.1/15-E/15-H.

## تفاوت دقیق variant

در هر selector call، instrumentation موجود round را فقط از ترتیب ثابت
`server_count × 2` تعیین می‌کند. برای Round 1 مسیر baseline اجرا می‌شود. فقط در
Round 2، پس از ساخت هر chromosome اولیه با همان `randint`های baseline، بیت‌های
منتخب از انتهای canonical task-ID order بدون draw اضافی حذف می‌شوند تا subset
feasible شود. fitness، selection، crossover، mutation و ASSUMP-042 تغییر
نمی‌کنند.

## مرز مقایسه repair قبلی

artifact قبلی seed، workload hash، policy seed، replay و source artifact SHA را
ثبت کرده و برای مقایسه معتبر است. اما آن repair در Round 1 و Round 2 اعمال شده
و config SHA در artifact پاک‌سازی‌شده قبلی ذخیره نشده است. بنابراین سهم اثر
R2-only با scope difference صریح محاسبه می‌شود و برابری config hash قبلی ادعا
نمی‌شود.

## گیت‌ها

- exact same-variant replay؛
- primitive RNG counts، final state و call shape یکسان میان replayها؛
- Option-A baseline RNG boundary؛
- هیچ repair اولیه در Round 1؛
- `PRE_ADMISSION_INFEASIBLE` برابر baseline؛
- Utility conservation با tolerance `1e-9`؛
- capacity/state invariantهای موتور؛
- no task IDs، chromosomes، raw workload یا raw trace در artifact عمومی.

## workflow

`Stage 15-K.1 R2-only initialization repair pilot` با `workflow_dispatch`،
`max-parallel: 2`، `fail-fast: false`، timeout نود دقیقه و retention چهارده روز.
هر pair یک result، validation report و checksum manifest مستقل خواهد داشت.

## شرط توسعه

اجرای پنج-seed فقط در Stage 15-K.2 و پس از موفقیت علمی pilot و تأیید جداگانه
کاربر مجاز است. اجرای ۳۰ workload ممنوع باقی می‌ماند.
