# Stage 15-K.1 — ممیزی امنیتی پیش از انتشار

## دامنه

این ممیزی فقط فایل‌های کد، آزمون، workflow، fixture پاک‌سازی‌شده و مستندات
Stage 15-K/K.1 را پوشش می‌دهد. تغییر قبلی `.gitignore` و پوشه‌های
`.pytest-full-stage13i/` و `.pytest-stage13i/` خارج از دامنه و دست‌نخورده‌اند.

## نتیجه اسکن

- secret، credential، token واقعی، private key و مقدار Bearer: یافت نشد؛
- مسیر شخصی Windows یا مسیر home کاربر: یافت نشد؛
- `.env`، PDF، archive، raw workload، task trace و chromosome: در فهرست انتشار نیست؛
- workflow هیچ `secrets.*` ندارد و فقط `contents: read` دارد؛
- `actions: read` لازم نیست، زیرا baseline و repair قبلی از fixtureهای
  checksum-pinned مخزن خوانده می‌شوند و artifact قبلی دانلود نمی‌شود؛
- هر سه Action با SHA کامل چهل‌رقمی pin شده‌اند؛
- artifact عمومی flagهای حذف Task ID، chromosome، raw workload و raw trace را
  fail-fast کنترل می‌کند؛
- validator عمداً امضای رشته‌های حساس مانند `github_pat_` و `C:\Users\` را
  به‌عنوان الگوی ممنوعه در کد خود نگه می‌دارد؛ این رشته‌ها detector هستند و
  credential یا مسیر واقعی محسوب نمی‌شوند.

## ورودی‌های reuse

- config با SHA-256 نرمال‌شده LF برابر
  `b0ae2597119fb5ee3a27b2998d27e252b5d66e67356408abb7315238056f1963`؛
- baseline fixture با SHA-256 نرمال‌شده LF برابر
  `5a76406da63fdcb853a5cb04d57e0a3e0bc41d6dac94b90b39e562ce686bc3ca`؛
- prior-repair fixture با SHA-256 نرمال‌شده LF برابر
  `06eec52a4d346cb6014b8cd29e73323659a5c72c4e8ac86e81dac57932a25c12`؛
- baseline diagnostic fixture با SHA-256 نرمال‌شده LF برابر
  `eba441a8d23461a8ba0ad02d03432c04b5a2b03529102e0f2f61e3ac68de90b0`.

fixture تشخیصی جدید فقط شمارنده‌های aggregate، hashها، seedهای مصوب و funnel
پاک‌سازی‌شده Stage 15-B را نگه می‌دارد؛ Task ID، workload خام و trace ندارد.

## آزمون‌های پیش از انتشار

- آزمون مستقیم Stage 15-K.1: 16/16 موفق؛
- مجموعه رگرسیون Stage 15-D/E/H/K.1: 49/49 موفق؛
- Ruff: موفق؛
- mypy روی چهار فایل اصلی: موفق؛
- `git diff --check`: موفق؛ هشدار line-ending فقط مربوط به `.gitignore`
  خارج از دامنه بود.

یک اجرای اولیه مجموعه رگرسیون در collection به‌علت نبود `scripts` در
`PYTHONPATH` شکست خورد. اجرای مجدد با محیط موردانتظار پروژه 49/49 موفق شد؛ این
خطا پیش از اجرای آزمون و نامرتبط با منطق علمی بود.

## نتیجه

فهرست انتشار از نظر امنیتی مجاز است. هیچ داده خام یا artifact حجیم commit
نمی‌شود و هیچ مجوز، secret یا credential جدید لازم نیست.
