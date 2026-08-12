# مرحله دهم-I: Pipeline Double Knapsack Preemption

## وضعیت علمی

- `[صریح در مقاله]` v2 Section V-B: total-capacity knapsack روی current+returning،
  scoreهای 1000/1، ترتیب نزولی و امکان preempt هر تعداد current job.
- `[فرض بازتولید]` ASSUMP-016 تا ASSUMP-019: repack اتمیک، score boundary،
  GA رسمی و حذف شفاف قیمت عددی مفقود Round 2.
- `[ابزار کمکی]` Exact selector فقط oracle مسئله کوچک است و مسیر رسمی GA نیست.

## کنترل‌جریان پیاده‌سازی‌شده

1. Round 1 دقیقاً از Pipeline DK-R موجود استفاده می‌کند.
2. current allocationهای هر server در آغاز Round 2 snapshot می‌شوند.
3. GA روی total capacity و اجتماع current+returning اجرا می‌شود.
4. time_remaining منجمد و score لفظی محاسبه می‌شود.
5. tie دقیق یا تناقض اولویت member/nonmember fail-fast می‌شود.
6. یک plan از ظرفیت کل خالی ساخته می‌شود.
7. current fitشده retain، current غیرfit preempt، returning fit admit و returning
   غیرfit reject می‌شود.
8. plan روی snapshot جدید commit می‌شود؛ state ورودی تغییر نمی‌کند.
9. Round 2 هیچ قیمت ساختگی ندارد.

## نتیجه اجرای واقعی مثال

```text
pyeasyga = 0.3.1
population/tournament/generations = 200/20/50
seed = 20240810
mean/std/f = 10.5 / 6.103277807866851 / 3.786394411346463
R1 selected = [extra]
R1 prices = incoming:19.0, extra:2.7
R2 GA membership = [extra,incoming]
R2 score order = [incoming,extra,current-high,current-low]
scores = [1004.0,1001.0,3.5,2.5]
accepted = [incoming,extra]
preempted = [current-high,current-low]
retained = []
rejected = []
residual after = (0,0,0,0)
Round-2 bid count = 0
Round-2 price status = absent_no_source_formula_ASSUMP-019
fixed-seed repeat equal = true
Exact auxiliary objective = 23
official GA objective = 23
objective gap = 0
selected membership equal = true
```

تطابق Exact فقط برای این مثال کوچک با optimum یکتا است و ادعای بهینگی عمومی GA
یا بازتولید نتایج عددی مقاله نیست.

## اعتبارسنجی نهایی

```text
pytest: 168 passed in 3.85s
Ruff format: 68 files already formatted
Ruff lint: All checks passed
mypy: no issues found in 68 source files
pip check: No broken requirements found
artifact SHA-256 (run 1): C7E1EC7E08F0EDBF2C33303C36E4E034845F743CB68BD71680A4252211B9758F
artifact SHA-256 (run 2): C7E1EC7E08F0EDBF2C33303C36E4E034845F743CB68BD71680A4252211B9758F
```

دو اجرای متوالی با seed ثابت، artifact بایت‌به‌بایت یکسان تولید کردند.
