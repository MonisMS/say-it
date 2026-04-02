@echo off
pushd "%~dp0"

echo Installing RealtimeSTT (ONNX variant, no full PyTorch needed)...
pip install RealtimeSTT onnxruntime

echo.
echo Running proof-of-concept...
python test_realtime_poc.py

popd
pause
