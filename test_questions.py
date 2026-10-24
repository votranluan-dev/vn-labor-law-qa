import time
from history_aware_generation import ask_question, reset_history

# Mỗi câu: (câu hỏi, danh sách từ khóa BẮT BUỘC có trong câu trả lời)
# Từ khóa so sánh không phân biệt hoa thường.
TESTS = [
    ("Người lao động nghỉ việc phải báo trước bao nhiêu ngày?", ["45", "30", "03"]),
    ("Thời gian thử việc tối đa là bao nhiêu ngày?", ["180", "60", "30", "06"]),
    ("Lao động nữ được nghỉ thai sản bao lâu?", ["06 tháng", "02 tháng"]),
    ("Thời giờ làm việc bình thường tối đa là bao nhiêu giờ trong một ngày?", ["08 giờ"]),
    ("Người lao động được nghỉ phép năm bao nhiêu ngày?", ["12", "14", "16"]),
    ("Làm thêm giờ vào ngày lễ được trả lương bao nhiêu phần trăm?", ["300%"]),
    ("Hợp đồng lao động có những loại nào?", ["xác định thời hạn"]),
    ("Người sử dụng lao động có được giữ bản chính giấy tờ tùy thân của người lao động không?", ["không được", "Điều 17"]),
    ("Công ty nợ lương tôi mấy tháng rồi thì tôi làm gì được?", ["không cần báo trước", "Điều 35"]),
    ("Tôi tự ý nghỉ việc mấy ngày liền thì công ty cho nghỉ luôn có đúng không?", ["cộng dồn", "lý do chính đáng", "Điều 125"]),
    ("Mức đóng bảo hiểm xã hội bắt buộc là bao nhiêu phần trăm lương?", ["không đủ thông tin"]),
]


def run_tests():
    passed = 0
    report = []
    start = time.time()

    for i, (question, keywords) in enumerate(TESTS, 1):
        reset_history()  # mỗi câu độc lập
        t0 = time.time()
        answer = ask_question(question)
        elapsed = time.time() - t0

        low = answer.lower()
        missing = [k for k in keywords if k.lower() not in low]
        ok = not missing
        passed += ok
        report.append((i, ok, missing, elapsed, question))

    print("\n" + "=" * 70)
    print("KẾT QUẢ TEST")
    print("=" * 70)
    for i, ok, missing, elapsed, question in report:
        status = "ĐẠT   " if ok else "KHÔNG ĐẠT"
        print(f"{i:2d}. [{status}] {elapsed:5.0f}s  {question[:60]}")
        if missing:
            print(f"      thiếu: {missing}")
    print(f"\nTổng: {passed}/{len(TESTS)} đạt | Thời gian: {(time.time()-start)/60:.1f} phút")


if __name__ == "__main__":
    run_tests()