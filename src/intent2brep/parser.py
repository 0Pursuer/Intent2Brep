from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod

from .models import BasePlate, Constraint, Hole, PartIntent, Slot, WebPlate

NUM = r"(\d+(?:\.\d+)?)"


class IntentParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> PartIntent: ...


class RegexIntentParser(IntentParser):
    """Offline parser for a deliberately constrained MVP grammar.

    It is not intended to replace an LLM. It keeps the demo reproducible and
    demonstrates that the downstream geometry stack is independent of the LLM.
    """

    def parse(self, text: str) -> PartIntent:
        normalized = text.replace("Ｘ", "x").replace("×", "x").replace("＊", "*")
        normalized = normalized.replace("毫米", "mm")

        base = self._parse_base(normalized)
        web = self._parse_web(normalized)
        holes = self._parse_holes(normalized, web is not None)
        slots = self._parse_slots(normalized)
        unsupported = []
        if re.search(r"(?:圆角|fillet|R\s*\d+)", normalized, re.I):
            unsupported.append("fillet requested but v0.1 leaves fillet recognition/building for the next milestone")
        if re.search(r"(?:倒角|chamfer)", normalized, re.I):
            unsupported.append("chamfer requested but not implemented in v0.1")

        assumptions: list[str] = []
        if web and web.centered_on_base:
            assumptions.append("web is centered on the base in X/Y")
        for h in holes:
            if h.centered_on_target:
                assumptions.append(f"Ø{h.diameter:g} hole is centered on its {h.target}")

        if not base:
            raise ValueError(
                "Could not find a base plate. Example: '100x60x10 mm 底板' or 'base plate 100x60x10 mm'."
            )

        constraints: list[Constraint] = []
        if web and web.centered_on_base:
            constraints.append(Constraint(type="centered", a="web", b="base"))
            constraints.append(Constraint(type="perpendicular", a="web", b="base"))
        for i, h in enumerate(holes):
            if h.centered_on_target:
                constraints.append(Constraint(type="centered", a=f"hole[{i}]", b=h.target))

        return PartIntent(
            base=base,
            web=web,
            holes=holes,
            slots=slots,
            constraints=constraints,
            assumptions=assumptions,
            unsupported_requests=unsupported,
        )

    def _parse_base(self, text: str) -> BasePlate | None:
        patterns = [
            rf"(?:底板|基板|base\s*plate)[^\d]{{0,16}}{NUM}\s*[x*]\s*{NUM}\s*[x*]\s*{NUM}",
            rf"{NUM}\s*[x*]\s*{NUM}\s*[x*]\s*{NUM}\s*(?:mm)?[^。；,;]{{0,16}}(?:底板|基板|base\s*plate)",
        ]
        for p in patterns:
            m = re.search(p, text, re.I)
            if m:
                a, b, c = map(float, m.groups())
                return BasePlate(length=a, width=b, thickness=c)
        return None

    def _parse_web(self, text: str) -> WebPlate | None:
        # Preferred grammar: 宽60mm、厚10mm、高50mm的支撑板
        obj = r"(?:竖板|支撑板|腹板|web(?:\s*plate)?)"
        window_patterns = [
            rf"(?:宽\s*{NUM}\s*(?:mm)?[^。；,;]{{0,20}}厚\s*{NUM}\s*(?:mm)?[^。；,;]{{0,20}}高\s*{NUM})[^。；,;]{{0,20}}{obj}",
            rf"{obj}[^。；,;]{{0,35}}宽\s*{NUM}[^。；,;]{{0,20}}厚\s*{NUM}[^。；,;]{{0,20}}高\s*{NUM}",
            rf"web(?:\s*plate)?[^\d]{{0,12}}{NUM}\s*[x*]\s*{NUM}\s*[x*]\s*{NUM}",
        ]
        for i, p in enumerate(window_patterns):
            m = re.search(p, text, re.I)
            if m:
                w, t, h = map(float, m.groups())
                return WebPlate(width=w, thickness=t, height=h, centered_on_base=True)
        return None

    def _parse_holes(self, text: str, has_web: bool) -> list[Hole]:
        holes: list[Hole] = []
        for m in re.finditer(rf"(?:Ø|φ|直径\s*)\s*{NUM}\s*(?:mm)?[^。；,;]{{0,30}}(?:通孔|孔|hole)", text, re.I):
            d = float(m.group(1))
            context = text[max(0, m.start()-35):m.end()+35]
            target = "web" if has_web and re.search(r"(?:竖板|支撑板|腹板|web)", context, re.I) else "base"
            centered = bool(re.search(r"(?:中间|中心|居中|center)", context, re.I))
            x = self._coord(context, "x")
            y = self._coord(context, "y")
            z = self._coord(context, "z")
            holes.append(Hole(
                diameter=d, target=target, through=True,
                centered_on_target=centered, x=x, y=y, z=z
            ))
        # English diameter after 'hole': through hole diameter 20
        if not holes:
            for m in re.finditer(rf"(?:through\s*)?hole[^\d]{{0,16}}(?:diameter\s*)?{NUM}", text, re.I):
                context = text[max(0, m.start()-35):m.end()+35]
                target = "web" if has_web and re.search(r"web", context, re.I) else "base"
                centered = bool(re.search(r"(?:center|middle)", context, re.I))
                holes.append(Hole(
                    diameter=float(m.group(1)), target=target, through=True,
                    centered_on_target=centered,
                    x=self._coord(context, "x"), y=self._coord(context, "y"), z=self._coord(context, "z")
                ))
        return holes

    @staticmethod
    def _coord(text: str, axis: str) -> float | None:
        m = re.search(rf"\b{axis}\s*=\s*(-?\d+(?:\.\d+)?)", text, re.I)
        return float(m.group(1)) if m else None

    def _parse_slots(self, text: str) -> list[Slot]:
        slots = []
        p = rf"(?:槽|slot)[^\d]{{0,15}}(?:长\s*)?{NUM}\s*(?:mm)?[^\d]{{0,12}}(?:宽\s*)?{NUM}"
        for m in re.finditer(p, text, re.I):
            slots.append(Slot(length=float(m.group(1)), width=float(m.group(2))))
        return slots


class OpenAICompatibleIntentParser(IntentParser):
    """Optional LLM parser using an OpenAI-compatible chat-completions endpoint.

    Environment variables:
      LLM_BASE_URL  e.g. https://api.example.com/v1
      LLM_API_KEY
      LLM_MODEL
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "")
        if not self.base_url or not self.model:
            raise ValueError("LLM_BASE_URL and LLM_MODEL are required for --parser llm")

    def parse(self, text: str) -> PartIntent:
        try:
            import httpx
        except ImportError as e:
            raise RuntimeError("Install optional dependency: pip install -e '.[llm]'") from e

        schema = PartIntent.model_json_schema()
        system = (
            "You convert mechanical-part natural language into a strict engineering intent JSON. "
            "Do not invent dimensions when they are absent. This MVP supports one rectangular base plate, "
            "an optional centered vertical web plate, through/blind circular holes, and base slots. "
            "Return JSON only and conform to the supplied JSON schema. Put unsupported requests into unsupported_requests."
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system + "\nJSON Schema:\n" + json.dumps(schema, ensure_ascii=False)},
                {"role": "user", "content": text},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        r = httpx.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=90)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        return PartIntent.model_validate_json(content)
