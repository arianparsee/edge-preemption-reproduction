# محاسبه دستی مثال KnapsackGreedy Preemption

این سناریو `[آزمون کمکی]` است و نتیجه مقاله محسوب نمی‌شود. Round 1 و Round 2 از
کنترل‌جریان arXiv v2 و ASSUMP-003 تا ASSUMP-008 و ASSUMP-010 استفاده می‌کنند.
`ExactUtilityKnapsackSelector` فقط `[ابزار کمکی]` مثال کوچک است، نه GA رسمی مقاله.

## وضعیت اولیه

- server capacity: `(10,10,10,10)`
- victim-low: demand=`4` در هر بعد، utility=`4`، time_remaining=`4`، ratio=`1`
- victim-high: demand=`4` در هر بعد، utility=`12`، time_remaining=`4`، ratio=`3`
- residual: `(2,2,2,2)`
- auto: demand=`2`، utility=`8`
- incoming-first: demand=`4`، utility=`30`، deadline=`5`
- incoming-second: demand=`4`، utility=`20`، deadline=`5`
- rejected: demand=`4`، utility=`10`، deadline=`5`

## Round 1

فقط auto روی residual دو واحدی fit است؛ بنابراین selector کمکی آن را انتخاب می‌کند:

```text
price(auto) = 0.9 * 8 = 7.2
price(incoming-first)  = 30 * (1 - 0.025)   = 29.25
price(incoming-second) = 20 * (1 - 0.025)   = 19.5
```

برای rejected، فقط victim-low نسبت پایین‌تری دارد، پس percentile=`1/2` و congestion=`1`:

```text
price(rejected) = 10 * (1 - 0.025*0.5) = 9.875
```

هر چهار وظیفه به همان server بازمی‌گردند.

## snapshot آغاز Round 2

```text
[(victim-low, ratio=1, time=4), (victim-high, ratio=3, time=4)]
```

auto و تمام پذیرش‌های جدید خارج snapshot هستند.

## Round 2

1. auto پذیرفته می‌شود؛ residual به صفر می‌رسد.
2. incoming-first با new ratio=`30/5=6` بررسی می‌شود. victim-low نخستین قربانی است:
   `6 >= 1.05*1` و چهار واحد آزادشده دقیقاً کافی است.
3. victim-low حذف/غیرفعال است. incoming-second با new ratio=`20/5=4`، victim-high را
   preempt می‌کند: `4 >= 1.05*3` و منابع دقیقاً کافی‌اند.
4. rejected با new ratio=`10/5=2` دیگر قربانی فعالی در snapshot ندارد و رد می‌شود.
5. auto هرگز وارد victim pool نمی‌شود و در کل دور محافظت می‌ماند.

## انتظار نهایی

```text
accepted = [auto, incoming-first, incoming-second]
preempted = [victim-low, victim-high]
rejected = [rejected]
residual = (0,0,0,0)
```
