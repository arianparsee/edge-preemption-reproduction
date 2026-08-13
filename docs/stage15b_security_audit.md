# Stage 15-B - گزارش ممیزی امنیتی پیش از انتشار

## نتیجه

وضعیت ممیزی مجموعه قابل‌انتشار: **موفق**.

- secret، credential، token و private key: یافت نشد.
- ارجاع به GitHub Actions secrets در workflow: وجود ندارد.
- مسیر شخصی Windows یا Linux: یافت نشد.
- فایل `.env`: وجود ندارد.
- داده خام، trace، `results/`، `data/` یا `figures/`: در مجموعه انتشار وجود ندارد.
- PDF، تصویر، archive، database یا فایل binary: وجود ندارد.
- فایل بزرگ‌تر از 500,000 بایت: وجود ندارد.
- metadata محیط محلی در artifact یا log عمومی تولید نمی‌شود.

PDF و CSVهای Stage 14-A/15-A فقط محلی باقی ماندند. commit محلی پیشین، پیش از push،
amend شد تا این فایل‌ها وارد تاریخچه عمومی نشوند؛ هیچ نسخه محلی حذف یا بازنویسی نشد.

## فایل‌های مجاز برای انتشار

| مسیر | اندازه (بایت) | SHA-256 پیش از commit |
| --- | ---: | --- |
| `.github/stage15b-dispatch` | 24 | `a439c95c83d54a36c9a9ca1edb6e55e478bf3d43a14f180676f0057a9d0f5525` |
| `.github/workflows/stage15b-ga-diagnostic.yml` | 6504 | `eceeea7be83b50ba9c252663ad8f18730325e316ff6f8172803ed1fa8eed350d` |
| `docs/stage13k_report.md` | 4715 | `f252bf3376e6509f712505af8becb4b48a132ecf6c3dd31f7cc7ebfef8de331f` |
| `docs/stage14a_figure6.md` | 1791 | `c8759f63f4bfefc731845c3cbc67cd227f9d01d53f160863bed6f3b6ba2749c7` |
| `docs/stage15a_dk_diagnostic.md` | 4461 | `dfd0bdf8e663725b39b6723afa7a1c86d852d9299300ba13283939484777311b` |
| `docs/stage15b_plan.md` | 1359 | `72eec0fe22f54b7c6ac592475199f484cf7b71a386175be4e1f91e6c410654d1` |
| `scripts/analyze_stage15a_dk_weakness.py` | 17967 | `5d98755aee207245c771173df09e2cdf1499da8b6a5a9e2da6d3405ef75f1367` |
| `scripts/audit_stage15b_publication.py` | 4161 | `916b0165236138a5d091506c695c485b32f5974ef1f584e1a8cb895ddaae4a3b` |
| `scripts/merge_stage15b_diagnostics.py` | 2262 | `a72645c1477ad66cae858f4085e64bbdae5097111a8d5151d0efe07baea436af` |
| `scripts/register_stage14a_figure6.py` | 9968 | `aa57918ed0c49d12e9a2552b9d007b3711c7188921b727b3aaf654798753b90c` |
| `scripts/run_stage15b_ga_diagnostic.py` | 7513 | `f48968417ad059ed3bcb527fb0a67a6580183443471d6f72834c528b77c3321a` |
| `scripts/stabilize_stage13k_artifacts.py` | 18181 | `a64e2b03fac835c2d038b7d6dc5da3774a6020c618b409b84bc61e1eea122d94` |
| `src/edge_reproduction/diagnostics/__init__.py` | 284 | `018d1c06e34f4beb4134465cfe799f69b90fca17e6cc69ebb46cf23cc8277116` |
| `src/edge_reproduction/diagnostics/ga_instrumentation.py` | 7814 | `31e6230bcddc56ebce58de41264bc02162342230f4c3ee0551f8ec2cf0e8832c` |
| `tests/fixtures/stage15b_baseline_fingerprints.json` | 2233 | `49a27106b74854cb1f76583575d15f6092f763285ac525238bff657aee6766c9` |
| `tests/unit/test_stage14a_stage15a_reporting.py` | 3721 | `9bdef02e567d0ae674e414ec59967ef8b5e740632c6318d3c3fdf249168cfcba` |
| `tests/unit/test_stage15b_ga_instrumentation.py` | 2998 | `a54ab820185337b05a7dae298f6d50aa2d6676596c176b23cf06dec4f31487fe` |
| `tests/unit/test_stage15b_publication_audit.py` | 1660 | `a883192723864f07ed4a76f45789ce96e685e9cd242256de5eaa7e6020052bf0` |
| `tests/unit/test_stage15b_workflow_security.py` | 1195 | `ba917292348727958e8eadf4cc8983c8b8399bc89f895a7bd6d8421ad516940d` |

خود این گزارش نیز پیش از commit با همان قواعد اسکن می‌شود. artifact ابری فقط JSON
تجمیعی تشخیصی با retention هفت‌روزه است و raw result یا workload را شامل نمی‌شود.
