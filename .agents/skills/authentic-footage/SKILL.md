---
name: authentic-footage
description: Download and audit authentic public-science footage without generative alterations.
---

# Authentic footage audit
1. Đọc assets.json và truy cập source_page chính thức cho TỪNG video.
2. So khớp media đúng tệp, nhãn agency, địa điểm, captured_date, footage description và quyền dùng cụ thể.
3. Tải trực tiếp từ domain allowlist; tính SHA256; dùng ffprobe để ghi duration/streams.
4. Không re-use một clip làm bằng chứng cho sự kiện khác, kể cả nhìn tương tự.
5. Không đánh dấu human-approved hoặc license-approved; tạo danh sách pending để người phụ trách xác nhận.
6. Nếu thiếu footage hoặc giấy phép không rõ, báo BLOCKED và đề nghị footage thay thế từ tổ chức khoa học.
