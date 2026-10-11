# SCIENCE AUDIT — sự kiện Kīlauea 2018

**Mục đích:** bằng chứng đối chiếu được cho mỗi phân cảnh, không phải chứng nhận tự động mọi phát biểu đều đúng. Các mục đã được đối chiếu với văn bản trên USGS; nhóm vẫn phải tự xem video và xác nhận nguồn gốc, quyền sử dụng.

| Cảnh | Điều kiện đúng | Nguồn gốc |
|---|---|---|
| 16/05 khe nứt 18 | Video USGS khoảng 02:00 HST 16/05/2018, có âm thanh hiện trường. | https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-16-2018 |
| 22/05 khe nứt 22 | Footage UAS đêm 22/05, bài đăng ngày 24/05. | https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-24-2018 |
| 03–04/06 Kapoho Bay | Lava từ fissure 8 **vào biển tối 03/06** (muộn nhất 22:30); USGS quay clip sáng và chiều **04/06**. Không khẳng định hiện tượng bắt đầu ngày 04/06. | https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-june-4-2018 |
| 30/06 đỉnh núi | Video 30/06 ghi đá rơi/cột bụi nhỏ; bài xuất bản 02/07. Không mô tả cảnh này là camera ghi lại toàn bộ đáy miệng núi sụp. | https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-july-2-2018 |

Bản tổng quan cơ chế magma di chuyển, khe nứt mở 03/05, magma đỉnh suy giảm và sụt lún: https://www.usgs.gov/volcanoes/kilauea/science/2018-lower-east-rift-zone-eruption-and-summit-collapse-kilauea

Công bố chuyên môn USGS/Neal et al. 2019: https://www.usgs.gov/publications/2018-rift-eruption-and-summit-collapse-kilauea-volcano

## Quy trình kiểm duyệt bắt buộc
1. Đọc claims.json, mở URL chính thức và xem footage MP4 đã tải. Không dùng footage trong ngữ cảnh sai.
2. Đối chiếu lời dẫn trong narration.json; chú ý ngày ghi hình khác với ngày công bố, và ngày bắt đầu sự kiện có thể khác ngày quay.
3. Điền review.json: từng asset và **từng claim** có approved, reviewed_by, reviewed_at, rights_checked/source_read.
4. Nếu đổi script, tạo lại MP3 và WordBoundary; không dùng lại phụ đề cũ.
5. Nội dung video phải đạt các yêu cầu trong đề bài môn học; kiểm tra tên/MSSV, logo trường/môn/sponsor, hình/âm, thời lượng.
6. AI chỉ thực hiện kiểm tra cấu trúc, so khớp timestamp và tạo bản nháp. **Không được tự đánh dấu nội dung là đúng khoa học.**

## Chưa kiểm chứng xong
Chưa tự mở và xem đầy đủ các MP4 gốc ở môi trường chạy này; chưa có video cuối cùng hoặc giọng đọc do nhóm phê duyệt. Các URL nguồn tồn tại và có mô tả khoa học phù hợp, nhưng audit của con người vẫn bắt buộc.

## Trạng thái rà soát độc lập (AI, 2026-10-11) — KHÔNG phải phê duyệt
Rà soát do agent thực hiện; mọi trang www.usgs.gov đều trả 403/405 cho truy cập tự động, nên phần lớn trích dẫn chỉ đến từ đoạn trích của công cụ tìm kiếm. Chỉ bản ghi pubs.usgs.gov của Neal et al. (2019) được đọc trực tiếp. Người duyệt phải tự mở từng trang.

**BLOCKED — Kapoho (claim `kapoho`, asset `jun04_kapoho`):**
- Không tìm thấy trang `.../photo-and-video-chronology-kilauea-june-4-2018` (đã thấy các chronology 1/6, 11/6, 20/6, 25/6). Các mốc 06:15 / 13:38 HST và "lúc 22:30 ngày 3/6" xuất hiện trên trang *media item* riêng của USGS, không phải trang chronology đang trích.
- `compilation.mp4` (68,47 s) khớp độ dài 1:08 của mục "Video Compilation of Kapoho Bay Ocean Entry", chưa gắn được với trang 4/6.
- Không duyệt claim/asset này cho đến khi người duyệt mở được trang USGS chính xác chứa đúng tệp video, đọc phần quyền sử dụng của chính tệp đó, rồi sửa `source_page`/`reference` (việc sửa sẽ làm duyệt cũ mất hiệu lực, đúng như thiết kế).

**Cần người quyết định (chưa xác thực):**
- Cửa sổ clip: `start_seconds = 0` hiện lấy cả logo/tiêu đề/slate đen USGS (qa.py sẽ báo lỗi). `python footage_report.py` đề xuất (đo trên tệp thật): cảnh 1 ≈ 6,9 s + cắt viền đen hai bên `{"w":728,"h":1080,"x":598,"y":0}`; cảnh 2 — máy dò không thấy tiêu đề chồng trên cảnh động, xem tay thấy logo 0–1 s và tiêu đề đến ≈4 s; cảnh 3 ≈ 11,1 s (thuộc bản quay buổi sáng); cảnh 4 ≈ 4,6 s. Người duyệt phải xem và tự quyết.
- Diễn đạt: "dung nham trào lên" (cảnh 1) cho cảnh phun bắn (spattering); tiêu đề "ĐỈNH NÚI SỤT LÚN" trên cảnh đá rơi + cột bụi nhỏ (cảnh 4); cảnh 2 lời đọc nói về magma dưới lòng đất trong khi hình là dòng dung nham trên mặt.
- Câu chưa có claim riêng: "Năm 2018 … hàng loạt khe nứt" (cảnh 1, chỉ có bằng chứng ở `rift_activity` cảnh 2), "Vì sao … cách xa đỉnh núi?" (cảnh 2), "Một núi lửa có thể thay đổi …" (cảnh 5). Gate tự động chỉ kiểm tra mỗi *cảnh* có claim, không kiểm tra từng *câu*.
- Credit: trang USGS ghi footage khe nứt 22 là "courtesy of the U.S. Department of the Interior Office of Aviation Services"; dải credit trong video in đúng `agency_credit`, nhưng chú thích cảnh và outro chỉ ghi "USGS".
- Video đỉnh núi: media item có ngày 1/7, `assets.json` ghi "published July 2" (ngày chronology).

