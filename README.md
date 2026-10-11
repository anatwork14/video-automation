# GE1013 Video Automation — footage thật, có nguồn USGS

Mục tiêu: sản xuất bản nháp TikTok địa chất 120 giây (108–132 giây theo đề bài), **chỉ sử dụng video tư liệu thật**, AI hỗ trợ nghiên cứu và giọng đọc (được ghi rõ là giọng tổng hợp). Không có ảnh hay video AI-generated. Nội dung mẫu: **Kīlauea 2018**, nhóm cần xác nhận trước khi nộp.

## ĐÃ TÍCH HỢP
- **Free TTS mặc định:** [rany2/edge-tts](https://github.com/rany2/edge-tts), giọng `vi-VN-NamMinhNeural`, không cần API key hoặc phí theo lượt gọi hiện tại; cần Internet. KHÔNG phải phần mềm TTS offline, tính ổn định và quyền sử dụng do nhà cung cấp quyết định. Có thể chọn giọng nữ `vi-VN-HoaiMyNeural`.
- **Word timestamps:** speech output kèm WordBoundary và hash nội dung script, sinh caption từ thời điểm từng từ, không ước lượng từ số chữ. Nội dung thay đổi sẽ chặn dùng lại giọng/phụ đề cũ.
- **Fact/provenance gate:** `claims.json` và `SCIENCE_AUDIT.md` chứa bằng chứng USGS; người thật duyệt từng claim trong `review.json`. `media_audit.py` xác minh SHA256, file có video stream và đủ thời lượng. Clip thiếu bị chặn, KHÔNG tự đóng băng khung hình.
- **Dựng tự động:** FFmpeg/Pillow ghép 9:16, intro có logo, nhóm, MSSV, subtitles và source credit, QA kỹ thuật.
- **GitHub CI:** kiểm tra code, manifest, tests; không tải footage vào repo và không tự đăng TikTok.

## BẮT ĐẦU (máy có Python 3.10+, FFmpeg+FFprobe và Internet)

```bash
git clone https://github.com/anatwork14/video-automation.git
cd video-automation
python -m pip install -r requirements.txt
cp group.example.json group.json
cp review.example.json review.json
# Điền group.json (3–5 người, số nhóm, ngôn ngữ). KHÔNG commit dữ liệu cá nhân.
# Copy file PDF giảng viên về máy, dùng đúng đường dẫn:
python pipeline.py prepare --assignment-pdf /path/to/GE1013_TIKTOK.pdf
```

Lệnh prepare: kiểm tra cấu trúc → tải footage USGS → trích ảnh logo bản nháp → tạo MP3 giọng Việt từng phân cảnh → phụ đề theo WordBoundary. **Nếu clip ngắn hơn phân cảnh hoặc TTS dài hơn phân cảnh, cần chỉnh timeline/script hoặc thêm footage thật rồi chạy lại.**

### Chốt nguồn khoa học trước render
Đọc `SCIENCE_AUDIT.md`, đối chiếu `claims.json` với USGS; nghe narration, xem video và kiểm tra quyền sử dụng + ngày quay. Thành viên nhóm tự đánh dấu `review.json` cho từng **asset** và **claim**, đánh dấu script/logos đã duyệt. AI không được tự tick và script không tự đăng.

```bash
python validate.py --strict
python pipeline.py render
# output/GE1013_Kilauea_2018_DRAFT.mp4
```

Giọng khác: `python pipeline.py prepare --voice vi-VN-HoaiMyNeural --force-tts --assignment-pdf ...`.

Không dùng giọng AI: `python pipeline.py prepare --no-tts --no-subtitles --assignment-pdf ...`, đặt `assets/voiceover.wav` (bắt đầu nói sau intro) và căn caption thủ công qua Descript hoặc phần mềm dựng. **TTS không phải giọng người thật**.

## GIỚI HẠN KHÔNG ĐƯỢC GIẤU
1. Pipeline mới kiểm thử cú pháp/cấu trúc và unit tests trong GitHub CI; **chưa render một video thật end-to-end** bởi vì repo công khai không có bản tải MP4/giọng/logo/thông tin nhóm.
2. Xác minh hash file **không chứng minh** license hay độ chính xác của hình. Phải xem clip, đối chiếu USGS trực tiếp.
3. Giọng nói có thể đọc sai tên riêng tiếng Hawaii; cần nghe và sửa script phát âm.
4. Nguồn tư liệu cho Kapoho Bay: dung nham vào biển tối **03/06**, video ghi **04/06**. Không ghi sai ngày đầu tiên.
5. Intro bắt buộc tên video/số nhóm/tên+MSSV/GE1013/logo trường, môn và sponsor; nếu nhóm có thành viên chương trình Tiếng Anh thì dùng Anh toàn bộ. Đây là repo công khai nên không commit MSSV, keys, media thật.
6. Sau khi xem/nghe và đối chiếu rubric, nhóm tự đăng và nộp link TikTok trước hạn nộp có trong PDF.

Đọc tiếp [RUNBOOK.md](RUNBOOK.md), [SCIENCE_AUDIT.md](SCIENCE_AUDIT.md), [AGENTS.md](AGENTS.md).
