#include <iostream>
#include <opencv2/opencv.hpp>
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <zmq.hpp>

using namespace std;

int main()
{
    cv::VideoCapture cap(0);
    if (!cap.isOpened())
    {
        std::cerr << "カメラキャプチャーに失敗しました" << std::endl;
        return -1;
    }

    // ZMQセットアップ
    zmq::context_t context(1);

    // c++からpythonへ画像を送信するソケット
    zmq::socket_t publisher(context, ZMQ_PUB);  // PUBLISHERソケットに変更
    publisher.bind("tcp://*:5555");             // bindに変更

    // c#からc++へプログラムの開始終了を受け取るソケット
    zmq::socket_t subscriber(context, ZMQ_SUB); // SUBSCRIBERソケット
    subscriber.connect("tcp://localhost:5557"); // connect
    subscriber.setsockopt(ZMQ_SUBSCRIBE, "", 0); // すべてのメッセージを購読

    cv::Mat frame;
	bool is_active = false; // プログラムの開始終了を受け取るフラグ

    cout << "C#からの情報を待ちます" << endl;
    
    while (true)
    {
        // 非ブロッキングで制御メッセージを確認
        zmq::message_t control_message;
        if (subscriber.recv(control_message, zmq::recv_flags::dontwait))
        {
            string command(static_cast<char*>(control_message.data()), control_message.size());
            cout << "Command received: " << command << endl;

            if (command == "START")
            {
                is_active = true; // 動作開始
            }
            else if (command == "STOP")
            {
                is_active = false; // 動作停止
            }
            else if (command == "END")
            {
                cout << "プログラムを終了します" << endl;
                break; // プログラム終了
            }
        }

        if (is_active)
        {
            // カメラからフレームを取得
            if (!cap.read(frame))
            {
                cerr << "カメラキャプチャーに失敗しました" << endl;
                continue;
            }

            // フレームをエンコード
            vector<uchar> encoded_frame;
            cv::imencode(".jpg", frame, encoded_frame);

            if (encoded_frame.empty())
            {
                cerr << "フレームを取得できませんでした" << endl;
                continue;
            }

            // エンコードされた画像データを送信
            publisher.send(zmq::buffer(encoded_frame.data(), encoded_frame.size()), zmq::send_flags::none);
        }
    }
    cap.release();
	publisher.close();
	subscriber.close();

    return 0;
}
