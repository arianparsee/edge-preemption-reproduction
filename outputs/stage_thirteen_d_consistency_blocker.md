# مرحله سیزدهم-D: دروازه سازگاری پیش از پیاده‌سازی

تاریخ: 2026-08-12

وضعیت: **هر دو گزینه A در 2026-08-12 تأیید شدند؛ دروازه پیاده‌سازی باز است**

منبع مبنا arXiv v2 سال 2024 است. ASSUMP-033 تا ASSUMP-041 همگی
`[فرض بازتولید]` مصوب‌اند و تنظیم صریح مقاله نیستند. هیچ‌یک از این تصمیم‌ها یا
تعارض‌های زیر به پیام سرویس `Selected model is at capacity` مربوط نیست.

## 1. کارهای انجام‌شده

- وضعیت واقعی repository و آخرین implementation کامل بررسی شد.
- مشخص شد Stage 13-B آخرین زیربخش اجرایی کامل و Stage 13-C فقط ممیزی اسنادی است.
- قراردادهای `Task`، `Allocation`، `SimulationState`، چهار policy و تنظیمات GA
  موجود بررسی شدند.
- متن نهایی ASSUMP-033 تا ASSUMP-041 در سند فرض‌ها و ماتریس ردیابی ثبت شد.
- پیش از ساخت موتور، سازگاری ASSUMP-035، ASSUMP-036، ASSUMP-038 و ASSUMP-039
  به‌صورت جبری بررسی شد.
- هیچ موتور زمانی، canonicalizer، lifecycle، aggregator، config اجرایی یا smoke
  result جدیدی ساخته نشد.

## 2. تعارض مسدودکننده اول: نرخ computation و تأخیر pipeline

### محل اول

ASSUMP-035 و ASSUMP-036:

- پذیرش در epoch `e` از ابتدای `e+1` فعال می‌شود.
- `service_slots = D - e`، که `D` همان `absolute_deadline_slot` شامل است.
- نرخ ثابت allocation برابر `remaining_computation / service_slots` است و
  افزایش پنهانی آن ممنوع است.

### محل دوم

ASSUMP-038:

- active slot اول فقط upload دارد.
- computation از active slot دوم آغاز می‌شود.
- download از active slot سوم آغاز می‌شود.

### اثبات تعارض

از `e+1` تا `D` شامل، دقیقاً `S = D-e` active slot وجود دارد. چون active slot
اول computation ندارد، تعداد فرصت‌های computation برابر `S-1` است. برای
`K>0` و نرخ ثابت `r=K/S` داریم:

```text
maximum_computed = (S - 1) * K / S < K
```

بنابراین هیچ وظیفه دارای computation مثبت، حتی بدون رقابت منابع، نمی‌تواند تا
deadline کامل شود. برای نمونه اگر `e=0`، `D=3` و `K=30` باشد، نرخ مصوب 10 است؛
active slotهای 1، 2 و 3 وجود دارند ولی computation فقط در slotهای 2 و 3 انجام
می‌شود، پس حداکثر 20 از 30 تکمیل می‌شود.

### اثر

- smoke test واقعی نمی‌تواند completion مثبت معنادار تولید کند.
- feasibility در ASSUMP-039 همیشه برای `K>0` منفی خواهد بود.
- Completed Utility چهار policy به‌صورت مصنوعی صفر می‌شود.
- انتخاب هر راه‌حل در کد بدون تأیید، تغییر یکی از فرض‌های مصوب و فرض پنهانی است.

### گزینه‌ها

1. **گزینه A — پیشنهادی و نزدیک‌تر به pipeline سه‌مرحله‌ای مصوب:**
   `compute_eligible_slots = service_slots - 1` و برای computation مثبت الزام
   `compute_eligible_slots > 0` برقرار شود؛ سپس
   `compute_per_slot = remaining_computation / compute_eligible_slots`. نرخ پس از
   admission ثابت بماند. علاوه بر fit چهاربعدی، canonicalizer یک dry-run دقیق و
   deterministic از ASSUMP-038 را از `e+1` تا `D` انجام دهد تا کفایت نرخ‌های
   upload/download و قیود تقدم نیز برای completion بررسی شود. این گزینه
   ASSUMP-036 را اصلاح می‌کند ولی lagهای صریح ASSUMP-038 را حفظ می‌کند.
2. **گزینه B:** فرمول ASSUMP-036 حفظ شود، اما computation از active slot اول و
   download از active slot دوم مجاز شود. این گزینه زمان‌بندی سه‌اسلاتی مصوب در
   ASSUMP-038 را تغییر می‌دهد.
3. **گزینه C:** نرخ `K/S` و lagها هر دو حفظ شوند، اما در آخرین slot نرخ computation
   موقتاً افزایش یابد. این گزینه ممنوعیت افزایش پنهانی نرخ active allocation را
   نقض می‌کند و توصیه نمی‌شود.

پیشنهاد بازتولید: گزینه A.

## 3. تعارض مسدودکننده دوم: expiration و آزادسازی منابع

### محل اول

ASSUMP-034، ASSUMP-035 و ASSUMP-039 ایجاب می‌کنند وظیفه ناقص پس از فرصت deadline
شامل، `EXPIRED` و terminal شود و باقی‌ماندن وظیفه nonterminal موجب fail-fast باشد.

### محل دوم

ASSUMP-038 می‌گوید منابع «فقط پس از completion یا preemption» و به‌صورت اتمیک
آزاد شوند.

### اثر

اگر یک allocation فعال deadline را از دست بدهد، دو رفتار ممکن هر دو ناسازگارند:

- تبدیل آن به `EXPIRED` بدون release، allocation فعال و منابع رزروشده برای یک
  وظیفه terminal باقی می‌گذارد؛
- release هنگام expiration، از فهرست انحصاری completion/preemption در ASSUMP-038
  فراتر می‌رود.

### گزینه‌ها

1. **گزینه A — پیشنهادی:** ASSUMP-038 به «completion، preemption یا expiration»
   اصلاح شود. expiration یک transition اتمیک باشد که allocation را غیرفعال،
   همه منابع را آزاد و Utility را صفر می‌کند.
2. **گزینه B:** هر active deadline miss به‌جای `EXPIRED`، `PREEMPTED` نامیده شود.
   این semantics رخداد preemption را مخدوش می‌کند و با ASSUMP-039 ناسازگارتر است.
3. **گزینه C:** allocation پس از `EXPIRED` فعال بماند. این گزینه ناوردای سازگاری
   state/resource را نقض می‌کند و توصیه نمی‌شود.

پیشنهاد بازتولید: گزینه A.

## 4. مثال دستی هدف پس از رفع تعارض

مثال نهایی Stage 13-D باید حداقل سه active slot داشته باشد و موارد زیر را با
محاسبه دستی و اجرای برنامه مقایسه کند:

- active slot 1: فقط upload؛
- active slot 2: upload سپس computation؛
- active slot 3: upload، computation، download؛
- حداقل یک completion شامل؛
- حداقل یک rejection موقت و retry؛
- حداقل یک expiration؛
- در policy پیش‌دستانه، یک preemption terminal در صورت برآورده‌شدن شرط مصوب.

این مثال هنوز اجرا نشده است.

## 5. وضعیت اجرا و آزمون

پس از ثبت اسناد، مجموعه آزمون موجود برای اطمینان از عدم رگرسیون اجرا می‌شود.
هیچ آزمون یا smoke test مربوط به موتور Stage 13-D نوشته یا اجرا نشده است، زیرا
رفتار مرکزی موتور به دو تصمیم بالا وابسته است.

## 6. تصمیم موردنیاز

پیش از پیاده‌سازی باید برای هر تعارض یک گزینه تأیید شود. پیشنهاد فنی کم‌فاصله‌تر:

- تعارض نرخ computation: گزینه A؛
- تعارض release هنگام expiration: گزینه A.

پس از تأیید، Stage 13-D از همین نقطه با پیاده‌سازی، آزمون‌ها، مثال دستی و smoke
کوچک ادامه می‌یابد؛ اجرای 100 slot × 30 run و Figure 6 همچنان خارج از این
زیربخش می‌ماند.

## 7. تصمیم نهایی کاربر

کاربر در 2026-08-12 گزینه A هر دو تعارض را تأیید کرد:

- نرخ computation بر تعداد slotهای واقعاً computation-eligible یعنی
  `service_slots - 1` تقسیم می‌شود و feasibility با dry-run قطعی pipeline کنترل
  می‌شود؛
- expiration یک release اتمیک منابع ایجاد می‌کند و Utility آن صفر است.

هر دو تصمیم `[فرض بازتولید]` هستند و تنظیم صریح arXiv v2 معرفی نمی‌شوند.
