Bản Firefox có tự đóng tab khi skip

Cài:
    pip install -r requirements_firefox.txt

Chạy:
    python fb_review_profiles_firefox.py --input friends_input.txt

Chỉ người 0 tương tác:
    python fb_review_profiles_firefox.py --input friends_input.txt --only-zero

Dùng dạng facebook.com/<id>:
    python fb_review_profiles_firefox.py --input friends_input.txt --url-style slash

Nếu muốn Enter/k/u cũng tự đóng tab sau khi đánh dấu:
    python fb_review_profiles_firefox.py --input friends_input.txt --close-after-action

Phím:
    Enter = reviewed
    k     = keep
    u     = đã tự gỡ bằng tay
    s     = skip và tự đóng tab hiện tại
    b     = quay lại, đồng thời đóng tab hiện tại
    q     = thoát

Lưu ý:
    - Script dùng Firefox Selenium, nên nó mở cửa sổ Firefox riêng.
    - Lần đầu bạn đăng nhập Facebook trong cửa sổ đó.
    - Sau đó login được lưu trong thư mục firefox_fb_profile.
    - Script không tự gỡ bạn bè, không tự click nút Facebook.
