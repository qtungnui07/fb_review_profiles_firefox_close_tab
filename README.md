# fb_review_profiles_firefox_close_tab

Công cụ hỗ trợ mở từng profile Facebook bằng trình duyệt Firefox (qua Selenium) để bạn xem lại (review) và lọc bạn bè thủ công một cách nhanh chóng. Tính năng nổi bật là tool có khả năng tự động đóng tab profile khi bạn bỏ qua (skip) hoặc sau khi đánh dấu xong.

## 🚀 Cài đặt

1. Đảm bảo bạn đã cài đặt [Python 3](https://www.python.org/) và trình duyệt [Firefox](https://www.mozilla.org/firefox/new/) trên máy tính.
2. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements_firefox.txt
   ```

## 📝 Chuẩn bị dữ liệu đầu vào (Input)

Vì lý do bảo mật thông tin cá nhân, các file dữ liệu người dùng (như `friends_input.txt`, `ids_only.txt`,...) đã được thiết lập `.gitignore` để không bị đẩy lên mã nguồn này. Do đó, sau khi clone code về, bạn cần **tự tạo file dữ liệu**.

Mặc định, tool sẽ ưu tiên đọc file có tên `friends_input.txt` cùng cấp thư mục với code. 

**Định dạng file `friends_input.txt`:**
Code tự động lấy và phân tích file theo block. Mỗi người là một cụm text:
```text
10001234567890
Nguyễn Văn A
Lượt thích 10 / 5
Số tin nhắn 2

10009876543210
Trần Thị B
Lượt thích 0 / 0
Số tin nhắn 0
```
- **Dòng ID:** Chứa chuỗi số định danh Facebook (từ 6-20 chữ số).
- **Dòng Tên:** Nằm ngay dưới dòng ID.
- **Dòng Tương tác (Tùy chọn):** Tool sẽ tìm các cụm từ chứa `Lượt thích X / Y` (trong đó X là likes, Y là comments) và `Số tin nhắn Z`.

*Tip: Bạn có thể copy/paste text từ các tool crawl dữ liệu tương tác bạn bè Facebook vào file txt này, tool sẽ tự động bóc tách ID và điểm tương tác.*

## ⚙️ Cách sử dụng

Chạy lệnh mặc định:
```bash
python fb_review_profiles_firefox.py --input friends_input.txt
```

**Các tham số tùy chọn (Options):**
- `--only-zero`: Chỉ lấy ra những bạn bè có tương tác bằng 0 (0 like, 0 cmt, 0 tin nhắn).
- `--url-style slash`: Mở đường link theo định dạng `facebook.com/<id>` (mặc định là `facebook.com/profile.php?id=<id>`).
- `--close-after-action`: Bật tính năng tự động đóng tab sau khi bạn thực hiện mọi thao tác đánh dấu (`Enter`/`k`/`u`). Nếu không dùng tham số này, tab chỉ tự đóng khi bạn nhấn skip (`s`).

## ⌨️ Phím tắt khi thao tác

Khi script chạy, nó sẽ tự mở từng tab. Bạn chuyển qua lại giữa màn hình Terminal/Command Line và gõ các phím:

- `Enter` = Đã xem qua (Reviewed)
- `k`     = Giữ lại bạn này (Keep)
- `u`     = Đã gỡ bạn bằng tay trên Facebook (Unfriended manually)
- `s`     = Bỏ qua (Skip) và tự động đóng tab hiện tại
- `b`     = Quay lại người trước đó (Back)
- `q`     = Thoát chương trình (Quit)

## 📁 Các file tự động sinh ra trong quá trình chạy
Quá trình chạy tool sẽ sinh ra một số file/thư mục. Những dữ liệu này cũng sẽ được tự động bỏ qua (ignore) không đẩy lên Git:
- **`firefox_fb_profile/`**: Thư mục lưu trữ phiên trình duyệt Firefox. Lần chạy đầu tiên bạn cần tự đăng nhập tay vào Facebook trên trình duyệt bật lên. Lần sau trình duyệt sẽ dùng profile này để bạn không cần đăng nhập lại.
- **`review_progress.json`**: Lưu lại trạng thái xử lý (ai đã duyệt, ai được keep,...). Nhờ file này, nếu bạn tắt tool giữa chừng, lần sau mở lên tool sẽ không bắt bạn duyệt lại từ đầu.
- **`review_results.csv`**: File thống kê (dạng Excel/CSV) xuất kết quả các thao tác bạn đã chọn.
- **`review_queue.csv` / `ids_only.txt`**: File hàng chờ các profile và ID đang chuẩn bị được duyệt.

> **LƯU Ý QUAN TRỌNG:** 
> - Tool chỉ tự động mở tab và đóng tab theo lệnh của bạn. Tool **KHÔNG** tự động gỡ bạn bè (unfriend) hay click lung tung trên Facebook của bạn.
> - Đây là thao tác thủ công, an toàn cho tài khoản Facebook vì bạn vẫn là người tự ra quyết định và thao tác (chỉ giúp bạn mở nhanh thay vì tự bấm tay từng người).
