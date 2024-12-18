@echo off

echo Installing virtualenv...
python -m pip install virtualenv
echo Installation complete
virtualenv venv
call venv\Scripts\activate
pause

echo Entered venv environment
pause
echo Installing the dependency packages required for ExVR...
pip install cv2_enumerate_cameras==1.1.17 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install keyboard==0.13.5 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install matplotlib==3.9.2 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install mediapipe==0.10.13 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install numpy==2.1.3 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install opencv_contrib_python==4.10.0.84 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install opencv_python==4.10.0.84 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install pygrabber==0.2 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install pynput==1.7.7 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install PyQt5==5.15.11 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install PyQt5_sip==12.15.0 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install python_osc==1.9.0 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install scipy==1.14.1 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install torch==2.5.0 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install torchvision==0.20.1 -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
pip install msvc-runtime -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
echo Installation complete
pause

echo If you didn't installed Microsoft Visual C++.
echo You shoud view this website to download and install it.
echo https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170

echo venv environment is ready to use.
echo the dependency packages required is installed.
pause 
