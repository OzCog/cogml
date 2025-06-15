/*
  Project: OpenCogER
  File: FileCapture.hpp
  Author: Mandeep Singh Bhatia
  License: AGPL
  Date: May 2017
*/
#ifndef FILECAPTURE_H
#define FILECAPTURE_H


#include "ImageSource.hpp"

#include "opencv2/core.hpp"
#include "opencv2/highgui.hpp"
#include "opencv2/imgproc.hpp"

#include <iostream>
#include <string>
#include <cstdio>
#include <thread>
#include <mutex>

using namespace std;
using namespace cv;

class FileCapture: public ImageSource
{
    public:
        static FileCapture *init(string src_name,string fileName,
            double max_fps=30.0);
            //max fps is not guaranteed
        virtual ~FileCapture();
        bool isOn();
        bool isOk();
        string getState();
        Mat getCurrentFrame();//Mat is like shared_ptr, make deep copy here and use mutex
    protected:
    private:
        FileCapture(string src_name, string fileName, double max_fps);
		  static FileCapture *_file_cap;
        string fName;
        Mat current;
        VideoCapture capture;
        static void thread_loop(FileCapture* cc);
        thread* run;
        mutex rd;
        int wait_time;
        
};

#endif // FILECAPTURE_H
