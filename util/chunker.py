import re
from typing import List, Dict, Iterable, Optional


class Chunker:
    """
    공지/문서용 청킹 유틸리티.

    규칙:
      0) 내부 마커([IMAGE OCR], [OCR_ERROR] 등) 제거
      1) 문단(\n\n) 기준 1차 분할
      2) 문단 내부에서 '숫자 항목(1. 2) ① ② ...)' 시작 지점 기준 2차 분할
      3) 토큰 한도 초과 시 슬라이딩 윈도우로 쪼개기(오버랩 적용)
      4) 너무 짧은 조각은 이전과 병합
      5) 각 청크의 임베딩 텍스트는 [TITLE] 프리픽스 포함

    반환: [{"chunk_index", "raw", "embed"} ...]
    """

    def __init__(
        self,
        max_tokens: int = 600,      # 대략 토큰 한도(문자→토큰 근사)
        overlap_tokens: int = 80,   # 문맥 유지를 위한 오버랩
        min_tokens: int = 120,      # 너무 짧은 덩어리 병합 임계
        markers_to_strip: Optional[Iterable[str]] = None,
    ) -> None:
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.min_tokens = min_tokens
        # 청킹에서 제거할 내부 마커들
        self.markers_to_strip = set(markers_to_strip or [
            "[IMAGE OCR]",
            "[OCR_ERROR]",
        ])

        # 숫자/항목 시작 패턴들: "1. ", "2) ", "① ", "⑩ ", "Ⅰ.", "iv)" 등
        self.NUM_BULLET = r'(?:\d{1,3}[\.\)]|[①-⑳]|[Ⅰ-Ⅹ]|[ivx]{1,5}[\.\)])'
        self.item_splitter = re.compile(rf'\n(?=\s*{self.NUM_BULLET}\s+)')

    # ====== public API ======

    def chunk(self, title: str, text: str) -> List[Dict]:
        """외부에서 호출하는 메인 청킹 함수"""
        cleaned_text = self._strip_internal_markers(text or "")

        # 1) 문단 기준 → 빈 줄 2개 이상을 기준으로 split
        paragraphs = [
            p.strip()
            for p in re.split(r'\n{2,}', cleaned_text)
            if p.strip()
        ]

        # 2) 문단 내부에서 숫자 항목 기준 세분화
        units: List[str] = []
        for para in paragraphs:
            units.extend(self._split_paragraph(para))

        # 3) 토큰 한도 강제 (슬라이딩 윈도우)
        units = self._enforce_limit(units)

        # 4) 너무 짧은 조각 병합
        merged = self._merge_short_units(units)

        # 5) 결과 조립
        results: List[Dict] = []
        for idx, raw in enumerate(merged):
            embed = f"[TITLE] {title}\n[CHUNK] {raw}"
            results.append(
                {
                    "chunk_index": idx,
                    "raw": raw,    # UI 노출/하이라이트용
                    "embed": embed # 임베딩/검색용
                }
            )
        return results

    # ====== internal helpers ======

    @staticmethod
    def _est_tokens(s: str) -> int:
        """
        아주 러프한 토큰 근사:
        - 한글/영문 섞인 문서 기준 문자 1개 ≈ 0.5~1.0 토큰 → 보수적으로 // 2
        """
        return max(1, len(s) // 2)

    def _strip_internal_markers(self, s: str) -> str:
        """
        [IMAGE OCR], [OCR_ERROR] 같은 내부 마커만 제거.
        OCR 텍스트 내용은 그대로 유지.
        """
        cleaned_lines = []
        for line in s.splitlines():
            stripped = line.strip()
            if stripped in self.markers_to_strip:
                # 이 줄은 청킹/임베딩에 쓸 필요 없음
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    def _split_paragraph(self, p: str) -> List[str]:
        """
        문단 내부에 숫자/항목이 있으면 항목 단위로 분리,
        없으면 문단 그대로 반환.
        """
        if re.search(rf'^\s*{self.NUM_BULLET}\s+', p, re.MULTILINE):
            parts = re.split(self.item_splitter, p.strip())
            return [s.strip() for s in parts if s.strip()]
        return [p.strip()]

    def _enforce_limit(self, chunks: List[str]) -> List[str]:
        """
        max_tokens 기준으로 초과하는 덩어리는
        문자 기반 슬라이딩 윈도우로 잘라내기.
        """
        out: List[str] = []
        for c in chunks:
            t = self._est_tokens(c)
            if t <= self.max_tokens:
                out.append(c)
                continue

            # 문자 길이 ↔ 토큰 수 근사 비율
            ratio = len(c) / t
            win_chars = int(self.max_tokens * ratio)
            step_chars = int(max(1, (self.max_tokens - self.overlap_tokens) * ratio))

            for i in range(0, len(c), step_chars):
                seg = c[i:i + win_chars].strip()
                if seg:
                    out.append(seg)
        return out

    def _merge_short_units(self, units: List[str]) -> List[str]:
        """
        min_tokens 이하로 너무 짧은 조각은 이전 조각과 병합.
        """
        merged: List[str] = []
        buf = ""

        for u in units:
            if not buf:
                buf = u
                continue

            if self._est_tokens(buf) < self.min_tokens:
                buf = (buf + "\n\n" + u).strip()
            else:
                merged.append(buf)
                buf = u

        if buf:
            merged.append(buf)

        return merged
