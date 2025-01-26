import zmq
import cv2
import numpy as np

def main():
    # ZMQ セットアップ
    context = zmq.Context()

    # c++からpythonへ画像を受け取るソケット
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # すべてのメッセージを購読

    # pythonからc++へ画像を送信するソケット
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5556")

    # c#からpythonへプログラムの開始終了を受け取るソケット
    subscriber_from_csharp = context.socket(zmq.SUB)
    subscriber_from_csharp.connect("tcp://localhost:5560")
    subscriber_from_csharp.setsockopt_string(zmq.SUBSCRIBE, "")

    # C#から開始と停止を受け取る
    is_active = True

    print("サーバー起動中...")

    try:
        while True:
            # 制御ソケットの状態を確認
            try:
                # 非ブロッキングで制御メッセージを受信
                control_message = subscriber_from_csharp.recv_string(flags=zmq.NOBLOCK)
                print(f"Control message received: {control_message}")

                if control_message == "END":
                    is_active = False
                    print("C#から終了メッセージを受信しました")
                    break
                
            except zmq.Again:
                # メッセージがない場合はスルー
                pass

            if is_active:
                # C++から画像データを受信
                frame_data = socket.recv()
                
                # バイトデータをnumpy配列に変換
                nparr = np.frombuffer(frame_data, np.uint8)
                
                # numpy配列を画像にデコード
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # 画像をC#に送信するためにJPEG形式で再エンコード
                _, encoded_frame = cv2.imencode('.jpg', frame)
                publisher.send(encoded_frame.tobytes())

    except KeyboardInterrupt:
        print("\n処理を中止します")
    
    finally:
        socket.close()
        publisher.close()
        subscriber_from_csharp.close()
        context.term()

if __name__ == "__main__":
    main()