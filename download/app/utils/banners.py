from flet import Colors
from typing import List
from app.models import BannerInfo

BANNERS: List[BannerInfo] = [
    BannerInfo(
        title = 'Support PyCon 2025!',
        description = "Become an official partner with PyTogo Store.",
        image = 'banners/1.png',
        color = Colors.AMBER_900
    ),
    BannerInfo(
        title = 'Opportunity for Sponsors !',
        description = 'Associate your brand with our exclusive products.',
        image = 'banners/2.png',
        color = Colors.BLUE_800
    ),
    BannerInfo(
        title = 'Visibility with PyCon 2025',
        description = "Sponsor the event and maximize your visibility.",
        image = 'banners/3.png',
        color = Colors.TEAL_800
    ),
    BannerInfo(
        title = 'PyCon 2025: Perfect Showcase !',
        description = "Associate your brand and benefit from maximum exposure.",
        image = 'banners/4.png',
        color = Colors.ORANGE_900
    ),
    BannerInfo(
        title = 'PyCon 2025: Ideal Partner !',
        description = "Turnkey solutions to maximize your presence.",
        image = 'banners/6.png',
        color = Colors.RED_800
    ),
]