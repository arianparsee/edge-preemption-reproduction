# Stage 15-C - گزارش funnel غیرمداخله‌ای تصمیم DK

## 1. وضعیت اجرا و عدم مداخله

- [آزمون کمکی] Run `31708325126` روی workload نخست ASSUMP-033 با seed
  `541501192080118187` و commit `8714a5d8950593be3727fec5fa8a8a66bfa1382f` موفق شد.
- baseline معتبر Run `31624982369` بازاجرا نشد.
- fingerprint علمی برای DK-R و DK-P دقیقاً برابر baseline بود.
- هیچ seed، ترتیب candidate، تنظیم GA، random draw، policy یا فرض علمی تغییر نکرد.
- artifact شامل task ID، chromosome bits، raw workload یا trace نیست.

## 2. funnel تفصیلی تک-seed

اعداد entry ممکن است یک task را در سرورها یا epochهای مختلف چند بار بشمارند و task ID یکتا
نیستند.

| مرحله | DK-R | DK-P |
| --- | ---: | ---: |
| Requesting task attempts | 6783 | 6773 |
| Round-1 candidate entries | 54264 | 54184 |
| Round-1 raw-best selected entries | 27005 | 26873 |
| Round-1 post-repair selected entries | 16 | 22 |
| Round-1 repaired GA calls | 838/856 | 843/864 |
| Round-1 tasks selected on at least one server | 15 | 12 |
| Round-1 server assignments | 6783 | 6773 |
| Round-2 candidate entries | 6783 | 7005 |
| Round-2 raw-best selected entries | 3389 | 3620 |
| Round-2 post-repair selected entries | 24 | 168 |
| Round-2 repaired GA calls | 106/111 | 104/128 |
| Round-2 accepted | 24 | 46 |
| Round-2 rejected | 6759 | 6727 |
| Round-2 retained | 0 | 226 |
| Round-2 preempted | 0 | 6 |

## 3. تحلیل گلوگاه‌ها

### Round 1: repair شدید، اما نه gate مستقیم server assignment

- raw-best chromosome تقریباً نیمی از candidate-entryها را انتخاب کرده بود: DK-R برابر
  `27005/54264` و DK-P برابر `26873/54184`.
- با این حال، 97.90% فراخوانی‌های GA در DK-R و 97.57% در DK-P raw-best ناممکن داشتند و
  طبق ASSUMP-042 به مجموعه تهی repair شدند.
- در مجموع 26989 entry در DK-R و 26851 entry در DK-P در فاصله raw-best تا خروجی نهایی
  selector حذف شدند.
- با وجود این، `round_1_no_server=0` و همه 6783/6773 درخواست server assignment گرفتند.

[استخراج مستقیم] در پیاده‌سازی فعلی، membership کوله‌پشتی Round 1 قیمت را تغییر می‌دهد، اما
nonmembership الزاماً task را از انتخاب سرور حذف نمی‌کند. بنابراین repair بسیار شدید Round 1
یک علامت مهم ضعف feasibility/fitness است، ولی gate مستقیم افت admission نیست.

### Round 2: gate مستقیم پذیرش DK-R

- در DK-R، 6783 returning-entry وارد Round 2 شدند؛ raw-bestها 3389 entry انتخاب کردند، اما
  106 از 111 فراخوانی واقعی GA repair شد و فقط 24 entry باقی ماند.
- همان 24 entry پذیرفته و هر 24 task بعداً complete شدند.
- `6759/6783 = 99.646%` تصمیم‌های Round 2 رد شدند.
- 5481 retry ثبت شد و 1278 task پس از تکرار رد، در نخستین epoch ناممکن بعدی منقضی شدند.

[استخراج مستقیم] برای DK-R، افت اصلی به‌طور مستقیم در GA/repair Round 2 رخ می‌دهد؛ پس از
پذیرش، completion شکست ندارد.

### Round 2: combined-pool و repacking در DK-P

- 7005 candidate-entry شامل 6773 returning و 232 current-entry بود.
- پس از repair فقط 168 member-entry باقی ماند: 144 current و 24 returning.
- مرحله score/repacking در مجموع 226 current را retained، تعداد 6 را preempted، 46 returning
  را accepted و 6727 returning را rejected کرد.
- accepted بیشتر از 24 returning-member است، زیرا الگوریتم پس از اولویت members، nonmemberها
  را نیز برحسب score و ظرفیت بررسی می‌کند؛ این رفتار همان Pipeline DK-P مصوب است.
- 46 پذیرش به 40 completion و 6 preemption terminal انجامید.

[استخراج مستقیم] برای DK-P، repair Round 2 شدید است ولی repacking بخشی از nonmemberهای
returning را نیز نجات می‌دهد. با این حال `6727/6773 = 99.321%` تلاش‌های returning رد می‌شوند.

## 4. lifecycle

| رویداد | DK-R | DK-P |
| --- | ---: | ---: |
| Accepted | 24 | 46 |
| Completed | 24 | 40 |
| Preempted | 0 | 6 |
| Retry scheduled | 5481 | 5471 |
| Expired after Round-2 rejection | 1278 | 1256 |
| Expired during canonicalization | 89 | 89 |
| Expired waiting at deadline | 4 | 4 |

canonicalization و waiting-deadline expiration میان دو DK تقریباً یکسان‌اند. اختلاف عملکرد
در funnel policy، به‌ویژه GA/repair و commit Round 2، متمرکز است.

## 5. آزمون‌ها و اجرای واقعی

- Ruff: موفق.
- mypy: موفق.
- آزمون‌های محلی مرتبط: `38 passed in 4.19s`.
- آزمون قرارداد عدم مداخله در هر دو job GitHub: موفق.
- گام رسمی DK-R: 19 دقیقه و 1 ثانیه.
- گام رسمی DK-P: 19 دقیقه و 21 ثانیه.
- workflow کامل: حدود 20 دقیقه و 1 ثانیه.
- سه job، validator امنیتی، merge و checksum: همگی موفق.

## 6. artifactهای پایدار

| Artifact | اندازه | SHA-256 | تطبیق GitHub |
| --- | ---: | --- | --- |
| merged | 2258 B | `24c3fa6743f3ec2567a4f30594d40623795b268e36a29ad19bb1beffdf7cb097` | موفق |
| DK-P | 1892 B | `41c52769ba05ea2d41a13fce2ab0aa71dcaa06f2dd1aece625dae7c8f08eea60` | موفق |
| DK-R | 1846 B | `1487a45c04b40db3cfb77b852f4d5856b45c81dcb1645d0dd8d6b425cb4337d4` | موفق |

artifactها و manifest در `backups/stage15c-run-31708325126/` پایدار و gitignored هستند و
در مخزن عمومی commit نمی‌شوند.

## 7. فرض‌ها و محدودیت‌ها

- هیچ فرض بازتولید جدیدی استفاده نشد.
- این نتیجه تک-seed و `[آزمون کمکی]` است؛ نتیجه سی‌تکراری Figure 6 را جایگزین نمی‌کند.
- مشاهده حاضر رابطه علی counterfactual را اثبات نمی‌کند؛ فقط محل افت را مشخص می‌کند.
- اصلاح encoding، fitness یا repair یک تغییر علمی/الگوریتمی است و بدون تأیید کاربر مجاز نیست.

## 8. مرحله بعدی پیشنهادی

**Stage 15-D**: طراحی آزمایش‌های counterfactual تک‌عاملی برای علت ریشه‌ای repair شامل
feasibility-aware initialization، penalty fitness و repair operator. این مرحله رفتار الگوریتم
را تغییر می‌دهد و پیش از هر پیاده‌سازی یا اجرا به تأیید صریح فرض‌ها و دامنه نیاز دارد.
