# مرحله نهم: پیاده‌سازی شبیه‌ساز پایه

## 1. کارهای انجام‌شده

- دو فرض بازتولید تأییدشده در `docs/assumptions.md` ثبت شدند.
- schema رویداد immutable و JSON-serializable ایجاد شد.
- موتور رویدادگسسته scripted با clock چهار slot پیاده‌سازی شد.
- سناریوی 2 server و 4 task ایجاد شد.
- سناریو شامل پذیرش، رد، preemption، Deadline miss و completion دقیقاً روی deadline است.
- محاسبه دستی مستقل ثبت و با خروجی واقعی مقایسه شد.
- event log و summary با اجرای script تولید شدند.

## 2. مرز وفاداری

- `[صریح در مقاله]` server مستقل، task arrival، دو منبع تصمیم server، پذیرش/رد، preemption، deadline و Utility all-or-nothing مبنای stateها هستند.
- `[فرض بازتولید؛ تأییدشده]` Deadline inclusive است.
- `[فرض بازتولید؛ تأییدشده]` روابط (2)-(6) برای server منتخب سنجیده می‌شوند.
- `[پیشنهاد فنی]` policy موتور scripted است. این policy روش مقاله یا baseline نیست و فقط تزریق تصمیم برای آزمون engine است.
- `[آزمون کمکی]` مقادیر ظرفیت، demand و Utility این سناریو به مقاله نسبت داده نمی‌شوند.

## 3. اجزای کد

| جزء | مسئولیت |
| --- | --- |
| `SimulationEvent` | ثبت زمان، task/server، event، منابع قبل/بعد، Utility، earned Utility، price و reason |
| `SimulationCommand` | تصمیم صریح با `(time,order)` بدون tie-breaking پنهان |
| `run_scripted_simulation` | clock، expiration، اجرای transaction و ساخت summary |
| `stage_nine_smoke_scenario` | fixture مشترک script و integration test |
| `run_smoke_scenario.py` | اجرای واقعی و ذخیره JSONL/JSON |

## 4. گردش موتور

برای هر `time` در افق:

1. clock state تنظیم می‌شود.
2. allocationهای active که از Deadline فراگیر گذشته‌اند expire و آزاد می‌شوند.
3. commandهای همان زمان به ترتیب `order` اجرا می‌شوند.
4. پس از commandها invariantهای ظرفیت و state/resource بررسی می‌شوند.
5. در پایان، outcomeها و Utilityها فقط از state/eventهای واقعی ساخته می‌شوند.

## 5. رویدادهای واقعی

| Seq | Time | Event | Task | Server | Resources before → after | Utility/Price | Reason |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 0 | 0 | arrived | A | - | - | U=10 | arrival |
| 1 | 0 | arrived | B | - | - | U=8 | arrival |
| 2 | 0 | arrived | D | - | - | U=12 | arrival |
| 3 | 0 | accepted | A | S1 | `(10,10,10,10)→(4,6,8,8)` | P=9 | fit scripted |
| 4 | 0 | accepted | D | S2 | `(4,4,4,4)→(0,0,0,0)` | P=10.8 | fit scripted |
| 5 | 0 | rejected | B | - | - | P=None | no residual fit |
| 6 | 1 | arrived | C | - | - | U=30 | arrival |
| 7 | 1 | preempted | A | S1 | `(4,6,8,8)→(10,10,10,10)` | earned=0 | scripted preemption |
| 8 | 1 | accepted | C | S1 | `(10,10,10,10)→(3,5,8,8)` | P=None | scripted preemption |
| 9 | 2 | expired | D | S2 | `(0,0,0,0)→(4,4,4,4)` | earned=0 | inclusive deadline missed |
| 10 | 3 | completed | C | S1 | `(3,5,8,8)→(10,10,10,10)` | earned=30 | exact inclusive deadline |

## 6. خروجی واقعی

```text
events=11
completed_utility=30.0
states={"task-a":"preempted","task-b":"rejected","task-c":"completed","task-d":"expired"}
```

محاسبه دستی و خروجی برنامه در تمام outcomeها، Utilityها و منابع نهایی اختلاف صفر دارند.

## 7. آزمون‌ها

- آزمون schema و serialization رویداد؛
- آزمون خروجی taskها و Utility؛
- آزمون ledger منابع تمام تصمیم‌ها؛
- آزمون آزادشدن کامل منابع نهایی؛
- آزمون completion دقیقاً روی Deadline فراگیر؛
- آزمون رد semantics ناسازگار با ASSUMP-001؛
- آزمون‌های قبلی مدل و روابط.

نتیجه اجرای کامل واقعی:

```text
112 passed in 0.25s
43 files already formatted
All checks passed!                 # Ruff
Success: no issues found in 43 source files  # mypy
No broken requirements found.     # pip check
```

آزمون تکرارپذیری نیز با دو اجرای متوالی موفق بود:

```text
events.jsonl SHA-256 = E5DD4F4B6C412987E1A18763EEF9825E42EAE3EBDBFD2CADA84E082B92ADD012
summary.json SHA-256 = 2F17C9AAC138392367CBE8F8B66E3BEA00FFECEFA811612574183EEB21408FD8
```

هش هر فایل پیش و پس از اجرای دوم یکسان بود.

## 8. محدودیت‌ها

- engine هنوز upload/compute/download progress خودکار تولید نمی‌کند؛ completion تصمیم scripted است.
- Round 1/Round 2 policy و bidding واقعی در Stage 10 پیاده می‌شوند.
- قیمت task C عمداً `None` است، چون preemption price به تفسیر congestion حل‌نشده وابسته است.
- task B پس از rejection retry نمی‌کند، چون retry policy مقاله نامشخص است.
- سناریو نتیجه مقاله محسوب نمی‌شود؛ فقط verification موتور است.
