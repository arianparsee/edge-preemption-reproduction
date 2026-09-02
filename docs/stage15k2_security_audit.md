# Stage 15-K.2 — ممیزی امنیتی و دامنه پیش از dispatch

## دامنه انتشار

فایل‌های مجاز شامل پیاده‌سازی observer aggregate، runner/validator/finalizer،
workflow محدود، fixture reuse پاک‌سازی‌شده، آزمون‌ها و اسناد Stage 15-K.2
هستند. داده خام، artifact حجیم، workload، Task ID، chromosome و trace در
commit قرار نمی‌گیرند.

Fixture reuse هشت pair از archive پایدار و معتبر Stage 15-E ساخته شده است.
هر فایل منبع با manifest محلی `validated_20_of_20` و SHA-256 همان فایل کنترل
شد؛ fixture فقط fingerprint، hash، funnel و شمارنده‌های aggregate را نگه
می‌دارد و simulation جدیدی اجرا نمی‌کند.

## وابستگی و مجوز workflow

- matrix دقیقاً چهار seed جدید × DK-R/DK-P است؛ seed اول در matrix نیست؛
- هر logical pair دو replay در همان job دارد؛
- artifact seed اول فقط از repository فعلی، Run `33663692202` و نام pin‌شده
  دریافت می‌شود؛ SHA-256 دو result در finalizer کنترل می‌شود؛
- workflow فقط `contents: read` و `actions: read` دارد؛
- هیچ `secrets.*` یا credential جدید وجود ندارد؛
- checkout/setup/download/upload همگی به SHA کامل pin شده‌اند؛
- timeout و retention صریح‌اند و baseline اجرا نمی‌شود.

## مرز انتشار عمومی

Validator هر artifact را از نظر replay، RNG، invariant، عدم recompute baseline
و نبود flagهای raw بررسی می‌کند. مشاهده‌گر فقط aggregate می‌نویسد و به state،
ترتیب policy یا RNG دست نمی‌زند. seed اول فاقد diagnostic جدید است و این کمبود
صریحاً در final report ثبت می‌شود، نه اینکه از داده دیگر بازسازی شود.

## نتیجه آزمون پیش از dispatch

- 25 آزمون مستقیم و مرتبط اولیه: موفق؛
- 68 آزمون رگرسیون Stage 15-D/E/H/K.1/K.2: موفق؛
- Ruff روی فایل‌های جدید: موفق؛
- mypy strict روی فایل‌های جدید: موفق؛
- `git diff --check`: موفق؛
- هیچ workload رسمی به‌صورت محلی اجرا نشد.

ممیزی نهایی staged diff و secret/path/large-file scan باید بلافاصله پیش از
commit و push دوباره اجرا و نتیجه آن در گزارش dispatch ثبت شود.
