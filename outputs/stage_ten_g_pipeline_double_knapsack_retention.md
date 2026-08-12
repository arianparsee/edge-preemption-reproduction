# مرحله دهم-G: Pipeline Double Knapsack Retention

## وضعیت علمی

- `[صریح در مقاله]` arXiv v2 دو round مزایده و دو knapsack را برای DK بیان می‌کند.
- `[استخراج از مرجع مستقیم مقاله]` مرجع [4] هدف Utility، Case-3 pricing و استفاده
  از GA را مشخص می‌کند؛ مرجع [1] نیز هدف Utility در Round 2 را پشتیبانی می‌کند.
- `[فرض بازتولید]` ASSUMP-011 تا ASSUMP-015 جزئیات مفقود threshold، چهار بعد،
  `f`، tie، seed و تنظیم رسمی 200/20/50 را تثبیت می‌کنند.
- `[ابزار کمکی]` Exact selector فقط oracle مثال کوچک است و وارد Pipeline رسمی نشده است.

## پیاده‌سازی

Pipeline رسمی شامل R1 knapsack روی residual هر server، قیمت‌گذاری سه‌شاخه، انتخاب
کمینه‌قیمت با tie یکنواخت seeded، R2 knapsack روی residual با حفظ current jobs،
پذیرش اتمیک و قیمت نهایی است. هیچ preemption در DK-R رخ نمی‌دهد. تمام تنظیمات
GA و آمار workload-level قیمت‌گذاری در metadata نتیجه ثبت می‌شوند.

## نتیجه اجرای واقعی مثال

```text
pyeasyga version = 0.3.1
population/tournament/generations = 200/20/50
seed = 20240810
mean/std/f = 15.4 / 8.890444308357148 / 5.620511260807136
R1 selected = [a,b]
R1 prices = a:18.0, b:10.8, c:10.606840321498638,
            impossible:30.000000000000004
R2 prices = a:19.338332420607586, b:11.533622867597023
accepted = [a,b]
rejected = [impossible,c]
residual after = (0,0,0,0)
fixed-seed repeat equal = true
Exact auxiliary objective = 32
official GA objective = 32
objective gap = 0
selected subset equal = true
```

این تطابق فقط برای مثال کوچک با optimum یکتا است و ادعای بهینگی عمومی GA یا
بازتولید نتایج عددی مقاله نیست.

## اعتبارسنجی نهایی

```text
pytest: 158 passed in 2.63s
Ruff format: 64 files already formatted
Ruff lint: All checks passed
mypy: no issues found in 64 source files
pip check: No broken requirements found
artifact SHA-256 (run 1): 28A5A2866531F97D08612AFF6258917E9D342A07A4E73492E0883054F538769F
artifact SHA-256 (run 2): 28A5A2866531F97D08612AFF6258917E9D342A07A4E73492E0883054F538769F
```

دو اجرای متوالی با seed ثابت، artifact بایت‌به‌بایت یکسان تولید کردند.

## وضعیت Batch DK-R

Batch DK-R همچنان `[نامشخص]/blocked` است، زیرا فرمول معتبر success-count pricing
در منابع موجود یافت نشده است. هیچ فایل الگوریتم Batch و هیچ فرمول عددی دلخواه
ساخته نشد.
