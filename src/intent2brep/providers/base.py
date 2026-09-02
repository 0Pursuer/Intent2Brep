from __future__ import annotations

from pathlib import Path
from typing import Mapping, Protocol, runtime_checkable


@runtime_checkable
class TextToImageProvider(Protocol):
    name: str
    def generate(self, prompt: str, output: Path, *, seed: int = 42) -> Path: ...


@runtime_checkable
class ImageTo3DProvider(Protocol):
    name: str
    def generate(self, images: Mapping[str, Path], output: Path, *, seed: int = 42) -> Path: ...


@runtime_checkable
class MultiViewProvider(Protocol):
    name: str
    def generate(self, image: Path, output_dir: Path, *, seed: int = 42) -> dict[str, Path]: ...
