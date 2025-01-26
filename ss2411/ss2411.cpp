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
        std::cerr << "�J�����L���v�`���[�Ɏ��s���܂���" << std::endl;
        return -1;
    }

    // ZMQ�Z�b�g�A�b�v
    zmq::context_t context(1);

    // c++����python�։摜�𑗐M����\�P�b�g
    zmq::socket_t publisher(context, ZMQ_PUB);  // PUBLISHER�\�P�b�g�ɕύX
    publisher.bind("tcp://*:5555");             // bind�ɕύX

    // c#����c++�փv���O�����̊J�n�I�����󂯎��\�P�b�g
    zmq::socket_t subscriber(context, ZMQ_SUB); // SUBSCRIBER�\�P�b�g
    subscriber.connect("tcp://localhost:5557"); // connect
    subscriber.setsockopt(ZMQ_SUBSCRIBE, "", 0); // ���ׂẴ��b�Z�[�W���w��

    cv::Mat frame;
	bool is_active = false; // �v���O�����̊J�n�I�����󂯎��t���O

    cout << "C#����̏���҂��܂�" << endl;
    
    while (true)
    {
        // ��u���b�L���O�Ő��䃁�b�Z�[�W���m�F
        zmq::message_t control_message;
        if (subscriber.recv(control_message, zmq::recv_flags::dontwait))
        {
            string command(static_cast<char*>(control_message.data()), control_message.size());
            cout << "Command received: " << command << endl;

            if (command == "START")
            {
                is_active = true; // ����J�n
            }
            else if (command == "STOP")
            {
                is_active = false; // �����~
            }
            else if (command == "END")
            {
                cout << "�v���O�������I�����܂�" << endl;
                break; // �v���O�����I��
            }
        }

        if (is_active)
        {
            // �J��������t���[�����擾
            if (!cap.read(frame))
            {
                cerr << "�J�����L���v�`���[�Ɏ��s���܂���" << endl;
                continue;
            }

            // �t���[�����G���R�[�h
            vector<uchar> encoded_frame;
            cv::imencode(".jpg", frame, encoded_frame);

            if (encoded_frame.empty())
            {
                cerr << "�t���[�����擾�ł��܂���ł���" << endl;
                continue;
            }

            // �G���R�[�h���ꂽ�摜�f�[�^�𑗐M
            publisher.send(zmq::buffer(encoded_frame.data(), encoded_frame.size()), zmq::send_flags::none);
        }
    }
    cap.release();
	publisher.close();
	subscriber.close();

    return 0;
}
