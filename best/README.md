# YOLO 权重目录

请将训练好的 **best.pt** 放在本目录下：

```
UnmannedAerialVehicle-admin/
  best/
    best.pt   <-- 放这里
```

后端接口 `POST /v1/ai/detect` 会使用该权重对上传的图片或视频进行目标检测。
