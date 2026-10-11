# GE1013 Video Automation — 100% real footage

Bộ công cụ dựng TikTok khoa học Trái Đất từ **tư liệu ghi hình thật**, không sinh ảnh/video bằng AI. Chủ đề mẫu: **Kīlauea 2018** (chưa chốt với nhóm). Đây là **starter + automation**, KHÔNG phải bài nộp đã hoàn thành.

## Yêu cầu từ đề bài môn học (PDF do nhóm cung cấp)
- Nhóm 3–5 sinh viên; thời lượng 108–132 giây (mục tiêu 120 giây).
- Intro BẮT BUỘC: tên video, số nhóm, họ tên và MSSV, môn GE1013, logo trường, logo môn và nhà tài trợ chính.
- Nếu có thành viên chương trình tiếng Anh, toàn bộ video dùng tiếng Anh.
- Nội dung đúng khoa học, dễ hiểu và có tính sáng tạo; sao chép/trùng lặp từ 50% trở lên bị xem là không hợp lệ.
- Hạn nộp để xét giải: 16/10/2026. Nhóm tự đăng TikTok và nộp link theo hướng dẫn giảng viên.

## Cách chạy
Yêu cầu Python 3.10+, FFmpeg / FFprobe (trong PATH); máy có Internet khi tải footage. KHÔNG commit MSSV thật, API keys, MP4/video tải về.

1. Cài thư viện: python -m pip install -r requirements.txt
2. Điền group.json dựa trên group.example.json (tệp group.json đã được .gitignore).
3. Mở assets.json và các source_page tương ứng; một thành viên nhóm tự đọc giấy phép và metadata, sau đó đánh dấu approved trong review.json (sao chép từ review.example.json); KHÔNG nhờ AI tự đánh dấu thay.
4. Tải bản quay gốc từ USGS: python download_assets.py (nếu liên kết hỏng, mở source_page và tải thủ công, lưu đúng tên).
5. Trích logo từ PDF bài tập trên máy: python extract_logos.py /duong-dan/toi/GE1013_TIKTOK.pdf . Kiểm tra vị trí cắt và logo nhà tài trợ.
6. Chọn âm thanh: tự thu và lưu assets/voiceover.wav; hoặc dùng giọng tổng hợp (có công bố nội bộ) bằng python voiceover.py (cần OPENAI_API_KEY, có phát sinh chi phí và phải nghe kiểm duyệt).
7. Kiểm tra cấu trúc: python validate.py ; kiểm tra nộp bài: python validate.py --strict.
8. Dựng bản nháp: python build.py; kiểm tra báo cáo: python qa.py; nghe/xem toàn bộ output trước khi đăng.
9. Có thể dùng Descript để soát phụ đề, cắt cảnh, cân âm. KHÔNG dùng tính năng generate B-roll/AI images/video.

## Pipeline
USGS originals → provenance/rights/manual approval → download + SHA256 → script/claims review → narration → FFmpeg 9:16 → technical QA → human scientific & visual QA → manual publication.

## Các file chính
- assets.json: bốn footage MP4 USGS chính thống, URL nguồn và ngày quay.
- timeline.json: phân cảnh 120 giây theo thời gian.
- NARRATION_AND_STORYBOARD.md: bản nháp lời dẫn, có nguồn.
- group.example.json: mẫu thông tin nhóm; KHÔNG đưa MSSV thật lên repo public.
- review.example.json: chốt kiểm chứng độc lập bắt buộc.
- download_assets.py, extract_logos.py, voiceover.py, build.py, validate.py, qa.py: pipeline.
- AGENTS.md + CLAUDE.md + .agents/skills/: quy tắc & kỹ năng cho ChatGPT, Claude, Codex.
- .github/workflows/ci.yml: kiểm tra code, cấu trúc và test trên mỗi push.

## Nguyên tắc bắt buộc
1. Không tạo hay biến đổi video theo hướng dựng giả sự kiện. Chỉ cắt, ghép, chỉnh sáng cơ bản, letterbox, chèn phụ đề và attribution.
2. Không dùng footage không xác định được quay ở đâu/khi nào, giấy phép nào.
3. Không sử dụng câu chuyện khoa học do AI tự suy đoán. Mỗi claim quan trọng cần nguồn kiểm chứng.
4. Tôn trọng giấy phép riêng của từng media; không suy luận mọi ảnh trên website USGS đều public domain.
5. Hoạt động nghiên cứu/dựng có thể tự động; **duyệt khoa học, tư liệu và bấm đăng/nộp vẫn phải do nhóm** thực hiện.
6. Repo công khai: không đưa MSSV của bạn học, giọng thu cá nhân hay API key lên GitHub.

**Trạng thái:** chưa có footage tải sẵn, logo được cung cấp riêng qua ZIP trước đó, chưa có giọng đọc và chưa có bài MP4 đã nghiệm thu. Tất cả clip nguồn được dẫn trong manifest để tải và kiểm tra trên máy người dùng.
