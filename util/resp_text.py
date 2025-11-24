def _resp_text(resp) -> str:
    try:
        return resp.output_text
    except Exception:
        pass

    try:
        # fallback (responses API 구조)
        # resp.output[0].content[0].text.value
        return resp.output[0].content[0].text.value
    except Exception:
        pass

    # 최후 fallback
    return str(resp)
