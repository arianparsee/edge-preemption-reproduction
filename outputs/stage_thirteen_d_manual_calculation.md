# محاسبه دستی Stage 13-D

برچسب: `[آزمون کمکی]`؛ این مثال نتیجه مقاله یا اجرای 100×30 نیست.

## داده

- یک سرور با ظرفیت `(storage=4, computation=10, upload=10, download=10)`.
- `task-current`: ورود 0، deadline شامل 7، Utility=10،
  `(s,K,b_u,b_d)=(4,10,4,4)`.
- `task-incoming`: ورود 1، deadline شامل 6، Utility=12،
  `(s,K,b_u,b_d)=(4,6,4,4)`.
- مطابق ASSUMP-037، خروجی هر دو برابر 4 است.

## task-current

در epoch 1 وارد auction می‌شود. `service_slots=7-1=6` و
`compute_eligible_slots=5`، پس reservation computation برابر `10/5=2` است.
از epoch 2 فعال می‌شود:

| epoch | active slot | uploaded | computed | downloaded |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 1 | 4 | 0 | 0 |
| 3 | 2 | 4 | 2 | 0 |
| 4 | 3 | 4 | 4 | 1.6 |
| 5 | 4 | 4 | 6 | 2.4 |
| 6 | 5 | 4 | 8 | 3.2 |
| 7 | 6 | 4 | 10 | 4 |

بنابراین در مرز شامل deadline کامل می‌شود.

## task-incoming و Retention

در epoch 2 وارد auction می‌شود، ولی storage residual صفر است و rejection موقت
می‌گیرد. dry-run برای retry در epoch 3 هنوز feasible است؛ پس یک retry ثبت می‌شود.
در epoch 3 دوباره جا نمی‌شود. retry بعدی در epoch 4 فقط دو slot computation-
eligible/download-window کافی ندارد، بنابراین `EXPIRED` می‌شود.

نتیجه KG-R و DK-R: Completed=`task-current` با Utility 10؛
Rejected=`task-incoming` با Utility 12؛ raw auction rejections=2.

## task-incoming و Preemption

در epoch 2 نسبت وظیفه جدید `12/4=3` و نسبت قربانی `10/5=2` است؛
`3 >= 1.05×2` برقرار است. هر دو روش KG-P و DK-P در مثال smoke قربانی را حذف و
وظیفه جدید را می‌پذیرند. reservation computation آن `6/(6-2-1)=2` است و از
epoch 3 تا 6 به `(uploaded,computed,downloaded)=(4,6,4)` می‌رسد.

نتیجه KG-P و DK-P: Completed=`task-incoming` با Utility 12؛
Rejected=`task-current` با Utility 10؛ ever-preempted overlay شامل
`task-current` است.
