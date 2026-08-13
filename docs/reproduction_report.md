# گزارش بازتولید جاری — تا پایان Stage 15-G

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

دو counterfactual feasibility-aware، یعنی initialization repair و offspring repair، completed Utility را برای DK-R و DK-P در هر پنج seed افزایش دادند. این نتیجه فقط `[آزمون کمکی]` است. قوی‌ترین مظنون اختلاف، feasibility ضعیف chromosomeها یا تفاوت بازسازی encoding/repair با اجرای نویسندگان است؛ اما چون کد رسمی، repair، encoding و جزئیات کامل GA منتشر نشده، علت نهایی `[نامشخص]` باقی می‌ماند.

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
