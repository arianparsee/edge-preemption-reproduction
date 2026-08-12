# مرحله دوازدهم-A — ممیزی منبع و قابلیت پردازش trace واقعی Southampton

تاریخ ممیزی: 2026-08-11  
منبع مبنا: arXiv:2403.15665v2 (2024)  
وضعیت نهایی: **مسدود برای preprocessing وفادار؛ raw trace و نگاشت اجرایی موجود نیست**

## 1. منابع بررسی‌شده

| منبع | محل بررسی | نقش | نتیجه |
| --- | --- | --- | --- |
| arXiv v2 | Section VI-B3، PDF pp.10-12؛ source `main.tex` lines 551-593 | مبنای بازتولید | توصیف سطح‌بالا و نمودارها موجود؛ URL/schema/raw file مفقود |
| بسته source رسمی v2 | `arxiv_2403.15665v2_source.tar` | بررسی ancillaryها | پنج تصویر PNG مربوط به trace موجود؛ CSV/JSON/code/data dictionary وجود ندارد |
| مرجع مستقیم [1] | Section V-C، PDF pp.8-10؛ Table III | `[استخراج از مرجع مستقیم مقاله]` | priority examples و Utility distribution را اضافه می‌کند؛ raw/schema/date را نمی‌دهد |
| نسخه IEEE 2025 | Section VI-B4، PDF pp.12-14 | `[منبع تکمیلی خارج از مبنای v2]` | همان شکاف‌ها باقی است؛ acknowledgment می‌گوید تیم HPC در فراهم‌کردن trace کمک کرده است |
| صفحه رسمی Southampton HPC | وب، بررسی 2026-08-11 | تأیید هویت Iridis | Iridis را سرویس HPC دانشگاه معرفی می‌کند؛ لینک این trace را عرضه نمی‌کند |
| arXiv، Southampton ePrints/Open Data، DOI و GitHub web search | بررسی 2026-08-11 | کشف dataset/code عمومی | هیچ رکورد رسمی قابل‌انتساب به این trace پیدا نشد |

SHA-256 منابع محلی:

- arXiv v2 PDF: `29E51E385E1C15C22B632A95273E83219500A82985B28BCBDE7B8EF3A0E32DBE`
- reference [1] PDF: `D0101C98C7DAB68AA8EB16B78D7277ACD8849B088511BB2C3C4975025EC98564`
- IEEE 2025 PDF: `31EB8AB30BABBFA0699310C6F27A0CF22419C74DF42D79D1D34B8F587FC4EF89`
- arXiv v2 source tar: `418FDCC0EFE86194151D591BCB6B54C1873A5DC3D761CA81D95290BD63073165`

منابع وب:

- [صفحه arXiv مقاله](https://arxiv.org/abs/2403.15665)
- [صفحه رسمی سرویس HPC/Iridis دانشگاه Southampton](https://www.southampton.ac.uk/isolutions/staff/high-performance-computing.page)
- [رکورد انتشاراتی مرجع مستقیم [1] در Penn State](https://pure.psu.edu/en/publications/scalable-resource-allocation-techniques-for-edge-computing-system/)

عدم یافتن یک رکورد عمومی اثبات نمی‌کند که داده در هیچ محل غیرنمایه‌شده‌ای وجود
ندارد. نتیجه محدودتر این ممیزی آن است که **از منابع رسمی و جست‌وجوهای قابل‌دسترسی،
dataset عمومی قابل‌تأیید پیدا نشد**.

## 2. هویت trace و پروتکل قابل‌اثبات

| مؤلفه | اطلاعات قابل‌اثبات | محل | برچسب |
| --- | --- | --- | --- |
| سازمان | University of Southampton | v2 Section VI-B3 | `[صریح در مقاله]` |
| سامانه | Iridis Compute Cluster / Southampton HPC | [1] p.8 و صفحه رسمی HPC | `[استخراج مستقیم]` |
| نوع داده | workload trace شامل arrival و job attributes | v2 p.10؛ [1] p.8 | `[صریح در مقاله]` |
| طول trace کامل | چهار سال | v2 p.10 | `[صریح در مقاله]` |
| پنجره آزمایش | سه روز در آوریل 2021 | v2 p.10 | `[صریح در مقاله]` |
| دلیل انتخاب | نمونه workload پایدار درون ترم | v2 p.10 | `[صریح در مقاله]` |
| گام زمانی | یک auction در هر 10 دقیقه | v2 p.10 | `[صریح در مقاله]` |
| priority | high/medium/low بر اساس user group | v2 p.10 | `[صریح در مقاله]` |
| تعداد server | دو high-memory و سه regular | v2 p.11 | `[صریح در مقاله]` |
| RAM server | 768 GB و 192 GB | v2 p.11 | `[صریح در مقاله]` |
| download per slot | `B_d × slot_duration ~ N(10, 0.2)` GB | v2 p.11 | `[صریح در مقاله]` |
| deadline variant | cap حداکثر دو ساعت، برابر 12 slot ده‌دقیقه‌ای | v2 pp.11-12 | `[استخراج مستقیم]` |

`[استنباط از منابع]` acknowledgment مرجع [1] و نسخه نهایی می‌گوید Southampton
HPC team در «providing the trace data» کمک کرده است. همراه با نبود URL/DOI، این
شاهد با provision مستقیم داده برای پژوهشگران سازگار است، اما خصوصی‌بودن یا ممنوعیت
انتشار را به‌تنهایی اثبات نمی‌کند.

## 3. Data Dictionary اثبات‌پذیر و شکاف‌های schema

این جدول schema فایل خام نیست؛ فقط مفاهیمی است که متن ادعا می‌کند در trace یا
پردازش مشتق‌شده وجود داشته‌اند.

| مفهوم مقصد | شاهد موجود | واحد گزارش‌شده | ستون خام | تبدیل لازم | وضعیت |
| --- | --- | --- | --- | --- | --- |
| job arrival | «exact job arrivals» | timestamp/slot نامشخص | نامشخص | timestamp → 10-minute slot | مسدود |
| `s_j` storage | trace storage histogram | Gigabytes در شکل | نامشخص | raw field → GB/MB | مسدود |
| `K_j` computation | trace computation histogram | **Gigabytes در شکل** | نامشخص | raw field → MFlops | ناسازگار/مسدود |
| `d_j` deadline | trace deadline histogram | hours | نامشخص | raw deadline → slots | مسدود |
| user group | userها anonymous؛ group قابل استنباط بوده | category | نامشخص | raw group → priority | مسدود |
| priority | high/medium/low | category | مشتق‌شده | mapping کامل groupها | ناقص |
| `U_j` utility | بر اساس priority | utility | در trace نیست/مشتق‌شده | seeded draw | نیازمند فرض |
| `S_i` server storage | 2×768 و 3×192 | GB RAM | config مشتق‌شده | GB → واحد مدل | تا حدی کامل |
| `C_i` server compute | گفته شده از node statistics گرفته شده | مقدار عددی گزارش نشده | نامشخص | node CPU → MFlops/slot | مسدود |
| `B_{d,i}` | Normal per-slot draw | GB/slot | synthetic config | RNG + seed | ناقص |
| `B_{u,i}` | هیچ مقدار trace گزارش نشده | نامشخص | نامشخص | نامشخص | مسدود |
| `s'_j` output size | گزارش نشده | نامشخص | نامشخص | نامشخص | مسدود |

### ناسازگاری واحد computation

- `[صریح در مدل]` v2 و [1]، `K_j` را با MFlops و `C_i` را با MFlops/s تعریف می‌کنند.
- `[صریح در شکل]` محور افقی «Trace Workload Computation Distribution» در هر دو
  مقاله `Gigabytes` است.
- `[نامشخص]` معلوم نیست این شکل requested memory، total CPU allocation، data size
  یا کمیت دیگری را نمایش می‌دهد؛ تبدیل GB به MFlops از منابع ممکن نیست.
- اثر: feasibility، duration، deadline success، ranking و تمام Figs. 19-20 تغییر
  می‌کنند. ساخت تبدیل دلخواه مجاز نیست.

## 4. اطلاعات فقط موجود در مرجع مستقیم [1]

موارد زیر به v2 نسبت داده نمی‌شوند:

| مورد | مقدار | محل | وضعیت انتقال به v2 |
| --- | --- | --- | --- |
| High priority examples | WorldPop/data-processing group، research staff، misc research | [1] Section V-C، p.8 | مثال است، mapping exhaustive نیست |
| Medium examples | PhD students، ML/GPU-heavy jobs | [1] p.8 | مثال است، mapping exhaustive نیست |
| Low examples | undergraduates، serial/batch، سایر کاربران | [1] p.8 | مثال است، mapping exhaustive نیست |
| High Utility | `N(100,10)` | [1] Table III، p.9 | نیازمند فرض انتقال به v2 |
| Medium Utility | `N(40,10)` | [1] Table III، p.9 | نیازمند فرض انتقال به v2 |
| Low Utility | `N(20,4)` | [1] Table III، p.9 | نیازمند فرض انتقال به v2 |
| 45-minute example | 5 slot پس از time scaling | [1] p.9 | off-by-one و rounding عمومی را تعیین نمی‌کند |

## 5. آنچه از شکل‌ها قابل و غیرقابل استخراج است

- `[صریح در مقاله]` Figs. 16-18/v2 و Figs. 7-9/[1] histogramهای storage،
  computation و deadline را به تفکیک priority نشان می‌دهند.
- محور عمودی probability است، ولی bin edges، normalization denominator، تعداد
  رکوردها و مقادیر پشت شکل ارائه نشده‌اند.
- rasterهای source فقط PNG هستند؛ داده جدولی همراه آن‌ها وجود ندارد.
- digitization می‌تواند فقط `[مقادیر تقریبی خوانده‌شده از شکل]` تولید کند و raw
  trace، timestampها، correlation میان فیلدها یا رکوردهای مشترک را بازسازی نمی‌کند.
- بنابراین digitization برای preprocessing رسمی داده واقعی مناسب نیست.

## 6. اطلاعات مفقود و اثر آن‌ها

| اطلاعات مفقود | محل‌های بررسی‌شده | اثر |
| --- | --- | --- |
| URL/DOI/license/checksum raw trace | v2 pp.10-12، [1] pp.8-10، IEEE 2025 pp.12-14، source tar، جست‌وجوی رسمی | دریافت و اصالت‌سنجی ممکن نیست |
| سه تاریخ دقیق April 2021 | همان | هیچ window وفاداری قابل انتخاب نیست |
| timezone و مرز slot | همان | arrival slot و deadline off-by-one می‌شود |
| schema/type/null semantics | همان | parser و validation قابل تعریف نیست |
| row count و filtering rules | همان | audit count و مقایسه شکل‌ها ممکن نیست |
| mapping کامل user group | v2 p.10، [1] p.8 | priority/Utility تغییر می‌کند |
| تعریف/واحد computation | model و Figs. 17/8 | تبدیل به `K_j` و `C_i` ممکن نیست |
| upload و output size | تمام منابع | مدل چهاربعدی و زمان batch ناقص است |
| seed Utility و `B_d` | v2/[1] | نتایج عددی تکرارپذیر نیست |
| روش deadline cap/rounding | v2/[1] | مرز دو ساعت و slotها مبهم است |

## 7. گزینه‌های ادامه

### گزینه A — دریافت artifact اصلی و اطلاعات همراه (پیشنهاد نزدیک‌ترین به مقاله)

از نویسندگان یا Southampton HPC team موارد زیر دریافت شود:

1. raw یا نسخه anonymized سه‌روزه استفاده‌شده؛
2. تاریخ/زمان دقیق پنجره و timezone؛
3. schema و واحد هر ستون؛
4. script استخراج/فیلتر و mapping user group؛
5. تعریف computation و تبدیل آن به `K_j/C_i`؛
6. upload/output-size handling؛
7. seeds و نسخه کد؛
8. مجوز استفاده/بازنشر و checksum.

مزیت: تنها مسیر قابل دفاع برای بازتولید عددی Figs. 16-20.  
وضعیت: تا تأمین فایل، preprocessing مسدود است.

### گزینه B — trace سازگار ولی غیرهمسان

یک export جدید/مجاز از scheduler Iridis با schema مستند دریافت و mapping جدید
طراحی شود. این مسیر به چند فرض بازتولید نیاز دارد و نتیجه باید
`[داده واقعی جایگزین؛ نه trace مقاله]` نام‌گذاری شود.

### گزینه C — surrogate از histogramها

از rasterها binهای تقریبی خوانده و یک داده مصنوعی surrogate ساخته شود. این مسیر
correlationها و arrival sequence را از دست می‌دهد و فقط برای آزمون کیفی مناسب است؛
بازتولید داده واقعی یا نتایج مقاله محسوب نمی‌شود.

## 8. تصمیم پیشنهادی

**گزینه A توصیه می‌شود.** هیچ mapping یا فرض عددی جدید در این مرحله اعمال نشد.
تا دریافت raw/schema یا انتخاب صریح گزینه B/C، ساخت `southampton.py` و اجرای
preprocessing متوقف می‌ماند.

## 9. وضعیت قابلیت بازتولید

| مؤلفه | وضعیت |
| --- | --- |
| هویت سازمان/cluster | تا حد زیادی کامل |
| پنجره زمانی | ناقص و مسدودکننده |
| دسترسی raw | مسدودشده |
| schema | مسدودشده |
| arrival discretization | ناقص ولی پس از داشتن timestamp قابل تصمیم |
| priority mapping | ناقص |
| Utility mapping | ناقص؛ فقط [1] مقدار می‌دهد |
| server storage | تا حد زیادی کامل |
| server computation/upload/output | مسدودشده |
| بازتولید Figs. 16-20 | مسدودشده |

