# CLAUDE.md

Đọc AGENTS.md trước. Áp dụng các guardrail cho footage thực, khoa học có nguồn, bản quyền và dữ liệu cá nhân cho tất cả thay đổi.

Phân vai khuyến nghị:
- Claude/ChatGPT Research: nghiên cứu USGS, lập claims và metadata.
- Reviewer độc lập: phát hiện mâu thuẫn, kiểm tra ngày quay và độ chính xác trước render.
- Python/FFmpeg: dựng deterministic từ timeline và media đã được nhóm approve.
- Human: chấp thuận usage rights, kịch bản và đầu ra trước đăng.

Với mọi output phải liệt kê: bằng chứng đã có; điểm chưa được xác thực; lệnh tái tạo; giới hạn của tự động hóa. Không khẳng định đã duyệt thay người dùng.

- Mandatory: run python review_hashes.py (read-only); require user to sign all approvals in review.json. Never auto-populate true/name/ISO time/source excerpts.
- Require successful python validate.py --strict, python pipeline.py render, python qa.py and human visual/audio/scientific verification. CI alone is never end-to-end certification.
