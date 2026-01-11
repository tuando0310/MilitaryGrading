import numpy as np

class GradingService:
    def __init__(self):
        # Mapping index sang tên khớp (Dựa trên cấu trúc 13 khớp đã thống nhất)
        self.INDEX_MAP = {
            0: "hip", 1: "right_shoulder", 2: "right_elbow", 3: "right_wrist",
            4: "left_shoulder", 5: "left_elbow", 6: "left_wrist", 7: "right_hip",
            8: "right_knee", 9: "right_ankle", 10: "left_hip", 11: "left_knee", 12: "left_ankle"
        }

    def _calculate_frame_detail(self, user_frame, model_frame, joint_thresholds, default_threshold):
        """
        Tính toán chi tiết sai số cho từng khớp trong 1 frame.
        """
        p_user = np.array(user_frame)
        p_model = np.array(model_frame)
        
        # 1. Tính khoảng cách Euclidean cho từng cặp khớp
        diff = p_user - p_model
        dists = np.sqrt(np.sum(diff**2, axis=1)) # Mảng 13 phần tử
        
        total_error = np.sum(dists)
        bad_joints = []

        # 2. Kiểm tra từng khớp xem có vượt ngưỡng không
        for i, dist in enumerate(dists):
            # Lấy ngưỡng riêng cho khớp i, nếu không có thì dùng ngưỡng mặc định
            threshold = joint_thresholds.get(i, default_threshold)
            
            if dist > threshold:
                joint_name = self.INDEX_MAP.get(i, f"unknown_{i}")
                bad_joints.append(joint_name)
                
        return total_error, bad_joints

    def evaluate_performance_detailed(self, user_sequence, model_sequence, mapping, config):
        """
        Phiên bản nâng cấp: Trả về cả tổng lỗi và danh sách khớp sai.
        """
        results = []
        
        joint_thresholds = config.get('joint_thresholds', {})
        default_threshold = config.get('default_joint_threshold', 0.1)
        
        n_frames = len(user_sequence)
        max_model_idx = len(model_sequence) - 1 # Chỉ số lớn nhất cho phép
        
        for i in range(n_frames):
            user_frame = user_sequence[i]
            
            # --- BẮT ĐẦU SỬA LỖI TẠI ĐÂY ---
            # Lấy index từ mapping
            raw_model_idx = mapping[i]
            
            # Đảm bảo index không vượt quá giới hạn của mảng model
            if raw_model_idx > max_model_idx:
                model_idx = max_model_idx
            elif raw_model_idx < 0:
                model_idx = 0
            else:
                model_idx = raw_model_idx
            # --- KẾT THÚC SỬA LỖI ---

            model_frame = model_sequence[model_idx]
            
            # Gọi hàm tính chi tiết
            total_err, bad_joints = self._calculate_frame_detail(
                user_frame, model_frame, joint_thresholds, default_threshold
            )
            
            results.append({
                "frame_index": i,
                "mapped_model_frame": model_idx,
                "total_error": total_err,
                "bad_joints": bad_joints
            })
            
        return results

    def _calculate_frame_detail_with_rules(self, user_frame, model_frame, rules):
        """
        Tính toán điểm số và phát hiện lỗi dựa trên bộ rules config.
        Trả về: (score_penalty, error_messages)
        """
        p_user = np.array(user_frame)
        p_model = np.array(model_frame)
        
        diff = p_user - p_model  # (N, 3) user - model
        
        total_penalty = 0
        error_messages = []
        
        # Đảo ngược INDEX_MAP để tìm index từ tên khớp
        # self.INDEX_MAP: {0: "hip", ...} -> name_to_idx: {"hip": 0, ...}
        name_to_idx = {v: k for k, v in self.INDEX_MAP.items()}
        
        for error_rule in rules.get('errors', []):
            joint_name = error_rule.get('joint')
            if joint_name not in name_to_idx:
                continue
                
            joint_idx = name_to_idx[joint_name]
            
            # Lấy vector khoảng cách của khớp này: [dx, dy, dz]
            # diff[joint_idx] là array([dx, dy, dz])
            d_vec = diff[joint_idx]
            
            # error_rule['distance'] chứa cấu hình cho x, y, z
            dist_rules = error_rule.get('distance', {})
            
            axes = ['x', 'y', 'z']
            for axis_idx, axis_name in enumerate(axes):
                # Giá trị chênh lệch trên trục này
                val = d_vec[axis_idx]
                
                axis_rule = dist_rules.get(axis_name)
                if not axis_rule:
                    continue
                
                # Xác định hướng lỗi: positive (dương) hoặc negative (âm)
                # Rule: "positive": { "threshold": 5, ... }
                direction = "positive" if val > 0 else "negative"
                
                rule_detail = axis_rule.get(direction)
                if not rule_detail:
                    continue
                
                threshold = rule_detail.get('threshold', 0)
                
                # So sánh giá trị tuyệt đối với ngưỡng
                if abs(val) > threshold:
                    penalty = rule_detail.get('penalty_point', 0)
                    msg = rule_detail.get('message', f"Error at {joint_name} {axis_name}")
                    
                    total_penalty += penalty
                    error_messages.append(msg)
                    
        return total_penalty, error_messages

    def evaluate_performance_with_rules(self, user_sequence, model_sequence, mapping, rules):
        """
        Chấm điểm toàn bộ video dựa trên rules.
        """
        results = []
        
        n_frames = len(user_sequence)
        max_model_idx = len(model_sequence) - 1
        
        for i in range(n_frames):
            user_frame = user_sequence[i]
            
            # Mapping index
            raw_model_idx = mapping[i]
            if raw_model_idx > max_model_idx:
                model_idx = max_model_idx
            elif raw_model_idx < 0:
                model_idx = 0
            else:
                model_idx = raw_model_idx
                
            model_frame = model_sequence[model_idx]
            
            # Tính lỗi
            penalty, msgs = self._calculate_frame_detail_with_rules(
                user_frame, model_frame, rules
            )
            
            results.append({
                "frame_index": i,
                "mapped_model_frame": model_idx,
                "penalty": penalty,
                "score": max(0, 100 - penalty), 
                "errors": msgs
            })
            
        return results