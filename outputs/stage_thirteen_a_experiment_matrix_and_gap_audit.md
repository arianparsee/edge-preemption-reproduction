# مرحله سیزدهم-A - ماتریس اجرایی آزمایش‌ها و ممیزی شکاف‌ها

تاریخ: 2026-08-12  
منبع مبنا: arXiv:2403.15665v2 (2024)  
دامنه: specification و readiness audit؛ بدون اجرای آزمایش مقاله

## 1. منابع و صفحات بررسی‌شده

- Section V-A2، PDF pp.7-8 و Figs.3-5 برای Round-1 diagnostics؛
- Section VI-A، PDF pp.8-10 برای OPT و Pipeline Normal؛
- Section VI-B، PDF pp.9-12 برای Batch، Bimodal و Southampton؛
- Tables I-II و captions کامل Figs.3-20؛
- source رسمی `main.tex` lines 387-593؛
- گزارش Stage 5، پیاده‌سازی policyها، simulator پایه، مولدهای Stage 11 و ممیزی
  Southampton در Stages 12-A تا 12-C.

صفحات 7 تا 12 با render موجود در resolution کامل بازبینی بصری شدند.

## 2. artifact ساخته‌شده

برای 12 خانواده آزمایش، 12 JSON مستقل در `configs/experiments` ساخته شد و registry
آن‌ها را به baseline و وضعیت اجرا متصل می‌کند. فیلدهای مفقود run control عمداً
`null` هستند. هیچ config دارای seed پنهان نیست.

## 3. نتیجه readiness

| وضعیت | تعداد | آزمایش‌ها |
| --- | ---: | --- |
| قابل اجرای رسمی | 0 | - |
| فقط auxiliary و مسیر رسمی blocked | 1 | TRACE-DIAG |
| blocked | 11 | OPT-25/18/10، R1-DIAG، Pipeline×2، Batch×3، TRACE-BASE/CAP |

Stage 12-C فقط Storage/Deadline raster surrogate را برای QA کیفی فراهم می‌کند؛
این مسیر به TRACE-BASE یا TRACE-CAP ورودی الگوریتمی نمی‌دهد.

## 4. پوشش شکل‌ها

- Figs.1-2 conceptual هستند و experiment config ندارند.
- Figs.3-20 هرکدام دقیقاً در یک specification ثبت شدند.
- Tables I-II به generatorهای Stage 11 نگاشت شده‌اند.
- هیچ مقدار bar از raster در configهای اجرای آینده وارد نشده است.

## 5. شکاف implementation در برابر شکاف علمی

| خانواده | شکاف علمی | شکاف implementation |
| --- | --- | --- |
| OPT | instance، Utility variant، solver settings/hardware | Gurobi/model absent |
| R1-DIAG | exact run/seed و KG GA settings | logger و temporal integration absent |
| Pipeline | horizon/repeats/seed، `s'_j`، retry، thresholds | policy-integrated simulator absent |
| Pipeline Time | slot/clock semantics | auction-time model absent |
| Batch | stage semantics و success-count price | Batch DK-R/simulator absent |
| Trace | raw rows/schema/mapping | official preprocessor absent |

## 6. یافته‌های مستقیم مهم

- `[صریح در مقاله]` rejected client فقط *ممکن است* در bidding phase بعدی resubmit
  کند؛ سیاست تصمیم‌گیری کاربر تعیین نشده است.
- `[صریح در مقاله]` arrival در epoch `e`، bidding در `e+1` و processing در `e+2`
  آغاز می‌شود، ولی event ordering کامل و termination policy گزارش نشده است.
- `[صریح در مقاله]` Preempted در Figs.6-15 Utility یا تعداد jobهایی است که حداقل
  یک بار preempt شده‌اند؛ category لزوماً partition نهایی نیست.
- `[نامشخص]` threshold تعریف high/low در Normal workload وجود ندارد.
- `[نامشخص]` output size و auction-time clock mapping وجود ندارد.

## 7. config guardها

هر spec موارد زیر را صریح ثبت می‌کند:

- baseline و محل منبع؛
- workload/methods/targets/metrics؛
- مقادیر paper-explicit؛
- run-controlهای حل‌نشده؛
- تصمیم‌های علمی حل‌نشده؛
- implementation gapها؛
- status و auxiliary capability.

این فایل‌ها specification هستند و تا رفع decision IDها به `ExperimentConfig`
اجرایی تبدیل نمی‌شوند.

## 8. مسیر پیشنهادی ادامه

نزدیک‌ترین گام بدون افزودن فرض علمی، Stage 13-B است:

1. orchestration harness عمومی؛
2. loader و validator برای specification/config اجرایی؛
3. fail-fast روی unresolved decisionها؛
4. raw output جدا و metadata کامل؛
5. smoke test روی regression تک‌مزایده‌ای چهار policy موجود؛
6. تکرارپذیری byte-level.

این smoke test نتیجه مقاله نیست. اجرای واقعی PIPE-NORMAL پس از آن همچنان نیازمند
تصمیم جداگانه درباره run control، output/progress، retry و metrics خواهد بود.

## 9. مواردی که عمداً انجام نشد

- Gurobi نصب نشد.
- Batch DK-R با فرمول ساختگی تکمیل نشد.
- Southampton surrogate به Task تبدیل نشد.
- horizon/repeats/seeds از bar heights استنباط نشد.
- high/low threshold از شکل‌ها fit نشد.
- هیچ آزمایش یا نمودار اصلی مقاله اجرا نشد.

## 10. نتیجه

پروتکل مقاله اکنون به 12 specification مستقل و قابل ممیزی تبدیل شده است. وضعیت
واقعی readiness شفاف است: 0 آزمایش رسمی runnable، 1 مسیر auxiliary-only و 11 مسیر
blocked. این نتیجه مانع اجرای ظاهری با defaultهای غیرمستند می‌شود و نقطه شروع
مطمئنی برای harness مرحله 13-B فراهم می‌کند.

## 11. اجرای واقعی و QA

اعتبارسنجی هدفمند پنج آزمون داشت:

1. registry دقیقاً 12 خانواده و 12 فایل مستقل دارد؛
2. run control فاقد default پنهان و همه seedها `null` هستند؛
3. Figs.3-20 دقیقاً یک‌بار پوشش داده می‌شوند؛
4. Southampton auxiliary با official execution اشتباه نمی‌شود؛
5. شکاف temporal Pipeline و Batch DK-R در configها ثبت شده است.

نتیجه هدفمند نهایی: `5 passed in 0.07s`.

QA کامل پس از همه تغییرها:

- Ruff format: 90 فایل، بدون تغییر لازم؛
- Ruff lint: موفق؛
- mypy strict: 80 source file، بدون issue؛
- pytest نهایی: `201 passed in 13.89s`؛
- آزمون ناموفق: صفر.

هیچ paper experiment در این مرحله اجرا نشد؛ بنابراین عدد شبیه‌سازی یا نمودار
جدیدی به‌عنوان نتیجه بازتولیدشده گزارش نشده است.
