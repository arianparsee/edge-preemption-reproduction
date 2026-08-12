# محاسبه دستی Pipeline Double Knapsack Preemption

این سناریو `[آزمون کمکی]` است و نتیجه مقاله نیست. منطق Round 2 از v2 Section V-B
و ASSUMP-016 تا ASSUMP-019 و GA از تنظیم ممیزی‌شده ASSUMP-018 استفاده می‌کند.

## ورودی

- ظرفیت server در هر چهار بعد: `10`
- current-high: demand=`4`، Utility=`10`، time_remaining=`4`
- current-low: demand=`4`، Utility=`9`، time_remaining=`6`
- incoming: demand=`8`، Utility=`20`، time_remaining=`5`
- extra: demand=`2`، Utility=`3`، time_remaining=`3`
- residual پیش از مزایده: `2` در هر بعد
- GA: pyeasyga=`0.3.1`، population=`200`، tournament=`20`، generations=`50`،
  seed=`20240810`.

## پارامتر workload-level

```text
utilities = (10,9,20,3)
mean = 10.5
population std = 6.103277807866851
f = mean - 1.1*std = 3.786394411346463
```

## Round 1 بدون تغییر

روی residual دوواحدی فقط extra جا می‌شود:

```text
R1 knapsack = {extra}
price(extra) = 0.9*3 = 2.7
```

incoming در ظرفیت کل feasible ولی خارج subset است. برای آن:

```text
violation = 1 + f * 4*((8+2)/10)
          = 16.145577645385852
discount = min(1/violation, 0.05) = 0.05
price(incoming) = 20*(1-0.05) = 19
```

هر دو قیمت از Utility متناظر بیشتر نیستند؛ بنابراین هر دو وظیفه به همان server
بازمی‌گردند.

## Round 2 روی ظرفیت کل

pool برابر چهار وظیفه است. subset یکتای بیشینه‌کننده Utility:

```text
{incoming, extra}: demand=10, objective=23
{current-high, current-low, extra}: demand=10, objective=22
```

پس `{incoming,extra}` انتخاب می‌شود. scoreها:

```text
incoming     = 1000 + 20/5 = 1004.0  (member)
extra        = 1000 + 3/3  = 1001.0  (member)
current-high = 1 + 10/4    = 3.5     (nonmember)
current-low  = 1 + 9/6     = 2.5     (nonmember)
```

در repack اتمیک از total capacity، incoming هشت واحد و extra دو واحد را می‌گیرند.
residual صفر می‌شود؛ current-high و current-low هر دو fit نمی‌شوند و preempt می‌شوند.

## انتظار نهایی

```text
accepted = [incoming, extra]
retained = []
preempted = [current-high, current-low]
rejected = []
residual = (0,0,0,0)
Round-2 price = absent under ASSUMP-019
GA objective = Exact auxiliary objective = 23
```
