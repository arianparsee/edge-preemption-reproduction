# Stage 15-G — بازسازی مفهومی Figure 1

## 1. منبع و دامنه

- منبع مبنا: **arXiv:2403.15665v2 (2024)**، صفحه PDF 3، بخش III (`SYSTEM
  OVERVIEW`) و Figure 1.
- caption `[صریح در مقاله]`: “The arrival of jobs, along with the bidding and processing
  procedures.”
- متن ارجاع‌دهنده `[صریح در مقاله]`: الگوریتم تخصیص دو فاز `bidding` و `processing`
  دارد؛ پس از پایان bidding یک job set، processing آن آغاز می‌شود. وظایف پذیرفته‌شده
  در bid epoch 1 در epoch 2 پردازش را آغاز می‌کنند. وظایف ورودی epoch 2 در epoch 3
  bidding و در epoch 4 processing را آغاز می‌کنند.
- خود مقاله می‌گوید Figure 1 برای convenience از مرجع [1] بازنشر شده است. در این
  پروژه هیچ عنصر گرافیکی آن کپی نشده و فقط ساختار علمی از نو رسم شده است.
- هیچ workload، simulator، policy، seed یا آزمایش عددی در Stage 15-G اجرا نشد و وضعیت
  رسمی Figure 6 همچنان «بازتولید نشد» است.

## 2. استخراج اجزا و سلسله‌مراتب

| سطح | اجزا | وضعیت منبع |
|---|---|---|
| ردیف‌های زمانی | `Epoch`، `Arrivals`، `Bidding`، `Processing` | `[صریح در مقاله]` |
| بازه‌های نمایش‌داده‌شده | epochهای `0`، `1` و `2` با مرزهای عمودی | `[صریح در مقاله]` |
| گروه‌های مزایده | `Job set 1` و `Job set 2` | `[صریح در مقاله]` |
| خروجی مزایده | شاخه‌های `Allocated` و `Rejected` برای هر job set | `[صریح در مقاله]` |
| پردازش | `Accepted jobs at Epoch 1` و پیکان ادامه پردازش | برچسب `[صریح در مقاله]`؛ طول دقیق `[نامشخص]` |
| ادامه timeline | نقاط و مرز سمت راست بدون شماره epoch | وجود `[صریح در مقاله]`؛ شماره و دامنه `[نامشخص]` |

ساختار مرجع یک timeline است، نه نمودار معماری شبکه. بنابراین server، client، packet،
upload/download stage، preemption و Round 1/Round 2 به شکل افزوده نشده‌اند؛ این مفاهیم
در متن بخش III آمده‌اند ولی در Figure 1 به‌صورت جزء یا مسیر مجزا نمایش داده نمی‌شوند.

## 3. روابط و جهت پیکان‌ها

| رابطه | جهت | منشأ |
|---|---|---|
| arrival epoch 0 → `Job set 1` در epoch 1 | پایین-راست | `[استخراج مستقیم]` از شکل و قاعده متن |
| arrival epoch 1 → `Job set 2` در epoch 2 | پایین-راست | `[صریح در مقاله]`/شکل |
| arrival epoch 2 → bidding آینده | پایین-راست | `[استخراج مستقیم]` از ادامه الگو |
| هر `Job set` → `Allocated` | رو به پایین | `[صریح در مقاله]` |
| هر `Job set` → `Rejected` | پایین-راست | `[صریح در مقاله]` |
| `Rejected` در epoch 1 → `Job set 2` | بالا-راست | `[صریح در مقاله]`: امکان resubmit در bidding بعدی |
| `Rejected` در epoch 2 → bidding آینده | بالا-راست | `[صریح در مقاله]`/ادامه الگو |
| `Allocated` در epoch 1 → processing در epoch 2 | پایین-راست | `[صریح در مقاله]` |
| `Allocated` در epoch 2 → processing آینده | پایین-راست | `[استخراج مستقیم]` از تکرار قاعده |
| processing پذیرفته‌های epoch 1 → ادامه زمان | راست | وجود پیکان `[صریح در مقاله]`؛ طول `[نامشخص]` |

فهرست دقیق 37 جزء، شامل 12 رابطه جهت‌دار، در JSON و CSV machine-readable نگهداری
می‌شود. هر سطر برچسب شواهد، محل منبع، تفسیر، مختصات و endpointهای رابطه را دارد.

## 4. موارد نامشخص و تصمیم‌های گرافیکی

- `[نامشخص]` تعداد نقطه‌های هر خوشه arrival چه معنای کمی دارد؛ تعداد نقطه‌ها فقط
  motif نمادین شکل است و به workload size تعبیر نشده است.
- `[نامشخص]` شماره epoch و معنای دقیق نقاط ادامه سمت راست.
- `[نامشخص]` طول واقعی پردازش و محل پایان پیکان افقی.
- `[نامشخص]` آیا همه rejectedها بازمی‌گردند؛ متن فقط می‌گوید client «may choose» به
  resubmit. پیکان شکل امکان بازگشت را نشان می‌دهد، نه تضمین آن را.
- `[پیشنهاد فنی]` بوم landscape بزرگ‌تر، فونت DejaVu Sans، ضخامت خطوط، فاصله‌ها،
  مختصات و رنگ آبی/قرمز epochهای 1/2 برای خوانایی‌اند و معنای الگوریتمی ندارند.
- `[پیشنهاد فنی]` پس‌زمینه سفید زیر برچسب processing مانع عبور بصری مرز epoch از متن
  می‌شود؛ توپولوژی پیکان‌ها را تغییر نمی‌دهد.

## 5. مقایسه شکل اصلی و بازسازی

| معیار | Figure 1 مقاله | بازسازی Stage 15-G | نتیجه |
|---|---|---|---|
| ساختار | timeline چهارردیفه | همان چهار ردیف و ترتیب | منطبق ساختاری |
| epochها | 0، 1، 2 و ادامه بدون شماره | همان | منطبق |
| اجزا | arrivals، دو job set، allocated/rejected، processing | همان اجزای معنایی | منطبق |
| روابط | arrival→bid، دو outcome، retry، allocation→processing، continuation | همان 12 رابطه جهت‌دار | منطبق توپولوژیک |
| متن | برچسب‌های انگلیسی کوتاه | همان برچسب‌ها؛ footer منشأ افزوده شده | footer `[پیشنهاد فنی]` |
| ظاهر | raster کوچک سیاه/سفید با accent محدود | برداری، فاصله بیشتر و accent آبی/قرمز | عمداً پیکسل‌به‌پیکسل نیست |
| اطلاعات کمی | هیچ مقدار آزمایشی ندارد | هیچ مقدار یا مسیر جدید افزوده نشده | منطبق |

## 6. خروجی‌ها و بازتولید

- `scripts/reproduce_figure1.py`: منبع واحد inventory، SVG/PDF/PNG و manifest.
- `figures/stage15g/figure1_reconstructed.svg`: نسخه برداری قابل‌ویرایش؛ textها به‌صورت
  `<text>` حفظ شده و metadata روابط درون SVG قرار دارد.
- `figures/stage15g/figure1_reconstructed.pdf`: خروجی برداری یک‌صفحه‌ای.
- `figures/stage15g/figure1_reconstructed.png`: خروجی raster با ابعاد `2640×1232`.
- `results/aggregated/stage15g/figure1_inventory.{json,csv}`: inventory اجزا/روابط.
- `results/aggregated/stage15g/manifest.json`: اندازه و SHA-256 خروجی‌ها.

فرمان بازتولید:

```powershell
.\.venv\Scripts\python.exe scripts\reproduce_figure1.py --project-root .
```

## 7. اعتبارسنجی و سطح بازتولید

- آزمون topology، endpointها، evidence labelها، ابعاد بوم و عدم هم‌مرکزی labelها اجرا شد.
- SVG از نظر وجود text editable، metadata و `viewBox` بررسی شد.
- PDF با Poppler دوباره به PNG رندر و بصری بررسی شد؛ متن PDF نیز مستقل استخراج شد.
- SVG با renderer مستقل Sharp به PNG رندر و بصری بررسی شد.
- PNG اصلی با رزولوشن واقعی بررسی شد؛ بریدگی، متن ناخوانا یا هم‌پوشانی باقی نماند.
- تولید دوباره پنج artifact اصلی SHA-256 یکسان داد.

سطح نتیجه: **بازتولید ساختاری/مفهومی کامل** برای اجزا و روابط قابل مشاهده؛ نه بازتولید
پیکسل‌به‌پیکسل و نه نتیجه آزمایشی. ابهام‌های continuation، dot count و duration مانع
ادعای وفاداری بصری/کمی کامل‌اند.
