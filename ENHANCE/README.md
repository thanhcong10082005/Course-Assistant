# ENHANCE — Kế hoạch cải tiến Course Assistant

Thư mục này chứa kế hoạch triển khai 06 bước cải tiến hệ thống Course Assistant
hiện tại. Mục tiêu là đưa repo từ mức **prototype/sample** lên mức **bài nộp hoàn
chỉnh**, bám sát yêu cầu trong `NLPAssignment-Course Assistant.pdf`.

## Thứ tự thực hiện đề xuất

| Thứ tự | Tài liệu | Nội dung | Phụ thuộc | Ước lượng |
|---|---|---|---|---|
| 1 | [`PART1-PARSER-TOKENIZER.md`](./PART1-PARSER-TOKENIZER.md) | Sửa tokenizer, grammar, parser; câu sai trả `()` | — | 4–5 ngày |
| 2 | [`PART2-GENERATIVE.md`](./PART2-GENERATIVE.md) | Sinh ≤ 10.000 câu hợp lệ, có kiểm tra ngữ nghĩa | Part 1 | 2–3 ngày |
| 3 | [`PART3-KNOWLEDGE-BASE.md`](./PART3-KNOWLEDGE-BASE.md) | Load dữ liệu từ `data/`, bỏ hard-code, sửa lỗi KB/Answer | Part 1 | 4–6 ngày |
| 4 | [`PART4-DIALOUGE.md`](./PART4-DIALOUGE.md) | Tích hợp `DialogueManager`, resolve tham chiếu | Part 3 | 2–3 ngày |
| 5 | [`PART5-EVALUATION.md`](./PART5-EVALUATION.md) | Test set 50–100 câu, chấm cả answer và context | Part 1–4 | 3–4 ngày |
| 6 | [`PART6-SUBMISSION.md`](./PART6-SUBMISSION.md) | README, REPORT, video, Docker, đóng gói | Part 1–5 | 2–3 ngày |

Tổng thời gian gợi ý: **17–24 ngày làm việc**, có thể chạy song song Part 1 và
Part 3 sau khi chốt schema dữ liệu.

## Nguyên tắc chung

1. **Không sửa output bằng tay.** Mọi file trong `output/` phải sinh lại được
   bằng lệnh trong README.
2. **Một nguồn dữ liệu duy nhất.** Knowledge base lấy từ `data/`; không hard-code
   nội dung môn học rải rác trong code.
3. **Parser là nguồn xác thực câu.** Một câu chỉ được coi là hợp lệ nếu parser
   thật sự parse được, không dựa vào fallback "đoán" mọi input.
4. **Đánh giá phải đo đúng thứ mình tuyên bố.** Nếu báo cáo answer accuracy thì
   test set phải có tiêu chí answer, không chỉ intent/entity.
5. **Mỗi bước có acceptance test riêng.** Chỉ chuyển bước khi test của bước đó
   pass.

## Trạng thái hiện tại (baseline)

- `src/` có 8 module nhưng phần lớn là code mẫu.
- `data/` chỉ có `course_data.txt`, chưa dùng để load KB.
- `output/` có đủ 9 file nhưng một số file chưa khớp code hiện tại.
- Parser trả cây cho cả câu sai; samples vượt 10.000 dòng và có câu vô nghĩa.
- Evaluation 20 case, answer accuracy 15%, chưa có no-info/context case.

Chi tiết bằng chứng nằm trong từng tài liệu.
