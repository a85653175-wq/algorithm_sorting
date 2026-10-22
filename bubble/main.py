from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
# CORS 설정: GAS 클라이언트 웹 앱에서의 요청을 허용
CORS(app, resources={r"/queue": {"origins": "*"}})

# 고정 길이 큐를 메모리 상에서 관리하기 위한 전역 변수
QUEUE_SIZE = 20
queue_data = []

@app.route('/queue', methods=['POST', 'OPTIONS'])
def queue_endpoint():
    """
    클라이언트로부터 요청(action)과 파라미터를 받아 고정 길이 큐 연산을 수행하고 결과를 반환하는 API
    """
    if request.method == 'OPTIONS':
        return '', 204

    global queue_data
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "요청 데이터가 없습니다."}), 400

        action = data.get('action')
        param = data.get('param', None)
        response_data = {"status": "success"}

        # 1. 초기화 (Initialize)
        if action == 'init':
            size_val = int(param) if param is not None else 20
            global QUEUE_SIZE
            QUEUE_SIZE = size_val
            queue_data = []
            response_data["message"] = f"큐가 초기화되었습니다. (사이즈: {QUEUE_SIZE})"

        # 2. Push (데이터 추가)
        elif action == 'push':
            # 배열이 전달된 경우 여러 개 push, 단일 값이면 단일 push
            items = param if isinstance(param, list) else [param]
            for item in items:
                if len(queue_data) >= QUEUE_SIZE:
                    return jsonify({"status": "error", "message": "큐가 가득 찼습니다 (Overflow)!"}), 400
                queue_data.append(item)
            response_data["message"] = f"데이터 {items}가 큐에 추가되었습니다."

        # 3. Pop (데이터 제거 및 반환)
        elif action == 'pop':
            if len(queue_data) == 0:
                return jsonify({"status": "error", "message": "큐가 비어 있습니다 (Underflow)!"}), 400
            popped_item = queue_data.pop(0) # 선입선출(FIFO)
            response_data["message"] = f"데이터 {popped_item}가 팝(Pop) 되었습니다."
            response_data["popped"] = popped_item

        # 4. 현재 데이터 개수(길이/크기) 반환
        elif action == 'size':
            response_data["result"] = len(queue_data)
            response_data["message"] = f"현재 큐의 데이터 개수: {len(queue_data)}"

        # 5. 상태 검사 (Full / Empty 여부)
        elif action == 'status':
            is_full = len(queue_data) >= QUEUE_SIZE
            is_empty = len(queue_data) == 0
            response_data["result"] = {"full": is_full, "empty": is_empty}
            response_data["message"] = f"상태 검사 - Full: {is_full}, Empty: {is_empty}"

        # 6. 전면(Front) 데이터 확인
        elif action == 'front':
            if len(queue_data) == 0:
                response_data["result"] = None
                response_data["message"] = "큐가 비어 있어 전면 데이터를 확인할 수 없습니다."
            else:
                response_data["result"] = queue_data[0]
                response_data["message"] = f"전면(Front) 데이터: {queue_data[0]}"

        # 7. 큐 전체 데이터 삭제
        elif action == 'clear':
            queue_data = []
            response_data["message"] = "큐의 모든 데이터가 삭제되었습니다."

        # 8. 값의 index 검색
        elif action == 'index':
            val = float(param) if '.' in str(param) else int(param)
            if val in queue_data:
                idx = queue_data.index(val)
                response_data["result"] = idx
                response_data["message"] = f"값 {val}의 인덱스 위치: {idx}"
            else:
                response_data["result"] = -1
                response_data["message"] = f"값 {val}이 큐에 존재하지 않습니다."

        # 9. 값의 개수 검색
        elif action == 'count':
            val = float(param) if '.' in str(param) else int(param)
            cnt = queue_data.count(val)
            response_data["result"] = cnt
            response_data["message"] = f"값 {val}의 개수: {cnt}개"

        # 10. 값의 존재 여부 검사 (Contains)
        elif action == 'contains':
            val = float(param) if '.' in str(param) else int(param)
            exists = val in queue_data
            response_data["result"] = exists
            response_data["message"] = f"값 {val} 존재 여부: {exists}"

        # 11. Front부터 Rear까지 출력 (전체 조회)
        elif action == 'display':
            response_data["result"] = list(queue_data)
            response_data["message"] = f"Front부터 Rear까지의 큐 내용: {queue_data}"

        else:
            return jsonify({"status": "error", "message": "알 수 없는 명령(action)입니다."}), 400

        # 공통으로 현재 큐 상태와 전체 내용을 반환
        response_data["queue"] = list(queue_data)
        response_data["max_size"] = QUEUE_SIZE
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    """서버 정상 작동 확인용 헬스체크"""
    return jsonify({"status": "online", "message": "Fixed-Size Queue Cloud Run Server is running!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
