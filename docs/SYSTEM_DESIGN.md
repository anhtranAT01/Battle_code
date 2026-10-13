# 🏆 BATTLECODE RPS 9×9 — HỆ THỐNG ĐẤU TRƯỜNG TRÍ TUỆ NHÂN TẠO

> **Tài Liệu Đặc Tả Thiết Kế Hệ Thống & Giới Thiệu Tính Năng Nền Tảng**  
> *Một sân chơi chiến thuật đỉnh cao, nơi các lập trình viên tranh tài bằng tư duy thuật toán và bản lĩnh làm chủ trí tuệ nhân tạo.*

---

## 🌟 1. Giới Thiệu Nền Tảng (What is Battlecode RPS 9×9?)

**Battlecode RPS 9×9** là một nền tảng thi đấu cờ tự động hoá toàn diện, được thiết kế nhằm mang lại trải nghiệm thi đấu lập trình hấp dẫn, công bằng và kịch tính cho sinh viên. 

Thay vì chỉ viết code giải các bài toán tĩnh đơn điệu, người tham gia sẽ đóng vai trò là những **kiến trúc sư chiến thuật**, xây dựng các thuật toán điều khiển đạo quân Oẳn Tù Tì (Búa - Bao - Kéo) trên một bàn cờ rộng lớn 9×9. 

Hệ thống hoạt động theo mô hình **Đấu Trường Tập Trung (Centralized Arena)**:
* Người chơi thỏa sức sáng tạo và nộp bot lên máy chủ.
* Máy chủ tự động ghép cặp, điều phối trận đấu ngầm, ghi lại toàn bộ diễn biến.
* Mọi khoảnh khắc kịch tính đều được tái hiện sống động qua **Trình chiếu Replay trực quan**, mang lại cảm xúc hồi hộp như đang theo dõi một giải đấu Esport đích thực.

---

## 🎮 2. Trò Chơi Chiến Thuật: Cờ Oẳn Tù Tì 9×9

Trọng tâm của nền tảng là một biến thể cờ bàn độc đáo, kết hợp giữa sự cân não của Cờ Vua và tính khắc chế bất ngờ của Oẳn Tù Tì:

```
[Rank 9]   ✌ ✌ ✌   ✋ ✋ ✋   ✊ ✊ ✊     <--- Player 2 (Xanh) - Ô đích: a1 (góc dưới-trái)
[Rank 8]   .  .  .   .  .  .   .  .  .
[Rank 7]   .  .  .   .  .  .   .  .  .
[Rank 6]   .  .  .   .  .  .   .  .  .
[Rank 5]   .  .  .   .  .  .   .  .  .
[Rank 4]   .  .  .   .  .  .   .  .  .
[Rank 3]   .  .  .   .  .  .   .  .  .
[Rank 2]   .  .  .   .  .  .   .  .  .
[Rank 1]   ✊ ✊ ✊   ✋ ✋ ✋   ✌ ✌ ✌     <--- Player 1 (Đỏ)   - Ô đích: i9 (góc trên-phải)
          a  b  c   d  e  f   g  h  i
```

### 2.1 Bàn cờ & Đạo quân
* **Quy mô bàn cờ**: Lưới ma trận **9×9** với 81 ô tọa độ (từ cột `a` đến `i`, từ hàng `1` đến `9`).
* **Lực lượng mỗi bên**: Gồm 9 quân cờ chia đều cho 3 loại binh chủng:
  * **3 Quân Đấm (Rock - ✊)**
  * **3 Quân Lá (Paper - ✋)**
  * **3 Quân Kéo (Scissors - ✌)**
* **Vị trí xuất phát**:
  * **Player 1 (Đội Đỏ)**: Trấn giữ hàng 1 (`a1` đến `i1`), mục tiêu là tiến đánh tới ô góc **`i9`**.
  * **Player 2 (Đội Xanh)**: Trấn giữ hàng 9 (`a9` đến `i9`), mục tiêu là tiến đánh tới ô góc **`a1`**.

### 2.2 Quy tắc di chuyển & Giao tranh
* **Cách đi quân**: Mỗi lượt, quân cờ có thể di chuyển 1 ô theo **8 hướng** (ngang, dọc, chéo — tương tự quân Vua trong cờ vua).
* **Luật khắc chế Oẳn Tù Tì**:
  * ✊ **Đấm** đập tan ✌ **Kéo**
  * ✌ **Kéo** cắt đứt ✋ **Lá**
  * ✋ **Lá** bao bọc ✊ **Đấm**
* **Chiến đấu & Chặn đường**:
  * Một quân cờ **chỉ có thể đi vào ô đối thủ nếu nó khắc chế và ăn được quân đó**.
  * Hai quân cùng loại (ví dụ ✊ gặp ✊) **không thể ăn nhau** mà tạo thành bức tường cản trở lẫn nhau, tạo nên chiều sâu chiến thuật che chắn và chặn đường cực kỳ biến hóa.

### 2.3 Ba con đường dẫn tới vinh quang (Win Conditions)
Để chiến thắng, bot có thể theo đuổi các trường phái chiến thuật khác nhau:
1. 🚩 **Chiến thuật Đột phá (Goal Rush)**: Đưa bất kỳ một quân cờ nào của mình vượt qua phòng tuyến đối phương và đặt chân an toàn lên **ô đích** của đối thủ (`i9` cho P1 hoặc `a1` cho P2).
2. ⚔️ **Chiến thuật Diệt chủng (Wipeout Strike)**: Truy lùng và tiêu diệt sạch toàn bộ **3 quân của bất kỳ một loại nào** của đối thủ (ví dụ: ăn hết cả 3 quân Kéo của đối phương). Khi đó đối thủ mất cân bằng sinh thái chiến đấu và thua ngay tức khắc!
3. ⏱️ **Chiến thuật Sinh tồn & Áp đảo (Survival Tiebreaker)**: Nếu sau **200 lượt đi** chưa bên nào chạm đích hay diệt sạch quân, bên nào còn **nhiều quân cờ sống sót hơn** trên bàn cờ sẽ giành chiến thắng.
4. 🛑 **Xử thua kỹ thuật**: Nếu bot của người chơi bị sập (crash), suy nghĩ quá thời gian cho phép (1 giây/lượt) hoặc trả về nước đi không hợp lệ, hệ thống sẽ truất quyền thi đấu và trao chiến thắng ngay lập tức cho đối thủ.

---

## 🚀 3. Hệ Thống Mang Lại Những Gì Cho Người Tham Gia? (Player Experience)

Nền tảng được xây dựng với phương châm **"Dễ tiếp cận - Khó thành thạo - Trải nghiệm cuốn hút"**:

```
[Tải Starter Kit] ──> [Luyện Tập Máy Nhà] ──> [Kéo-Thả Nộp Bot] ──> [Thách Đấu FFA] ──> [Xem Replay Sống Động]
```

### 3.1 Bộ Hỗ Trợ Tận Răng (Starter Kit & Local Arena)
Sinh viên không cần phải bắt đầu từ con số không:
* **Mẫu Bot chuẩn (`bot_template.py`)**: Hướng dẫn rõ ràng cách đọc bàn cờ, kiểm tra các nước đi hợp lệ và ra quyết định.
* **Bot AI Mẫu (`heuristic_bot.py`)**: Một bot có sẵn thuật toán đánh giá đa tầng thông minh (biết ưu tiên ăn bàn khi có cơ hội, biết né đòn nguy hiểm, biết tính khoảng cách Manhattan/Chebyshev về đích).
* **Đấu trường giả lập tại máy cá nhân (`local_arena.py`)**: Cho phép sinh viên chạy kiểm thử hàng trăm trận giữa các phiên bản bot của mình ngay trên máy tính mà không cần kết nối mạng hay gửi mã nguồn lên server. Hỗ trợ tự động đổi bên (`swap-sides`) và xuất bảng phân tích tỷ lệ thắng chi tiết.

### 3.2 Quy trình nộp bài "Một chạm" & Bảo mật mã nguồn 100%
* **Giao diện kéo-thả trực quan**: Chỉ cần kéo file code Python thả vào trang cá nhân.
* **Bộ lọc kiểm tra an toàn tức thì**: Hệ thống tự động phân tích cú pháp code chỉ trong vài mili-giây, thông báo ngay lập tức nếu code thiếu hàm điều khiển hoặc chứa lỗi cú pháp.
* **Bảo vệ chất xám tuyệt đối**: Mã nguồn của sinh viên được lưu trữ độc quyền trong vùng an toàn của server, **không bất kỳ đối thủ nào có thể xem trộm hoặc sao chép ý tưởng chiến thuật**.

### 3.3 Đấu Trường Tự Do (FFA Arena)
* **Thách đấu mọi đối thủ**: Người chơi có thể lựa chọn thách đấu bất kỳ người nào trên bảng xếp hạng chỉ bằng một nút click chuột.
* **Xử lý ngầm không gián đoạn**: Trận đấu được đẩy vào hàng đợi và chạy ngầm độc lập. Người chơi không phải ngồi chờ đợi mà có thể tiếp tục duyệt web hoặc viết code phiên bản bot tiếp theo.

### 3.4 Trình Chiếu Replay 9×9 Tương Tác Cực Đỉnh (Visualizer)
Mỗi trận đấu sau khi kết thúc đều để lại một bản ghi Replay hoàn chỉnh, cho phép người chơi "thưởng thức" trận đánh như một video trực tiếp:
* **Bàn cờ sống động**: Thể hiện trực quan từng quân cờ với biểu tượng ✊, ✋, ✌ và màu sắc sắc nét phân biệt giữa hai phe Đỏ và Xanh.
* **Bộ điều khiển toàn diện**:
  * ⏯️ Nút **Phát / Tạm dừng (Play / Pause)** tự động.
  * ⏩ Nút **Tua nhanh tốc độ (1x, 2x, 4x)** giúp xem nhanh các trận đấu dài 200 lượt.
  * 🎚️ **Thanh trượt thời gian (Scrubber Slider)**: Cho phép kéo chuột tới bất kỳ thời điểm nào của trận đấu để xem lại bước ngoặt chiến thuật.
  * ⌨️ **Phím tắt tiện lợi**: Bấm phím cách (Space) để Play/Pause, phím Mũi tên Trái/Phải để lùi/tiến từng nước.
* **Bảng đếm quân số thời gian thực**: Theo dõi trực tiếp số lượng quân ✊, ✋, ✌ còn lại của từng bên sau mỗi pha giao chiến. Quân nào bị tiêu diệt sạch sẽ chuyển sang trạng thái cảnh báo!
* **Bảng lịch sử ký hiệu nước đi chuẩn (SAN Notation)**: Ghi lại từng nước cờ dưới dạng ký hiệu cờ quốc tế sinh động (ví dụ: `✊a1-a2`, `✋d1xe2(✌)`), bấm vào nước đi nào là bàn cờ nhảy ngay tới lượt đó.
* **Hiệu ứng vinh danh**: Khi trận đấu kết thúc, hệ thống bật bảng thông báo người thắng cuộc kèm nguyên nhân thắng thuyết phục (Chạm đích, Diệt sạch quân, hay Ưu thế quân số).

---

## 🏆 4. Hệ Thống Giải Đấu & Xếp Hạng Kịch Tính (Tournament Mechanics)

Hệ thống được thiết kế theo format giải đấu chuyên nghiệp nhiều giai đoạn, giữ lửa cạnh tranh từ đầu tới cuối:

```
[Vòng Bảng FFA (Ngày 1 -> n)]               [Vòng Chung Kết (Ngày n+1)]             [Vinh Danh Tổng Kết]
  - Đấu tự do tính điểm Elo                    - Top 8 / Top 16 hạt giống               - Điểm tổng hợp Elo + Playoff
  - Khung giờ vàng mở cổng                     - Thể thức loại trực tiếp BO3            - Trao cúp Vô Địch & Giải thưởng
  - Hệ số nhân Elo ngẫu nhiên (x)              - Cây sơ đồ nhánh đấu trực quan
```

### 4.1 Vòng Đua Rank Tự Do (Giai đoạn Ngày $1 \dots n$)
* **Khung giờ mở cổng cố định**: Cổng thi đấu chỉ mở vào "khung giờ vàng" hàng ngày (ví dụ 19h00 - 21h00), tạo không khí sôi động khi toàn bộ cộng đồng sinh viên cùng trực tuyến thi đấu và theo dõi.
* **Hệ số nhân Elo bí ẩn ($x \in [1.0, 3.0]$)**: Mỗi ngày, Ban tổ chức áp dụng một hệ số nhân Elo ngẫu nhiên. Trận đấu trong ngày có hệ số cao sẽ giúp các bot mới nổi có cơ hội "bứt phá ngoạn mục" lên đỉnh bảng xếp hạng, lội ngược dòng trước các đối thủ đi trước!
* **Bảng xếp hạng thời gian thực**: Cập nhật tức thời vị trí thứ hạng, điểm Elo, số trận Thắng - Thua - Hòa và trạng thái sẵn sàng của bot.

### 4.2 Vòng Chung Kết Loại Trực Tiếp (Ngày $n+1$ - Playoff Bracket)
* **Tuyển chọn tinh hoa**: Hệ thống tự động lọc ra Top 8 (hoặc Top 16) đấu thủ có phong độ xuất sắc nhất giai đoạn vòng bảng.
* **Phân nhánh hạt giống chuẩn Quốc tế**: Tự động chia cặp đấu để các hạt giống hàng đầu không chạm trán nhau quá sớm (Hạt giống #1 đối đầu #8, #4 đối đầu #5, #2 đối đầu #7, #3 đối đầu #6).
* **Thể thức BO3 (Best of 3)**: Mỗi cặp đấu thi đấu 3 ván để chọn ra người chiến thắng xứng đáng, loại bỏ yếu tố may rủi.
* **Cây sơ đồ nhánh đấu trực quan**: Giao diện hiển thị sơ đồ thi đấu dạng cây (Bracket View) cập nhật tỉ số và lộ trình tiến vào trận Chung kết trong mơ.

### 4.3 Cách Tính Điểm Tổng Kết Toàn Diện
Người chiến thắng chung cuộc là người dung hòa được cả phong độ đường dài và bản lĩnh đối đầu:
$$\text{Điểm Tổng Kết} = 50\% \times \text{Điểm Elo Chuẩn Hóa} + 50\% \times \text{Điểm Thành Tích Playoff}$$
* **Điểm Vòng Bảng**: Chuẩn hóa điểm Elo toàn bộ thí sinh về thang điểm 100.
* **Điểm Vòng Playoff**:
  * 🥇 **Quán Quân (Vô địch)**: 100 điểm
  * 🥈 **Á Quân**: 80 điểm
  * 🥉 **Top 4 (Bán kết)**: 60 điểm
  * 🎖️ **Top 8 (Tứ kết)**: 40 điểm
  * 🎗️ **Top 16**: 20 điểm

---

## 🛠️ 5. Hệ Thống Mang Lại Những Gì Cho Ban Tổ Chức? (Organizer & Admin Experience)

Ban tổ chức giải đấu không cần phải thao tác thủ công phức tạp mà có một **Trung tâm Điều Hành (Admin Dashboard)** đầy quyền năng:

| Tính Năng Ban Tổ Chức | Giá Trị Mang Lại |
| :--- | :--- |
| **Bật/Tắt Cổng Đấu 1 Chạm** | Khóa hoặc mở cổng thách đấu bất kỳ lúc nào, kể cả ngoài khung giờ mặc định. |
| **Điều Chỉnh Hệ Số Nhân $x$** | Tùy chỉnh hệ số nhân điểm Elo của ngày hôm nay chỉ với một ô nhập liệu. |
| **Kiểm Soát Giới Hạn Trận Đấu** | Điều chỉnh số lượt tối đa (ví dụ 200 lượt) hoặc thời gian suy nghĩ tối đa cho từng nước cờ (ví dụ 1.0 giây). |
| **Tạo Bảng Playoff Tự Động** | Chỉ cần bấm nút *"Tạo Nhánh Playoff"*, hệ thống tự động lọc danh sách Top hạt giống, sắp xếp cặp đấu và khởi tạo toàn bộ các trận đấu vòng loại trực tiếp. |
| **Giám Sát Toàn Diện** | Theo dõi mọi trận đấu đang diễn ra, xem chi tiết lịch sử và phát hiện các trường hợp bot vi phạm. |

---

## 🛡️ 6. Độ Ổn Định & Tính Công Bằng Tuyệt Đối (Fair Play & Security)

Để một giải đấu AI thành công, tính công bằng và an toàn là yếu tố sống còn. Nền tảng được thiết kế với cơ chế tự vệ 3 lớp:

```
[Mã Nguồn Bot] ──> [Lớp 1: AST Security Sandbox] ──> [Lớp 2: Isolated Process Runner] ──> [Lớp 3: Strict 1.0s Timeout Enforcement]
```

1. **Lớp 1 - Bộ quét mã độc tự động (AST Security Filter)**:
   * Chặn đứng mọi hành vi can thiệp hệ điều hành, đọc ghi file lén lút, kết nối Internet hoặc đào bới bộ nhớ server.
   * Chặn các thủ thuật phản chiếu (Reflection/Dunder exploits) cố tình vượt rào.
2. **Lớp 2 - Phòng đấu cô lập (Subprocess Worker Isolation)**:
   * Mỗi trận đấu diễn ra trong không gian bộ nhớ riêng biệt. Bot A và Bot B hoàn toàn không thể chạm vào biến số hay dữ liệu của nhau.
   * Lọc sạch toàn bộ các lệnh `print()` hoặc ghi log rác của người chơi, đảm bảo đường truyền tín hiệu của trận đấu luôn thông suốt.
3. **Lớp 3 - Đồng hồ bấm giờ tuyệt đối (Turn-by-turn Watchdog)**:
   * Mỗi nước đi chỉ có tối đa **1.0 giây** để tính toán.
   * Nếu bot bị rơi vào vòng lặp vô tận (như `while True: pass`) hoặc cố tình gọi lệnh tạm dừng (`sleep`), hệ thống lập tức cưỡng chế chấm dứt tiến trình và xử thua mà không làm máy chủ bị đơ hay chậm lại.

---

## 💻 7. Trải Nghiệm Khởi Chạy "Zero Hassle" (Vận Hành Trong 5 Giây)

Nền tảng được tối ưu hóa tối đa về mặt triển khai:
* **Không cần cấu hình phức tạp**: Không phụ thuộc các công cụ cài đặt cồng kềnh, không lo xung đột môi trường.
* **Khởi chạy bằng 1 dòng lệnh duy nhất**:
  ```powershell
  python main.py
  ```
* **Tự động hóa hoàn toàn**:
  * Tự động khởi tạo cơ sở dữ liệu.
  * Tự động tạo sẵn tài khoản quản trị Admin (`admin` / `admin123`).
  * Tự động nạp sẵn các bot mẫu vào hệ thống để người dùng vào trải nghiệm và đấu thử ngay lập tức.
* **Mở rộng dễ dàng**: Khi tổ chức giải đấu nội bộ hoặc trực tuyến, hệ thống dễ dàng kết hợp với các giải pháp mạng (như Cloudflare Tunnel hoặc mạng nội bộ LAN) để hàng trăm sinh viên cùng truy cập vào một địa chỉ web duy nhất.

---

## 🎯 8. Tổng Kết: Giá Trị Cốt Lõi Của Battlecode RPS 9×9

| Tiêu Chí | Battlecode RPS 9×9 Đem Lại |
| :--- | :--- |
| **Tính Sáng Tạo** | Biến thể cờ 9×9 độc đáo, kích thích sinh viên thử nghiệm từ thuật toán Heuristic, Minimax tới Alpha-Beta hay Học Tăng Cường (Reinforcement Learning). |
| **Tính Hấp Dẫn** | Đấu trường Elo kịch tính hàng ngày, hệ số điểm nhân động, vòng chung kết Playoff như giải đấu thể thao điện tử. |
| **Trải Nghiệm Thị Giác** | Trình chiếu Replay 9×9 mượt mà, đầy đủ tính năng tua chậm, nhảy cóc, thống kê quân số trực quan. |
| **Sự Tiện Lợi** | Starter Kit có sẵn bot mẫu và sàn đấu máy nhà giúp sinh viên làm quen ngay trong 10 phút. |
| **Sự Tin Cậy** | Bảo mật mã nguồn, chống treo máy chủ, phân xử thắng thua công tâm và minh bạch 100%. |

---
*Tài liệu được biên soạn phục vụ công tác giới thiệu, tổ chức giải đấu và trải nghiệm người dùng của nền tảng Battlecode RPS 9×9 Platform.*
