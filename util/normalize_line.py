import re

def normalize_broken_lines(text: str) -> str:
    # 1) 개행 통일
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2) 줄 단위로 쪼개고 양쪽 공백 제거
    lines = [line.strip() for line in text.split("\n")]

    paragraphs = []
    buf = []

    for line in lines:
        if not line:
            # 빈 줄이면 문단 끊기
            if buf:
                paragraphs.append(" ".join(buf))
                buf = []
        else:
            buf.append(line)

    if buf:
        paragraphs.append(" ".join(buf))

    # 3) 문단 내부 중복 공백 정리
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in paragraphs]

    # 4) 문단 사이에는 '\n\n' 유지 (청킹에서 문단 단위로 자를 때 사용 가능)
    return "\n\n".join(paragraphs)

def merge_broken_sentences(text: str) -> str:
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    merged = []
    buf = ""

    def is_sentence_end(line):
        return bool(re.search(r'[.!?…]$', line))

    def is_new_paragraph(line):
        # 숫자/소제목 등 새로운 블록 시작 감지
        return bool(re.match(r'^(\(?\d+[\).]?|[가-힣]\.)', line))

    for line in lines:
        if not buf:
            buf = line
            continue

        # 붙이는 조건
        if (not is_sentence_end(buf)) and (not is_new_paragraph(line)):
            # 공백 한 칸 두고 붙이기
            buf += " " + line
        else:
            merged.append(buf)
            buf = line

    if buf:
        merged.append(buf)

    # 내부 공백 정리
    merged = [re.sub(r'\s+', ' ', m).strip() for m in merged]
    return "\n\n".join(merged)
