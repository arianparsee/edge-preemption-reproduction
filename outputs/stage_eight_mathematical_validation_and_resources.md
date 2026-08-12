# مرحله هشتم: پیاده‌سازی مدل ریاضی و اعتبارسنجی منابع

## 1. دامنه و نتیجه

- منبع مبنا: *Improved Methods of Task Assignment and Resource Allocation with Preemption in Edge Computing Systems*، نسخه `arXiv:2403.15665v2`.
- مدل داده مرحله هفتم در 9 اوت 2026 توسط کاربر تأیید شد.
- Gurobi طبق تصمیم کاربر نصب یا فراخوانی نشد.
- objective و تمام روابط شماره‌دار (1) تا (31) به توابع مستقل و آزمون‌پذیر نگاشت شدند.
- تخصیص، آزادسازی و preemption منابع به‌صورت تراکنشی پیاده‌سازی شد.
- Deadline، زمان سپری‌شده، Utility، قیمت‌های صریح، Retention و Preemption feasibility پیاده‌سازی شدند.
- تفسیرهای ناسازگار مقاله به enumهای اجباری تبدیل شدند و هیچ default علمی ندارند.
- نتیجه نهایی اجرای واقعی: **105 passed, 0 failed**؛ Ruff، mypy strict و `pip check` نیز موفق‌اند.

## 2. فایل‌های اصلی ایجادشده

| فایل | مسئولیت | ارتباط مقاله |
| --- | --- | --- |
| `models/schedule.py` | سه دنباله slot-level و cumulative progress | `σ_j(n)`, `κ_j(n)`, `σ'_j(n)` |
| `optimization/constraints.py` | validatorهای روابط (2)-(31) | Section IV، صفحات 4-5 |
| `evaluation/utility.py` | objective و Utility all-or-nothing | رابطه (1) و متن Section IV |
| `simulation/time.py` | Deadline و elapsed slots با boundary صریح | `a_j+d_j` و ابهام event boundary |
| `simulation/invariants.py` | ظرفیت، assignment و state/resource consistency | روابط (15)-(21) و lifecycle |
| `simulation/accounting.py` | تخصیص، آزادسازی و جایگزینی تراکنشی | allocation/preemption Sections III-V |
| `algorithms/pricing.py` | fit/preemption price و gate impossible price | Section V-A1 و Algorithm 1 |
| `algorithms/feasibility.py` | Retention fit، victim resources و شرط 5٪ | Algorithm 2 و نثر صفحه 7 |

## 3. نگاشت کامل روابط به کد و آزمون

| رابطه | تابع | آزمون مثبت | آزمون منفی/مرزی | وضعیت |
| ---: | --- | --- | --- | --- |
| (1) | `all_or_nothing_utility`, `total_served_utility` | assigned+completed+on-time | preempted، unassigned، deadline miss | کامل |
| (2) | `check_equation_2_upload_upper_bound` | exact upload | over-upload و quantifier چند server | دو semantics اجباری |
| (3) | `check_equation_3_completed_upload` | completed exact؛ preempted partial | completed partial | دو semantics اجباری |
| (4) | `check_equation_4_computation_upper_bound` | exact compute | over-compute | دو semantics اجباری |
| (5) | `check_equation_5_completed_computation` | completed exact؛ preempted partial | completed partial | دو semantics اجباری |
| (6) | `check_equation_6_download_upper_bound` | exact download | over-download | دو semantics اجباری |
| (7) | `check_equation_7_completed_download` | completed exact؛ preempted partial | completed partial | کامل |
| (8) | `check_equation_8_preemption_before_full_download` | preempted fraction<1 | preempted fraction=1 | strict `<` حفظ شد |
| (9) | `check_equation_9_upload_before_computation` | 60٪/60٪ | compute=60.1٪ | تمام prefixها |
| (10) | `check_equation_10_computation_before_download` | 60٪/30٪ | download جلوتر | تمام prefixها |
| (11) | `check_equation_11_stage_order` | equality مجاز | ترتیب معکوس | کامل |
| (12) | `check_equations_12_to_14_minimum_stage_spans` | upload=1 | upload=0 | کامل |
| (13) | همان | processing=1 | processing=0 | کامل |
| (14) | همان | download=1 | download=0 | کامل |
| (15) | `check_equation_15_storage_capacity` | exact capacity | over-capacity | θ ورودی صریح |
| (16) | `check_equation_16_computation_capacity` | exact capacity | over-capacity | کامل |
| (17) | `check_equation_17_upload_capacity` | exact capacity | over-capacity | کامل |
| (18) | `check_equation_18_download_capacity` | exact capacity | over-capacity | کامل |
| (19) | `check_equation_19_single_assignment` | `(1,0,0)` | `(1,1,0)` | کامل |
| (20) | `check_equation_20_assignment_domain` | 0/1 | 2 | کامل |
| (21) | `check_equation_21_completion_domain` | 0/1 | 0.5 | کامل |
| (22) | `literal_activity_slots` + window check | upload داخل window | upload خارج window | فرمول چاپ‌شده |
| (23) | `check_equations_22_to_27_activity_window` | upload نامنفی | مقدار منفی داخل | فرمول چاپ‌شده |
| (24) | همان | compute خارج window صفر | مقدار غیرصفر خارج | فرمول چاپ‌شده |
| (25) | همان | compute داخل نامنفی | مقدار منفی داخل | فرمول چاپ‌شده |
| (26) | همان | download خارج window صفر | مقدار غیرصفر خارج | فرمول چاپ‌شده |
| (27) | همان | download داخل نامنفی | مقدار منفی داخل | فرمول چاپ‌شده |
| (28) | `check_equation_28_stop_domain` | `1≤d_t≤d_d` | `d_t>d_d` | کامل |
| (29) | `check_equation_29_completion_stop_relation` | completed با `d_t=d_d` | completed با نابرابری | کامل |
| (30) | `check_equation_30_preemption_before_completion` | preempted قبل از پایان | preempted در پایان | strict `<` حفظ شد |
| (31) | `derive_equation_31_storage_indicator` | compute مثبت پیوسته/ناپیوسته | مجموعه تهی → unresolved | literal min/max |

## 4. Deadline، زمان اجرا و Utility

### Deadline

`meets_deadline()` به پارامتر اجباری `DeadlineBoundary` نیاز دارد:

- `INCLUSIVE`: completion در `a_j+d_j` موفق است.
- `EXCLUSIVE`: completion باید پیش از `a_j+d_j` باشد.

هیچ default وجود ندارد. آزمون endpoint نشان می‌دهد همان task در حالت inclusive پذیرفته و در حالت exclusive رد می‌شود.

### زمان

`elapsed_slots()` نیز boundary را اجباری می‌گیرد. برای بازه 2 تا 5:

- inclusive برابر 4 slot؛
- exclusive برابر 3 slot.

این تابع انتخاب مقاله را وانمود نمی‌کند؛ فقط دو convention را محاسبه می‌کند.

### Utility

`[صریح در مقاله]` Utility all-or-nothing است:

```text
earned = U_j × x_ij × τ_j
```

با `deadline_met=False`، Utility صفر می‌شود. task preempted (`τ=0`) و task unassigned (`x=0`) نیز Utility صفر دارند.

## 5. قیمت‌گذاری

### fit price

`[صریح در مقاله]`:

```text
fit_price = 0.9 × utility
```

مثال آزمون‌شده: Utility 100 → price 90.

### preemption price

دو تفسیر بدون default پیاده شد:

- `CongestionPriceSemantics.PROSE`: استفاده از خود congestion؛
- `CongestionPriceSemantics.ALGORITHM_ONE`: استفاده از `1-congestion` مطابق خط شبه‌کد.

با `U=100`, percentile=0.8, congestion=0.2 و وزن‌های 0.025:

- prose → 97.5؛
- Algorithm 1 → 96.0.

جمع وزن‌ها بیش از 0.1 رد می‌شود، مطابق شرط صریح مقاله.

### impossible price

`impossible_price()` همیشه `UnresolvedDecisionError` ایجاد می‌کند. مقاله فقط می‌گوید price باید از Utility بیشتر باشد و مقدار یا sentinel را تعیین نمی‌کند.

## 6. تخصیص، آزادسازی و invariantها

### عملیات تراکنشی

- `allocate_now`: روی snapshot جدید تخصیص می‌دهد؛ state ورودی را تغییر نمی‌دهد.
- `release_now`: allocation را endشده ثبت و منابع را آزاد می‌کند.
- `preempt_and_allocate_now`: ابتدا همه victimهای صریح را روی snapshot آزاد و سپس incoming task را می‌پذیرد؛ failure state اصلی را تغییر نمی‌دهد.
- این executor victim انتخاب نمی‌کند و قاعده 5٪ را پنهانی اعمال نمی‌کند.

### invariantهای اجراشده

1. مجموع منابع active از ظرفیت server بیشتر نشود.
2. تفریق ظرفیت هیچ مؤلفه منفی تولید نکند.
3. هر task حداکثر یک allocation record جاری داشته باشد.
4. task terminal دارای allocation فعال نباشد.
5. task completed/preempted/expired دوباره مستقیماً تخصیص نیابد.
6. آزادسازی، allocation را inactive و state را terminal می‌کند.
7. active allocation فقط با stateهای accepted/processing سازگار است.

بازگشت task preempted به مزایده `[نامشخص]` است؛ تلاش برای re-allocation رکورد پایان‌یافته فعلاً خطای unresolved می‌دهد.

## 7. Retention و Preemption feasibility

- `can_retain_and_admit`: فقط residual resources را بررسی می‌کند و victimی آزاد نمی‌کند.
- `resources_available_after_preemptions`: residual را با منابع victimهای active صریح جمع می‌کند.
- `can_admit_after_preemptions`: fit مؤلفه‌ای incoming task را پس از victimها می‌سنجد.
- `can_preempt_single_victim`: fit و شرط Utility/time را با semantics اجباری ترکیب می‌کند.

شرط 5٪:

- `PROSE`: `incoming_ratio ≥ 1.05 × current_ratio`؛
- `ALGORITHM_TWO`: `1.05 × incoming_ratio ≥ current_ratio`.

یک مثال کنترل‌شده در آزمون طوری انتخاب شد که prose رد و Algorithm 2 قبول کند؛ بنابراین اختلاف واقعاً قابل مشاهده است و در کد پنهان نشده است.

## 8. ناسازگاری‌ها و تصمیم‌های موردنیاز پیش از استفاده

| اطلاعات مفقود/ناسازگار | محل بررسی | اثر | گزینه‌ها | نزدیک‌ترین گزینه به مقاله | وضعیت فعلی |
| --- | --- | --- | --- | --- | --- |
| quantifier روابط (2)-(6) | Section IV، صفحات 4-5؛ روابط چاپ‌شده و توضیح بعد آن‌ها | literal با چند server تقریباً هر flow را صفر می‌کند | `LITERAL_ALL_SERVERS`؛ `SELECTED_SERVER_ONLY` | selected-server-only کمترین اصلاح و سازگار با (19) | هر دو پیاده؛ بدون default؛ تأیید لازم |
| boundary Deadline | صفحات 3-5؛ `d_d≤d_j` و توصیف «by deadline» | outcome task و Utility | inclusive؛ exclusive | inclusive به‌دلیل `≤` در (11) نزدیک‌تر است | هر دو پیاده؛ تأیید لازم |
| congestion term | Section V-A1 صفحه 6 و Algorithm 1 | Round-1 price و انتخاب server | prose؛ `1-congestion` شبه‌کد | برای بازسازی خط‌به‌خط، Algorithm 1؛ برای نیت مفهومی نامشخص | هر دو پیاده؛ بدون default |
| شرط 5٪ | نثر و Algorithm 2 صفحه 7 | victim/admission متفاوت | prose؛ pseudocode | prose، چون «at least 5% greater» صریح است | هر دو پیاده؛ بدون default |
| پنجره‌های (22)-(27) | صفحه 5؛ مقایسه با (12)-(14) | بعضی spanهای یک-slot window تهی می‌شوند | literal؛ اصلاح endpoint | literal برای وفاداری فرمول؛ اصلاح برای سازگاری معنایی | فقط literal پیاده و برچسب‌خورده؛ استفاده نیازمند تأیید |
| θ برای compute تهی | رابطه (31)، صفحه 5 | storage task unprocessed قابل محاسبه نیست | all-zero؛ active upload-to-download؛ reject | all-zero کمترین extension ریاضی است | فعلاً unresolved error |
| بازه storage | رابطه (31) در برابر متن آزادسازی صفحه 5 | capacity storage قبل/بعد compute متفاوت | compute span؛ upload→download span | `[نامشخص]` | literal compute span موجود؛ انتخاب نشده |
| impossible price | Section V-A1 صفحه 6 | client server selection | `U+ε`؛ `nextafter(U,+∞)`؛ ثابت بزرگ | `nextafter` کمترین افزایش عددی، اما مقاله نگفته | unresolved error |
| واحد storage | Section IV صفحه 4 در برابر Table I صفحه 8 | fit/capacity عددی | MB؛ GB با ×1000؛ GiB با ×1024 | Table I هر دو را MB می‌دهد، پس MB نزدیک‌تر است | هیچ conversion اعمال نشده |
| retry پس از preemption | Sections III-V | امکان re-allocation و double-count | terminal؛ بازگشت auction؛ policy محدود | `[نامشخص]` | re-allocation مسدود |

هیچ‌یک از «نزدیک‌ترین گزینه‌ها» در اجرای علمی انتخاب نشده است؛ آن‌ها فقط پیشنهاد برای تأیید آینده‌اند.

## 9. آزمون‌ها و خروجی واقعی

### آزمون‌های این مرحله

- time/utility: 9 آزمون؛
- pricing: 5 آزمون؛
- schedule: 3 آزمون؛
- constraints: 22 آزمون؛
- accounting/invariants: 8 آزمون؛
- feasibility: 5 آزمون.

به‌همراه 53 آزمون مرحله هفتم، اجرای نهایی:

```text
105 passed in 0.24s
37 files already formatted
All checks passed!
Success: no issues found in 37 source files
No broken requirements found.
```

شکست میانی: mypy پنج خطای typing در callableهای parameterized تست constraints یافت؛ با Protocolهای دقیق اصلاح و کل کنترل‌ها دوباره اجرا شد. Ruff نیز ترتیب import دو فایل را اصلاح کرد. هیچ شکست علمی پنهان نشد.

## 10. فرض‌ها و محدودیت‌ها

### `[فرض بازتولید]`

هیچ فرض علمی تصویب یا اعمال نشد.

### `[پیشنهاد فنی]`

- tolerance پیش‌فرض صفر؛
- APIهای semantics بدون default؛
- indexing `TaskSchedule` در Python صفرمبنا، ولی API constraint window یک‌مبنای مقاله؛
- transactionها state تازه برمی‌گردانند؛
- re-allocation حل‌نشده fail-fast می‌شود؛
- wrapper مشترک برای قیود هم‌شکل (16)-(18).

### محدودیت فعلی

- validatorها feasibility یک solution داده‌شده را بررسی می‌کنند؛ optimizer یا schedule generator نیستند.
- Gurobi و مدل solver ساخته نشده است.
- Simulation engine هنوز event loop ندارد.
- تفسیرهای ambiguous تا تأیید کاربر قابل استفاده در config resolved نیستند.

## 11. نتیجه مرحله هشتم

مدل ریاضی و حسابداری منابع در سطح pure validation و transaction آماده است و همه اجزای قابل‌اجرای این مرحله آزمون شده‌اند. ورود به مرحله نهم برای ساخت سناریوی دستی کوچک ممکن است، اما اجرای سناریو نیازمند حداقل انتخاب boundary Deadline و semantics روابط assignment-flow است. سایر تصمیم‌ها را می‌توان تا مرحله الگوریتم به تعویق انداخت.

