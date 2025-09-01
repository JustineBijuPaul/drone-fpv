"""Performance monitoring and optimization for the drone human detection system."""

import time
import psutil
import threading
import logging
from typing import Deque, Optional, List
from dataclasses import dataclass
from collections import deque
import gc


@dataclass
class PerformanceMetrics:
    fps: float
    memory_usage_mb: float
    cpu_usage_percent: float
    frame_processing_time_ms: float
    detection_time_ms: float
    display_time_ms: float
    frames_processed: int
    frames_skipped: int
    memory_peak_mb: float


class PerformanceMonitor:
    """Monitors and optimizes system performance for real-time processing."""

    def __init__(self, target_fps: float = 15.0, max_memory_mb: float = 512.0):
        self.target_fps = target_fps
        self.max_memory_mb = max_memory_mb
        self.min_frame_time = 1.0 / target_fps

        # Performance tracking
        self.frame_times: Deque[float] = deque(maxlen=60)
        self.processing_times: Deque[float] = deque(maxlen=30)
        self.detection_times: Deque[float] = deque(maxlen=30)
        self.display_times: Deque[float] = deque(maxlen=30)

        # Counters
        self.frames_processed = 0
        self.frames_skipped = 0
        self.total_frames = 0

        # Memory tracking
        self.memory_samples: Deque[float] = deque(maxlen=100)
        self.memory_peak = 0.0
        self.last_gc_time = time.time()
        self.gc_interval = 30.0

        # Frame skipping logic
        self.skip_frames = False
        self.skip_counter = 0
        self.skip_ratio = 2
        self.consecutive_slow_frames = 0

        # Adaptive quality settings
        self.current_quality_level = 1.0
        self.quality_adjustment_enabled = True

        # Threading for background monitoring
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Logger and rate-limiters
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Performance monitor initialized: target_fps={target_fps}, max_memory={max_memory_mb}MB")
        self._last_memory_warn_time = 0.0

    def start_monitoring(self):
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Background performance monitoring started")

    def stop_monitoring(self):
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        self.logger.info("Background performance monitoring stopped")

    def _background_monitor(self):
        while self.monitoring_active:
            try:
                self._update_memory_usage()
                self._check_garbage_collection()
                self._adjust_frame_skipping()
                try:
                    self._adjust_quality_level()
                except Exception:
                    pass
                time.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Error in background monitoring: {e}")

    def record_frame_start(self) -> float:
        return time.time()

    def record_frame_end(self, start_time: float, detection_time: float = 0.0, display_time: float = 0.0, skipped: bool = False):
        end_time = time.time()
        frame_time = end_time - start_time

        self.total_frames += 1

        if skipped:
            self.frames_skipped += 1
        else:
            self.frames_processed += 1
            self.frame_times.append(frame_time)
            self.processing_times.append(frame_time)
            if detection_time > 0:
                self.detection_times.append(detection_time)
            if display_time > 0:
                self.display_times.append(display_time)
            if frame_time > self.min_frame_time * 1.5:
                self.consecutive_slow_frames += 1
            else:
                self.consecutive_slow_frames = 0

    def should_skip_frame(self) -> bool:
        if not self.skip_frames:
            self.skip_counter = 0
            return False
        self.skip_counter += 1
        return (self.skip_counter % self.skip_ratio) != 0

    def _adjust_frame_skipping(self):
        current_fps = self.get_current_fps()
        if current_fps < self.target_fps * 0.8:
            if not self.skip_frames:
                self.skip_frames = True
                self.logger.info(f"Enabling frame skipping: current_fps={current_fps:.1f}, target={self.target_fps}")
        elif current_fps > self.target_fps * 0.95:
            if self.skip_frames:
                self.skip_frames = False
                self.skip_counter = 0
                self.logger.info(f"Disabling frame skipping: current_fps={current_fps:.1f}")

        if self.skip_frames:
            fps_ratio = current_fps / max(1e-6, self.target_fps)
            if fps_ratio < 0.5:
                self.skip_ratio = 3
            elif fps_ratio < 0.7:
                self.skip_ratio = 2
            else:
                self.skip_ratio = 2

    def get_current_fps(self) -> float:
        if len(self.frame_times) < 2:
            return 0.0
        recent_frames = min(30, len(self.frame_times))
        if recent_frames < 2:
            return 0.0
        total_time = sum(list(self.frame_times)[-recent_frames:])
        if total_time > 0:
            return recent_frames / total_time
        return 0.0

    def _update_memory_usage(self):
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.memory_samples.append(memory_mb)
            self.memory_peak = max(self.memory_peak, memory_mb)
            if memory_mb > self.max_memory_mb:
                now = time.time()
                if now - self._last_memory_warn_time > 5.0:
                    self.logger.warning(f"High memory usage: {memory_mb:.1f}MB (limit: {self.max_memory_mb}MB)")
                    self._last_memory_warn_time = now
        except Exception as e:
            self.logger.error(f"Error updating memory usage: {e}")

    def _check_garbage_collection(self):
        current_time = time.time()
        should_gc = (current_time - self.last_gc_time > self.gc_interval)
        if self.memory_samples:
            current_memory = self.memory_samples[-1]
            should_gc = should_gc or (current_memory > self.max_memory_mb * 0.8)
        if should_gc:
            self._run_garbage_collection()
            self.last_gc_time = current_time

    def _run_garbage_collection(self):
        try:
            before_memory = self.get_current_memory_usage()
            collected = gc.collect()
            after_memory = self.get_current_memory_usage()
            memory_freed = before_memory - after_memory
            self.logger.info(f"Garbage collection: freed {memory_freed:.1f}MB, collected {collected} objects")
        except Exception as e:
            self.logger.error(f"Error during garbage collection: {e}")

    def get_current_memory_usage(self) -> float:
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def get_cpu_usage(self) -> float:
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0

    def get_performance_metrics(self) -> PerformanceMetrics:
        return PerformanceMetrics(
            fps=self.get_current_fps(),
            memory_usage_mb=self.get_current_memory_usage(),
            cpu_usage_percent=self.get_cpu_usage(),
            frame_processing_time_ms=self._get_average_time(self.processing_times) * 1000,
            detection_time_ms=self._get_average_time(self.detection_times) * 1000,
            display_time_ms=self._get_average_time(self.display_times) * 1000,
            frames_processed=self.frames_processed,
            frames_skipped=self.frames_skipped,
            memory_peak_mb=self.memory_peak,
        )

    def _get_average_time(self, time_deque: deque) -> float:
        if not time_deque:
            return 0.0
        return sum(time_deque) / len(time_deque)

    def get_optimization_suggestions(self) -> List[str]:
        suggestions: List[str] = []
        metrics = self.get_performance_metrics()
        if metrics.fps < self.target_fps * 0.8:
            suggestions.append(f"FPS is low ({metrics.fps:.1f}/{self.target_fps}). Consider reducing resolution or detection frequency.")
        if metrics.memory_usage_mb > self.max_memory_mb * 0.8:
            suggestions.append(f"Memory usage is high ({metrics.memory_usage_mb:.1f}MB). Consider reducing frame buffer size.")
        if metrics.cpu_usage_percent > 80:
            suggestions.append(f"CPU usage is high ({metrics.cpu_usage_percent:.1f}%). Consider using GPU acceleration or reducing processing load.")
        if metrics.frame_processing_time_ms > (1000 / self.target_fps) * 1.2:
            suggestions.append("Frame processing is slow. Consider optimizing detection model or reducing frame size.")
        skip_ratio = metrics.frames_skipped / max(1, metrics.frames_processed + metrics.frames_skipped)
        if skip_ratio > 0.3:
            suggestions.append(f"High frame skip ratio ({skip_ratio:.1%}). System may be overloaded.")
        return suggestions

    def _adjust_quality_level(self):
        if not self.quality_adjustment_enabled:
            return
        current_fps = self.get_current_fps()
        if current_fps <= 0.0:
            return
        try:
            if current_fps < self.target_fps * 0.6:
                new_quality = max(0.25, self.current_quality_level * 0.5)
            elif current_fps < self.target_fps * 0.8:
                new_quality = max(0.5, self.current_quality_level * 0.75)
            elif current_fps > self.target_fps * 0.95:
                new_quality = min(1.0, self.current_quality_level + 0.25)
            else:
                new_quality = self.current_quality_level
            if abs(new_quality - self.current_quality_level) > 1e-3:
                self.logger.info(f"Adjusting quality level {self.current_quality_level:.2f} -> {new_quality:.2f} based on FPS {current_fps:.1f}")
                self.current_quality_level = new_quality
        except Exception as e:
            self.logger.error(f"Error adjusting quality level: {e}")

    def reset_metrics(self):
        self.frame_times.clear()
        self.processing_times.clear()
        self.detection_times.clear()
        self.display_times.clear()
        self.memory_samples.clear()
        self.frames_processed = 0
        self.frames_skipped = 0
        self.total_frames = 0
        self.memory_peak = 0.0
        self.consecutive_slow_frames = 0
        self.logger.info("Performance metrics reset")

    def log_performance_summary(self):
        metrics = self.get_performance_metrics()
        self.logger.info("=== Performance Summary ===")
        self.logger.info(f"FPS: {metrics.fps:.1f} (target: {self.target_fps})")
        self.logger.info(f"Memory: {metrics.memory_usage_mb:.1f}MB (peak: {metrics.memory_peak_mb:.1f}MB)")
        self.logger.info(f"CPU: {metrics.cpu_usage_percent:.1f}%")
        self.logger.info(f"Frame processing: {metrics.frame_processing_time_ms:.1f}ms")
        self.logger.info(f"Detection time: {metrics.detection_time_ms:.1f}ms")
        self.logger.info(f"Display time: {metrics.display_time_ms:.1f}ms")
        self.logger.info(f"Frames processed: {metrics.frames_processed}")
        self.logger.info(f"Frames skipped: {metrics.frames_skipped}")
        suggestions = self.get_optimization_suggestions()
        if suggestions:
            self.logger.info("Optimization suggestions:")
            for suggestion in suggestions:
                self.logger.info(f"  - {suggestion}")