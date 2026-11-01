#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# LINUX UTILITY & AUTOMATION TOOLKIT
# Tổng hợp các lệnh xử lý văn bản, tìm kiếm, quản lý process và bảo mật hệ thống
# ==============================================================================

# --- 1. XỬ LÝ VĂN BẢN VÀ DỮ LIỆU (AWK, SED, GREP, SORT, UNIQ) ---
process_text_data() {
    local file="${1:-textfile.txt}"
    [[ -f "$file" ]] || { echo "Lỗi: Không tìm thấy file $file"; return 1; }

    echo "=== [1.1] Lọc dòng có cột 2 là số và > 60 ==="
    awk '$2 ~ /^[0-9]+$/ && $2 > 60' "$file"

    echo "=== [1.2] Thống kê tần suất từ xuất hiện nhiều nhất ==="
    tr ' ' '\n' < "$file" | sort | uniq -c | sort -nr | head -n 10

    echo "=== [1.3] Lọc bỏ dòng trống và xóa khoảng trắng thừa ==="
    grep -v '^$' "$file" | sed 's/^[ \t]*//'

    echo "=== [1.4] Tìm kiếm kèm context (2 dòng trước, 3 dòng sau) ==="
    grep -B 2 -A 3 "ERROR" "$file" 2>/dev/null || echo "Không tìm thấy từ khóa ERROR."
}

# --- 2. TÌM KIẾM VÀ DỌN DẸP FILE (FIND, XARGS) ---
file_management_tools() {
    local target_dir="${1:-.}"

    echo "=== [2.1] Tìm file lớn hơn 50MB hoặc sửa đổi trong 24h ==="
    find "$target_dir" -type f -size +50M
    find "$target_dir" -type f -mtime -1

    echo "=== [2.2] Dọn dẹp file .tmp an toàn (Safe mode) ==="
    find "$target_dir" -name "*.tmp" | while read -r f; do
        echo "Xóa file: $f"
        rm -f "$f"
    done

    echo "=== [2.3] Kiểm tra kích thước thư mục top đầu ==="
    du -h "$target_dir" | sort -hr | head -n 10
}

# --- 3. QUẢN LÝ PROCESS (PS, PGREP, KILL) ---
manage_processes() {
    read -r -p "Nhập tên process cần tìm/quản lý: " name
    
    # Kiểm tra xem công cụ cần thiết đã cài chưa
    command -v pgrep >/dev/null || { echo "Lỗi: pgrep chưa được cài đặt"; return 1; }

    local pids
    pids=$(pgrep -f "$name" || true)

    if [[ -z "$pids" ]]; then
        echo "Không tìm thấy process nào khớp với '$name'."
        return 1
    fi

    echo "Tìm thấy các PID sau:"
    echo "$pids"

    read -r -p "Chọn tín hiệu kill - Thường (15) hay Mạnh (9)? [15/9]: " sig

    for pid in $pids; do
        if [[ "$sig" == "9" ]]; then
            echo "Đang ép buộc kết thúc (SIGKILL) PID: $pid"
            kill -9 "$pid" 2>/dev/null || true
        else
            echo "Đang gửi tín hiệu kết thúc nhẹ nhàng (SIGTERM) PID: $pid"
            kill "$pid" 2>/dev/null || true
            sleep 2
            # Kiểm tra lại nếu chưa chết thì kill -9
            if kill -0 "$pid" 2>/dev/null; then
                echo "Process không phản hồi, tiến hành kill -9 PID: $pid"
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
    done

    echo "Hoàn tất xử lý process."
}

# --- 4. KIỂM TRA BẢO MẬT VÀ PHÂN QUYỀN (PERMISSIONS, SUID) ---
security_audit() {
    echo "=== [4.1] Tìm các binary SUID (Nguy cơ leo thang đặc quyền) ==="
    find / -perm -4000 2>/dev/null || true

    echo "=== [4.2] Tìm các file có quyền SGID ==="
    find / -perm -2000 2>/dev/null || true
}

# --- MENU CHÍNH ---
main() {
    clear
    echo "============================================"
    echo "         LINUX AUTOMATION TOOLKIT           "
    echo "============================================"
    echo "1. Xử lý & Phân tích văn bản"
    echo "2. Quản lý & Tìm kiếm file"
    echo "3. Quản lý Process thông minh"
    echo "4. Kiểm tra bảo mật (SUID/SGID)"
    echo "0. Thoát"
    echo "--------------------------------------------"
    read -r -p "Lựa chọn của cậu [0-4]: " choice

    case "$choice" in
        1) 
            read -r -p "Nhập đường dẫn file text (mặc định textfile.txt): " tf
            process_text_data "${tf:-textfile.txt}" 
            ;;
        2) 
            read -r -p "Nhập thư mục cần quét (mặc định .): " td
            file_management_tools "${td:-.}" 
            ;;
        3) 
            manage_processes 
            ;;
        4) 
            security_audit 
            ;;
        0) 
            exit 0 
            ;;
        *) 
            echo "Lựa chọn không hợp lệ." 
            ;;
    esac
}

main "$@"