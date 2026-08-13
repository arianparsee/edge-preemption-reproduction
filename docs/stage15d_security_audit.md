# Stage 15-D — ممیزی امنیتی پیش از انتشار

## نتیجه

- تاریخ: 2026-08-13
- وضعیت: **موفق**
- دامنه: فقط فایل‌های کد، آزمون، workflow، fixture تجمیعی پاک‌سازی‌شده و مستندات
  Stage 15-D
- فایل‌های ممیزی‌شده اولیه: 16
- secret/token/credential/private key: یافت نشد
- ارجاع به GitHub secrets در workflow: وجود ندارد
- مسیر شخصی مطلق Windows/Linux: یافت نشد
- `.env`، PDF، تصویر، archive یا فایل binary: وجود ندارد
- پوشه‌های raw data، results، figures، tmp، backups و `.venv`: در مجموعه انتشار نیستند
- فایل بزرگ‌تر از 500,000 بایت: وجود ندارد
- مجوز workflow: فقط `contents: read`
- Actionها: همگی با SHA کامل pin شده‌اند

گزارش ماشینی کامل در `tmp/stage15d_publication_audit.json` نگهداری می‌شود؛ این مسیر
gitignored است و commit نمی‌شود.

## فایل‌های مجاز برای انتشار

1. `.github/stage15d-dispatch`
2. `.github/workflows/stage15d-counterfactual.yml`
3. `docs/assumptions.md`
4. `docs/stage15d_counterfactual_design.md`
5. `docs/stage15d_rng_gate.md`
6. `docs/stage15d_security_audit.md`
7. `outputs/traceability_matrix_arxiv_v2.md`
8. `src/edge_reproduction/diagnostics/ga_counterfactual.py`
9. `src/edge_reproduction/diagnostics/ga_instrumentation.py`
10. `scripts/run_stage15d_counterfactual.py`
11. `scripts/merge_stage15d_counterfactuals.py`
12. `tests/fixtures/stage15d_stage15c_rng_guard.json`
13. `tests/unit/test_stage15d_counterfactual_selector.py`
14. `tests/unit/test_stage15d_runner.py`
15. `tests/unit/test_stage15d_merge.py`
16. `tests/unit/test_stage15d_workflow_security.py`
17. `tests/integration/test_stage15d_counterfactual_policies.py`

fixture مربوط به RNG فقط شمارنده‌ها و hashهای تجمیعی artifact معتبر Stage 15-C را
نگه می‌دارد؛ task ID، chromosome، workload یا trace خام در آن وجود ندارد.

## موارد عمداً خارج از انتشار

- تغییر قبلی و نامرتبط `.gitignore`؛
- `.pytest-full-stage13i/` و `.pytest-stage13i/`؛
- `tmp/stage15d_publication_audit.json`؛
- artifactهای Stage 15-C در `backups/`؛
- داده خام، نتیجه pairها و artifactهای دانلودشده آینده.

هیچ‌یک از موارد خارج از دامنه stage یا commit نمی‌شوند.
