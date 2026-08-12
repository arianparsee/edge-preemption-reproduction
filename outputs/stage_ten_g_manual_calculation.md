# محاسبه دستی Pipeline Double Knapsack Retention

این سناریو `[آزمون کمکی]` است و نتیجه مقاله نیست. مسیر الگوریتم از Pipeline DK-R،
تنظیم GA از ASSUMP-013/015 و قیمت‌گذاری اجرایی از ASSUMP-011/012 استفاده می‌کند.

## ورودی

- ظرفیت server در هر چهار بعد: `10`
- current: demand=`2`، Utility=`4`؛ از قبل فعال و retain می‌شود.
- a: demand=`5`، Utility=`20`
- b: demand=`3`، Utility=`12`
- c: demand=`4`، Utility=`11`
- impossible: demand=`11`، Utility=`30`
- residual آغاز مزایده در هر بعد: `8`
- GA رسمی مثال: pyeasyga `0.3.1`، population=`200`، tournament=`20`،
  generations=`50`، seed=`20240810`.

## محاسبه یک‌باره f

برای کل workload با Utilityهای `(4,20,12,11,30)`:

```text
mean = 15.4
population std (ddof=0) = 8.890444308357148
f = mean - 1.1*std = 5.620511260807136
```

## Round 1

روی residual هشت‌واحدی، subset یکتای بهینه از نظر Utility برابر `{a,b}` است:

```text
demand(a+b) = 8
objective(a+b) = 20+12 = 32
price(a) = 0.9*20 = 18
price(b) = 0.9*12 = 10.8
```

برای c که feasible ولی انتخاب‌نشده است:

```text
violation(c) = 1 + f * 4*((4+8)/10)
             = 27.978454051874255
discount     = min(1/violation, 0.05)
             = 0.035741788954669236
price(c)     = 11*(1-discount)
             = 10.606840321498638
```

برای impossible، تقاضای 11 از ظرفیت کل 10 بیشتر است:

```text
price(impossible) = nextafter(30,+inf) = 30.000000000000004
```

پس impossible به علت `price > Utility` سروری انتخاب نمی‌کند. سه وظیفه دیگر به
تنها server بازمی‌گردند.

## Round 2 و Retention

current آزاد یا preempt نمی‌شود؛ residual همچنان 8 است. دومین knapsack نیز subset
`{a,b}` را با objective=`32` انتخاب می‌کند و c رد می‌شود.

```text
violation(a) = 1 + f*4*((5+8)/10) = 30.22665855619711
price2(a)    = 20*(1-1/violation) = 19.338332420607586

violation(b) = 1 + f*4*((3+8)/10) = 25.730249547551402
price2(b)    = 12*(1-1/violation) = 11.533622867597023
```

## انتظار نهایی

```text
accepted = [a,b]
rejected = [impossible,c]
retained = [current]
preempted = []
residual = (0,0,0,0)
GA objective = Exact auxiliary objective = 32
```
