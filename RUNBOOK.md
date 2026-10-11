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
# Mặc định TTS trực tuyến Edge, giọng tiếng Anh en-US-GuyNeural (video nộp 100% tiếng Anh), không key.
# Chọn giọng nữ, cần ghi đè audio khi đã nghe và đồng ý bản script mới:
python pipeline.py prepare --assignment-pdf /path/to/file.pdf --voice en-US-ChristopherNeural --force-tts
```
Tự tải MP4 qua các URL USGS, tạo SHA256 sidecar và audio/{01..05}.mp3 + .timings.json. Tự tạo captions.srt từ TTS WordBoundary; **không có giả thời điểm âm thanh**.
- Nếu network/source thất bại: chạy lại downloader. Downloader KHÔNG chứng thực file tải tay (không có provenance); nếu URL gốc không còn hoạt động, tìm nguồn mới có URL/quyền rõ ràng, cập nhật assets.json sau khi tự kiểm tra.
- `qa.py` báo "black/frozen footage from …s": đó thường là slate/logo USGS ở đầu/cuối clip. Người duyệt chọn `start_seconds` mới trong timeline.json (rồi duyệt lại timeline); không được che bằng hình khác.
- Nếu video source quá ngắn: `python media_audit.py` báo lỗi; tìm thêm footage thật được duyệt hoặc sửa timeline. Không tự loop/freeze/cắt bỏ lời thoại.
- TTS phụ thuộc dịch vụ trực tuyến, có thể thay đổi/bị giới hạn; không được cam kết miễn phí lâu dài.
- TTS tạo giọng tổng hợp. Nếu bắt buộc audio 100% người thật, thu lời qua điện thoại -> assets/voiceover.wav; dùng `--no-tts --no-subtitles` và căn phụ đề thủ công.

## Kiểm tra trước render
```bash
python validate.py
python footage_report.py   # đề xuất start_seconds/crop + preview; người duyệt quyết định
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

## Human approvals gắn chặt với nội dung và chữ ký người duyệt
- Sau khi có footage, audio và logo thật, chạy `python review_hashes.py`. Script chỉ hiển thị expected digests (không in tên/MSSV), KHÔNG tự tick approved.
- Điền `review.json` từ `review.example.json`:
  - từng asset: `approved_manifest_sha256`, `approved_media_sha256`, `rights_evidence_excerpt`;
  - từng claim: `approved_claim_sha256`, `source_excerpt` trích từ USGS;
  - `script.approved_narration_sha256` và `script.approved_claim_set_sha256` (tập ID/cảnh của claim; xoá hay chuyển claim sẽ làm duyệt cũ mất hiệu lực);
  - `timeline.approved_timeline_sha256`: người duyệt đã xem thứ tự clip, `start_seconds`, `crop`, tiêu đề/chú thích trên màn hình;
  - `logos.approved_sha256`, `audio.approved_audio_digest`, `audio.mode`, và `audio.synthetic_voice` (true/false do người duyệt khai báo; Edge TTS bắt buộc `true`).
- `reviewed_by` phải trùng chính xác tên trong group.json, `reviewed_at` ISO8601 có timezone và không ở tương lai, `approved/rights_checked/source_read` là boolean `true`.
- Giọng thu âm: đặt `group.json.narration_audio_file` (mặc định `assets/voiceover.wav`, phải nằm trong `assets/`). Cùng một đường dẫn được dùng cho validate, digest duyệt, render và build receipt.

### Chữ ký người duyệt (bắt buộc với `validate.py --strict`)
Digest chỉ chứng minh *nội dung nào* được duyệt; bất kỳ ai sửa được JSON đều có thể điền digest. Vì vậy mỗi người có tên trong `reviewed_by` phải ký `review.json` bằng SSH key của chính mình:
1. Mỗi thành viên duyệt chọn một `reviewer_id` (ví dụ GitHub username, không dùng MSSV) và ghi vào `group.json.team_members[].reviewer_id`.
2. Thêm khóa CÔNG KHAI vào `reviewers.allowed_signers` và **commit** file đó (key thay đổi phải hiện trong lịch sử git):
   `<reviewer_id> namespaces="ge1013-review" ssh-ed25519 AAAA...`
3. Khi `review.json` đã hoàn tất, từng người tự ký trên máy mình rồi đặt chữ ký vào `review.sigs/<reviewer_id>.sig` (thư mục bị .gitignore):
   ```bash
   ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n ge1013-review review.json
   mv review.json.sig review.sigs/<reviewer_id>.sig
   ```
4. Sửa bất kỳ byte nào trong `review.json` sau khi ký → mọi chữ ký mất hiệu lực, phải ký lại.

Giới hạn: chữ ký không chống được người đang giữ private key chưa khoá hoặc người có quyền commit khóa mới. Không bao giờ ký thay người khác; AI/automation không được ký.

**Về file tải thủ công:** không dùng `download_assets.py` để chứng thực một MP4 tự đặt vào `assets/`. Nếu tệp thiếu sidecar, di chuyển tệp ấy ra ngoài và tải lại bằng script từ URL gốc USGS. Nếu nguồn không còn khả dụng, phải tìm nguồn mới có URL/rights rõ ràng và cập nhật manifest sau khi tự kiểm tra, tuyệt đối không tạo provenance giả.

**Không gửi video cũ:** mỗi lần render có `output/build_manifest.json`. Chạy `python qa.py` trước khi tải lên; input, source video, narration, review hoặc MP4 thay đổi đều bị phát hiện qua SHA256.

## Trình tự đầy đủ: tạo và kiểm tra video 120 giây
```bash
# 0. Công cụ: Python 3.10+, FFmpeg + ffprobe (macOS: brew install ffmpeg), OpenSSH, git
python -m pip install -r requirements.txt
make test                                   # kiểm thử xác định (render FFmpeg thật trên dữ liệu thử)
cp group.example.json group.json            # điền 3–5 thành viên, MSSV, reviewer_id (KHÔNG commit)
cp review.example.json review.json          # để trống; chỉ người duyệt điền

# 1. Chuẩn bị: tải footage gốc USGS (+provenance), logo, giọng TTS từng cảnh, phụ đề
python pipeline.py prepare --assignment-pdf /path/to/GE1013_TIKTOK.pdf [--voice en-US-GuyNeural] [--rate -5%]

# 2. Đo đạc để NGƯỜI quyết định cửa sổ clip / cắt viền (không tự áp dụng)
python footage_report.py                    # xem output/previews/*.png
python draft.py                             # bản XEM THỬ từ timeline.proposed.json: watermark đỏ, CHƯA DUYỆT,
                                            # placeholder cho nhóm/logo; KHÔNG được đăng. Đồng ý -> chép giá trị vào timeline.json

# 3. Người duyệt: đọc nguồn USGS, xem clip, nghe giọng; điền review.json từ digest
python review_hashes.py
#    mỗi người có tên trong reviewed_by ký: ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n ge1013-review review.json
#    rồi mv review.json.sig review.sigs/<reviewer_id>.sig

# 4. Dựng + QA kỹ thuật
python validate.py --strict
python pipeline.py render                   # = validate --strict -> build.py -> qa.py
open output/GE1013_Kilauea_2018_DRAFT.mp4   # xem/nghe TOÀN BỘ; đọc output/captions.srt

# 5. Duyệt bản cuối đúng file MP4 này (người, không phải AI), rồi kiểm tra phát hành
shasum -a 256 output/GE1013_Kilauea_2018_DRAFT.mp4
#    viết output/final_review.json (xem release_check.py), ký vào output/final_review.sigs/<reviewer_id>.sig
python release_check.py --export-final      # PASS -> output/GE1013_Kilauea_2018_FINAL.mp4 (bản sao đúng MP4 đã duyệt);
                                            # tự đăng TikTok và nộp link thủ công
```
Kiểm thử gọi dịch vụ ngoài (Edge TTS trực tuyến) tách riêng: `make test-external` (gửi một câu thử tới dịch vụ).

## Trường tùy chọn trong timeline (chỉ có hiệu lực khi người duyệt timeline)
- `start_seconds`, `crop {w,h,x,y}`: cửa sổ và vùng cắt của footage thật.
- `fill: "blur"`: nền là chính cảnh đó làm mờ/tối phía sau khung hình đầy đủ (không cắt chủ thể) thay cho viền đen.
- `field_audio_lufs` (−40…−20): lớp âm thanh hiện trường thật của clip, đo EBU R128, có limiter, nằm dưới lời đọc. Clip có track im lặng sẽ bị từ chối.
- `background {asset_id, start_seconds, crop?, credit}` trên intro/outro: footage thật làm nền mờ cho tiêu đề, có dòng credit.
- Toàn bộ mix được chuẩn hóa −16 LUFS, đỉnh ≤ −1,5 dBTP; mỗi cảnh chuyển tiếp mờ 0,25 s.

## Nhạc nền và watermark
- `python music.py timeline.proposed.json` tạo bản nhạc nền GỐC (tổng hợp bằng sóng sin qua FFmpeg, không dùng mẫu hay nhạc của bên thứ ba) vào `assets/music/score.wav`; mỗi cảnh một hợp âm theo mạch truyện, nhịp tim ở cảnh sụt lún, kết bằng hợp âm chủ. Bật bằng `"music": {"file": "assets/music/score.wav", "lufs": -27}` trong timeline; giọng đọc tự hạ nhạc (sidechain). Duyệt timeline phải ghi `approved_music_sha256`. Đây không phải âm thanh núi lửa.
- `python draft.py --no-watermark`: bản xem thử không watermark theo yêu cầu chủ dự án; manifest vẫn ghi UNAPPROVED. Bản FINAL chỉ đến từ `release_check.py --export-final`.
- Thông tin nhóm riêng tư để trong `group_info/` (đã .gitignore) → `group.json` và `assets/logos_from_assignment.png` (cũng bị ignore). Không commit tên/MSSV/logo.

