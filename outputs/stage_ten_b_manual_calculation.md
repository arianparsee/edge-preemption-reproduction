# محاسبه دستی مثال KnapsackGreedy Retention

این مثال `[آزمون کمکی]` است و اعداد آن نتیجه مقاله نیستند. کنترل‌جریان KG-R مطابق arXiv v2 و
ASSUMP-007 تا ASSUMP-009 است؛ انتخاب subset با `ExactUtilityKnapsackSelector` یک
`[ابزار کمکی]` برای مثال کوچک است و جایگزین رسمی pyeasyga مقاله معرفی نمی‌شود.

## وضعیت اولیه

- ظرفیت server: `(10,10,10,10)`
- current: demand=`(4,4,4,4)`، utility=`5`، time_remaining=`4`
- residual اولیه: `(6,6,6,6)`
- auto: demand=`(6,6,6,6)`، utility=`15`
- rejected-high: demand=`(4,4,4,4)`، utility=`10`، time_remaining=`4`
- rejected-low: demand=`(2,2,2,2)`، utility=`4`، time_remaining=`4`
- impossible: demand=`(11,11,11,11)`، utility=`20`

## Round 1

subsetهای مهم feasible روی residual:

- `{auto}`: utility=`15`
- `{rejected-high,rejected-low}`: utility=`14`

پس selector کمکی به‌طور یکتا `{auto}` را انتخاب می‌کند و قیمت آن `0.9*15=13.5` است.

برای rejected-high:

```text
current_ratio = 5/4 = 1.25
new_ratio = 10/4 = 2.5
percentile = 1/1 = 1
congestion = mean(4/6,4/6,4/6,4/6) = 2/3
price = 10 * (1 - 0.025*1 - 0.025*(1-2/3))
      = 9.666666666666666
```

برای rejected-low:

```text
new_ratio = 4/4 = 1
percentile = 0/1 = 0
congestion = 2/6 = 1/3
price = 4 * (1 - 0 - 0.025*(1-1/3))
      = 3.933333333333333
```

برای impossible، demand از total capacity بیشتر است:

```text
price = nextafter(20,+inf) = 20.000000000000004 > 20
```

بنابراین impossible به server بازنمی‌گردد و سه وظیفه دیگر برمی‌گردند.

## Round 2 Retention

1. auto با علامت autoFit پذیرفته می‌شود و residual از `(6,6,6,6)` به صفر می‌رسد.
2. rejected-high و rejected-low به‌ترتیب نسبت‌های `2.5` و `1` بررسی می‌شوند.
3. هیچ‌کدام روی residual صفر fit نیستند؛ هر دو در Round 2 جاری رد می‌شوند.
4. current retained می‌ماند و هیچ Preemption رخ نمی‌دهد.

## انتظار نهایی

```text
accepted = [auto]
rejected = [impossible, rejected-high, rejected-low]
active = [current, auto]
preempted = []
residual = (0,0,0,0)
```
