# محاسبه دستی رگرسیون مشترک چهار policy

این سناریو `[آزمون کمکی]` برای کنترل‌جریان است و نتیجه مقاله یا بازتولید یکی از
نمودارهای آن نیست. معیار مقایسه نیز `active_utility_after_auction` است؛ یعنی مجموع
Utility تخصیص‌های فعال بلافاصله پس از یک مزایده، نه Utility وظایف تکمیل‌شده مقاله.

## ورودی مشترک

- یک server با ظرفیت `10` در هر چهار بعد؛
- `current-high`: تقاضا `4`، Utility=`10`، time remaining=`4`؛
- `current-low`: تقاضا `4`، Utility=`9`، time remaining=`6`؛
- `incoming`: تقاضا `4`، Utility=`20`، time remaining=`5`؛
- `extra`: تقاضا `2`، Utility=`3`، time remaining=`3`؛
- دو وظیفه `current-*` از ابتدا فعال‌اند و residual برابر `2` است؛
- seed روش‌های DK برابر `20240811` و GA رسمی برابر `200/20/50` است؛
- selector روش‌های KG در این رگرسیون Exact است و فقط `[ابزار کمکی]` محسوب می‌شود.

هر policy روی snapshot مستقل همان state اولیه اجرا می‌شود.

## KG-R

در Round 1 فقط `extra` در residual دوواحدی جا می‌شود. در Round 2 ابتدا `extra`
پذیرفته و residual صفر می‌شود؛ `incoming` رد می‌شود و هر دو current حفظ می‌شوند.

```text
active = {current-high, current-low, extra}
utility = 10 + 9 + 3 = 22
```

## KG-P

پس از پذیرش `extra`، نسبت ورودی `incoming` برابر `20/5=4` و نسبت قربانی کم‌ارزش
`current-low` برابر `9/6=1.5` است. شرط `4 >= 1.05*1.5` برقرار است و آزادسازی چهار
واحد قربانی برای تقاضای چهارواحدی ورودی کافی است. بنابراین `current-low` preempt
و `incoming` پذیرفته می‌شود.

```text
active = {current-high, extra, incoming}
utility = 10 + 3 + 20 = 33
```

## Pipeline DK-R

GA رسمی روی residual در Round 1 و Round 2، `extra` را انتخاب می‌کند؛ Retention
اجازه حذف currentها را نمی‌دهد. در نتیجه خروجی حالت با KG-R برابر است:

```text
active = {current-high, current-low, extra}
utility = 22
```

## Pipeline DK-P

کوله‌پشتی Round 2 روی ظرفیت کل و pool مشترک اجرا می‌شود. subset یکتای بهتر:

```text
{current-high, incoming, extra}: demand=10, utility=33
{current-high, current-low, extra}: demand=10, utility=22
```

پس `current-high` حفظ، `current-low` preempt و هر دو ورودی پذیرفته می‌شوند؛ Utility
فعال پس از مزایده `33` است. این برابری با KG-P فقط متعلق به همین مثال کوچک است.

## انتظار رگرسیون

| روش | پذیرفته | رد | حفظ‌شده | Preempt | Utility فعال | residual |
| --- | --- | --- | --- | --- | ---: | ---: |
| KG-R | extra | incoming | current-high, current-low | — | 22 | 0 |
| KG-P | extra, incoming | — | current-high | current-low | 33 | 0 |
| DK-R | extra | incoming | current-high, current-low | — | 22 | 0 |
| DK-P | incoming, extra | — | current-high | current-low | 33 | 0 |

