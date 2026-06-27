from __future__ import annotations

import base64
import re
from pathlib import Path

from blog_admin.core.path_security import decode_path

from .repository import AssetRepository


class ImageNamingService:
    def __init__(self, repository: AssetRepository) -> None:
        self.repository = repository

    def get_next_image_number(self, article_path: str) -> int:
        asset_folder = self.repository.resolve_asset_folder(article_path)
        if not asset_folder.exists():
            return 1

        max_num = 0
        for path in asset_folder.iterdir():
            if not path.is_file():
                continue
            match = re.search(r"img(\d+)", path.name, flags=re.IGNORECASE)
            if match:
                max_num = max(max_num, int(match.group(1)))
        return max_num + 1

    def build_image_name(self, article_path: str, image_ext: str) -> str:
        next_num = self.get_next_image_number(article_path)
        article_name = Path(decode_path(article_path).replace("\\", "/")).stem
        return f"{article_name}-img{next_num}{image_ext}"

    @staticmethod
    def decode_image_data(image_data: str) -> bytes:
        b64_data = re.sub(r"^data:image/[-+.\w]+;base64,", "", image_data.strip(), flags=re.IGNORECASE)
        return base64.b64decode(b64_data)
