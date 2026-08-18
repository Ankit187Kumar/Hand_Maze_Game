import { HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';

export class HandTracker {
  constructor() {
    this.handLandmarker = null;
    this.pinchThreshold = 0.08;
    this.smoothingFactor = 0.4;
    this.prevPos = null;
  }

  async initialize() {
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.9/wasm"
    );
    this.handLandmarker = await HandLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`,
        delegate: "GPU"
      },
      runningMode: "VIDEO",
      numHands: 1
    });
  }

  getHandInfo(videoElement, canvasWidth, canvasHeight) {
    if (!this.handLandmarker) return null;

    let startTimeMs = performance.now();
    const results = this.handLandmarker.detectForVideo(videoElement, startTimeMs);

    if (results.landmarks && results.landmarks.length > 0) {
      const landmarks = results.landmarks[0];
      
      const thumbTip = landmarks[4];
      const indexTip = landmarks[8];
      
      const tx = (1 - thumbTip.x) * canvasWidth; // mirrored
      const ty = thumbTip.y * canvasHeight;
      const ix = (1 - indexTip.x) * canvasWidth; // mirrored
      const iy = indexTip.y * canvasHeight;

      // Distance between thumb and index normalized by canvas width
      const dist = Math.hypot(tx - ix, ty - iy) / canvasWidth;
      const pinchActive = dist < this.pinchThreshold;

      const rawX = (tx + ix) / 2;
      const rawY = (ty + iy) / 2;

      let smoothedPos;
      if (!this.prevPos) {
        smoothedPos = { x: rawX, y: rawY };
      } else {
        smoothedPos = {
          x: this.prevPos.x * (1 - this.smoothingFactor) + rawX * this.smoothingFactor,
          y: this.prevPos.y * (1 - this.smoothingFactor) + rawY * this.smoothingFactor
        };
      }
      this.prevPos = smoothedPos;

      // Thumb down detection (Y increases downwards)
      // Wrist is landmark 0. If thumb tip Y is much greater than wrist Y, thumb is down.
      const wrist = landmarks[0];
      const thumbDown = thumbTip.y > wrist.y + 0.1;

      return {
        pos: smoothedPos,
        pinchActive,
        thumbDown,
        landmarks: landmarks // for drawing
      };
    }

    this.prevPos = null;
    return null;
  }

  drawLandmarks(ctx, landmarks, cw, ch) {
    ctx.fillStyle = '#A0F0A0';
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 2;

    for (let i = 0; i < landmarks.length; i++) {
      const lm = landmarks[i];
      const x = (1 - lm.x) * cw;
      const y = lm.y * ch;
      
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    }
  }
}
