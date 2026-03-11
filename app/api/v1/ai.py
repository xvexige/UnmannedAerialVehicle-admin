"""
YOLO 目标检测接口：支持上传图片或视频，使用 best.pt 权重进行识别。
权重文件路径：项目根目录下 best/best.pt（即 UnmannedAerialVehicle-admin/best/best.pt）
返回检测结果 + 标注图 base64（便于前端直接展示）。
"""
import base64
import logging
import tempfile
from pathlib import Path

import cv2

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from app.api.deps import require_roles
from app.schemas.common import ResponseModel
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI 识别"])
logger = logging.getLogger("drone.api")

def _find_project_root() -> Path:
    """从 ai.py 所在位置向上查找包含 app 与 best 的目录作为项目根。"""
    p = Path(__file__).resolve().parent
    for _ in range(8):
        if (p / "app").is_dir() and (p / "best").is_dir():
            return p
        if (p / "app").is_dir():
            return p  # 有 app 即视为项目根，best 应在该根下
        p = p.parent
    return Path(__file__).resolve().parent.parent.parent.parent

PROJECT_ROOT = _find_project_root()
DEFAULT_WEIGHTS = PROJECT_ROOT / "best" / "best.pt"


class DetectionItem(BaseModel):
    class_name: str
    confidence: float
    x: float  # 归一化 0-1
    y: float
    width: float
    height: float


def _get_yolo_model():
    """懒加载 YOLO 模型，避免启动时未放置权重文件报错。"""
    if not DEFAULT_WEIGHTS.exists():
        raise FileNotFoundError(
            f"未找到 YOLO 权重文件，请将 best.pt 放置于: {DEFAULT_WEIGHTS}"
        )
    from ultralytics import YOLO
    return YOLO(str(DEFAULT_WEIGHTS))


def _run_detect_on_image(image_path: str | Path, conf_thres: float = 0.25):
    """对单张图片做检测，返回 (检测列表, 标注图 BGR numpy 或 None)。"""
    model = _get_yolo_model()
    results = model.predict(
        source=str(image_path),
        conf=conf_thres,
        verbose=False,
    )
    out = []
    plotted = None
    for r in results:
        if r.boxes is not None:
            h, w = r.orig_shape[:2]
            for box in r.boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                class_name = r.names.get(cls_id, f"class_{cls_id}")
                x1, y1, x2, y2 = xyxy
                x_center = ((x1 + x2) / 2) / w
                y_center = ((y1 + y2) / 2) / h
                width = (x2 - x1) / w
                height = (y2 - y1) / h
                out.append(DetectionItem(
                    class_name=class_name,
                    confidence=round(conf, 4),
                    x=round(x_center, 4),
                    y=round(y_center, 4),
                    width=round(width, 4),
                    height=round(height, 4),
                ))
        # 标注图：ultralytics 的 plot() 返回 BGR numpy
        plotted = r.plot()
    return out, plotted


def _run_detect_on_video(video_path: str | Path, max_frames: int = 5, conf_thres: float = 0.25):
    """对视频做检测，取前 max_frames 帧；返回 (检测列表, 第一帧标注图 BGR 或 None)。"""
    model = _get_yolo_model()
    results = model.predict(
        source=str(video_path),
        conf=conf_thres,
        verbose=False,
        stream=True,
    )
    all_detections = []
    first_plotted = None
    frame_count = 0
    for r in results:
        if frame_count >= max_frames:
            break
        if r.boxes is not None:
            h, w = r.orig_shape[:2]
            for box in r.boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                class_name = r.names.get(cls_id, f"class_{cls_id}")
                x1, y1, x2, y2 = xyxy
                x_center = ((x1 + x2) / 2) / w
                y_center = ((y1 + y2) / 2) / h
                width = (x2 - x1) / w
                height = (y2 - y1) / h
                all_detections.append(DetectionItem(
                    class_name=class_name,
                    confidence=round(conf, 4),
                    x=round(x_center, 4),
                    y=round(y_center, 4),
                    width=round(width, 4),
                    height=round(height, 4),
                ))
            if first_plotted is None:
                first_plotted = r.plot()
        frame_count += 1
    return all_detections, first_plotted


@router.post("/detect", response_model=ResponseModel, summary="图片/视频 YOLO 识别")
async def detect(
    file: UploadFile = File(..., description="图片或视频文件"),
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
):
    """
    上传一张图片或一段视频，使用项目下 best/best.pt 进行目标检测。
    图片：整图识别；视频：取前几帧识别结果返回。
    返回检测框（归一化坐标）及类别、置信度。
    """
    content_type = (file.content_type or "").lower()
    is_video = "video/" in content_type or file.filename and (
        file.filename.endswith(".mp4") or file.filename.endswith(".avi")
        or file.filename.endswith(".mov") or file.filename.endswith(".webm")
    )
    is_image = "image/" in content_type or file.filename and (
        file.filename.endswith(".jpg") or file.filename.endswith(".jpeg")
        or file.filename.endswith(".png") or file.filename.endswith(".bmp")
    )

    if not is_image and not is_video:
        return ResponseModel.error(code=40001, message="请上传图片或视频文件（如 .jpg / .png / .mp4）")

    try:
        body = await file.read()
    except Exception as e:
        logger.exception("读取上传文件失败: %s", e)
        return ResponseModel.error(code=50001, message="读取文件失败")

    suffix = ".mp4" if is_video else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(body)
        tmp_path = tmp.name

    try:
        if is_video:
            detections, plotted = _run_detect_on_video(tmp_path, max_frames=5)
        else:
            detections, plotted = _run_detect_on_image(tmp_path)
        # 标注图转 base64（PNG）
        image_base64 = None
        if plotted is not None:
            _, buf = cv2.imencode(".png", plotted)
            image_base64 = base64.b64encode(buf.tobytes()).decode("utf-8")
        data = [
            {
                "class": d.class_name,
                "confidence": d.confidence,
                "x": d.x,
                "y": d.y,
                "width": d.width,
                "height": d.height,
            }
            for d in detections
        ]
        return ResponseModel.ok(data={"detections": data, "image_base64": image_base64})
    except FileNotFoundError as e:
        logger.warning("YOLO 权重未就绪: %s", e)
        return ResponseModel.error(code=50001, message=str(e))
    except Exception as e:
        logger.exception("YOLO 推理异常: %s", e)
        return ResponseModel.error(code=50001, message="识别失败，请检查文件格式与权重")
    finally:
        Path(tmp_path).unlink(missing_ok=True)
