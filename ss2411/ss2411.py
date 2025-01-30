import zmq
import cv2
import numpy as np
import threading
import torch


def receive_end_message(subscriber, stop_event):
    """
    C#からの終了メッセージ（END）を受信するスレッド用関数
    """
    while not stop_event.is_set():
        try:
            control_message = subscriber.recv_string(flags=zmq.NOBLOCK)
            print(f"Control message received: {control_message}")

            if control_message == "END":
                print("C#から終了メッセージを受信しました")
                stop_event.set()  # プログラム全体を停止
        except zmq.Again:
            pass  # メッセージがない場合はスルー

def draw_detections(frame, results):
    """
    YOLOv5の検出結果をフレームに描画する
    """
    for det in results.xyxy[0]:  # 各検出結果に対してループ
        x1, y1, x2, y2, conf, cls = det.cpu().numpy()
        label = f"{results.names[int(cls)]}: {conf:.2f}"
        
        # バウンディングボックスを描画
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        
        # ラベルを描画
        cv2.putText(frame, label, (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return frame


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

    # c#からpythonへプログラムの終了メッセージを受け取るソケット
    subscriber_from_csharp = context.socket(zmq.SUB)
    subscriber_from_csharp.connect("tcp://localhost:5561")
    subscriber_from_csharp.setsockopt_string(zmq.SUBSCRIBE, "")

    # スレッド制御用の終了フラグ
    stop_event = threading.Event()

    # 終了メッセージ受信スレッドの起動
    control_thread = threading.Thread(
        target=receive_end_message,
        args=(subscriber_from_csharp, stop_event),
        daemon=True
    )
    control_thread.start()

    print("サーバー起動中...")

    # モデルのロード
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    model.eval()

    try:
        while not stop_event.is_set():
            try:
                # C++から画像データを受信
                frame_data = socket.recv(flags=zmq.NOBLOCK)

                # バイトデータをnumpy配列に変換
                nparr = np.frombuffer(frame_data, np.uint8)

                # numpy配列を画像にデコード
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # 画像をモデルに入力
                results = model(frame)

                # 検出結果を描画
                frame = draw_detections(frame, results)

                # 画像をC#に送信するためにJPEG形式で再エンコード
                _, encoded_frame = cv2.imencode('.jpg', frame)
                publisher.send(encoded_frame.tobytes())

            except zmq.Again:
                pass  # 画像がまだ来ていない場合はスルー

    except KeyboardInterrupt:
        print("\n処理を中止します")
    finally:
        # 終了処理
        stop_event.set()
        control_thread.join()
        socket.close()
        publisher.close()
        subscriber_from_csharp.close()
        context.term()
        print("サーバーを終了しました")


if __name__ == "__main__":
    main()