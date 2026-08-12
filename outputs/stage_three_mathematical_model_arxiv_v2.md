# مرحله سوم: استخراج کامل مدل ریاضی

## 1. دامنه و روش استخراج

- منبع مبنا: `arXiv:2403.15665v2`، صفحات 4 و 5، Section IV.
- روابط از `main.tex` رسمی arXiv استخراج و با رندر PDF تطبیق داده شدند.
- نسخه 2025 در این تحلیل استفاده نشده است.
- مدل مقاله یک MINLP متمرکز و oracle برای pipeline processing است؛ heuristic آنلاین Section V مدل دیگری است.
- هیچ `[فرض بازتولید]` در این مرحله اعمال نشده است.

## 2. ماهیت مدل

`[صریح در مقاله]` یک entity متمرکز تمام مشخصات سرورها، jobها و arrivalهای آینده را می‌داند. هدف، بیشینه‌کردن Utility کل jobهایی است که تا پایان اجرا می‌شوند. مدل دارای:

- assignment دودویی؛
- allocation پیوسته upload/computation/download در هر slot؛
- متغیر دودویی preemption/completion؛
- متغیرهای زمانی مراحل job؛
- حاصل‌ضرب متغیرها و قیود نسبت؛
- و در نتیجه ساختار Mixed-Integer Non-Linear Program است.

## 3. جدول نمادها

### 3.1 مجموعه‌ها و اندیس‌ها

| نماد | تعریف | نوع | دامنه | واحد | محل ذکر | کاربرد در کد آینده |
| --- | --- | --- | --- | --- | --- | --- |
| `I` | مجموعه serverها | مجموعه | محدود | ندارد | صفحه 4 | `[پیشنهاد فنی] Server collection` |
| `J` | مجموعه jobها | مجموعه | محدود | ندارد | صفحه 4 | `[پیشنهاد فنی] Task collection` |
| `N` | مجموعه slotهای افق زمانی | مجموعه مرتب | محدود | slot | صفحه 4 | `[پیشنهاد فنی] TimeHorizon` |
| `i` | اندیس server | اندیس | `i∈I` | ندارد | روابط متعدد | `[پیشنهاد فنی] server_id` |
| `j` | اندیس job | اندیس | `j∈J` | ندارد | روابط متعدد | `[پیشنهاد فنی] task_id` |
| `n` | slot جاری | اندیس زمانی | `n∈N` | slot | روابط (9)، (10)، (15)-(18) | `[پیشنهاد فنی] slot` |
| `l_j` | اندیس جمع زمانی برای job j | اندیس زمانی | 1 تا افق/slot جاری | slot | روابط (2)-(10)، (15) | `[پیشنهاد فنی] progress_slot` |

### 3.2 پارامترها

| نماد | تعریف | نوع | دامنه | واحد | محل ذکر | کاربرد در کد آینده |
| --- | --- | --- | --- | --- | --- | --- |
| `a_j` | arrival time وظیفه j | صحیح موردانتظار | داخل افق | slot | صفحه 4 | `[پیشنهاد فنی] Task.arrival_slot` |
| `d_j` | deadline نسبی پس از arrival | صحیح موردانتظار | مثبت | slot | صفحه 4 | `[پیشنهاد فنی] Task.deadline_slots` |
| `U_j` | Utility در صورت completion تا deadline | حقیقی | احتمالاً نامنفی | utility unit | صفحه 4 | `[پیشنهاد فنی] Task.utility` |
| `s_j` | نیاز storage/حجم داده ورودی | حقیقی | باید مثبت باشد | MB | صفحه 4 | `[پیشنهاد فنی] Task.input_size_mb` |
| `s'_j` | اندازه result data | حقیقی | باید مثبت باشد | `[نامشخص]` | فقط روابط (6)-(10) | `[پیشنهاد فنی] Task.output_size_mb` |
| `K_j` | نیاز محاسباتی کل | حقیقی | باید مثبت باشد | MFlops | صفحه 4 | `[پیشنهاد فنی] Task.compute_mflops` |
| `S_i` | ظرفیت storage server | حقیقی | نامنفی | GB در متن؛ MB در Table I | صفحه 4 | `[پیشنهاد فنی] Server.storage_capacity_mb` |
| `C_i` | ظرفیت computation server در هر slot | حقیقی | نامنفی | MFlops/s در متن | صفحه 4 | `[پیشنهاد فنی] Server.compute_per_slot` |
| `B_{u,i}` | ظرفیت upload server در هر slot | حقیقی | نامنفی | data/slot | صفحه 4 | `[پیشنهاد فنی] Server.upload_per_slot` |
| `B_{d,i}` | ظرفیت download server در هر slot | حقیقی | نامنفی | data/slot | صفحه 4 | `[پیشنهاد فنی] Server.download_per_slot` |

`[نامشخص]` مقاله دامنه پارامترها را رسماً اعلام نکرده است. مثبت‌بودن `s_j`، `s'_j` و `K_j` برای جلوگیری از تقسیم بر صفر در (8)-(10) ضروری است، اما قید صریح ندارد.

### 3.3 متغیرهای تصمیم و متغیر مشتق

| نماد | تعریف | نوع | دامنه | واحد | محل ذکر | کاربرد در کد آینده |
| --- | --- | --- | --- | --- | --- | --- |
| `x_{i,j}` | 1 اگر job j به server i تخصیص یابد | تصمیم دودویی | `{0,1}` | ندارد | متن و (20) | `[پیشنهاد فنی] assignment[i,j]` |
| `σ_j(n)` | مقدار داده uploadشده در slot n | تصمیم پیوسته | نامنفی در window؛ صفر بیرون | data/slot | متن، (22)-(23) | `[پیشنهاد فنی] upload[j,n]` |
| `κ_j(n)` | computation رزروشده در slot n | تصمیم پیوسته | نامنفی در window؛ صفر بیرون | computation/slot | متن، (24)-(25) | `[پیشنهاد فنی] compute[j,n]` |
| `σ'_j(n)` | result data ارسال‌شده در slot n | تصمیم پیوسته | نامنفی در window؛ صفر بیرون | data/slot | متن، (26)-(27) | `[پیشنهاد فنی] download[j,n]` |
| `τ_j` | 0 اگر preempted؛ 1 اگر run-to-end | تصمیم دودویی | `{0,1}` | ندارد | متن و (21) | `[پیشنهاد فنی] completed[j]` |
| `d_{j,u}` | span/offset پایان upload | تصمیم زمانی | حداقل 1؛ integrality صریح نیست | slot | متن، (11)-(12) | `[پیشنهاد فنی] upload_end_offset[j]` |
| `d_{j,p}` | span/offset پایان processing | تصمیم زمانی | حداقل 1؛ integrality صریح نیست | slot | متن، (11)، (13) | `[پیشنهاد فنی] compute_end_offset[j]` |
| `d_{j,d}` | span/offset پایان download | تصمیم زمانی | حداقل 1؛ integrality صریح نیست | slot | متن، (11)، (14) | `[پیشنهاد فنی] download_end_offset[j]` |
| `d_{j,t}` | slot-count/offset توقف بر اثر preemption | تصمیم زمانی | `{1,…,d_{j,d}}` | slot | متن، (28) | `[پیشنهاد فنی] stop_offset[j]` |
| `θ_j(n)` | نشانگر اشغال storage براساس بازه computation مثبت | مشتق/indicator | `{0,1}` در تعریف | ندارد | (31) | `[پیشنهاد فنی] storage_active[j,n]` |

`[ناسازگاری]` متن `τ_j` را ابتدا «parameter» می‌نامد، اما سپس آن را decision variable می‌داند و دامنه دودویی برای آن می‌گذارد. از ساختار مدل روشن است که متغیر تصمیم است.

## 4. مثال عددی مشترک

برای توضیح روابط، مثال زیر فقط `[آزمون کمکی]` است و به مقاله نسبت داده نمی‌شود:

- یک server و یک job؛ `N={1,2,3,4}`؛
- `a=1`, `d=4`, `U=10`, `s=4 MB`, `s'=2 MB`, `K=8 MFlops`؛
- `S=10 MB`, `C=4`, `B_u=2`, `B_d=1`؛
- `x=1`, `τ=1`, `d_u=2`, `d_p=3`, `d_d=d_t=4`؛
- allocation:

| slot | `σ(n)` upload | `κ(n)` compute | `σ'(n)` download |
| ---: | ---: | ---: | ---: |
| 1 | 2 | 0 | 0 |
| 2 | 2 | 4 | 0 |
| 3 | 0 | 4 | 1 |
| 4 | 0 | 0 | 1 |

مثال preemption کمکی: `τ=0`, `d_t=3<d_d=4` و download تجمعی `1<2`.

## 5. تحلیل تک‌تک روابط

### رابطه (1): تابع هدف

$$
\max \sum_{i=1}^{\lvert\mathcal I\rvert}\sum_{j=1}^{\lvert\mathcal J\rvert} U_j\tau_jx_{i,j}
$$

- نمادها: `U_j` Utility، `τ_j` completion/preemption، `x_{i,j}` assignment.
- مفهوم: `[صریح در مقاله]` بیشینه‌کردن Utility کل jobهای assigned و run-to-end.
- کد آینده: `[پیشنهاد فنی] compute_total_utility()` و `build_objective()`.
- شرط مرزی: unassigned یا `τ=0` سهم صفر دارد؛ assignment چندسروری با (19) منع می‌شود.
- مثال: `10×1×1=10`.
- آزمون: completed، preempted و unassigned را با جمع دستی مقایسه کند.

### رابطه (2): سقف upload کل

$$
\sum_{l_j=1}^{\lvert\mathcal N\rvert}\sigma_j(l_j)\le s_jx_{i,j},\qquad \forall i\in\mathcal I,\forall j\in\mathcal J
$$

- نمادها: `σ_j` upload، `s_j` input size، `x_{i,j}` assignment.
- مفهوم اعلامی: upload از کل input بیشتر نشود و job غیرassigned upload نکند.
- کد آینده: `[پیشنهاد فنی] check_upload_upper_bound()`.
- شرط مرزی: `x=0 ⇒ Σσ=0`؛ در چندسروری quantifier فعلی مشکل اساسی دارد.
- مثال تک‌سروری: `4≤4`.
- آزمون: exact/under/over upload و آزمون دو server که خطای quantifier را آشکار کند.

### رابطه (3): الزام upload کامل برای completion

$$
\tau_j\left(\sum_{l_j=1}^{\lvert\mathcal N\rvert}\sigma_j(l_j)-s_jx_{i,j}\right)=0,
\qquad \forall i\in\mathcal I,\forall j\in\mathcal J
$$

- نمادها: همان (2) به‌اضافه `τ_j`.
- مفهوم: اگر `τ=1`، upload باید کامل باشد؛ اگر `τ=0` قید آزاد می‌شود.
- کد آینده: `[پیشنهاد فنی] check_completed_upload()`.
- شرط مرزی: completion با upload ناقص نامعتبر؛ preempted می‌تواند partial upload داشته باشد.
- مثال: `1×(4-4)=0`؛ برای preempted، `0×(2-4)=0`.
- آزمون: completed-incomplete باید fail؛ preempted-partial باید pass؛ multi-server quantifier test.

### رابطه (4): سقف computation کل

$$
\sum_{l_j=1}^{\lvert\mathcal N\rvert}\kappa_j(l_j)\le K_jx_{i,j},
\qquad \forall i\in\mathcal I,\forall j\in\mathcal J
$$

- نمادها: `κ_j` computation allocation، `K_j` total compute، `x` assignment.
- مفهوم: computation از requirement بیشتر نشود.
- کد آینده: `[پیشنهاد فنی] check_compute_upper_bound()`.
- شرط مرزی: `K_j=0` با روابط نسبتی ناسازگار است؛ باید مثبت باشد.
- مثال: `8≤8`.
- آزمون: zero assignment، exact compute، overcompute و multi-server quantifier.

### رابطه (5): computation کامل برای completion

$$
\tau_j\left(\sum_{l_j=1}^{\lvert\mathcal N\rvert}\kappa_j(l_j)-K_jx_{i,j}\right)=0,
\qquad \forall i\in\mathcal I,\forall j\in\mathcal J
$$

- نمادها: `τ`, `κ`, `K`, `x`.
- مفهوم: `τ=1` نیازمند processing کامل است؛ `τ=0` partial processing را مجاز می‌کند.
- کد آینده: `[پیشنهاد فنی] check_completed_compute()`.
- شرط مرزی: completion با یک واحد computation کم نامعتبر است.
- مثال: `1×(8-8)=0`.
- آزمون: completed exact/partial و preempted partial.

### رابطه (6): سقف download نتیجه

$$
\sum_{l_j=1}^{\lvert\mathcal N\rvert}\sigma'_j(l_j)\le s'_jx_{i,j},
\qquad \forall i\in\mathcal I,\forall j\in\mathcal J
$$

- نمادها: `σ'_j` download allocation، `s'_j` result size، `x` assignment.
- مفهوم: result data از کل result بیشتر نشود و unassigned job download نکند.
- کد آینده: `[پیشنهاد فنی] check_download_upper_bound()`.
- شرط مرزی: `s'_j` باید مثبت/تعریف‌شده باشد؛ quantifier چندسروری همان مشکل (2) را دارد.
- مثال: `2≤2`.
- آزمون: exact/over download، missing output size و multi-server.

### رابطه (7): download کامل برای completion

$$
\tau_j\left(\sum_{l_j=1}^{\lvert\mathcal N\rvert}\sigma'_j(l_j)-s'_j\right)=0,
\qquad \forall j\in\mathcal J
$$

- نمادها: `τ`, `σ'`, `s'`.
- مفهوم: job run-to-end باید تمام result data را به user برساند.
- کد آینده: `[پیشنهاد فنی] check_completed_download()`.
- شرط مرزی: `τ=0` download ناقص/حتی کامل را به‌تنهایی منع نمی‌کند؛ (8) completion کامل preempted را منع می‌کند.
- مثال: `1×(2-2)=0`.
- آزمون: completed partial fail؛ preempted partial pass؛ preempted complete باید توسط (8) fail شود.

### رابطه (8): preemption پیش از download صددرصد

$$
\frac{\sum_{l_j=1}^{\lvert\mathcal N\rvert}\sigma'_j(l_j)}{s'_j}<1+\tau_j,
\qquad \forall j\in\mathcal J
$$

- نمادها: fraction download و `τ`.
- مفهوم: اگر `τ=0`، fraction باید کمتر از 1 باشد؛ اگر `τ=1`، همراه (7) برابر 1 می‌شود.
- کد آینده: `[پیشنهاد فنی] check_preemption_before_full_download()`.
- شرط مرزی: strict inequality در Gurobi به شکل چاپ‌شده قابل ورود نیست؛ `s'_j=0` تقسیم بر صفر است.
- مثال completion: `2/2=1<2`؛ preemption: `1/2<1`.
- آزمون: preempted fraction=1 باید fail؛ fraction نزدیک 1 مسئله tolerance را آشکار کند.

### رابطه (9): تقدم upload بر computation در pipeline

$$
\sum_{l_j=1}^{n}\kappa_j(l_j)
\le
\frac{\sum_{l_j=1}^{n}\sigma_j(l_j)}{s_j}K_j,
\qquad \forall n\in\mathcal N,\forall j\in\mathcal J
$$

- نمادها: cumulative compute/upload و requirements `K`, `s`.
- مفهوم: درصد computation از درصد upload جلو نزند.
- کد آینده: `[پیشنهاد فنی] check_pipeline_upload_compute_ratio()`.
- شرط مرزی: `s_j>0` ضروری است؛ در n قبل arrival هر دو طرف صفرند.
- مثال در n=2: `4≤(4/4)×8=8`.
- آزمون: 60% upload/60% compute pass؛ 60% upload/61% compute fail.

### رابطه (10): تقدم computation بر download

$$
\sum_{l_j=1}^{n}\sigma'_j(l_j)
\le
\frac{\sum_{l_j=1}^{n}\kappa_j(l_j)}{K_j}s'_j,
\qquad \forall n\in\mathcal N,\forall j\in\mathcal J
$$

- نمادها: cumulative download/compute و `s'`, `K`.
- مفهوم: درصد download از درصد computation جلو نزند.
- کد آینده: `[پیشنهاد فنی] check_pipeline_compute_download_ratio()`.
- شرط مرزی: `K_j>0` ضروری است.
- مثال در n=3: `1≤(8/8)×2=2`.
- آزمون: 40% compute/40% download pass؛ download بیشتر fail.

### رابطه (11): ترتیب endpointهای مراحل

$$
d_{j,u}\le d_{j,p}\le d_{j,d}\le d_j,
\qquad \forall j\in\mathcal J
$$

- نمادها: endpoint/span مراحل و deadline.
- مفهوم: upload دیرتر از processing و processing دیرتر از download تمام نمی‌شود؛ equality در pipeline مجاز است.
- کد آینده: `[پیشنهاد فنی] check_stage_order()`.
- شرط مرزی: equality مجاز؛ integrality سه متغیر صریح نیست.
- مثال: `2≤3≤4≤4`.
- آزمون: ordered/equal/reversed endpoints.

### رابطه (12): حداقل upload span

$$d_{j,u}\ge1,\qquad\forall j\in\mathcal J$$

- مفهوم: upload حداقل یک slot.
- کد آینده: `[پیشنهاد فنی] check_upload_duration()`.
- مرزی/مثال: `d_u=1` کمینه و در window (23) دقیقاً یک slot فعال می‌دهد.
- آزمون: 0 fail، 1 pass.

### رابطه (13): حداقل processing span

$$d_{j,p}\ge1,\qquad\forall j\in\mathcal J$$

- مفهوم اعلامی: processing حداقل یک slot.
- کد آینده: `[پیشنهاد فنی] check_compute_duration()`.
- مرزی: با window (25)، `d_p=1` هیچ slot فعالی ایجاد نمی‌کند؛ ناسازگاری off-by-one.
- مثال مشترک: `d_p=3≥1`.
- آزمون: `d_p=1` باید ناسازگاری semantic/window را آشکار کند.

### رابطه (14): حداقل download span

$$d_{j,d}\ge1,\qquad\forall j\in\mathcal J$$

- مفهوم اعلامی: download حداقل یک slot.
- کد آینده: `[پیشنهاد فنی] check_download_duration()`.
- مرزی: با window (27)، `d_d=1` یا `2` window خالی می‌دهد.
- مثال: `d_d=4≥1`.
- آزمون: مقادیر 1، 2 و 3 را در برابر window بررسی کند.

### رابطه (15): ظرفیت storage

$$
\sum_{j=1}^{\lvert\mathcal J\rvert}\sum_{l_j=1}^{n}
\sigma_j(l_j)x_{i,j}\theta_j(n)\le S_i,
\qquad \forall i\in\mathcal I,\forall n\in\mathcal N
$$

- نمادها: cumulative upload، assignment، storage indicator و ظرفیت.
- مفهوم اعلامی: مجموع storage اشغال‌شده در هر server/slot از ظرفیت بیشتر نشود.
- کد آینده: `[پیشنهاد فنی] check_storage_capacity()`.
- مرزی: تفاوت واحد MB/GB؛ `θ=0` قبل/بعد computation storage را صفر حساب می‌کند؛ set خالی (31).
- مثال در n=2: `4×1×1=4≤10`.
- آزمون: چند job، conversion units، pre-compute upload و post-compute download.

### رابطه (16): ظرفیت computation

$$
\sum_{j=1}^{\lvert\mathcal J\rvert}\kappa_j(n)x_{i,j}\le C_i,
\qquad \forall i\in\mathcal I,\forall n\in\mathcal N
$$

- مفهوم: compute allocation هر server/slot از ظرفیت تجاوز نکند.
- کد آینده: `[پیشنهاد فنی] check_server_compute_capacity()`.
- مرزی: `C_i=0` فقط allocation صفر؛ واحد rate در برابر amount/slot مبهم است.
- مثال n=2: `4≤4`.
- آزمون: zero/exact/over capacity و چند job.

### رابطه (17): ظرفیت upload

$$
\sum_{j=1}^{\lvert\mathcal J\rvert}\sigma_j(n)x_{i,j}\le B_{u,i},
\qquad \forall i\in\mathcal I,\forall n\in\mathcal N
$$

- مفهوم: upload کل server در slot از ظرفیت تجاوز نکند.
- کد آینده: `[پیشنهاد فنی] check_server_upload_capacity()`.
- مرزی: slot duration باید در `B_u` لحاظ شده باشد.
- مثال n=1: `2≤2`.
- آزمون: exact/over و assignment به server دیگر.

### رابطه (18): ظرفیت download

$$
\sum_{j=1}^{\lvert\mathcal J\rvert}\sigma'_j(n)x_{i,j}\le B_{d,i},
\qquad \forall i\in\mathcal I,\forall n\in\mathcal N
$$

- مفهوم: download کل server در slot از ظرفیت تجاوز نکند.
- کد آینده: `[پیشنهاد فنی] check_server_download_capacity()`.
- مرزی: همان تبدیل rate×slot duration.
- مثال n=3: `1≤1`.
- آزمون: exact/over و simultaneous jobs.

### رابطه (19): حداکثر یک server برای هر job

$$
\sum_{i=1}^{\lvert\mathcal I\rvert}x_{i,j}\le1,
\qquad\forall j\in\mathcal J
$$

- مفهوم: job یا unassigned است یا فقط روی یک server قرار می‌گیرد.
- کد آینده: `[پیشنهاد فنی] check_single_server_assignment()`.
- مرزی: sum=0 مجاز است.
- مثال: `[1,0]` مجموع 1.
- آزمون: zero/one/two assignments.

### رابطه (20): دامنه assignment

$$x_{i,j}\in\{0,1\},\qquad\forall i\in\mathcal I,\forall j\in\mathcal J$$

- مفهوم: assignment دودویی.
- کد آینده: `[پیشنهاد فنی] validate_binary_assignment()`.
- مرزی/مثال: 0 و 1 معتبر؛ 0.5 نامعتبر.
- آزمون: domain test.

### رابطه (21): دامنه completion/preemption

$$\tau_j\in\{0,1\},\qquad\forall j\in\mathcal J$$

- مفهوم: 0 preempted، 1 run-to-end.
- کد آینده: `[پیشنهاد فنی] validate_binary_completion()`.
- مرزی/مثال: `τ=1` برای مثال کامل.
- آزمون: 0/1 pass و fractional fail.

### رابطه (22): upload خارج از window صفر

$$
\sigma_j(n)=0,
\quad \forall j\in\mathcal J,
\quad n\in\{1,\ldots,a_j-1,\ a_j+\min(d_{j,u},d_{j,t}),\ldots,\lvert\mathcal N\rvert\}
$$

- مفهوم: upload پیش از arrival و پس از پایان/preemption مجاز نیست.
- کد آینده: `[پیشنهاد فنی] upload_activity_window()`.
- مرزی: `a_j=1` بخش قبل arrival تهی است.
- مثال: `a=1,d_u=2,d_t=4` ⇒ upload از n=3 به بعد صفر.
- آزمون: before/inside/after window.

### رابطه (23): upload داخل window نامنفی

$$
\sigma_j(n)\ge0,
\quad \forall j\in\mathcal J,
\quad n\in\{a_j,\ldots,a_j+\min(d_{j,u},d_{j,t})-1\}
$$

- مفهوم: upload از arrival آغاز می‌شود.
- کد آینده: `[پیشنهاد فنی] validate_upload_window()`.
- مرزی/مثال: window مثال `{1,2}`.
- آزمون: مقدار منفی fail؛ endpointها pass.

### رابطه (24): computation خارج از window صفر

$$
\kappa_j(n)=0,
\quad \forall j\in\mathcal J,
\quad n\in\{1,\ldots,a_j,\ a_j+\min(d_{j,p},d_{j,t}),\ldots,\lvert\mathcal N\rvert\}
$$

- مفهوم: computation زودتر از slot پس از arrival شروع نمی‌شود و پس از stop/end صفر است.
- کد آینده: `[پیشنهاد فنی] compute_activity_window()`.
- مرزی: `d_p=1` window فعال (25) تهی است.
- مثال: `a=1,d_p=3` ⇒ n=1 و n≥4 صفر.
- آزمون: off-by-one و preemption earlier than d_p.

### رابطه (25): computation داخل window نامنفی

$$
\kappa_j(n)\ge0,
\quad \forall j\in\mathcal J,
\quad n\in\{a_j+1,\ldots,a_j+\min(d_{j,p},d_{j,t})-1\}
$$

- مفهوم: computation از یک slot پس از arrival فعال می‌شود.
- کد آینده: `[پیشنهاد فنی] validate_compute_window()`.
- مرزی/مثال: window مثال `{2,3}`.
- آزمون: `d_p=1` empty، `d_p=2` یک slot و مقدار منفی.

### رابطه (26): download خارج از window صفر

$$
\sigma'_j(n)=0,
\quad \forall j\in\mathcal J,
\quad n\in\{1,\ldots,a_j+1,\ a_j+\min(d_{j,d},d_{j,t}),\ldots,\lvert\mathcal N\rvert\}
$$

- مفهوم: download زودتر از دو slot پس از arrival شروع نمی‌شود.
- کد آینده: `[پیشنهاد فنی] download_activity_window()`.
- مرزی: d_d≤2 active window را تهی می‌کند.
- مثال: `a=1,d_d=4` ⇒ n=1,2 و n≥5 صفر.
- آزمون: start/end و preemption.

### رابطه (27): download داخل window نامنفی

$$
\sigma'_j(n)\ge0,
\quad \forall j\in\mathcal J,
\quad n\in\{a_j+2,\ldots,a_j+\min(d_{j,d},d_{j,t})-1\}
$$

- مفهوم: download از دو slot پس از arrival فعال می‌شود.
- کد آینده: `[پیشنهاد فنی] validate_download_window()`.
- مرزی/مثال: window مثال `{3,4}`.
- آزمون: d_d=1/2/3 و مقدار منفی.

### رابطه (28): دامنه زمان توقف

$$d_{j,t}\in\{1,\ldots,d_{j,d}\},\qquad\forall j\in\mathcal J$$

- مفهوم: preemption می‌تواند در هر offset فعال تا پایان download رخ دهد.
- کد آینده: `[پیشنهاد فنی] validate_stop_offset()`.
- مرزی: d_t=1 و d_t=d_d مجاز؛ `d_d` باید صحیح باشد ولی integrality آن اعلام نشده است.
- مثال: `d_t=4∈{1,2,3,4}`.
- آزمون: lower/upper/out-of-range و noninteger `d_d`.

### رابطه (29): completion مستلزم برابری stop/end

$$
\tau_j(d_{j,t}-d_{j,d})=0,
\qquad\forall j\in\mathcal J
$$

- مفهوم: اگر `τ=1` آنگاه `d_t=d_d`؛ اگر `τ=0` این رابطه به‌تنهایی محدودیتی ندارد.
- کد آینده: `[پیشنهاد فنی] check_completion_stop_consistency()`.
- مرزی: bilinear است.
- مثال completion: `1×(4-4)=0`؛ preempted: `0×(3-4)=0`.
- آزمون: τ=1 unequal fail؛ τ=0 unequal pass.

### رابطه (30): preemption باید پیش از completion باشد

$$
\frac{d_{j,t}}{d_{j,d}}<1+\tau_j,
\qquad\forall j\in\mathcal J
$$

- مفهوم: `τ=0 ⇒ d_t<d_d`؛ همراه (29)، `τ=1 ⇒ d_t=d_d`.
- کد آینده: `[پیشنهاد فنی] check_preemption_before_completion()`.
- مرزی: strict inequality؛ `d_d>0` لازم است. با integer offsets قابل بازنویسی دقیق است.
- مثال: completion `4/4=1<2`؛ preemption `3/4<1`.
- آزمون: preempt at exact end fail؛ one slot before pass.

### رابطه (31): نشانگر storage

$$
\theta_j(n)=
\begin{cases}
1,&
\text{if }\min\{a_j+l_j\mid\kappa_j(a_j+l_j)>0\}\le n
\le\max\{a_j+l_j\mid\kappa_j(a_j+l_j)>0\},\\
0,&\text{otherwise.}
\end{cases}
$$

- نمادها: `θ`, arrival، اندیس و allocation computation.
- مفهوم: storage در بازه اولین تا آخرین slot دارای computation مثبت فعال در نظر گرفته می‌شود.
- کد آینده: `[پیشنهاد فنی] derive_storage_indicator()`.
- مرزی: اگر هیچ `κ>0` نباشد، min/max مجموعه تهی تعریف نشده است.
- مثال: computation در n=2,3 ⇒ `θ(2)=θ(3)=1` و بقیه صفر.
- آزمون: contiguous/noncontiguous compute، no-compute job و storage قبل/بعد compute.

## 6. جدول نگاشت فرمول به کد

| فرمول | هدف | ورودی کد | خروجی کد | تابع پیشنهادی | آزمون اصلی |
| --- | --- | --- | --- | --- | --- |
| (1) | objective | assignment/completion/utility | scalar | `compute_total_utility` | manual objective |
| (2) | upload ceiling | upload/input/assignment | bool | `check_upload_upper_bound` | multi-server quantifier |
| (3) | completed upload | upload/input/x/tau | bool | `check_completed_upload` | completed partial |
| (4) | compute ceiling | compute/K/x | bool | `check_compute_upper_bound` | overcompute |
| (5) | completed compute | compute/K/x/tau | bool | `check_completed_compute` | completed partial |
| (6) | download ceiling | download/output/x | bool | `check_download_upper_bound` | multi-server quantifier |
| (7) | completed download | download/output/tau | bool | `check_completed_download` | completed partial |
| (8) | preempt before full download | fraction/tau | bool | `check_preemption_before_full_download` | strict boundary |
| (9) | upload→compute precedence | cumulative progress | bool | `check_upload_compute_ratio` | 60%/61% |
| (10) | compute→download precedence | cumulative progress | bool | `check_compute_download_ratio` | 60%/61% |
| (11) | stage order | stage offsets/deadline | bool | `check_stage_order` | equal/reversed |
| (12) | upload min | d_u | bool | `check_upload_duration` | 0/1 |
| (13) | compute min | d_p | bool | `check_compute_duration` | empty window |
| (14) | download min | d_d | bool | `check_download_duration` | empty window |
| (15) | storage capacity | upload/x/theta/S | bool | `check_storage_capacity` | unit/window |
| (16) | compute capacity | compute/x/C | bool | `check_compute_capacity` | exact/over |
| (17) | upload capacity | upload/x/B_u | bool | `check_upload_capacity` | exact/over |
| (18) | download capacity | download/x/B_d | bool | `check_download_capacity` | exact/over |
| (19) | single assignment | x matrix | bool | `check_single_assignment` | two servers |
| (20) | x binary | x | bool | `validate_assignment_domain` | 0.5 fail |
| (21) | tau binary | tau | bool | `validate_completion_domain` | 0.5 fail |
| (22) | upload zero window | a/d_u/d_t/N | mask | `upload_activity_window` | off-window zero |
| (23) | upload active window | mask/upload | bool | `validate_upload_window` | endpoint |
| (24) | compute zero window | a/d_p/d_t/N | mask | `compute_activity_window` | off-by-one |
| (25) | compute active window | mask/compute | bool | `validate_compute_window` | d_p=1/2 |
| (26) | download zero window | a/d_d/d_t/N | mask | `download_activity_window` | off-by-one |
| (27) | download active window | mask/download | bool | `validate_download_window` | d_d=1/2/3 |
| (28) | stop domain | d_t/d_d | bool | `validate_stop_offset` | endpoints |
| (29) | tau-stop relation | tau/d_t/d_d | bool | `check_completion_stop` | unequal completion |
| (30) | preempt before end | tau/d_t/d_d | bool | `check_preemption_timing` | strict boundary |
| (31) | storage indicator | compute schedule/arrival | binary mask | `derive_storage_indicator` | empty set |

تمام نام تابع‌ها `[پیشنهاد فنی]` هستند.

## 7. ناسازگاری‌ها و ابهامات مدل

### 7.1 ناسازگاری بحرانی assignment در روابط (2)-(6)

- محل اول: تعریف `x_{i,j}` و قید (19)، صفحات 4-5؛ هر job حداکثر به یک server تخصیص می‌یابد.
- محل دوم: روابط (2)-(6) برای تمام `i` نوشته شده‌اند، اما `σ_j`, `κ_j`, `σ'_j` server index ندارند.
- نوع ناسازگاری: quantification/indexing.
- اثر: با حداقل دو server، برای هر job assigned حداقل یک server انتخاب‌نشده `x=0` دارد؛ قید آن server تمام جریان job را صفر می‌کند. بنابراین مدل چاپ‌شده عملاً service غیرصفر را ناممکن می‌کند.
- تفسیرهای ممکن:
  1. جایگزینی RHS با `s_j Σ_i x_{i,j}` و مشابه آن برای `K_j` و `s'_j`؛
  2. server-index کردن flow variables به‌شکل `σ_{i,j}(n)` و غیره؛
  3. اعمال قیود فقط برای server منتخب با indicator constraints.
- تفسیر پیشنهادی برای بازتولید: `[پیشنهاد فنی؛ نیازمند تأیید]` گزینه 1 کمترین تغییر را دارد، چون capacity constraints از flow بدون server index ضربدر `x_{i,j}` استفاده می‌کنند.

### 7.2 مقدار τ برای job تکمیل‌شده

- محل اول: تعریف صفحه 4 و روابط (29)-(30): run-to-end برابر `τ=1`.
- محل دوم: توضیح رابطه (3) در صفحه 5 یک بار می‌گوید job served-to-end دارای `τ=0` است.
- نوع: خطای متنی آشکار.
- اثر: برداشت معکوس از completion و objective.
- تفسیر پیشنهادی: `[استخراج مستقیم]` مقدار صحیح completion برابر 1 است؛ تعریف، objective و روابط پایانی همگی آن را تأیید می‌کنند.

### 7.3 `s'_j` تعریف نشده است

- محل اول: متن پارامترها فقط `s_j` و `K_j` را تعریف می‌کند.
- محل دوم: روابط (6)-(10) از `s'_j` استفاده می‌کنند.
- نوع: پارامتر مفقود.
- اثر: مدل download و تولید داده قابل اجرا نیست.
- تفسیرهای ممکن: output size مستقل؛ برابر input size؛ نسبت ثابتی از input.
- پیشنهاد: `[نامشخص]` هیچ مقدار یا رابطه‌ای بدون منبع [1]/[4] یا تأیید کاربر انتخاب نشود.

### 7.4 واحد storage و computation

- محل اول: `s_j` بر حسب MB و `S_i` بر حسب GB در صفحه 4.
- محل دوم: Table I هر دو storage server/job را MB نشان می‌دهد.
- نوع: واحد ناسازگار.
- اثر: قید (15) در صورت تبدیل‌نکردن 1024 برابر خطا می‌کند.
- پیشنهاد: `[پیشنهاد فنی؛ نیازمند تأیید]` canonical unit برابر MB و تبدیل صریح ورودی‌ها.

همچنین `C_i` با MFlops/s معرفی شده، اما `κ_j(n)` مقدار computation در slot است. اگر slot یک ثانیه نباشد، تبدیل `rate×slot_duration` لازم است؛ متن این تبدیل را فقط برای bandwidth صریح کرده است.

### 7.5 duration در برابر endpoint و off-by-one

- محل اول: متن `d_{j,u}`, `d_{j,p}`, `d_{j,d}` را «تعداد slotهایی که فاز span می‌کند» می‌نامد و (12)-(14) حداقل 1 می‌گذارند.
- محل دوم: windows (23)، (25)، (27) به‌ترتیب از `a`, `a+1`, `a+2` آغاز می‌شوند و همگی در `a+d-1` پایان می‌یابند.
- نوع: semantic/off-by-one.
- اثر: `d_p=1` هیچ compute slot و `d_d≤2` هیچ download slot ایجاد نمی‌کند، برخلاف توضیح «هر process حداقل یک slot».
- تفسیرهای ممکن: این متغیرها endpoint offset هستند، نه duration؛ یا lower bounds باید 1/2/3 باشند.
- پیشنهاد: قبل از پیاده‌سازی، فرمول چاپ‌شده و ادعای روایی به‌صورت دو variant کنترل‌شده بررسی شوند؛ هیچ‌کدام فعلاً انتخاب نشده است.

### 7.6 strict inequality در (8) و (30)

- محل: روابط (8) و (30).
- نوع: قابلیت بیان در solver.
- اثر: Gurobi strict inequality را مستقیماً نمی‌پذیرد.
- تفسیر پیشنهادی برای (30): با integer بودن offsets، `d_t≤d_d-(1-τ)` همراه (29) معادل دقیق است.
- تفسیر (8): نیازمند epsilon یا minimum data quantum است و مقدار آن در مقاله گزارش نشده؛ `[نامشخص]`.

### 7.7 دامنه متغیرهای زمانی

- محل اول: `d_t` مجموعه صحیح دارد.
- محل دوم: `d_u`, `d_p`, `d_d` فقط نامساوی دارند، با اینکه در index set استفاده می‌شوند.
- نوع: domain declaration missing.
- اثر: اگر continuous باشند، بازه‌های اندیس تعریف‌پذیر نیستند.
- پیشنهاد: `[استخراج مستقیم]` قصد نویسندگان به‌احتمال زیاد integer slot offsets است، ولی برای پیاده‌سازی به تأیید نیاز دارد.

### 7.8 تعریف θ روی مجموعه تهی

- محل: رابطه (31).
- نوع: undefined min/max.
- اثر: برای unassigned job یا preemption پیش از computation، `θ` تعریف ندارد.
- پیشنهاد: `[پیشنهاد فنی؛ نیازمند تأیید]` اگر هیچ `κ>0` وجود ندارد، `θ_j(n)=0` برای همه n.

### 7.9 بازه storage در رابطه (31) و متن آزادسازی

- محل اول: (31) storage را فقط از اولین تا آخرین compute-positive slot فعال می‌کند.
- محل دوم: متن می‌گوید storage پس از execution و ارسال results آزاد می‌شود.
- نوع: temporal inconsistency.
- اثر: upload ذخیره‌شده پیش از اولین compute و دوره download پس از آخرین compute در (15) شمرده نمی‌شوند.
- تفسیرهای ممکن: θ باید از اولین upload تا پایان download فعال باشد؛ یا فقط input در حال processing مدنظر است.
- پیشنهاد: فرمول (31) برای reproduction literal حفظ و alternative فقط در sensitivity test بررسی شود؛ اجرای این پیشنهاد نیازمند تأیید است.

### 7.10 معنی `d_{j,t}`

- محل اول: متن آن را تعداد slotهای spent in processing پیش از preemption می‌نامد.
- محل دوم: در (22)، (24)، (26) پایان upload، compute و download را هم محدود می‌کند.
- نوع: semantic inconsistency.
- اثر: تفسیر event زمان preemption مبهم است.
- پیشنهاد: `[استخراج مستقیم]` در فرمول‌ها بیشتر به global stop offset شبیه است؛ هنوز انتخاب اجرایی نشده است.

## 8. محدودیت‌های بازتولید مدل دقیق

1. مدل چاپ‌شده بدون اصلاح indexing روابط (2)-(6) برای سیستم چندسروری قابل استفاده نیست.
2. `s'_j` و داده آن موجود نیست.
3. strict inequality (8) بدون epsilon/quantum قابل ورود به solver نیست.
4. دامنه integer سه endpoint میانی اعلام نشده است.
5. storage indicator برای no-compute job تعریف ندارد.
6. تنظیمات Gurobi، tolerance، NonConvex setting، time limit، threads و نسخه solver گزارش نشده‌اند.
7. فرمول minimum resource مورد استفاده heuristic بخشی از این MINLP نیست.

## 9. تصمیم‌های لازم پیش از پیاده‌سازی مدل

هیچ تصمیم زیر در این مرحله اعمال نشده است:

1. اصلاح روابط (2)-(6) با aggregate assignment یا server-indexed flows؛
2. مقدار/منبع `s'_j`؛
3. canonical units و slot duration؛
4. interpretation متغیرهای زمانی و lower bounds؛
5. epsilon رابطه (8)؛
6. تعریف θ برای مجموعه تهی و بازه storage.

نزدیک‌ترین تفسیر پیشنهادی برای خطای بحرانی روابط (2)-(6)، استفاده از `y_j=Σ_i x_{i,j}` در RHS است، اما تا تأیید کاربر نباید در کد اعمال شود.

## 10. نتیجه مرحله سوم

- تمام 31 رابطه استخراج و به مفهوم، تابع آینده، مثال و آزمون متصل شدند.
- مدل از نظر مفهومی روشن، ولی از نظر چاپ‌شده دارای یک خطای indexing مسدودکننده و چند ابهام اجرایی است.
- هیچ کد optimization تولید یا اجرا نشد.
- هیچ `[فرض بازتولید]` استفاده نشد.

