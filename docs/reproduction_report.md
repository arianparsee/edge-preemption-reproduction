# گزارش بازتولید جاری — تا تکمیل Stage 15-H و آماده‌سازی Stage 15-I

## مبنا و وضعیت کلی

منبع مبنا arXiv:2403.15665v2 (2024) است. نسخه نهایی 2025 فقط در موارد ثبت‌شده منبع تکمیلی خارج از مبنا بوده است. این گزارش وضعیت پروژه را تا پایان جمع‌بندی تشخیصی Figure 6 ثبت می‌کند و گزارش نهایی مرحله هجدهم نیست.

## مؤلفه‌های بازسازی‌شده

- مدل داده task/server/resource/bid/allocation و state؛
- مدل pipeline چند-epoch، deadline inclusive، retry، expiration و preemption؛
- KG-R، KG-P، Pipeline DK-R و Pipeline DK-P؛
- مولدهای Synthetic Normal و Synthetic Bimodal با فرض‌های مصوب؛
- workload صد-slotی PIPE-NORMAL با 30 seed و چهار policy؛
- aggregation، CSV و PNG/PDF Figure 6؛
- instrumentation غیرمداخله‌ای و counterfactualهای تشخیصی DK؛
- surrogate Southampton صرفاً برای آزمون فنی/کیفی.
- Figure 1 به‌صورت ساختاری/مفهومی در SVG/PDF/PNG و inventory قابل‌ردیابی بازسازی شد.

## وضعیت Figure 6

- `[صریح در مقاله]` ترتیب کیفی گزارش‌شده: `DK-P > KG-P > DK-R > KG-R`.
- `[نتیجه اجرای واقعی]` ترتیب بازتولید: `KG-P > KG-R > DK-P > DK-R`.
- وضعیت رسمی: **بازتولید نشد**.
- 120/120 pair اجرای رسمی PIPE-NORMAL کامل و اعتبارسنجی شده‌اند.
- repairهای تشخیصی Figure 6 را بازنویسی نکرده‌اند.

## وضعیت Figure 1

- `[صریح در مقاله]` Figure 1 یک timeline برای arrival، bidding و processing است.
- `[نتیجه اجرای واقعی]` هر چهار lane، epochهای 0/1/2، دو job set، شاخه‌های
  Allocated/Rejected، retry و انتقال به processing در خروجی برداری بازسازی شدند.
- سطح بازتولید: **بازتولید ساختاری/مفهومی کامل**؛ pixel copy انجام نشده است.
- موارد `[نامشخص]`: معنای کمی dot count، epoch ادامه سمت راست و طول پردازش.
- هیچ آزمایش عددی اجرا نشد و وضعیت Figure 6 تغییر نکرد.

## جمع‌بندی تشخیصی Stage 15-A تا Stage 15-F

شواهد non-interventional محل افت DK را در admission، به‌ویژه Round 2، قرار می‌دهند. canonicalization اختلاف DK/KG را توضیح نمی‌دهد و completion پس از پذیرش DK-R کامل است. نرخ بسیار بالای GA repair و فروپاشی raw-best به subsetهای بسیار کوچک مشاهده شد.

دو counterfactual feasibility-aware، یعنی initialization repair و offspring repair، completed Utility را ابتدا در هر پنج seed و سپس در اعتبارسنجی Stage 15-H در هر ۳۰ seed برای DK-R و DK-P افزایش دادند. این نتیجه فقط `[آزمون کمکی]` است. قوی‌ترین مظنون اختلاف، feasibility ضعیف chromosomeها یا تفاوت بازسازی encoding/repair با اجرای نویسندگان است؛ اما چون کد رسمی، repair، encoding و جزئیات کامل GA منتشر نشده، علت نهایی `[نامشخص]` باقی می‌ماند.

گزارش کامل زنجیره شواهد در `docs/stage15f_figure6_diagnostic_closure.md` ثبت شده است.

## مؤلفه‌های بازسازی‌شده با فرض

- run control و seedهای ASSUMP-033؛
- horizon/drain، lifecycle و pipeline progress طبق ASSUMP-034 تا ASSUMP-040؛
- GA و tie semantics طبق فرض‌های مصوب؛
- output size مصنوعی و computation per-slot؛
- surrogate Southampton؛
- counterfactualهای ASSUMP-044 تا ASSUMP-047 فقط به‌عنوان آزمون کمکی.

هیچ‌یک از این فرض‌ها تنظیم صریح arXiv v2 معرفی نمی‌شوند.

## موارد غیرقابل‌بازتولید یا مسدود

- Figure 6 از نظر ترتیب کیفی و فاصله ادعاشده بازتولید نشد؛
- Figs.7–8 به‌دلیل threshold نامشخص high/low؛
- Figs.9–10 به‌دلیل auction-time semantics؛
- Figs.11–15 به‌دلیل Batch DK-R pricing/lifecycle؛
- Figs.16–20 به‌دلیل نبود raw Southampton trace و schema؛
- آزمایش‌های OPT به‌دلیل نبود instance دقیق و solver settings؛
- انتساب قطعی ضعف DK به یک جزء مشخص GA به‌دلیل نبود کد رسمی نویسندگان.

## ارزیابی وفاداری جاری

| مؤلفه | وضعیت |
|---|---|
| مدل سیستم و منابع | بازسازی‌شده با فرض‌های مستند |
| مدل ریاضی | بازسازی‌شده؛ چند نگاشت زمانی با فرض |
| KG-R/KG-P | پیاده‌سازی و آزمون‌شده با فرض‌های ثبت‌شده |
| Pipeline DK-R/DK-P | پیاده‌سازی و آزمون‌شده؛ جزئیات رسمی GA/repair ناقص |
| داده Synthetic Normal | قابل تولید و تکرار با config مصوب |
| داده Synthetic Bimodal | قابلیت کمکی آزمون‌شده؛ آزمایش batch مسدود |
| Southampton واقعی | مسدود؛ surrogate داده واقعی نیست |
| Figure 6 | 120/120 اجرا کامل؛ نتیجه «بازتولید نشد» |
| Figure 1 | بازتولید ساختاری/مفهومی کامل؛ ابهام کمی ندارد چون شکل مفهومی است |
| سایر شکل‌های ارزیابی | رسمی مسدود یا هنوز اجرا نشده |

## محدودیت انتشار

داده خام، artifactهای حجیم، PDFها و مسیرهای محلی پایدار در مخزن عمومی commit نمی‌شوند. گزارش‌ها فقط به manifestها، checksumها و خروجی‌های پاک‌سازی‌شده ارجاع می‌دهند.

## نزدیک‌ترین هدف بعدی

Figure 1 در Stage 15-G تکمیل شد. نزدیک‌ترین قابلیت ارزیابی‌مانند پس از آن، R1-DIAG-AUX برای histogram
قیمت/discount Server 5 در epoch 43، نزدیک Fig.3 است. مسیر دوم بدون seed و workload رسمی مقاله فقط
`[آزمون کمکی]` خواهد بود و پیش از اجرا به تأیید دامنه نیاز دارد.

## Stage 15-H — اعتبارسنجی ۳۰-workload دو repair تشخیصی

- `[نتیجه اجرای واقعی؛ آزمون کمکی]` ۱۰۰ pair جدید و ۲۰ pair reuse، در مجموع
  ۱۲۰/۱۲۰ logical pair، کامل و از نظر checksum، seed، workload hash، policy seed،
  replay و RNG درون-variant معتبر شدند.
- baselineهای ۱۲۰/۱۲۰ Stage 13-J/13-K فقط reuse شدند و دوباره اجرا نشدند.
- initialization repair و offspring repair completed Utility را برای DK-R و DK-P
  در ۳۰/۳۰ workload افزایش دادند.
- میانگین completed Utility برای DK-R از `1329.51` به `10369.97` و `10472.30`
  و برای DK-P از `3607.44` به `9380.26` و `9447.00` رسید؛ مقادیر به‌ترتیب
  initialization و offspring هستند.
- ترتیب کمکی حاصل `KG-P > DK-R-offspring > DK-R-initialization > KG-R >
  DK-P-offspring > DK-P-initialization` است. این ترتیب روش مقاله یا Figure 6 جدید
  محسوب نمی‌شود.
- Run `32474360245` فقط در job تجمیع شکست خورد؛ ۱۰۰/۱۰۰ job محاسباتی جدید موفق
  بودند. علت، مسیر قدیمی فایل baseline پس از download-artifact بود، نه خطای علمی.
- finalizer موجود با مسیر واقعی روی artifactهای پایدار، بدون اجرای workload یا
  policy، وضعیت `complete_and_valid` برای ۱۲۰ repair و ۱۲۰ baseline را تأیید کرد.
- وضعیت رسمی Figure 6 همچنان **«بازتولید نشد»** است.

## Stage 15-I — مرز اصلاح فنی

Stage 15-I فقط مسیر baseline را به‌صورت fail-fast از artifact دانلودشده کشف و
aggregation-only را روی نتایج موجود اجرا می‌کند. اجرای simulator، workload، policy،
GA، baseline یا repair pair در این مرحله ممنوع است. هیچ مقدار علمی، seed، config یا
artifact رسمی Stage 14-A تغییر نمی‌کند.

اجرای aggregation-only با شناسه `32829531291` نشان داد اصلاح مسیر
`raw_run_metrics.csv` درست بوده و دانلود ۱۰۰ pair جدید، reuse بیست pair و baseline
تجمیعی موفق است. اجرا سپس پیش از finalization به‌علت نبود فایل مشتق‌شده و
gitignoredِ `per_run_lifecycle.csv` روی runner پاک شکست خورد. این شکست فنی است و
هیچ workload یا policy را اجرا نکرد.

اصلاح دوم فایل lifecycle را فقط از ۱۲۰ `result.json` معتبر Run `31644121025`
بازمادی‌سازی می‌کند. artifact بیست pair نخست به digest رسمی GitHub
`e17e18cd…ad179` pin شده و پنج دستهٔ بیست‌تایی باقی‌مانده با digestهای رسمی GitHub
و سپس manifest علمی ۱۲۰-pair کنترل می‌شوند. خروجی محلی مستقل دقیقاً SHA-256
`fac98f37…4610a` معتبر Stage 15-A را بازتولید کرد. این عملیات بازاجرای baseline یا
شبیه‌سازی نیست.

Run اصلاح‌شده `32831698843` با موفقیت کامل شد. خروجی نهایی `120/120` repair،
`120/120` baseline و `30/30` workload را تأیید کرد؛ همهٔ replayهای درون variant
دقیق‌اند. artifact در مسیر پشتیبان محلی پایدار شد و manifest مستقل ۳۰ فایل با
SHA-256 ساخت. گزارش عددی کامل در `docs/stage15i_report.md` ثبت شده است. وضعیت رسمی
Figure 6 همچنان **«بازتولید نشد»** است.
