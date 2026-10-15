from flask import Flask, jsonify, request
import os

app = Flask(__name__)

def bubble_sort_steps(arr):
    """
    버블 정렬을 수행하면서 각 단계별(비교 및 스왑) 상태를 기록하여 반환합니다.
    - arr: 정렬할 숫자 리스트
    - returns: 각 단계별 배열 상태와 설명이 담긴 리스트
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
            # 현재 비교 중인 두 원소의 인덱스 기록
            comparing = [j, j + 1]
            
            if arr[j] > arr[j + 1]:
                # 앞의 원소가 뒤의 원소보다 크면 교환 (스왑)
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
        
        # 이번 패스에서 교환이 전혀 발생하지 않았다면 이미 정렬 완료된 상태
        if not swapped_in_pass:
            break
            
    # 최종 완료 상태 기록
    steps.append({
        "array": list(arr),
        "message": "버블 정렬이 성공적으로 완료되었습니다!",
        "comparing": [],
        "swapped": False
    })
    return steps

@app.route('/sort', methods=['POST'])
def sort_endpoint():
    """
    클라이언트로부터 숫자들이 담긴 배열을 받아 버블 정렬 단계별 결과를 반환하는 API 엔드포인트
    """
    try:
        data = request.get_json()
        arr = data.get('array', [64, 34, 25, 12, 22, 11, 90])
        
        # 입력값 검증 (숫자 리스트인지 확인)
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
    """서버 정상 작동 여부를 확인하는 헬스체크 엔드포인트"""
    return jsonify({"status": "online", "message": "Bubble Sort Cloud Run Server is running!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
