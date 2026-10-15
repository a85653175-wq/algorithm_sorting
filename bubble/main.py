from flask import Flask, jsonify, request
from flask_cors import CORS  # CORS 라이브러리 임포트
import os

app = Flask(__name__)
# 모든 도메인(GAS 웹 앱 포함)에서의 접근을 허용합니다.
CORS(app, resources={r"/sort": {"origins": "*"}})

def bubble_sort_steps(arr):
    """
    버블 정렬을 수행하면서 각 단계별(비교 및 스왑) 상태를 기록하여 반환합니다.
    """
    steps = []
    n = len(arr)
    
    # 초기 상태 기록
    steps.append({
        "array": list(arr),
        "message": "초기 배열 상태입니다.",
        "comparing": [],
        "swapped": False
    })
    
    for i in range(n):
        swapped_in_pass = False
        for j in range(0, n - i - 1):
            comparing = [j, j + 1]
            
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped_in_pass = True
                steps.append({
                    "array": list(arr),
                    "message": f"인덱스 {j} ({arr[j+1]})와 {j+1} ({arr[j]}) 값을 비교 후 교환 발생",
                    "comparing": comparing,
                    "swapped": True
                })
            else:
                steps.append({
                    "array": list(arr),
                    "message": f"인덱스 {j} ({arr[j]})와 {j+1} ({arr[j+1]}) 값을 비교 (교환 없음)",
                    "comparing": comparing,
                    "swapped": False
                })
        
        if not swapped_in_pass:
            break
            
    steps.append({
        "array": list(arr),
        "message": "버블 정렬이 성공적으로 완료되었습니다!",
        "comparing": [],
        "swapped": False
    })
    return steps

@app.route('/sort', methods=['POST', 'OPTIONS'])  # OPTIONS 메서드 허용 (pre-flight 대응)
def sort_endpoint():
    # CORS pre-flight 요청에 대한 빈 응답 처리
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON 데이터가 전달되지 않았습니다."}), 400
            
        arr = data.get('array', [64, 34, 25, 12, 22, 11, 90])
        
        if not isinstance(arr, list) or not all(isinstance(x, (int, float)) for x in arr):
            return jsonify({"error": "유효한 숫자 배열을 전달해주세요."}), 400
            
        steps = bubble_sort_steps(arr)
        
        return jsonify({
            "status": "success",
            "steps": steps,
            "complexity": {
                "time_worst": "O(n^2)",
                "time_best": "O(n)",
                "space": "O(1)"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Bubble Sort Cloud Run Server is running!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
