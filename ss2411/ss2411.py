import zmq
import cv2
import numpy as np

def main():
    # ZMQ セットアップ
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # すべてのメッセージを購読

    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://localhost:5556")

    print("サーバー起動中...")

    try:
        while True:
            # 画像データを受信
            frame_data = socket.recv()
            
            # バイトデータをnumpy配列に変換
            nparr = np.frombuffer(frame_data, np.uint8)
            
            # numpy配列を画像にデコード
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 画像をC#に送信するためにJPEG形式で再エンコード
            _, encoded_frame = cv2.imencode('.jpg', frame)
            publisher.send(encoded_frame.tobytes())
            
            # 'q'キーで終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n処理を中止します")
    
    finally:
        socket.close()
        publisher.close()
        context.term()

if __name__ == "__main__":
    main()