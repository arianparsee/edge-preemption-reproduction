# زیرمرحله حفاظتی پیش از Stage 13-J

تاریخ: 2026-08-12

مبنا: `arXiv:2403.15665v2 (2024)`

وضعیت: **پنج workload و بیست pair موجود حفاظت، inventory و بدون محاسبه مجدد بازیابی شدند؛ هیچ batch مرحله ۱۳-J اجرا نشد.**

## نسخه‌های پایدار

دو نسخه byte-identical نگهداری می‌شوند:

1. نسخه gitignored داخل پروژه:
   `backups/stage13h-stage13i-protected-20260812/`
2. نسخه ثانویه خارج از repository:
   `C:\Users\htsh3\Documents\Codex\backups\edge-reproduction-stage13h-stage13i-protected-20260812\`

هر نسخه شامل ۸۶ فایل و `150,716,645` بایت است. هیچ فایل خام یا موقتی حذف نشد.
پوشه اول با قاعده `backups/` و تمام مسیرهای `results/` و `tmp/` با قواعد موجود
`.gitignore` از مخزن عمومی خارج هستند.

## Inventory و configهای دقیق

- `inventory.csv`: ۸۵ فایل فهرست‌شده، شامل نام نسبی، اندازه و SHA-256؛ خود inventory
  برای جلوگیری از hash خودارجاعی در ردیف‌های خودش نیست.
- SHA-256 inventory: `28300ed1ba5a220d401c6930931acf8efcca4c81b6c07946b16bb50c0386e434`
- SHA-256 verification report:
  `31dc4f124b6dcabb1a751e18cea298b3640ac596b09bf3e8fb4653bd1124ddc2`
- config دقیق Stage 13-H:
  `afa7c249911d34cdacefa4b2b80cdbfc44cddf47a7f2cfd0e246e7cd70fee3f0`
- config دقیق commit اجرای Stage 13-I:
  `b0ae2597119fb5ee3a27b2998d27e252b5d66e67356408abb7315238056f1963`

## کامل‌بودن بیست pair

برای هر pair وجود و hash فایل‌های `result.json`، `manifest.json` و `workload.json`
کنترل شد. بررسی‌ها شامل موارد زیر بود:

- Stage 13-H: یک workload و چهار policy؛
- Stage 13-I run `31629941152`: چهار workload و شانزده policy pair؛
- تطابق workload seed، policy seed و policy با config مادی‌شده؛
- تطابق result/workload SHA-256 با manifest؛
- یکسان‌بودن workload hash میان چهار policy هر seed؛
- افراز Completed و Rejected و زیرمجموعه‌بودن Preempted از Rejected؛
- دقیقاً ۵ workload و ۲۰ pair.

## آزمون بازیابی و resume

Verifier از هر دو مسیر پایدار اجرا شد. هر ۲۰ فراخوانی `run_full_pair(..., resume=True)`
وضعیت `skipped_existing_verified` برگرداند. hash هر payload پیش و پس از resume یکسان
ماند؛ بنابراین نه محاسبه مجدد و نه overwrite انجام شد.

## طرح پنج batch مستقل Stage 13-J

تقسیم batchها صرفاً `[پیشنهاد فنی برای اجرای resume-safe]` است و تنظیم مقاله نیست.
هر batch پنج workload و بیست pair دارد.

| Batch | Workload seeds |
| ---: | --- |
| 1 | 3972957962913175742، 4613587492413520585، 5320799758894818643، 5332330353602182806، 5719437079811370844 |
| 2 | 6003037148864077347، 6160038443179490880، 6417545337548839552، 6450436194684705298، 6671311904076009556 |
| 3 | 6893869117720259993، 7445649785757218883، 10810354314660334134، 11272760893988164789، 12076343533614044711 |
| 4 | 12667240223407183712، 13882333362331482238، 13932446904601729842، 14323796733708422592، 15626834761513784926 |
| 5 | 16228533004597355411، 16367340573487986447، 17123938884094496196، 17701681522849640973، 17715622485147679829 |

## برآورد و سیاست هر batch

برآوردها `[آزمون کمکی/برون‌یابی از Stage 13-I]` هستند:

| مؤلفه | برآورد هر batch |
| --- | ---: |
| مجموع runner time بیست pair | حدود 296.4 دقیقه |
| زمان دیواری با رفتار صف Stage 13-I | حدود 49.3 دقیقه |
| artifact فشرده GitHub | حدود 8.9 MB |
| نسخه محلی بازشده | حدود 150 MB |

Workflow فقط `workflow_dispatch` دارد، batch و عبارت تأیید
`RUN-STAGE13J-BATCH-N` را الزام می‌کند و trigger خودکار `push` ندارد. ۲۰ pair مستقل‌اند؛
در همان run می‌توان فقط jobهای شکست‌خورده را rerun کرد. summary فقط پس از اعتبارسنجی
هر ۲۰ pair ساخته می‌شود.

سیاست نگهداری:

- artifact مستقل هر pair و یک summary/config artifact؛
- retention برابر ۱۴ روز؛
- پیش از batch بعدی، دانلود محلی پایدار، inventory و resume verification اجباری؛
- raw data در Git عمومی commit نمی‌شود؛
- حذف artifact یا فایل محلی بدون تأیید جداگانه ممنوع است.

## وضعیت اجرا

- اجرای حفاظت: کامل؛
- Stage 13-J batch 1: **شروع نشده**؛
- Stage 13-J batchهای 2 تا 5: **شروع نشده**؛
- وضعیت علمی: 5/30 workload و 20/120 pair؛
- aggregation سی‌تکراری و Figure 6: انجام نشده‌اند.
