# Stage 15-K.1 — ممیزی امنیتی پیش از انتشار

## دامنه

این ممیزی فقط فایل‌های کد، آزمون، workflow، fixture پاک‌سازی‌شده و مستندات
Stage 15-K/K.1 را روی شاخه تمیز `codex/stage15k1-clean` پوشش می‌دهد. شاخه
مستقیماً از `origin/main` در commit `90b53c9` ساخته شد. cherry-pick متعارض
لغو و فقط patchهای Stage 15-K/K.1 منتقل شدند؛ هیچ commit، workflow، recovery
یا aggregation مربوط به Stage 15-H/15-I وارد شاخه نشد.

## فهرست انتشار و ضرورت هر فایل

| فایل | ضرورت |
|---|---|
| `.github/workflows/stage15k1-r2-initialization-repair.yml` | اجرای محدود دو policy و دو replay در GitHub |
| `docs/assumptions.md` | ثبت وضعیت ASSUMP-048/049 و غیرفعال‌بودن 050–053 |
| `docs/stage15k1_pilot_plan.md` | ثبت دامنه، گیت‌ها و شرط توقف Pilot |
| `docs/stage15k1_security_audit.md` | ثبت ممیزی دامنه، dependency و امنیت |
| `docs/stage15k_candidate_corrections.md` | ثبت گزینه‌های اصلاحی تأییدنشده Stage 15-K |
| `docs/stage15k_strictness_audit.md` | ممیزی شواهد سخت‌گیری‌های بازتولید |
| `outputs/traceability_matrix_arxiv_v2.md` | ردیابی Stage 15-K/K.1 بدون تغییر ردیف‌های قبلی |
| `scripts/run_stage15k1_pilot.py` | اجرای دو replay و گیت علمی/RNG برای ASSUMP-049 |
| `scripts/validate_stage15k1_public_pair.py` | اعتبارسنجی schema و پاک‌سازی artifact عمومی |
| `src/edge_reproduction/diagnostics/ga_counterfactual.py` | variant مستقل R2-only و repair بدون draw اضافه |
| `src/edge_reproduction/diagnostics/ga_instrumentation.py` | انتقال فقط context دور و پذیرش مقدار `stage15k1` |
| `tests/fixtures/stage15k1_baseline_diagnostics.json` | شواهد aggregate و checksum-pinned baseline بدون Task ID |
| `tests/integration/test_stage15d_counterfactual_policies.py` | کنترل replay variant جدید در هر دو policy |
| `tests/unit/test_stage15k1_runner.py` | کنترل reuse، checksum و retry فنی محدود |
| `tests/unit/test_stage15k1_selector.py` | کنترل Round 1 ثابت و RNG repair فقط در Round 2 |
| `tests/unit/test_stage15k1_workflow_security.py` | کنترل matrix، مجوز، pin، scope و عدم اجرای baseline |

## بسته‌شدن وابستگی‌ها

تمام importها، CLI inputها، config و fixtureهای runner روی `origin/main` موجود
بودند. `run_stage15b_ga_diagnostic.py`، `run_stage15d_counterfactual.py`، config
Stage 13-F، دو fixture Stage 15-E و ماژول‌های GA/pipeline مستقیماً import شدند.
workflow هیچ artifact قدیمی را دانلود نمی‌کند و به workflow یا recovery مسیر
Stage 15-H/15-I وابسته نیست. در instrumentation فقط `stage15k1` اضافه شد؛
`stage15h` عمداً منتقل نشد.

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
- import و dependency closure در worktree تمیز: موفق؛
- static workflow validation، matrix دو policy، دو replay و عدم اجرای baseline:
  موفق؛
- RNG Option-A و عدم repair در Round 1: موفق؛
- Ruff: موفق؛
- mypy روی چهار فایل اصلی: موفق؛
- `git diff --check`: موفق و بدون هشدار.

## نتیجه

فهرست انتشار از نظر امنیتی مجاز است. هیچ داده خام یا artifact حجیم commit
نمی‌شود و هیچ مجوز، secret یا credential جدید لازم نیست.
