# Stage 15-C - ممیزی امنیتی پیش از انتشار

## سیاست انتشار

- فقط کد، آزمون، workflow و مستندات UTF-8 کوچک منتشر می‌شوند.
- raw workload، result، task trace، chromosome bits، PDF، تصویر و artifact commit نمی‌شوند.
- workflow فقط `contents: read` دارد و هیچ secret یا credential جدیدی مصرف نمی‌کند.
- همه Actionها به SHA چهل‌رقمی pin شده‌اند.
- artifactهای تشخیصی JSON کمتر از 100000 بایت و با retention هفت‌روزه‌اند.
- artifact شامل task ID، chromosome bits، مسیر محلی یا raw workload نیست.

## نتیجه ممیزی پیش از push

نتیجه باید با `scripts/audit_stage15b_publication.py` روی مجموعه دقیق staged ثبت شود.
هر secret، token، private key، مسیر شخصی، `.env`، داده خام، PDF، binary یا فایل بزرگ موجب
fail-closed خواهد شد. فایل `.gitignore` تغییریافته کاربر و پوشه‌های pytest محلی خارج از
staging باقی می‌مانند.

## نتیجه واقعی

ممیزی پیش از staging با وضعیت `passed` روی 13 فایل انجام شد. مجموعه مجاز انتشار دقیقاً
شامل موارد زیر است:

- `.github/stage15c-dispatch`
- `.github/workflows/stage15c-dk-funnel.yml`
- `docs/stage15c_plan.md`
- `docs/stage15c_security_audit.md`
- `scripts/merge_stage15c_diagnostics.py`
- `scripts/run_stage15c_dk_funnel.py`
- `src/edge_reproduction/algorithms/genetic_knapsack.py`
- `src/edge_reproduction/diagnostics/__init__.py`
- `src/edge_reproduction/diagnostics/dk_funnel.py`
- `src/edge_reproduction/diagnostics/ga_instrumentation.py`
- `tests/unit/test_stage15c_dk_funnel.py`
- `tests/unit/test_stage15c_merge.py`
- `tests/unit/test_stage15c_workflow_security.py`

نتیجه scan: secret/token/private-key، credential، مسیر شخصی، `.env`، PDF، تصویر، archive،
raw data و فایل بزرگ‌تر از 500000 بایت یافت نشد. ممیزی باید پس از staging نیز روی همین
مجموعه تکرار شود و وجود هر فایل اضافه موجب توقف commit است.

## ممیزی پس از اجرای ابری

پس از موفقیت Run `31708325126`، فقط `docs/stage15c_report.md` به مجموعه انتشار افزوده شد.
ممیزی مستقل این گزارش `passed` بود. سه ZIP، چهار JSON استخراج‌شده و manifest پایدار داخل
`backups/` قرار دارند، توسط Git نادیده گرفته می‌شوند و وارد staging یا مخزن عمومی نمی‌شوند.
