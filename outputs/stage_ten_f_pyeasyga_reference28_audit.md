# مرحله دهم-F: ممیزی مرجع مستقیم pyeasyga [28]

## 1. کارهای انجام‌شده

- ASSUMP-011، ASSUMP-012 و ASSUMP-014 به‌عنوان approved و ASSUMP-013 به‌عنوان conditionally approved در ledger ثبت شدند.
- هویت زمانی مرجع [28] با releaseهای رسمی pyeasyga تطبیق داده شد.
- مستندات 0.3.1، امضای constructor، source module و مثال رسمی multidimensional knapsack بررسی شدند.
- population، selection، crossover، mutation، elitism، chromosome creation، fitness handling و seed mechanism ممیزی شدند.
- به علت یک ابهام مؤثر در population size، کدنویسی Pipeline DK-R آغاز نشد.

## 2. فایل‌های ایجاد یا تغییرکرده

- تغییر: `docs/assumptions.md`
- تغییر: `outputs/traceability_matrix_arxiv_v2.md`
- ایجاد: `outputs/stage_ten_f_pyeasyga_reference28_audit.md`
- بدون تغییر: `src/`، `tests/`، `scripts/` و dependencyهای محیط

## 3. ارتباط هر تغییر با مقاله و مرجع [28]

### هویت نسخه

- `[صریح در مقاله]` arXiv v2، مرجع [28]: A. Remi-Omosowon و Y. Gonzalez، «Pyeasyga documentation»، 2016.
- `[استخراج از مرجع مستقیم مقاله]` تاریخ release رسمی 0.3.1 برابر 5 اوت 2016 است و مستندات مستقیم عنوان `pyeasyga 0.3.1 documentation` دارند. بنابراین 0.3.1 نزدیک‌ترین نسخه قابل‌ردیابی به citation سال 2016 است.

منابع مستقیم: [PyPI release history](https://pypi.org/project/pyeasyga/)، [مستندات API نسخه 0.3.1](https://pyeasyga.readthedocs.io/en/latest/pyeasyga.html)، [source module نسخه مستند](https://pyeasyga.readthedocs.io/en/latest/_modules/pyeasyga/pyeasyga.html) و [مثال رسمی multidimensional knapsack](https://pythonhosted.org/pyeasyga/examples.html#multi-dimensional-knapsack-problem).

### تنظیمات استخراج‌شده

| تنظیم | مقدار/رفتار | منشأ | وضعیت |
| --- | --- | --- | --- |
| Library version | `pyeasyga==0.3.1` | `[استخراج از مرجع مستقیم مقاله]` مستندات و release سال 2016 | کامل |
| Generations | `50` | `[استخراج مستقیم]` [1]/[4] مقدار حدود 50؛ ASSUMP-013 آن را دقیقاً 50 تصویب کرده است | کامل با فرض تصویب‌شده |
| Generic population default | `50` | `[استخراج از مرجع مستقیم مقاله]` constructor 0.3.1 | کامل، ولی تعارض کاربردی دارد |
| Multidimensional example population | `200` | `[استخراج از مرجع مستقیم مقاله]` مثال رسمی MKP صریحاً default 50 را به 200 تغییر می‌دهد | کامل، ولی معلوم نیست مقاله از آن پیروی کرده باشد |
| Selection | tournament | `[استخراج از مرجع مستقیم مقاله]` source module | کامل |
| Tournament size | `population_size // 10`؛ اگر صفر شود، 2 | `[استخراج از مرجع مستقیم مقاله]` source module | کامل؛ برای population 50 برابر 5 و برای 200 برابر 20 |
| Crossover | one-point؛ probability `0.8` | `[استخراج از مرجع مستقیم مقاله]` constructor/source | کامل |
| Mutation | flip یک bit تصادفی؛ probability `0.2` | `[استخراج از مرجع مستقیم مقاله]` constructor/source | کامل |
| Mutation event semantics | یک draw برای pair؛ در موفقیت هر دو child یک bit mutate می‌شوند | `[استخراج از مرجع مستقیم مقاله]` source lines مربوط به `create_new_population` | کامل |
| Elitism | `True`؛ یک best chromosome در index صفر نسل جدید جای‌گذاری می‌شود | `[استخراج از مرجع مستقیم مقاله]` constructor/source | کامل |
| Maximise fitness | `True` | `[استخراج از مرجع مستقیم مقاله]` constructor | کامل |
| Initial chromosome | bit array تصادفی با طول تعداد items | `[استخراج از مرجع مستقیم مقاله]` source `create_individual` | کامل |
| MKP infeasibility | fitness برابر صفر | `[استخراج از مرجع مستقیم مقاله]` مثال رسمی multidimensional knapsack | کامل |
| Seed API | constructor پارامتر seed ندارد؛ از module-level `random` استفاده می‌کند | `[استخراج از مرجع مستقیم مقاله]` source module | کامل |

### نکته seed

منابع مقاله seed عددی گزارش نمی‌کنند. پیاده‌سازی می‌تواند بدون ادعای انتساب به مقاله، seed را ورودی اجباری قرار دهد، `random.seed(seed)` را بلافاصله پیش از اجرای هر GA اعمال و مقدار را در metadata ثبت کند. seed مثال دستی/آزمون با برچسب `[آزمون کمکی]` ثبت می‌شود. برای آزمایش‌های اصلی، نبود seed مقاله همچنان محدودیت بازتولید است.

## 4. فرمان‌ها و عملیات اجراشده

- جست‌وجوی وب فقط در مستندات، source repository و PyPI رسمی
- بازکردن صفحه Usage، API، source module و مثال MKP
- جست‌وجوی محلی config/seedهای فعلی با `rg`
- ثبت مستندات با `apply_patch`
- اجرای مجموعه رگرسیون پروژه پس از تغییر مستندات

هیچ package نصب یا دانلود نشد.

## 5. نتایج واقعی اجرا

- نسخه و تمام operatorهای لازم به‌جز انتخاب population اجرایی استخراج شدند.
- source module رفتار tournament، crossover، mutation و elitism را بدون نیاز به حدس مشخص کرد.
- تفاوت population واقعی و مؤثر است:
  - default عمومی: population 50، tournament size 5؛
  - مثال تخصصی MKP: population 200، tournament size 20.
- مقاله، [1] و [4] فقط generation count را بیان می‌کنند و population را گزارش نمی‌کنند.

## 6. آزمون‌های موفق و ناموفق

- آزمون Pipeline DK-R: اجرا نشد، چون پیاده‌سازی طبق شرط ASSUMP-013 متوقف است.
- آزمون رگرسیون پروژه: `146 passed in 0.27s`.
- آزمون ناموفق: صفر.
- ممیزی منبع: همه صفحات موردنیاز قابل دسترسی بودند.

## 7. فرض‌های استفاده‌شده

- ASSUMP-011، ASSUMP-012 و ASSUMP-014: approved و ثبت‌شده.
- ASSUMP-013: conditionally approved؛ هنوز فعال نشده است.
- فرض تازه اعمال‌شده: صفر.
- `population_size=200` هنوز استفاده یا ثبت نهایی نشده است.
- Exact Solver استفاده نشده است.

## 8. ابهام باقی‌مانده و گزینه‌ها

### ابهام مسدودکننده

`[نامشخص]` مقاله نمی‌گوید GA آن از default عمومی population 50 استفاده کرده یا از مثال رسمی multidimensional knapsack با population 200 پیروی کرده است. این مقدار بر کیفیت subset، تعداد random drawها، runtime و tournament size اثر مستقیم دارد.

### ASSUMP-015 پیشنهادی — Population رسمی Pipeline DK-R

`[فرض بازتولید؛ پیشنهادی و تأییدنشده]`:

1. مسیر رسمی Pipeline DK-R از `population_size=200` استفاده کند.
2. در نتیجه source behavior، `tournament_size=20` باشد.
3. `population_size=50` فقط در تحلیل حساسیت مستقل با برچسب `[آزمون کمکی]` اجرا شود.
4. مقدار population و tournament size در config و result metadata ثبت شوند.
5. seed ورودی اجباری باشد و default پنهانی نداشته باشد؛ seed مثال و آزمون صرفاً `[آزمون کمکی]` است.

دلیل پیشنهاد: مثال رسمی pyeasyga برای همان کلاس مسئله multidimensional knapsack، population را آگاهانه از default 50 به 200 افزایش می‌دهد. این نزدیک‌تر از default عمومی کتابخانه به کاربرد مقاله است، ولی چون مقاله آن را تصریح نکرده، همچنان فرض بازتولید است.

گزینه جایگزین: `population_size=50` و `tournament_size=5` براساس constructor default؛ این گزینه به default عمومی وفادارتر ولی به مثال تخصصی MKP دورتر است.

## 9. تصمیم موردنیاز از کاربر

پیش از کدنویسی باید ASSUMP-015 با population 200 تأیید شود یا کاربر گزینه جایگزین population 50 را انتخاب کند. سایر تنظیمات لازم از مرجع [28] کامل استخراج شده‌اند و فرض تازه دیگری لازم نیست.

## 10. مرحله بعدی پیشنهادی

پس از تصمیم population: pin کردن `pyeasyga==0.3.1`، ایجاد config کامل GA، پیاده‌سازی Pipeline DK-R، Exact Solver کمکی آزمون، آزمون‌های واحد/یکپارچه، مثال دستی و اجرای واقعی. Batch DK-R بدون تغییر blocked باقی می‌ماند.
