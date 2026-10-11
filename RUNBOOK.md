# RUNBOOK — Thao tác cuối cùng cho nhóm GE1013

## A. Cài đặt (máy riêng hoặc ChatGPT Work/Claude Code có quyền chạy lệnh)
1. Clone: git clone https://github.com/anatwork14/video-automation.git
2. cd video-automation
3. Cài FFmpeg + FFprobe (hệ thống cần nhận lệnh ffmpeg/ffprobe).
4. python -m pip install -r requirements.txt
5. Sao chép group.example.json → group.json và review.example.json → review.json. KHÔNG push 2 file này lên GitHub.
6. Điền số nhóm và 3–5 thành viên; ngôn ngữ vi/en đúng theo lớp.
7. Mở các trang gốc trong assets.json, đọc rights, tải/xem bản gốc; nhóm chỉ đánh dấu approved trong review.json sau khi đối chiếu. AI không được tự tick.

## B. Chuẩn bị 100% tự động phần kỹ thuật
- Không cần tự quay: python pipeline.py prepare --assignment-pdf /path/to/GE1013_TIKTOK.pdf
- Nếu CHỌN sử dụng giọng tổng hợp (có phí): thiết lập OPENAI_API_KEY trong môi trường riêng, rồi chạy python pipeline.py prepare --assignment-pdf /path/to/GE1013_TIKTOK.pdf --tts
- Nếu KHÔNG dùng TTS: thu một tệp assets/voiceover.wav từ xa; lời đọc bắt đầu sau intro 10 giây, và phải tự canh nhịp; lựa chọn ổn định hơn là cung cấp assets/audio/01.mp3 ... 05.mp3 theo từng cảnh.
- Nếu USGS chuyển hoặc chặn URL: mở source_page, tải đúng MP4 thực, đặt đúng filename trong assets/. Không thay bằng ảnh/video AI.
- Logo từ PDF là hình trích thô, nhóm kiểm tra logo môn, trường và nhà tài trợ. Không coi crop tự động là đã đúng.

## C. Render sau bước duyệt
- python pipeline.py render
- Thư mục output/: GE1013_Kilauea_2018_DRAFT.mp4, captions.srt, merged.mp4 và các bước trung gian.
- Tùy chọn bỏ burn caption: python pipeline.py render --no-subtitles (sau đó nhóm thêm caption đã duyệt trong Descript).
- Nếu thiếu phê duyệt: pipeline báo FAIL và không render. Đây là thiết kế để bảo vệ tính thật của nội dung.

## D. Human QA bắt buộc trước nộp
1. Toàn bộ sự kiện trong footage đúng chú thích ngày/địa điểm; nguồn từng clip có thể mở được.
2. Từng claim trong kịch bản được đối chiếu với tài liệu USGS; không có 50% nội dung sao chép.
3. Không có hình AI, AI B-roll hoặc clip minh họa tráo sự kiện.
4. Logo trường, môn GE1013, sponsor, title nhóm, họ tên/MSSV đúng.
5. Video 108–132 giây, dọc 1080x1920, âm rõ và phụ đề đúng thời điểm (SRT tự động chỉ ước lượng).
6. Tôn trọng chính sách public-domain riêng của từng footage, ghi USGS credit.
7. Đăng TikTok và nộp link qua form môn học THỦ CÔNG trước mốc quy định.

## E. Status
- Đã tự động: code/config/CI và bộ nguồn metadata; chưa có video gốc, logo được duyệt, người duyệt, audio thật hoặc rendered MP4 trong repo.
- CI trên GitHub chỉ kiểm tra cấu trúc/syntax/test; không có quyền duyệt nội dung hoặc tạo MP4 nộp.
- Không công khai group.json, review.json, audio có thông tin cá nhân, API keys.
