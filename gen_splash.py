"""splash.png placeholder 생성 — 단색 흰 배경.

PyInstaller `--splash` 옵션이 PNG 파일을 요구하므로, 디자인 작업 없이
580x120 흰 배경 placeholder 를 한 번 만든다. 모든 텍스트(BDT 로딩 단계)는
런타임에 `pyi_splash.update_text(...)` 로 표시되므로 이미지에는 글자가 없다.

Pillow 가 설치돼 있어야 함. build_exe_onepath.bat 가 splash.png 부재 시 자동 호출.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    out = Path(__file__).resolve().parent / "splash.png"
    img = Image.new("RGB", (580, 120), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 579, 119), outline=(180, 188, 200), width=1)
    try:
        font = ImageFont.truetype("malgun.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    draw.text((24, 44), "BatteryDataTool", fill=(40, 50, 70), font=font)
    img.save(out, format="PNG")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
