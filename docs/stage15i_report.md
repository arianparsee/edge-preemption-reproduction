# Stage 15-I — گزارش نهایی بازیابی aggregation-only برای Stage 15-H

## دامنه و منشأ

- طبقه‌بندی: `[آزمون کمکی]`؛ repairها روش مقاله نیستند.
- Run موفق: `32831698843`، commit `68c1444a4276631bb9e305bb50e5c12902627adf`.
- فقط job `aggregate-only` اجرا شد؛ `prepare`، matrix repair و aggregate عادی skip شدند.
- هیچ workload، policy، baseline، repair، GA یا simulator اجرا نشد.
- ۱۰۰ repair pair موفق Run `32474360245` و reuse معتبر ۲۰ pair بازیابی شدند.
- ۱۲۰ baseline از Run `31644121025` بدون بازاجرا بازیابی و با manifest علمی
  تطبیق داده شدند.

## گیت‌های اعتبار

- repair: `120/120`، baseline: `120/120`، workload: `30/30`.
- همهٔ replayهای درون-variant دقیق و Option-A RNG gate درون-variant موفق‌اند.
- مقایسهٔ کامل RNG variant با baseline همچنان `[نامشخص]` است، چون Stage 13 حالت
  نهایی و call-shape کامل RNG را ثبت نکرده بود.
- lifecycle مشتق‌شده دقیقاً SHA-256 معتبر Stage 15-A یعنی
  `fac98f37a6faf23bdb91387498ed11008611adef29b383d24f1c866f8504610a`
  را تولید کرد.
- digest آرشیو artifact نهایی:
  `ab3b29120ee3b32ead53cc25a0d6f2bde1e21e753562ee1e09ff37146d8ae623`.
- manifest تحویل ۲۸ فایل و manifest داخلی ۱۷ فایل را تأیید کرد. inventory پایدار
  ۳۰ فایل دانلودشده با مجموع `1,073,615` بایت را ثبت می‌کند.

## میانگین Completed Utility در ۳۰ workload

| سری | میانگین | CI 95% `[آزمون کمکی]` |
| --- | ---: | ---: |
| KG-P baseline | 11473.24 | [11273.77, 11672.72] |
| DK-R offspring repair | 10472.30 | [10160.43, 10784.17] |
| DK-R initialization repair | 10369.97 | [10057.36, 10682.58] |
| KG-R baseline | 9610.65 | [9153.84, 10067.46] |
| DK-P offspring repair | 9447.00 | [9129.33, 9764.66] |
| DK-P initialization repair | 9380.26 | [9088.18, 9672.34] |
| DK-P baseline | 3607.44 | [3402.59, 3812.29] |
| DK-R baseline | 1329.51 | [1149.20, 1509.82] |

## اثر paired repair نسبت به baseline همان seed

| Policy/repair | میانگین اثر مطلق | CI 95% اثر | میانه اثر | میانگین اثر نسبی | جهت در ۳۰ seed |
| --- | ---: | ---: | ---: | ---: | ---: |
| DK-R initialization | +9040.46 | [8645.02, 9435.91] | +8841.07 | +772.02% | 30+/0=/0− |
| DK-R offspring | +9142.79 | [8756.93, 9528.65] | +8928.29 | +779.46% | 30+/0=/0− |
| DK-P initialization | +5772.82 | [5417.91, 6127.72] | +5675.33 | +165.93% | 30+/0=/0− |
| DK-P offspring | +5839.55 | [5479.19, 6199.92] | +5862.05 | +167.52% | 30+/0=/0− |

Offspring repair از نظر میانگین برای هر دو policy قوی‌تر است. برای DK-R اختلاف
offspring منهای initialization برابر `+102.33` با CI برابر `[21.79, 182.86]`
است و offspring در ۱۸ seed از ۳۰ seed بهتر است. برای DK-P اختلاف میانگین `+66.74`
و CI برابر `[-59.82, 193.29]` است؛ بنابراین برتری مستقیم offspring برای DK-P با
این CI پایدار نیست، هرچند آن هم در ۱۸ seed بهتر است.

هر دو repair در مقایسه با baseline خود در `30/30` workload Utility را افزایش
دادند. ترتیب میانگین‌ها نشان می‌دهد DK-R repaired از KG-R عبور می‌کند ولی از KG-P
پایین‌تر می‌ماند؛ DK-P repaired از هر دو KG پایین‌تر می‌ماند. این تغییر ترتیب فقط
نتیجهٔ counterfactual کمکی است.

## وضعیت بازتولید

- initialization و offspring repair فقط `[آزمون کمکی]` هستند و به مقاله نسبت
  داده نمی‌شوند.
- Pipeline رسمی DK و artifactهای Stage 13-J/13-K و Stage 14-A تغییر نکردند.
- وضعیت رسمی Figure 6 بدون تغییر **«بازتولید نشد»** باقی می‌ماند.
- نمودارهای PNG از نظر خوانایی، بریدگی و هم‌پوشانی بررسی شدند و نقصی مشاهده نشد.
  چهار PDF تک‌صفحه‌ای، بدون رمزگذاری، با متن درون محدودهٔ صفحه هستند؛ Poppler در
  محیط حاضر موجود نبود، بنابراین بازبینی بصری مستقیم از نسخه‌های PNG متناظر انجام
  شد.
