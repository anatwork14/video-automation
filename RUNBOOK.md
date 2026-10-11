# RUNBOOK — GE1013 hoàn thành phim tư liệu thật

## Chuẩn bị
- Cài Python 3.10+, FFmpeg, ffprobe, `pip install -r requirements.txt` (gồm edge-tts).
- Copy group.example.json -> group.json và review.example.json -> review.json (đã .gitignore). Điền đầy đủ nhưng không push.
- Mở SCIENCE_AUDIT.md/claims.json và từng URL USGS trong assets.json, xem trang video gốc; video quay ngày khác với ngày trang được đăng.
- Chỉ tự mình mới đánh dấu review.json: asset `approved,rights_checked,reviewed_by,reviewed_at`; claim `approved,source_read,reviewed_by,reviewed_at`; script/logos đều reviewed.
- Trích logo từ PDF bản giảng viên: crop bằng code là minh họa ban đầu; logo trường/môn/sponsor phải có đủ và đúng.

## Miễn phí — tự chuẩn bị footage + giọng đọc
```bash
python pipeline.py prepare --assignment-pdf /path/to/261-KHOA-HOC-TRAI-DAT-1013-TIKTOK.pdf
# Mặc định TTS trực tuyến Edge giọng nam tiếng Việt, không key.
# Chọn giọng nữ, cần ghi đè audio khi đã nghe và đồng ý bản script mới:
python pipeline.py prepare --assignment-pdf /path/to/file.pdf --voice vi-VN-HoaiMyNeural --force-tts
```
Tự tải MP4 qua các URL USGS, tạo SHA256 sidecar và audio/{01..05}.mp3 + .timings.json. Tự tạo captions.srt từ TTS WordBoundary; **không có giả thời điểm âm thanh**.
- Nếu network/source thất bại: xem source_page, tải tay đúng file, chạy lại downloader để ghi hash. Vẫn phải xem video đối chiếu.
- Nếu video source quá ngắn: `python media_audit.py` báo lỗi; tìm thêm footage thật được duyệt hoặc sửa timeline. Không tự loop/freeze/cắt bỏ lời thoại.
- TTS phụ thuộc dịch vụ trực tuyến, có thể thay đổi/bị giới hạn; không được cam kết miễn phí lâu dài.
- TTS tạo giọng tổng hợp. Nếu bắt buộc audio 100% người thật, thu lời qua điện thoại -> assets/voiceover.wav; dùng `--no-tts --no-subtitles` và căn phụ đề thủ công.

## Kiểm tra trước render
```bash
python validate.py
python media_audit.py
python validate.py --strict
python pipeline.py render
python qa.py
```
Strict validation yêu cầu đúng ngôn ngữ, 3–5 thành viên, logo, script, tất cả claim và footage duyệt bởi **con người**, video đúng hash và đủ thời lượng.
MP4 bản nháp ở `output/GE1013_Kilauea_2018_DRAFT.mp4`, xem/nghe toàn bộ trước khi đăng.

## Checklist nộp bài
- Mỗi đoạn footage là hình USGS thật, không gán sai nguồn/ngày/địa điểm; caption "04/06" là ngày ghi hình, nước biển từ tối 03/06.
- Kịch bản là lời của nhóm, khoa học đúng, thông tin về magma, khe nứt và sụt lún khớp bài USGS.
- Không bị sao chép trên 50%; xem đủ 108–132 giây, audio dễ nghe, caption đọc được, phát âm địa danh đúng.
- Intro đủ tên video, số nhóm, MSSV, GE1013, logo trường/môn và sponsor; nhóm tiếng Anh dùng hoàn toàn tiếng Anh.
- Tự đăng TikTok và nộp link theo form môn học, không tự động bấm nộp.

## Kết quả kiểm thử
CI không tải các video thật và chưa thử MP4 cuối; pass CI không chứng minh đủ điểm hoặc đủ quyền sử dụng. Kiểm chứng con người là lớp cuối.

## Human approvals gắn chặt với nội dung (mới)
- Sau khi có footage, audio và logo thật, chạy `python review_hashes.py`. Chỉ đọc/hiển thị expected digests, KHÔNG tự tick approved.
- Điền `review.json` từ `review.example.json`: từng asset có `approved_manifest_sha256`, `approved_media_sha256`, `rights_evidence_excerpt`; từng claim có `approved_claim_sha256`, `source_excerpt` từ USGS.
- `script.approved_narration_sha256`, `audio.approved_audio_digest` và `logos.approved_sha256` phải là hash đúng. Chèn tên thành viên duyệt thực tế và ngày ISO8601 có timezone.
- Dù đã duyệt, đổi lời dẫn hay thay footage sẽ tự làm duyệt cũ mất hiệu lực. Với Edge TTS, `--no-subtitles` cũng không bỏ qua kiểm tra audio stale.
- Đánh dấu `approved` đúng kiểu JSON boolean `true` và `rights_checked/source_read` tương ứng. Chuỗi `"false"` bị từ chối.

**Về file tải thủ công:** không dùng `download_assets.py` để chứng thực một MP4 tự đặt vào `assets/`. Nếu tệp thiếu sidecar, di chuyển tệp ấy ra ngoài và tải lại bằng script từ URL gốc USGS. Nếu nguồn không còn khả dụng, phải tìm nguồn mới có URL/rights rõ ràng và cập nhật manifest sau khi tự kiểm tra, tuyệt đối không tạo provenance giả.
