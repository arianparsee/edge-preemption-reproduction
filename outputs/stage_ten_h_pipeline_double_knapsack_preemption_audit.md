# مرحله دهم-H: ممیزی Pipeline Double Knapsack Preemption

## 1. دامنه و سلسله‌مراتب منابع

منبع مبنا همچنان `arXiv:2403.15665v2` سال 2024 است. منابع [1] و [4] فقط با
برچسب `[استخراج از مرجع مستقیم مقاله]` استفاده شده‌اند. نسخه IEEE TPDS سال 2025
صرفاً `[منبع تکمیلی خارج از مبنای v2]` است و هیچ داده آن به v2 نسبت داده نمی‌شود.

صفحات کامل زیر هم متنی و هم بصری بررسی شدند:

- v2: Section V-A، PDF p.6 و Section V-B، PDF p.8؛
- [4]: Section IV-A2/IV-C و Algorithm 1، PDF pp.4-5 (printed 228-229)؛
- [1]: Section IV-D و Algorithm 1، PDF pp.5-6؛
- IEEE 2025: Section V-B، PDF p.8.

## 2. استخراج قطعی از arXiv v2

| مؤلفه | استخراج | وضعیت |
| --- | --- | --- |
| Round 1 | `[صریح در مقاله]` فقط Round 2 تغییر می‌کند؛ پس R1 همان Double Knapsack پایه است. | کامل |
| pool Round 2 | `[صریح در مقاله]` اجتماع currently-running و returning-from-R1 هر server. | کامل |
| ظرفیت knapsack | `[صریح در مقاله]` total capacity، نه residual. | کامل |
| هدف knapsack | `[استخراج مستقیم]` همان Utility-maximizing Double Knapsack پایه؛ متن فقط candidate pool و capacity را تغییر می‌دهد. | تا حد زیادی کامل |
| score عضو | `[صریح در مقاله]` `1000 + utility/time_remaining`. | کامل |
| score غیرعضو | `[صریح در مقاله]` `1 + utility/time_remaining`. | کامل |
| ترتیب | `[صریح در مقاله]` descending score؛ عضویت اولویت نخست و ratio اولویت دوم. | tie/مرز ناقص |
| preemption | `[صریح در مقاله]` هر تعداد job ممکن است preempt شود. | کامل |
| مزیت current | `[صریح در مقاله]` تنها مزیت، time_remaining کمتر و در نتیجه ratio بهتر است. | کامل |
| قیمت Round 2 | چاپ نشده است. | نامشخص |
| شبه‌کد | وجود ندارد. | ناقص |

## 3. تطبیق با منابع مستقیم

### مرجع [4]

`[استخراج از مرجع مستقیم مقاله]` Double Knapsack پایه در R2 یک knapsack روی
returning jobs اجرا می‌کند. عضوها پذیرفته می‌شوند و در Case 3 قیمت
`U-U/violation` می‌گیرند؛ غیرعضوها به pool می‌روند. این مرجع current jobs،
preemption، score یا پذیرش nonmember از gap را تعریف نمی‌کند.

### مرجع [1]

`[استخراج از مرجع مستقیم مقاله]` روش Clustering+Preemption در R2 current و
returning را با total capacity مقایسه می‌کند، current خارج‌شده را preempt و new
job خارج‌شده را reject می‌کند. اما ابتدا فقط `Y` job را وارد knapsack می‌کند و
قیمت `max(0.9U,1)` دارد؛ بنابراین الگوریتم آن با DK-P v2 یکسان نیست و فقط شاهدی
برای تفسیر state transition است.

### نسخه IEEE 2025

`[منبع تکمیلی خارج از مبنای v2]` Section V-B همان دو پاراگراف و همان scoreهای
v2 را تکرار می‌کند. هیچ شبه‌کد، tie-break، قیمت R2 یا تعریف resource-state جدیدی
اضافه نشده است.

## 4. شبه‌کد منبع‌وفادار با نقاط حل‌نشده

```text
for each server s:
    current = active jobs already on s
    returning = jobs that selected s after unchanged DK Round 1
    pool = current union returning
    members = UtilityKnapsack(total_capacity(s), pool)

    for job in pool:
        ratio[job] = utility[job] / time_remaining[job]
        score[job] = 1000 + ratio[job] if job in members
                     else 1 + ratio[job]

    ordered = descending_score(pool)          # tie unresolved
    for job in ordered:
        check job for fit                     # resource-state unresolved
        if fit:
            retain current OR admit returning # inferred mapping
        else:
            preempt current OR reject returning

    Round-2 price = UNKNOWN
```

## 5. تحلیل اجرایی خط‌به‌خط

| گام v2 | وضعیت پیش از اجرا | تغییر قطعی | شکاف |
| --- | --- | --- | --- |
| total-capacity knapsack | active current و returning معلوم‌اند | membership subset تولید می‌شود | تنظیم GA برای DK-P صریح نیست |
| score assignment | membership و time_remaining معلوم‌اند | دو score چاپ‌شده محاسبه می‌شوند | freeze time و ratio boundary ذکر نشده |
| descending sort | scoreها موجودند | یک ترتیب ایجاد می‌شود | tie و cross-tier score conflict نامشخص |
| individual fit check | ترتیب موجود است | jobها یکی‌یکی ارزیابی می‌شوند | residual اولیه و update semantics چاپ نشده |
| preemption | current job جا نمی‌شود | امکان preempt چند job وجود دارد | commit/rollback و state mapping شبه‌کد ندارد |
| final accounting | active set جدید ساخته می‌شود | allocation outcome قابل محاسبه است | قیمت R2 برای nonmember پذیرفته‌شده مفقود است |

## 6. شکاف‌ها، اثر و گزینه نزدیک‌تر

| شکاف | محل بررسی‌شده | اثر | گزینه‌ها | گزینه پیشنهادی |
| --- | --- | --- | --- | --- |
| resource state در fit pass | v2 p.8؛ IEEE 2025 p.8 | تعیین دقیق قربانیان و active set | live residual فعلی؛ یا repack از total capacity | repack اتمیک از total capacity، ASSUMP-016 |
| tie و ثابت 1000 | v2 p.8 | تغییر ترتیب پذیرش/preemption | lexicographic؛ seeded tie؛ literal+fail-fast | literal score و fail-fast، ASSUMP-017 |
| GA Round 2 | v2 pp.6,8؛ [4] pp.4-5؛ [28] audit | subset و reproducibility | config جدید؛ یا extension 200/20/50 | extension محدود تنظیم ممیزی‌شده، ASSUMP-018 |
| قیمت R2 | v2 p.8؛ [4] p.5؛ [1] p.6 | ثبت charge و سازگاری result | member-only؛ تعمیم همه؛ omission | عدم ساخت قیمت، ASSUMP-019 |

## 7. فرض‌های پیشنهادی

- ASSUMP-016: repack اتمیک combined pool از total capacity؛ current غیرقابل‌جا
  preempt و returning غیرقابل‌جا reject شود.
- ASSUMP-017: scoreها لفظی، time_remaining منجمد در آغاز دور، و tie یا تناقض
  cross-tier به‌صورت fail-fast.
- ASSUMP-018: استفاده از pyeasyga 0.3.1 با 200/20/50 و seed اجباری در DK-P R2؛
  Exact فقط کمک‌آزمون.
- ASSUMP-019: ثبت membership/score/decision بدون ساخت price عددی R2.

این چهار فرض هنوز تأیید نشده‌اند و هیچ‌کدام وارد کد نشده‌اند.

> به‌روزرسانی 2026-08-10: کاربر هر چهار فرض را دقیقاً با همین متن تصویب کرد؛
> پیاده‌سازی و آزمون آن‌ها در مرحله دهم-I انجام شد. عبارت بالا وضعیت تاریخی پایان
> ممیزی مرحله دهم-H را ثبت می‌کند.

## 8. نتیجه قابلیت پیاده‌سازی

اطلاعات برای ساخت skeleton یا نسخه حدسی کافی است، اما برای پیاده‌سازی وفادار و
آزمون‌پذیر DK-P کافی نیست. ASSUMP-016 تا ASSUMP-019 بر allocation، قربانیان،
تکرارپذیری و خروجی قیمت اثر مستقیم دارند؛ بنابراین کدنویسی مطابق دستور کاربر
تا اخذ تأیید متوقف شد.
