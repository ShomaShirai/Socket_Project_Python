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
        std::cerr << "Failed to open camera" << std::endl;
        return -1;
    }

    // ZMQ setup
    zmq::context_t context(1);

    // c++����python�։摜�𑗐M����\�P�b�g
    zmq::socket_t socket(context, ZMQ_PUB);  // PUBLISHER�\�P�b�g�ɕύX
    socket.bind("tcp://*:5555");             // bind�ɕύX

    // c#����c++�փv���O�����̊J�n�I�����󂯎��\�P�b�g
    zmq::socket_t socket(context, ZMQ_PUB); 
    socket.bind("tcp://*:5557");

    cv::Mat frame;
    cout << "aaa" << endl;
	cout << CV_VERSION << endl;

    while (cap.read(frame))
    {
        // �t���[�����G���R�[�h
        vector<uchar> encoded_frame;
        cv::imencode(".jpg", frame, encoded_frame);

        if (encoded_frame.empty())
        {
            std::cerr << "Failed to encode frame" << std::endl;
            continue;  // �X�L�b�v���Ď��̃t���[��������
        }

        // �G���R�[�h���ꂽ�摜�f�[�^�𑗐M
        socket.send(zmq::buffer(encoded_frame.data(), encoded_frame.size()), zmq::send_flags::none);

        const int key = cv::waitKey(1);
        if (key == 'q')
        {
            break;
        }
    }

    cap.release();
    return 0;
}
