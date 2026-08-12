# مرحله سیزدهم-D: موتور چند-epoch و smoke کوچک PIPE-NORMAL

تاریخ اجرا: 2026-08-12

وضعیت: **تکمیل زیربخش؛ smoke کوچک موفق؛ اجرای 100 slot × 30 run انجام نشد**

منبع مبنا arXiv v2 سال 2024 است. تمام ASSUMP-033 تا ASSUMP-041 و اصلاح‌های
ASSUMP-036-A/038-A `[فرض بازتولید]` هستند و تنظیم صریح مقاله معرفی نمی‌شوند.

## 1. دامنه پیاده‌سازی

- canonicalization تقاضای computation با slotهای computation-eligible؛
- dry-run قطعی feasibility برای upload/computation/download؛
- پیشرفت cumulative pipeline با ترتیب upload → computation → download؛
- lag آغاز سه مرحله در active slots 1/2/3؛
- retry یک‌بار در هر bidding epoch، expiration و preemption terminal؛
- آزادسازی اتمیک منابع در completion/preemption/expiration؛
- aggregator نهایی Completed/Rejected و ever-preempted overlay؛
- اتصال persistent RNG stream برای KG-R، KG-P، DK-R و DK-P؛
- KG GA جداگانه با pyeasyga 0.3.1 و تنظیم 200/20/30؛
- smoke دووظیفه‌ای و مثال دستی.

## 2. یافته فنی pyeasyga

در probe واقعی، pyeasyga 0.3.1 برای chromosome تک‌ژنی در one-point crossover با
`ValueError: empty range in randrange(1, 1)` شکست خورد. `[پیشنهاد فنی]` adapter
برای pool تک‌عضوی، همان objective دقیق را بدون RNG حل می‌کند: وظیفه Utility مثبت
اگر fit باشد انتخاب می‌شود؛ Utility صفر به دلیل tie مجموعه خالی/تک‌عضوی fail-fast
می‌ماند. مسیر GA برای poolهای چندعضوی تغییر نکرده است.

## 3. نتیجه واقعی smoke

| policy | Completed | Rejected | Ever-preempted | Completed Utility | Rejected Utility | Preempted Utility | raw auction rejections |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| KG-R | task-current | task-incoming | — | 10 | 12 | 0 | 2 |
| KG-P | task-incoming | task-current | task-current | 12 | 10 | 10 | 0 |
| DK-R | task-current | task-incoming | — | 10 | 12 | 0 | 2 |
| DK-P | task-incoming | task-current | task-current | 12 | 10 | 10 | 0 |

فایل خام: `results/raw/stage13d/stage13d_hand_smoke/result.json`

SHA-256 نتیجه:
`07B9177D14146B9A472B396646A2373FB9BE6C439E7B7B90D1E502ED9F9F9896`

## 4. آزمون و QA واقعی

فرمان‌ها:

```powershell
.\.venv\Scripts\python.exe scripts\run_stage13d_temporal_smoke.py --config configs\stage13d_temporal_smoke.json --output results\raw\stage13d\stage13d_hand_smoke\result.json
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pytest -q
```

نتیجه QA نهایی: Ruff موفق، mypy بدون خطا روی 92 فایل و 224 آزمون موفق در
64.18 ثانیه. آزمون صریح ASSUMP-038-A نیز تأیید می‌کند expiration allocation را
غیرفعال و تمام منابع را اتمیک آزاد می‌کند.

## 5. محدودیت‌ها

- `arrival_slots=100` و 30 seed در این smoke استفاده نشدند؛ config smoke عمداً
  `arrival_slots=2` دارد.
- Figure 6 تولید یا با مقاله مقایسه نشد.
- Figs.7-8 و high-value Figure 10 به علت
  `NORMAL_HIGH_LOW_THRESHOLDS` همچنان blocked هستند.
- auction-time experiments خارج از scope و blocked باقی مانده‌اند.
- Southampton raw trace همچنان در دسترس نیست.
