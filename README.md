# GE1013 Video Automation — footage thật, có nguồn USGS

> **Video nộp bài phải 100% tiếng Anh**: `narration.json` (language `en`), `timeline.json`, `group.json` (language `en`, course tiếng Anh) và giọng mặc định `en-US-GuyNeural`. `tests/test_english_only.py` chặn mọi chữ/lời tiếng Việt còn sót.

Mục tiêu: sản xuất bản nháp TikTok địa chất 120 giây (108–132 giây theo đề bài), **chỉ sử dụng video tư liệu thật**, AI hỗ trợ nghiên cứu và giọng đọc (được ghi rõ là giọng tổng hợp). Không có ảnh hay video AI-generated. Nội dung mẫu: **Kīlauea 2018**, nhóm cần xác nhận trước khi nộp.

## ĐÃ TÍCH HỢP
- **Free TTS mặc định:** [rany2/edge-tts](https://github.com/rany2/edge-tts), giọng mặc định theo ngôn ngữ narration (tiếng Anh: `en-US-GuyNeural`; tiếng Việt: `vi-VN-NamMinhNeural`), không cần API key hoặc phí theo lượt gọi hiện tại; cần Internet. KHÔNG phải phần mềm TTS offline, tính ổn định và quyền sử dụng do nhà cung cấp quyết định. Giọng nữ tiếng Anh: `en-US-JennyNeural`.
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
Đọc `SCIENCE_AUDIT.md`, đối chiếu `claims.json` với USGS; nghe narration, xem video và kiểm tra quyền sử dụng + ngày quay.

**Quy trình duyệt mới (fail-closed):** chạy `python review_hashes.py` để nhận đúng SHA256 của assets/claims/tập claim/narration/timeline/audio/logos; sau khi điền xong, mỗi người duyệt ký `review.json` bằng SSH key (xem RUNBOOK.md › Chữ ký người duyệt). Tự điền các digest đó vào `review.json` dựa trên `review.example.json`, kèm trích dẫn bằng chứng cụ thể, tên chính xác của một thành viên đã đăng ký, `reviewed_at` ISO8601 (ví dụ `2026-10-11T13:30:00+07:00`) và boolean `true` (không phải chuỗi `"true"`). AI không được tự tích ô phê duyệt. Mọi thay đổi tệp sẽ khiến digest cũ không hợp lệ.

Lưu ý: các MP4 gốc phải được tải và kiểm tra trước khi chạy `review_hashes.py`; digest tự nó **không chứng minh** video/claim đúng hay giấy phép hợp lệ. AI không được tự tick và script không tự đăng.

```bash
python validate.py --strict
python pipeline.py render
# output/GE1013_Kilauea_2018_DRAFT.mp4
```

Giọng khác: `python pipeline.py prepare --voice en-US-ChristopherNeural --force-tts --assignment-pdf ...` (giọng phải cùng ngôn ngữ với narration). Tốc độ đọc: `--rate -5%` hoặc `--rate +8%` (phải có dấu).

Trình tự đầy đủ từ chuẩn bị đến `release_check.py`: xem RUNBOOK.md › Trình tự đầy đủ.

**Không dùng giọng AI:** lệnh `prepare --no-tts --no-subtitles` rồi `pipeline.py render` sẽ tự bỏ burn caption khi chỉ có `assets/voiceover.wav`. Nếu cần phụ đề, hãy căn tay bằng Descript. Không thể sử dụng SRT thời gian ước lượng để giả làm transcript chuẩn.

Không dùng giọng AI: `python pipeline.py prepare --no-tts --no-subtitles --assignment-pdf ...`, đặt `assets/voiceover.wav` (bắt đầu nói sau intro) và căn caption thủ công qua Descript hoặc phần mềm dựng. **TTS không phải giọng người thật**.

## GIỚI HẠN KHÔNG ĐƯỢC GIẤU
1. CI (Python 3.10 và 3.12) cài FFmpeg và render end-to-end THẬT một phim 120 s 1080×1920 trên dữ liệu thử (mẫu hình FFmpeg + âm sine, có chữ ký review giả lập trong thư mục tạm) rồi chạy qa.py; CI thất bại nếu có test bị skip/expected-failure. **Chưa render video bằng footage USGS thật với review thật**, vì repo công khai không chứa MP4/giọng/logo/thông tin nhóm. CI pass không phải chứng nhận nộp bài.
2. Xác minh hash file **không chứng minh** license hay độ chính xác của hình. Phải xem clip, đối chiếu USGS trực tiếp.
3. Giọng nói có thể đọc sai tên riêng tiếng Hawaii; cần nghe và sửa script phát âm.
4. Nguồn tư liệu cho Kapoho Bay: dung nham vào biển tối **03/06**, video ghi **04/06**. Không ghi sai ngày đầu tiên.
5. Intro bắt buộc tên video/số nhóm/tên+MSSV/GE1013/logo trường, môn và sponsor; nếu nhóm có thành viên chương trình Tiếng Anh thì dùng Anh toàn bộ. Đây là repo công khai nên không commit MSSV, keys, media thật.
6. Sau khi xem/nghe và đối chiếu rubric, nhóm tự đăng và nộp link TikTok trước hạn nộp có trong PDF.

Đọc tiếp [RUNBOOK.md](RUNBOOK.md), [SCIENCE_AUDIT.md](SCIENCE_AUDIT.md), [AGENTS.md](AGENTS.md).

**Bảo vệ bản gốc:** `download_assets.py` từ chối MP4 thủ công không có SHA256 sidecar, thay vì tự ghi hash và tin file. Với URL gốc hoạt động, hãy chuyển file nghi vấn sang chỗ khác và chạy downloader để tự tải lại từ nguồn USGS.

## Bố cục, phụ đề và công bố giọng tổng hợp

- Khung 1080×1920 chia vùng cố định, không chồng nhau: hộp tiêu đề/chú thích (trên) · footage · phụ đề (y 1390–1610, tối đa 2 dòng) · nhãn giọng đọc (y≈1700) · dải credit (từ y 1842). Chữ tự thu nhỏ cho vừa; nếu vẫn quá dài, build **dừng** thay vì cắt bớt nội dung khoa học.
- Phụ đề được vẽ bằng Pillow và chèn ngay trong lần encode của từng cảnh (không cần libass, không encode lại lần hai). Thời gian chỉ lấy từ WordBoundary của TTS; chữ hiển thị được ánh xạ về đúng câu chữ trong `narration.json` (giữ dấu câu). `output/captions.srt` là bản phụ để soát/đăng caption.
- Khi `review.json.audio.synthetic_voice` là `true`, mọi cảnh có lời đọc hiện nhãn **"Giọng đọc tổng hợp (AI) · Edge TTS"** (tiếng Anh: "Synthetic AI voice"). Giọng thu âm người thật: người duyệt khai báo `false`.
- `python footage_report.py` đo từng clip (khung đen/đứng hình, viền đen hai bên) và đề xuất `start_seconds`/`crop` + ảnh xem trước 1 hình/giây trong `output/previews/`. **Chỉ là đề xuất**: không sửa timeline.json, không phát hiện được chữ/logo chồng lên cảnh đang chuyển động. Người duyệt phải xem, quyết định, sửa timeline rồi duyệt lại.

## Kiểm tra chất lượng & dấu vết đầu ra

- `download_assets.py` chỉ ghi `.sha256` + `.provenance.json` (URL gốc, URL cuối, ETag/Last-Modified, số byte, SHA256, thời lượng/kích thước/codec) **sau khi** đối chiếu Content-Length và giải mã toàn bộ luồng video thành công. Tải thiếu byte hay file hỏng bị xoá, không được ghi provenance.
- `build.py` dựng từng cảnh đúng `duration × 30` khung hình và kiểm tra lại; không loop/freeze/đệm hình. Âm thanh được ghép thành MỘT track: lời đọc chỉ được đệm im lặng, không bao giờ bị cắt. `crop` (tùy chọn, trong `timeline.json`) chỉ dùng khi người duyệt timeline đồng ý.
- `output/build_manifest.json` lưu SHA256 MP4, toàn bộ input (footage + provenance, lời thoại, review + chữ ký, logo, mọi file `.py`) và phiên bản ffmpeg/ffprobe/Python/Pillow/font. Input đổi trong lúc render → dừng.
- `qa.py` (fail-closed): thiếu ffmpeg/không đo được âm lượng = lỗi; 1080×1920 @30 fps; độ dài = timeline; lời đọc từng cảnh nghe được (đỉnh ≥ −20 dB, trung bình ≥ −40 dB); clipping 0 dBFS; **khung đen / đứng hình trong vùng footage** (thường là slate/logo USGS ở đầu clip → chọn `start_seconds` khác).
- Receipt chứng minh tính toàn vẹn, không chứng minh danh tính: ai chạy được build.py đều ghi được receipt. Duyệt cuối vẫn là người xem/nghe MP4.

**Nhóm chương trình tiếng Anh:** nếu trong nhóm có sinh viên hệ Tiếng Anh, phải thay toàn bộ `narration.json` và `timeline.json` sang tiếng Anh, cập nhật `group.course` và TTS giọng en-*. Strict gate chặn dấu tiếng Việt còn sót trên lời đọc/chữ hiện lên; kiểm tra tự động này không thay cho người duyệt ngôn ngữ.
