from pathlib import Path

from PIL import Image


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    png_path = project_root / "assets" / "icons" / "PrimalLogo.png"
    ico_path = project_root / "assets" / "icons" / "PrimalLogo.ico"

    if not png_path.exists():
        raise FileNotFoundError(f"No se encontro el logo PNG: {png_path}")

    with Image.open(png_path) as img:
        img.save(
            ico_path,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )

    print(f"ICO generado en: {ico_path}")


if __name__ == "__main__":
    main()
