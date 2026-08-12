# ممیزی هویت و کامل‌بودن منابع مستقیم [1] و [4]

تاریخ ممیزی: 9 اوت 2026

## 1. نتیجه نهایی

| فایل | تطبیق با ارجاع v2 | هویت | کامل‌بودن | وضعیت |
| --- | --- | --- | --- | --- |
| `1.pdf` | مرجع [1] | *Scalable Resource Allocation Techniques for Edge Computing Systems*، ICCCN 2022 | 10 صفحه کامل از صفحه عنوان تا References | تأیید شد |
| `4.pdf` | مرجع [4] | *Online Resource Allocation in Edge Computing Using Distributed Bidding Approaches*، IEEE MASS 2021 | 9 صفحه کامل، صفحات چاپی 225 تا 233، از عنوان تا References | تأیید شد |

هر دو فایل نسخه کامل مقاله کنفرانسی هستند، نه abstract، preview یا مجموعه صفحات جداشده. هیچ‌کدام پیوست، کد رسمی یا داده خام ضمیمه ندارند.

## 2. مشخصات فایل `1.pdf`

| ویژگی | مقدار |
| --- | --- |
| عنوان | *Scalable Resource Allocation Techniques for Edge Computing Systems* |
| نویسندگان | Caroline Rublein؛ Fidan Mehmeti؛ Taha D. Gunes؛ Sebastian Stein؛ Thomas F. La Porta |
| محل انتشار | 2022 International Conference on Computer Communications and Networks، ICCCN 2022 |
| DOI | `10.1109/ICCCN54977.2022.9868909` |
| تعداد صفحات PDF | 10 |
| اندازه صفحه | Letter، `612×792 pt` |
| رمزگذاری | ندارد |
| اندازه فایل | 738,436 بایت |
| SHA-256 | `D0101C98C7DAB68AA8EB16B78D7277ACD8849B088511BB2C3C4975025EC98564` |
| نقش در v2 | مرجع [1] یا `Rublein2022` |

### شواهد کامل‌بودن

- صفحه اول شامل عنوان، تمام نویسندگان، abstract، DOI و آغاز Introduction است.
- شماره‌گذاری صفحات PDF از 1 تا 10 پیوسته است.
- صفحه 10 شامل ادامه Related Work، Section VII Conclusion، Acknowledgment و فهرست References کامل تا مرجع [17] است.
- PDF بدون encryption، form یا JavaScript است و تمام صفحات توسط parser خوانده شدند.
- عنوان، نویسندگان و DOI metadata با محتوای صفحه اول یکسان‌اند.

## 3. مشخصات فایل `4.pdf`

| ویژگی | مقدار |
| --- | --- |
| عنوان | *Online Resource Allocation in Edge Computing Using Distributed Bidding Approaches* |
| نویسندگان | Caroline Rublein؛ Fidan Mehmeti؛ Mark Towers؛ Sebastian Stein؛ Thomas F. La Porta |
| محل انتشار | 2021 IEEE 18th International Conference on Mobile Ad Hoc and Smart Systems، MASS 2021 |
| DOI | `10.1109/MASS52906.2021.00038` |
| تعداد صفحات PDF | 9 |
| صفحات چاپی | 225 تا 233 |
| اندازه صفحه | Letter، `612×792 pt` |
| رمزگذاری | ندارد |
| اندازه فایل | 338,383 بایت |
| SHA-256 | `C7ACD2298E56B408A9659599F98144FD809B32631EEC94B835B7E5CF4DB2FE7D` |
| نقش در v2 | مرجع [4] یا `Rublein2021` |

### شواهد کامل‌بودن

- صفحه اول دارای عنوان، نویسندگان، abstract، DOI و شماره چاپی 225 است.
- صفحات چاپی به‌طور پیوسته از 225 تا 233 ادامه دارند.
- صفحه 233 شامل پایان Section VIII Conclusion، Acknowledgment و References کامل تا مرجع [15] است.
- PDF بدون encryption، form یا JavaScript است و هر 9 صفحه توسط parser خوانده شد.
- عنوان، نویسندگان و DOI metadata با صفحه اول منطبق‌اند.

## 4. نکات فنی ممیزی

- Poppler هنگام رندر درباره نبود display font محلی برای `Symbol` و `ArialUnicode` هشدار داد؛ با این حال صفحه‌های اول و آخر هر دو فایل خوانا بودند و نقص بصری یا حذف محتوا دیده نشد.
- عبارت IEEE Xplore درباره محدودیت استفاده در footer نشان‌دهنده نسخه ناشر است و نشانه ناقص‌بودن فایل نیست.
- `pdfinfo` در این محیط اندازه فایل را برای مسیر Unicode صفر گزارش کرد؛ اندازه واقعی با filesystem و SHA-256 مستقل محاسبه شد.

## 5. حدود استفاده در بازتولید

- `[استخراج مستقیم]` `1.pdf` منبع مستقیم تعریف Clustering، نسخه پیشین Preemption، تنظیمات trace و baseline Double Knapsack است.
- `[استخراج مستقیم]` Table III در `1.pdf` Utility گروه‌های trace را به‌صورت High=`N(100,10)`، Medium=`N(40,10)` و Low=`N(20,4)` گزارش می‌کند.
- `[استخراج مستقیم]` `4.pdf` منبع مستقیم Double Knapsack، pricing و ساختار مزایده پایه است.
- تنظیمات آزمایش این دو مقاله فقط وقتی به بازتولید v2 منتقل می‌شوند که v2 صریحاً همان workload یا روش را ارجاع داده باشد. سایر مقادیر آن‌ها نباید خودکار به آزمایش v2 نسبت داده شوند.

## 6. اطلاعاتی که این فایل‌ها تأمین نمی‌کنند

- کد رسمی مورد استفاده v2
- داده خام Southampton
- seedهای اجرای v2
- تعداد تکرارهای آزمایش v2
- نسخه و تنظیمات کامل Gurobi در v2
- سخت‌افزار اجرای آزمایش‌های v2
- داده عددی پشت شکل‌های v2

نتیجه: هر دو فایل منابع صحیح و کامل [1] و [4] هستند و می‌توان آن‌ها را در جایگاه منابع مستقیم مقاله استفاده کرد، ولی فایل تکمیلی، کد یا داده خام محسوب نمی‌شوند.
